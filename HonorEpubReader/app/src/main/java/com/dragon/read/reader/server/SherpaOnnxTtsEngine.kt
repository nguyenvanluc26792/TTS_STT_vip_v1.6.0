package com.dragon.read.reader.server

import android.content.Context
import android.util.Log
import com.k2fsa.sherpa.onnx.OfflineTts
import com.k2fsa.sherpa.onnx.OfflineTtsConfig
import com.k2fsa.sherpa.onnx.OfflineTtsModelConfig
import com.k2fsa.sherpa.onnx.OfflineTtsVitsModelConfig
import com.k2fsa.sherpa.onnx.OfflineTtsKokoroModelConfig
import org.json.JSONObject
import java.io.ByteArrayOutputStream
import java.io.File
import java.io.FileOutputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.concurrent.ConcurrentHashMap
import java.util.zip.ZipInputStream
import kotlin.math.abs
import kotlin.math.cos
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sqrt

/**
 * Động cơ tổng hợp giọng nói Neural Sherpa-ONNX (.onnx Piper VITS / VieNeu-TTS)
 * chạy trực tiếp 100% Offline trên thiết bị Android.
 */
object SherpaOnnxTtsEngine {
    private const val TAG = "SherpaOnnxTtsEngine"
    private val engineLock = Any()
    private val loadedEngines = ConcurrentHashMap<String, OfflineTts>()
    @Volatile
    private var espeakDataDirPath: String? = null

    /**
     * Giải nén espeak-ng-data.zip từ assets ra bộ nhớ trong của ứng dụng (chỉ chạy 1 lần đầu tiên).
     */
    @Synchronized
    fun ensureEspeakDataExtracted(context: Context): String {
        espeakDataDirPath?.let { existing ->
            if (File(existing, "phontab").exists()) return existing
        }

        val piperRoot = File(context.filesDir, "piper_offline_tts").apply { mkdirs() }
        val targetEspeakDir = File(piperRoot, "espeak-ng-data")
        val phontabFile = File(targetEspeakDir, "phontab")

        // 1. Tự động giải nén model .onnx gốc tích hợp trong assets (nếu có trong Full APK)
        try {
            val assetModels = listOf("vieneu_v3_turbo.onnx", "vieneu_v3_turbo.onnx.json")
            for (mName in assetModels) {
                val targetModelFile = File(piperRoot, mName)
                if (!targetModelFile.exists() || targetModelFile.length() < 1000) {
                    try {
                        context.assets.open(mName).use { input ->
                            FileOutputStream(targetModelFile).use { output ->
                                input.copyTo(output)
                            }
                        }
                        Log.i(TAG, "Đã giải nén asset model vào máy: " + mName + " (" + targetModelFile.length() + " bytes)")
                    } catch (_: Exception) {}
                }
            }
        } catch (e: Exception) {
            Log.w(TAG, "Không tìm thấy asset model để trích xuất: " + e.message)
        }

        if (!phontabFile.exists()) {
            Log.i(TAG, "Đang giải nén espeak-ng-data.zip từ APK assets...")
            try {
                context.assets.open("espeak-ng-data.zip").use { rawIn ->
                    ZipInputStream(rawIn).use { zis ->
                        var entry = zis.nextEntry
                        val buffer = ByteArray(32 * 1024)
                        while (entry != null) {
                            val relName = entry.name.replace('\\', '/')
                            val outFile = if (relName.startsWith("espeak-ng-data/")) {
                                File(piperRoot, relName)
                            } else {
                                File(targetEspeakDir, relName)
                            }
                            if (entry.isDirectory) {
                                outFile.mkdirs()
                            } else {
                                outFile.parentFile?.mkdirs()
                                FileOutputStream(outFile).use { fos ->
                                    var len: Int
                                    while (zis.read(buffer).also { len = it } > 0) {
                                        fos.write(buffer, 0, len)
                                    }
                                }
                            }
                            zis.closeEntry()
                            entry = zis.nextEntry
                        }
                    }
                }
                Log.i(TAG, "✅ Đã giải nén xong espeak-ng-data tại: ${targetEspeakDir.absolutePath}")
            } catch (e: Exception) {
                Log.e(TAG, "Lỗi giải nén espeak-ng-data.zip: ${e.message}", e)
            }
        }

        val defaultTokensFile = File(piperRoot, "default_tokens.txt")
        if (!defaultTokensFile.exists()) {
            try {
                context.assets.open("default_tokens.txt").use { input ->
                    defaultTokensFile.outputStream().use { output ->
                        input.copyTo(output)
                    }
                }
            } catch (e: Exception) {
                Log.w(TAG, "Không thể chép default_tokens.txt: ${e.message}")
            }
        }

        espeakDataDirPath = targetEspeakDir.absolutePath
        return targetEspeakDir.absolutePath
    }

    private data class ModelConfigParams(
        val tokensPath: String,
        val noiseScale: Float,
        val noiseW: Float,
        val lengthScale: Float
    )

    /**
     * Chuẩn bị file .tokens.txt cho model .onnx:
     * Ưu tiên chép bảng mã âm vị chuẩn từ APK assets (Mai Linh 154 tokens, VieNeu Turbo 166 tokens, VieNeu Nano 166 tokens),
     * chỉ sinh từ .onnx.json khi là model tuỳ biến ngoài, đảm bảo ghi nguyên tử và không bao giờ ghi đè khi đã hợp lệ.
     */
    private fun prepareModelTokensAndConfig(context: Context, onnxFile: File): ModelConfigParams {
        val piperRoot = File(context.filesDir, "piper_offline_tts").apply { mkdirs() }
        val fileName = onnxFile.name
        val customTokensFile = File(piperRoot, "$fileName.tokens.txt")

        // 1. Nếu file tokens đã tồn tại và hợp lệ (> 500 bytes), dùng luôn không ghi lại
        if (customTokensFile.exists() && customTokensFile.length() > 500) {
            return ModelConfigParams(customTokensFile.absolutePath, 0.667f, 0.8f, 1.0f)
        }

        // 2. Chép từ assets đã đóng gói sẵn trong APK (Chuẩn 100% không bao giờ lỗi bảng mã)
        val assetTokenCandidate = when {
            fileName.contains("mailinh", true) -> "mailinh250626.onnx.tokens.txt"
            fileName.contains("turbo", true) || fileName.contains("diemdam", true) -> "vieneu_v3_turbo.onnx.tokens.txt"
            fileName.contains("nano", true) || fileName.contains("altotram", true) -> "vieneu_v3_nano.onnx.tokens.txt"
            else -> null
        }
        if (assetTokenCandidate != null) {
            try {
                context.assets.open(assetTokenCandidate).use { input ->
                    val tmpTokens = File(piperRoot, "$fileName.tokens.tmp")
                    tmpTokens.outputStream().use { output -> input.copyTo(output) }
                    tmpTokens.renameTo(customTokensFile)
                }
                if (customTokensFile.exists() && customTokensFile.length() > 500) {
                    return ModelConfigParams(customTokensFile.absolutePath, 0.667f, 0.8f, 1.0f)
                }
            } catch (e: Exception) {
                Log.w(TAG, "Lỗi nạp asset tokens $assetTokenCandidate: ${e.message}")
            }
        }

        // 3. Fallback: Nếu là model tuỳ biến ngoài, sinh từ file .onnx.json (sắp xếp ID tăng dần và ghi nguyên tử)
        var jsonText: String? = null
        val diskJson = File(onnxFile.parentFile, "$fileName.json")
        if (diskJson.exists() && diskJson.length() > 100) {
            try {
                jsonText = diskJson.readText(Charsets.UTF_8)
            } catch (_: Exception) {}
        }

        if (jsonText == null) {
            val assetCandidates = listOf(
                "$fileName.json",
                when {
                    fileName.contains("mailinh", true) -> "mailinh250626.onnx.json"
                    fileName.contains("turbo", true) || fileName.contains("diemdam", true) -> "vieneu_v3_turbo.onnx.json"
                    fileName.contains("nano", true) || fileName.contains("altotram", true) -> "vieneu_v3_nano.onnx.json"
                    fileName.contains("banmai", true) -> "banmai.onnx.json"
                    fileName.contains("ngochuyen", true) -> "ngochuyen.onnx.json"
                    else -> "mailinh250626.onnx.json"
                }
            )
            for (assetName in assetCandidates) {
                try {
                    context.assets.open(assetName).use { stream ->
                        jsonText = stream.bufferedReader(Charsets.UTF_8).readText()
                    }
                    if (!jsonText.isNullOrEmpty()) break
                } catch (_: Exception) {}
            }
        }

        var noiseScale = 0.667f
        var noiseW = 0.8f
        var lengthScale = 1.15f

        if (!jsonText.isNullOrEmpty()) {
            try {
                val root = JSONObject(jsonText!!)
                val inf = root.optJSONObject("inference")
                if (inf != null) {
                    noiseScale = inf.optDouble("noise_scale", 0.667).toFloat()
                    noiseW = inf.optDouble("noise_w", 0.8).toFloat()
                    lengthScale = inf.optDouble("length_scale", 1.15).toFloat()
                }
                val pmap = root.optJSONObject("phoneme_id_map")
                if (pmap != null) {
                    val list = mutableListOf<Pair<String, Int>>()
                    val keys = pmap.keys()
                    while (keys.hasNext()) {
                        val sym = keys.next()
                        if (sym.codePointCount(0, sym.length) != 1) continue
                        val arr = pmap.optJSONArray(sym)
                        if (arr != null && arr.length() > 0) {
                            val id = arr.optInt(0, -1)
                            if (id >= 0) {
                                list.add(Pair(sym, id))
                            }
                        }
                    }
                    list.sortBy { it.second }
                    val sb = StringBuilder()
                    for ((sym, id) in list) {
                        sb.append(sym).append(' ').append(id).append('\n')
                    }
                    if (sb.isNotEmpty()) {
                        val tmpTokens = File(piperRoot, "$fileName.tokens.tmp")
                        tmpTokens.writeText(sb.toString(), Charsets.UTF_8)
                        tmpTokens.renameTo(customTokensFile)
                        return ModelConfigParams(customTokensFile.absolutePath, noiseScale, noiseW, lengthScale)
                    }
                }
            } catch (e: Exception) {
                Log.w(TAG, "Lỗi phân tích .onnx.json cho $fileName: ${e.message}")
            }
        }

        val fallbackTokens = File(piperRoot, "default_tokens.txt")
        return ModelConfigParams(fallbackTokens.absolutePath, noiseScale, noiseW, lengthScale)
    }

    private fun getNativePtr(tts: OfflineTts): Long {
        return try {
            val f = OfflineTts::class.java.getDeclaredField("ptr").apply { isAccessible = true }
            f.getLong(tts)
        } catch (_: Throwable) { -1L }
    }

    private fun getOrLoadEngine(context: Context, onnxFile: File): OfflineTts? {
        if (!onnxFile.exists() || onnxFile.length() < 10 * 1024 * 1024) return null
        val key = "${onnxFile.absolutePath}:${onnxFile.length()}"

        loadedEngines[key]?.let { engine ->
            if (getNativePtr(engine) != 0L) return engine
            loadedEngines.remove(key)
        }

        return try {
            val dataDir = ensureEspeakDataExtracted(context)
            val params = prepareModelTokensAndConfig(context, onnxFile)

            // Giải phóng model cũ trước khi nạp model mới để tránh OOM trên Android
            val keysToRelease = loadedEngines.keys().toList()
            for (k in keysToRelease) {
                loadedEngines.remove(k)?.let { old ->
                    try { old.release() } catch (_: Throwable) {}
                }
            }
            System.gc()

            val isKokoro = onnxFile.name.contains("kokoro", ignoreCase = true)
            val modelConfig = OfflineTtsModelConfig().apply {
                if (isKokoro) {
                    val modelDir = onnxFile.parentFile ?: File(context.filesDir, "piper_offline_tts")
                    val voicesBin = File(modelDir, "voices.bin")
                    val tokensFile = File(modelDir, "tokens.txt")
                    val lexiconFile = File(modelDir, "lexicon-vi.txt")
                    val kokoroConfig = OfflineTtsKokoroModelConfig(
                        model = onnxFile.absolutePath,
                        voices = voicesBin.absolutePath,
                        tokens = tokensFile.absolutePath,
                        dataDir = dataDir,
                        lexicon = if (lexiconFile.exists()) lexiconFile.absolutePath else "",
                        lengthScale = params.lengthScale
                    )
                    kokoro = kokoroConfig
                } else {
                    val vitsConfig = OfflineTtsVitsModelConfig(
                        model = onnxFile.absolutePath,
                        lexicon = "",
                        tokens = params.tokensPath,
                        dataDir = dataDir,
                        dictDir = "",
                        noiseScale = params.noiseScale,
                        noiseScaleW = params.noiseW,
                        lengthScale = params.lengthScale
                    )
                    vits = vitsConfig
                }
                numThreads = 2 // 2 luồng tối ưu mượt mà và an toàn tuyệt đối trên Android
                debug = false
                provider = "cpu"
            }
            val ttsConfig = OfflineTtsConfig().apply {
                model = modelConfig
                maxNumSentences = 1
            }

            Log.i(TAG, "Đang khởi tạo Sherpa-ONNX Native Engine cho model: ${onnxFile.name} (${onnxFile.length()} bytes)")
            val engine = OfflineTts(assetManager = null, config = ttsConfig)
            val ptr = getNativePtr(engine)
            if (ptr == 0L) {
                Log.e(TAG, "❌ Sherpa-ONNX native initialization failed (ptr == 0) for ${onnxFile.name}")
                return null
            }

            loadedEngines[key] = engine
            try {
                Log.i(TAG, "✅ Khởi tạo thành công Sherpa-ONNX Native Engine (${onnxFile.name}, SR=${engine.sampleRate()})")
            } catch (_: Throwable) {}
            engine
        } catch (t: Throwable) {
            Log.e(TAG, "Lỗi khởi tạo Sherpa-ONNX cho ${onnxFile.name}: ${t.message}", t)
            null
        }
    }

    /**
     * Làm mượt biên âm thanh tự nhiên bằng đường dốc cosine nhẹ nhàng:
     * - Giữ đệm đuôi hào phóng 120ms (hoặc 180ms với câu ngập ngừng) để tuyệt đối không cắt cụt đuôi chữ, âm gió hay tiếng thở.
     * - Fade out 25ms siêu mịn màng, loại bỏ hoàn toàn mọi tiếng lách cách (click/pop) hoặc rè rè cuối câu.
     */
    private fun applySmoothFadeAndTrim(samples: FloatArray, sampleRate: Int, fadeMs: Int = 25, isTrailing: Boolean = false): FloatArray {
        if (samples.size < 64) return samples
        var firstIdx = 0
        var lastIdx = samples.size - 1
        val threshold = 0.001f

        while (firstIdx < samples.size && abs(samples[firstIdx]) <= threshold) firstIdx++
        while (lastIdx > firstIdx && abs(samples[lastIdx]) <= threshold) lastIdx--

        val padStart = (sampleRate * 0.020f).toInt()
        val padEnd = (sampleRate * (if (isTrailing) 0.180f else 0.120f)).toInt()
        val start = max(0, firstIdx - padStart)
        val end = min(samples.size, lastIdx + padEnd + 1)
        val trimmed = if (end > start) samples.copyOfRange(start, end) else samples.copyOf()

        val fadeLen = min((sampleRate * (fadeMs / 1000.0f)).toInt(), trimmed.size / 4)
        if (fadeLen > 4) {
            for (i in 0 until fadeLen) {
                val ratio = i.toDouble() / fadeLen.toDouble()
                val fadeIn = (0.5 * (1.0 - cos(Math.PI * ratio))).toFloat()
                val fadeOut = (0.5 * (1.0 + cos(Math.PI * ratio))).toFloat()
                trimmed[i] *= fadeIn
                trimmed[trimmed.size - fadeLen + i] *= fadeOut
            }
        }
        return trimmed
    }

    /**
     * Đóng gói mảng FloatArray [-1.0..1.0] thành định dạng chuẩn RIFF WAVE 16-bit PCM Mono.
     */
    private fun encodePcm16Wav(samples: FloatArray, sampleRate: Int): ByteArray {
        val dataSize = samples.size * 2
        val totalSize = 36 + dataSize
        val buffer = ByteBuffer.allocate(44 + dataSize).order(ByteOrder.LITTLE_ENDIAN)

        // RIFF header
        buffer.put("RIFF".toByteArray(Charsets.US_ASCII))
        buffer.putInt(totalSize)
        buffer.put("WAVE".toByteArray(Charsets.US_ASCII))

        // fmt subchunk
        buffer.put("fmt ".toByteArray(Charsets.US_ASCII))
        buffer.putInt(16) // PCM chunk size
        buffer.putShort(1.toShort()) // AudioFormat = 1 (PCM)
        buffer.putShort(1.toShort()) // NumChannels = 1 (Mono)
        buffer.putInt(sampleRate)
        buffer.putInt(sampleRate * 2) // ByteRate
        buffer.putShort(2.toShort()) // BlockAlign
        buffer.putShort(16.toShort()) // BitsPerSample

        // data subchunk
        buffer.put("data".toByteArray(Charsets.US_ASCII))
        buffer.putInt(dataSize)

        // BẢO TỒN ĐỘ TRONG TRẺO NGUYÊN BẢN (CRYSTAL CLEAR LINEAR PEAK 0.84):
        // Dùng chuẩn hóa đỉnh tuyến tính giống hệt các file mẫu Master
        // Tuyệt đối không can thiệp dải nén (knee compression) để âm sắc trong vắt, không rè, không đục
        var maxPeak = 0.0001f
        for (s in samples) {
            val a = abs(s)
            if (a > maxPeak) maxPeak = a
        }
        val targetPeak = 0.84f
        val scale = if (maxPeak > 1e-4f) (targetPeak / maxPeak) else 1.0f

        for (s in samples) {
            val finalSample = max(-0.98f, min(0.98f, s * scale))
            val pcmVal = (finalSample * 32767.0f).toInt().toShort()
            buffer.putShort(pcmVal)
        }
        return buffer.array()
    }

    /**
     * Biến đổi cao độ (Pitch Shift) & nhịp điệu (Formant/Speed) mượt mà bằng DSP:
     * - semitones: Số bán cung tăng/giảm (-3.5 = Ông lão, -2.8 = Bà lão, +4.5 = Bé trai, +5.0 = Bé gái)
     * - speedFactor: Tỉ lệ tốc độ (0.88 = Chậm rãi người già, 1.15 - 1.18 = Líu lo trẻ con)
     */
    fun applyDspPitchAndSpeed(samples: FloatArray, sampleRate: Int, semitones: Float, speedFactor: Float): FloatArray {
        if (samples.isEmpty() || (semitones == 0f && speedFactor == 1f)) return samples
        var result = samples

        // 1. Pitch shift qua resampling + linear interpolation
        if (semitones != 0f) {
            val factor = Math.pow(2.0, semitones / 12.0).toFloat()
            val newLen = (result.size / factor).toInt().coerceAtLeast(1)
            val resampled = FloatArray(newLen)
            for (i in 0 until newLen) {
                val origPos = i * factor
                val idx0 = origPos.toInt().coerceIn(0, result.size - 1)
                val idx1 = (idx0 + 1).coerceIn(0, result.size - 1)
                val frac = origPos - idx0
                resampled[i] = (1f - frac) * result[idx0] + frac * result[idx1]
            }

            // Kéo giãn thời gian trở về độ dài gốc để giữ nguyên tốc độ khi chỉ đổi pitch
            val stretched = FloatArray(result.size)
            val scale = (newLen - 1).toFloat() / (result.size - 1).coerceAtLeast(1)
            for (i in 0 until result.size) {
                val pos = i * scale
                val idx0 = pos.toInt().coerceIn(0, newLen - 1)
                val idx1 = (idx0 + 1).coerceIn(0, newLen - 1)
                val frac = pos - idx0
                stretched[i] = (1f - frac) * resampled[idx0] + frac * resampled[idx1]
            }
            result = stretched
        }

        // 2. Speed factor
        if (speedFactor != 1f && speedFactor > 0.2f) {
            val targetLen = (result.size / speedFactor).toInt().coerceAtLeast(1)
            val sped = FloatArray(targetLen)
            val scale = (result.size - 1).toFloat() / (targetLen - 1).coerceAtLeast(1)
            for (i in 0 until targetLen) {
                val pos = i * scale
                val idx0 = pos.toInt().coerceIn(0, result.size - 1)
                val idx1 = (idx0 + 1).coerceIn(0, result.size - 1)
                val frac = pos - idx0
                sped[i] = (1f - frac) * result[idx0] + frac * result[idx1]
            }
            result = sped
        }

        return result
    }

        /**
     * Tổng hợp câu tiếng Việt trực tiếp từ file .onnx trên điện thoại, trả về byte[] WAV sạch 100%.
     * Toàn bộ quá trình nạp và sinh âm thanh được đồng bộ hoá tuyệt đối tránh race condition / crash C++.
     * Hỗ trợ chọn subvoice qua speakerId (sid) và biến đổi độ tuổi (Ông lão, Bà lão, Trẻ em).
     */
    fun synthesizeToWavBytes(
        context: Context,
        onnxFile: File,
        text: String,
        speed: Float = 1.0f,
        emotion: String = "normal",
        speakerId: Int = 0
    ): ByteArray? {
        val cleanText = text.trim()
        if (cleanText.isEmpty()) return null

        val safeSpeed = speed.coerceIn(0.5f, 2.2f)

        val isKokoro = onnxFile.name.contains("kokoro", ignoreCase = true)
        var pitchShift = 0f
        var dspSpeed = 1f
        var modelSid = 0

        if (isKokoro) {
            // Danh sách giọng đa dạng của Kokoro-Vietnamese:
            // 0: Diễm Trinh (Nữ miền Nam), 1: Hưng Thịnh (Nam miền Nam), 2: Mai Linh (Nữ miền Bắc),
            // 3: Mai Loan (Nữ miền Bắc truyền cảm), 4: Mạnh Dũng (Nam miền Bắc), 5: Mỹ Yến (Nữ miền Trung),
            // 6: Ngọc Huyền (Nữ trẻ miền Bắc), 7: Phát Tài (Nam miền Nam), 8: Thành Đạt (Nam miền Bắc),
            // 9: Thục Trinh (Nữ miền Nam), 10: Tuấn Ngọc (Nam miền Bắc ấm), 11: Đức An, 12: Đức Duy,
            // 13: NSƯT Kim Cúc (Giọng đọc truyện đêm khuya huyền thoại)
            when (speakerId) {
                14 -> { modelSid = 13; pitchShift = 0.0f; dspSpeed = 0.95f } // NSƯT Kim Cúc (Đọc truyện đêm khuya)
                0  -> { modelSid = 13; pitchShift = 0.0f; dspSpeed = 0.96f } // Dẫn chuyện mặc định: Kim Cúc
                1  -> { modelSid = 0;  pitchShift = 0.0f; dspSpeed = 1.00f } // Diễm Trinh (Nữ chính)
                2  -> { modelSid = 4;  pitchShift = 0.0f; dspSpeed = 1.00f } // Mạnh Dũng (Nam chính)
                3  -> { modelSid = 6;  pitchShift = 0.0f; dspSpeed = 1.00f } // Ngọc Huyền (Nữ trẻ dịu dàng)
                4  -> { modelSid = 1;  pitchShift = 0.0f; dspSpeed = 1.00f } // Hưng Thịnh (Nam miền Nam)
                5  -> { modelSid = 8;  pitchShift = 0.0f; dspSpeed = 1.00f } // Thành Đạt (Nam trẻ năng động)
                6  -> { modelSid = 10; pitchShift = 0.0f; dspSpeed = 0.98f } // Tuấn Ngọc (Nam trầm ấm)
                7  -> { modelSid = 7;  pitchShift = 0.0f; dspSpeed = 1.00f } // Phát Tài (Nam vui vẻ)
                8  -> { modelSid = 4;  pitchShift = -3.5f; dspSpeed = 0.82f } // Ông lão (Mạnh Dũng hạ pitch)
                9  -> { modelSid = 3;  pitchShift = -2.5f; dspSpeed = 0.90f } // Bà lão (Mai Loan hạ pitch)
                10 -> { modelSid = 6;  pitchShift = 4.2f;  dspSpeed = 1.00f } // Bé trai (Ngọc Huyền nâng pitch)
                11 -> { modelSid = 6;  pitchShift = 5.0f;  dspSpeed = 1.00f } // Bé gái (Ngọc Huyền nâng pitch cao)
                12 -> { modelSid = 2;  pitchShift = 0.0f;  dspSpeed = 1.00f } // Mai Linh
                13 -> { modelSid = 3;  pitchShift = 0.0f;  dspSpeed = 0.96f } // Mai Loan
                else -> { modelSid = speakerId.coerceIn(0, 13); pitchShift = 0f; dspSpeed = 1.00f }
            }
        } else {
            // Tra cứu profile DSP cho Piper VITS
            when (speakerId) {
                0 -> { modelSid = 0; pitchShift = 0.0f;  dspSpeed = 1.00f } // Ngọc Lan (Dẫn truyện - Nữ Bắc)
                1 -> { modelSid = 1; pitchShift = 0.0f;  dspSpeed = 1.00f } // Minh Anh (Nữ chính - Nữ Bắc)
                2 -> { modelSid = 2; pitchShift = 0.0f;  dspSpeed = 1.00f } // Quang Huy (Nam chính - Nam Bắc)
                3 -> { modelSid = 3; pitchShift = 0.0f;  dspSpeed = 1.00f } // Thu Hà (Nữ Bắc dịu dàng)
                4 -> { modelSid = 4; pitchShift = 0.0f;  dspSpeed = 1.00f } // Yến Nhi (Nữ Nam Bộ)
                5 -> { modelSid = 2; pitchShift = 1.2f;  dspSpeed = 1.00f } // Hải Đăng (Nam trẻ)
                6 -> { modelSid = 2; pitchShift = -1.5f; dspSpeed = 1.00f } // Thái Sơn (Nam trầm)
                7 -> { modelSid = 2; pitchShift = 0.6f;  dspSpeed = 1.00f } // Adam (Nam vui vẻ)
                8 -> { modelSid = 2; pitchShift = -3.8f; dspSpeed = 0.82f } // Ông lão (Trầm khàn, chậm rãi)
                9 -> { modelSid = 4; pitchShift = -2.8f; dspSpeed = 0.90f } // Bà lão (Hiền từ, từ tốn)
                10 -> { modelSid = 1; pitchShift = 4.5f; dspSpeed = 1.00f } // Bé trai (Lanh lợi, líu lo)
                11 -> { modelSid = 1; pitchShift = 5.0f; dspSpeed = 1.00f } // Bé gái (Trong trẻo, ngây thơ)
                12 -> { modelSid = 1; pitchShift = 1.2f; dspSpeed = 1.00f } // Bích Giao (Nữ trẻ lanh lợi, trong trẻo - Clone)
                13 -> { modelSid = 0; pitchShift = -0.8f; dspSpeed = 0.96f } // Kim Tuyến (Nữ đọc truyện truyền cảm, ấm áp - Clone)
                14 -> { modelSid = 5; pitchShift = 0.0f;  dspSpeed = 0.94f } // NSƯT Kim Cúc (Đọc Truyện Đêm Khuya VOV - Speaker Độc Lập 5)
                else -> { modelSid = speakerId.coerceIn(0, 5); pitchShift = 0f; dspSpeed = 1.00f }
            }
        }

        // Chuẩn hóa tốc độ VITS duy nhất 1 lần (tránh nhân đôi làm mất ngân ngắt diễn cảm):
        val isTrailing = emotion.equals("trailing", ignoreCase = true) || cleanText.endsWith("…") || cleanText.endsWith("...")
        // VITS phát âm ở nhịp điệu tự nhiên, độ co giãn nhân vật do DSP Time-Stretching đảm nhiệm
        val contextualSpeed = when (emotion.lowercase()) {
            "excited", "angry_shout", "cold_shout" -> (safeSpeed * 1.05f).coerceAtMost(2.2f)
            "trailing", "sad", "pain" -> (safeSpeed * 0.93f).coerceAtLeast(0.5f)
            "question" -> (safeSpeed * 1.02f).coerceAtMost(2.2f)
            else -> safeSpeed
        }

        return synchronized(engineLock) {
            try {
                val engine = getOrLoadEngine(context, onnxFile) ?: return@synchronized null
                if (getNativePtr(engine) == 0L) return@synchronized null

                val generated = engine.generate(text = cleanText, sid = modelSid, speed = contextualSpeed) ?: return@synchronized null
                val rawSamples = generated.samples
                val sr = if (generated.sampleRate > 0) generated.sampleRate else 22050
                if (rawSamples.isEmpty() || sr <= 0) return@synchronized null

                var processedSamples = rawSamples
                // Áp dụng DSP Pitch Shift và Time-Stretching chuyên sâu (ví dụ: ông lão chậm rãi 0.76x)
                if (pitchShift != 0f || dspSpeed != 1f) {
                    processedSamples = applyDspPitchAndSpeed(processedSamples, sr, pitchShift, dspSpeed)
                }

                val smoothSamples = applySmoothFadeAndTrim(processedSamples, sr, fadeMs = 8, isTrailing = isTrailing)
                encodePcm16Wav(smoothSamples, sr)
            } catch (t: Throwable) {
                Log.e(TAG, "Lỗi sinh âm thanh Sherpa-ONNX: ${t.message}", t)
                null
            }
        }
    }
}
