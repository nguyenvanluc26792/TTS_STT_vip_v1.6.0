package com.dragon.read.reader.server

import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.math.BigInteger
import java.security.MessageDigest
import java.security.SecureRandom
import java.util.Base64
import java.util.UUID
import java.util.concurrent.TimeUnit

object CapCutTtsHelper {
    private const val TAG = "CapCutTtsHelper"
    private const val BASE_URL = "https://editor-api-sg.capcutapi.com"
    private const val _AID = "359289"
    private const val _APPVR = "8.7.0"
    private const val _PATH_NEW = "/lv/v1/common_task/new"
    private const val _PATH_QUERY = "/lv/v1/common_task/query"

    private const val _RSA_N_STR = "19341813084631315671282549431798655160825512801013391560750156528444287447892559220236099203022189312996509243483755654291658808631344567184378689327273259390644661930225954596968213035923198083437102535618783415692653811348862243705526699107851690693125596736080099356396803461339216527691309374959691258789927689498378878482554514874089477069000113270337080049670332556471810330214798429795238319101401506608665290167760399585652278886979131868827422701738576086077151453279247167711376399900166201302369203349172030364626191019105037101985688867268590829086107225896220811741526787405362085604352187239844583176859"
    private const val _RSA_E_VAL = 65537L
    private const val DEFAULT_11LABS_RID = "7369525170723099153"

    private val rsaN = BigInteger(_RSA_N_STR)
    private val rsaE = BigInteger.valueOf(_RSA_E_VAL)

    private val client = OkHttpClient.Builder()
        .connectTimeout(6, TimeUnit.SECONDS)
        .readTimeout(8, TimeUnit.SECONDS)
        .build()

    private val secureRandom = SecureRandom()

    private fun logInfo(msg: String) {
        println("[$TAG] $msg")
    }

    private fun logError(msg: String, tr: Throwable? = null) {
        println("[$TAG ERROR] $msg")
        tr?.printStackTrace()
    }

    private fun md5(input: String): String {
        val md = MessageDigest.getInstance("MD5")
        val bytes = md.digest(input.toByteArray(Charsets.UTF_8))
        return bytes.joinToString("") { "%02x".format(it) }
    }

    private fun rsaEncrypt(msg: String): String {
        val m = msg.toByteArray(Charsets.UTF_8)
        val k = (rsaN.bitLength() + 7) / 8
        val psLen = k - m.size - 3
        if (psLen < 8) throw IllegalStateException("Message too long for RSA key")

        val ps = ByteArray(psLen)
        for (i in 0 until psLen) {
            var b: Int
            do {
                b = secureRandom.nextInt(256)
            } while (b == 0)
            ps[i] = b.toByte()
        }

        val goi = ByteArray(k)
        goi[0] = 0x00
        goi[1] = 0x02
        System.arraycopy(ps, 0, goi, 2, psLen)
        goi[2 + psLen] = 0x00
        System.arraycopy(m, 0, goi, 3 + psLen, m.size)

        val mInt = BigInteger(1, goi)
        val c = mInt.modPow(rsaE, rsaN)

        var cBytes = c.toByteArray()
        if (cBytes.size > k) {
            cBytes = cBytes.copyOfRange(cBytes.size - k, cBytes.size)
        } else if (cBytes.size < k) {
            val pad = ByteArray(k)
            System.arraycopy(cBytes, 0, pad, k - cBytes.size, cBytes.size)
            cBytes = pad
        }
        return Base64.getEncoder().encodeToString(cBytes)
    }

    private fun signHeader(path: String, deviceTime: String, tdid: String): String {
        val pathTail = if (path.length >= 7) path.substring(path.length - 7) else path
        val raw = "9e2c|$pathTail|3|$_APPVR|$deviceTime|$tdid|11ac"
        return md5(raw)
    }

    private fun signPayload(ssml: String, extraInfo: String, deviceId: String): String {
        var s = "appid:$_AID&did:$deviceId&creditDisable:false&ssml:${md5(ssml)}"
        if (extraInfo.isNotEmpty()) {
            s += "&extraInfo:$extraInfo"
        }
        return rsaEncrypt(s)
    }

    private fun escapeXml(text: String): String {
        return text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\"", "&quot;")
            .replace("'", "&apos;")
    }

    private fun generateDeviceId(): String {
        val num = (100000000000000000L + (Math.random() * 899999999999999999L).toLong())
        return "7$num".substring(0, 19)
    }

    fun synthesize(text: String, voiceId: String, isElevenLabs: Boolean = false): ByteArray? {
        var cleanText = text.replace(Regex("[\\s\\u00A0\\u1680\\u2000-\\u200A\\u2028\\u2029\\u202F\\u205F\\u3000\\uFEFF—–-]*[,，、﹐][\\s\\u00A0\\u1680\\u2000-\\u200A\\u2028\\u2029\\u202F\\u205F\\u3000\\uFEFF—–-]*(?:…|\\.{3})?"), ", ")
                            .replace(Regex(" {2,}"), " ")
                            .trim()
        if (cleanText.isEmpty()) return null

        val deviceId = generateDeviceId()
        val deviceTime = (System.currentTimeMillis() / 1000).toString()
        val tdid = deviceId

        // CapCut uses platform "sami" and req_key "sami_text_to_speech" for standard voices
        // ElevenLabs uses platform "11labs" or "sami" with rid = DEFAULT_11LABS_RID
        val platform = if (isElevenLabs) "11labs" else "sami"
        val reqKey = "${platform}_text_to_speech"
        val rid = if (isElevenLabs) DEFAULT_11LABS_RID else ""
        val voiceName = if (isElevenLabs) voiceId.replace("eleven_", "").trim() else voiceId

        val escapedText = escapeXml(cleanText)
        val ssml = "<speak version=\"1.0\" xmlns=\"http://www.w3.org/2001/10/synthesis\" xml:lang=\"en-US\">\n" +
                "    <voice name=\"$voiceName\" mock_tone_info=\"\" platform=\"$platform\" resource_id=\"$rid\" emotion=\"\" emotion_scale=\"0\" style=\"\" role=\"\" moyin_emotion=\"\" is_clone_tone=\"false\" need_subtitle_timestamp=\"false\">\n" +
                "        <prosody rate=\"1.0\">$escapedText</prosody>\n" +
                "    </voice>\n" +
                "</speak>"

        val extraInfo = "{\"benefit_info\":{}}"
        val sign = signPayload(ssml, extraInfo, deviceId)
        val babiStr = "{\"feature_entrance\":\"editor\",\"feature_entrance_detail\":\"editor-feature-text_to_speech\",\"feature_key\":\"text_to_speech\",\"scenario\":\"video_editor\"}"

        val payload = JSONObject().apply {
            put("audio_format", "mp3")
            put("babi_param", babiStr)
            put("credit_disable", false)
            put("extra_info", extraInfo)
            put("need_merge_voice", false)
            put("need_subtitle_timestamp", false)
            put("scene", "text_to_speech")
            put("ssml", ssml)
            put("sign", sign)
        }

        val payloadStr = payload.toString().replace("\\/", "/")
        val tasksArray = JSONArray().apply {
            put(JSONObject().apply {
                put("context", UUID.randomUUID().toString())
                put("payload", payloadStr)
                put("req_key", reqKey)
                put("task_version", "v3")
            })
        }

        var newBody = JSONObject().apply {
            put("bind_id", UUID.randomUUID().toString())
            put("can_queue", true)
            put("enter_from", "text_to_speech")
            put("tasks", tasksArray)
        }.toString().replace("\\/", "/")

        val queryParams = "aid=$_AID&app_name=CapCut&appvr=$_APPVR&channel=capcutpc_google&device_brand=Windows&device_id=$deviceId&device_platform=windows&device_type=Windows&iid=$deviceId&os_version=10.0.19045&region=VN&version_code=$_APPVR&version_name=$_APPVR&babi_param=%7B%22feature_entrance%22%3A%22editor%22%2C%22feature_entrance_detail%22%3A%22editor-feature-text_to_speech%22%2C%22feature_key%22%3A%22text_to_speech%22%2C%22scenario%22%3A%22video_editor%22%7D"
        val newUrl = "$BASE_URL$_PATH_NEW?$queryParams"

        val headerSign = signHeader(_PATH_NEW, deviceTime, tdid)

        val newReq = Request.Builder()
            .url(newUrl)
            .addHeader("content-type", "application/json")
            .addHeader("appvr", _APPVR)
            .addHeader("ch", "capcutpc_google")
            .addHeader("device-time", deviceTime)
            .addHeader("lan", "vi-VN")
            .addHeader("loc", "VN")
            .addHeader("pf", "3")
            .addHeader("sign-ver", "1")
            .addHeader("tdid", tdid)
            .addHeader("sign", headerSign)
            .addHeader("appid", _AID)
            .addHeader("x-ss-stub", md5(newBody))
            .addHeader("x-ss-dp", _AID)
            .addHeader("x-khronos", deviceTime)
            .addHeader("user-agent", "Cronet/TTNetVersion:1d7cc3b1 2025-07-16 QuicVersion:52c2b40d 2025-04-03")
            .post(newBody.toRequestBody("application/json; charset=utf-8".toMediaType()))
            .build()

        var taskId = ""
        var token = ""

        try {
            val resp = client.newCall(newReq).execute()
            val respBody = resp.body?.string() ?: ""
            logInfo("Create task response: $respBody")
            val json = JSONObject(respBody)
            val data = json.optJSONObject("data")
            val tasks = data?.optJSONArray("tasks")
            if (tasks != null && tasks.length() > 0) {
                val t = tasks.getJSONObject(0)
                taskId = t.optString("id")
                token = t.optString("token")
            }
        } catch (e: Exception) {
            logError("Lỗi tạo task CapCut/ElevenLabs: ${e.message}", e)
            return null
        }

        if (taskId.isEmpty()) return null

        // Poll query (tối ưu: kiểm tra nhanh 150ms ở 5 vòng đầu cho câu ngắn, sau đó 250ms cho câu dài)
        for (i in 0 until 28) {
            try {
                Thread.sleep(if (i < 5) 150L else 250L)
                val pollTime = (System.currentTimeMillis() / 1000).toString()
                val queryUrl = "$BASE_URL$_PATH_QUERY?app_name=CapCut&device_type=Windows&os_version=10.0.19045&channel=capcutpc_google&version_name=$_APPVR&device_brand=Windows&device_id=$deviceId&iid=$deviceId&version_code=$_APPVR&device_platform=windows&aid=$_AID"

                val qTasks = JSONArray().apply {
                    put(JSONObject().apply {
                        put("bind_id", "")
                        put("id", taskId)
                        put("req_key", reqKey)
                        put("task_version", "v3")
                        put("token", token)
                    })
                }

                val queryBody = JSONObject().apply {
                    put("tasks", qTasks)
                }.toString().replace("\\/", "/")

                val qSign = signHeader(_PATH_QUERY, pollTime, tdid)

                val queryReq = Request.Builder()
                    .url(queryUrl)
                    .addHeader("content-type", "application/json")
                    .addHeader("appvr", _APPVR)
                    .addHeader("ch", "capcutpc_google")
                    .addHeader("device-time", pollTime)
                    .addHeader("lan", "vi-VN")
                    .addHeader("loc", "VN")
                    .addHeader("pf", "3")
                    .addHeader("sign-ver", "1")
                    .addHeader("tdid", tdid)
                    .addHeader("sign", qSign)
                    .addHeader("appid", _AID)
                    .addHeader("x-ss-stub", md5(queryBody))
                    .addHeader("x-ss-dp", _AID)
                    .addHeader("x-khronos", pollTime)
                    .addHeader("user-agent", "Cronet/TTNetVersion:1d7cc3b1 2025-07-16 QuicVersion:52c2b40d 2025-04-03")
                    .post(queryBody.toRequestBody("application/json; charset=utf-8".toMediaType()))
                    .build()

                val qResp = client.newCall(queryReq).execute()
                val qRespStr = qResp.body?.string() ?: ""
                val qJson = JSONObject(qRespStr)
                val qData = qJson.optJSONObject("data")
                val tasks = qData?.optJSONArray("tasks")
                if (tasks != null && tasks.length() > 0) {
                    val taskObj = tasks.getJSONObject(0)
                    val status = taskObj.optString("status")
                    if (status == "succeed" || status == "success" || status == "done") {
                        var audioUrl = ""
                        val payloadStr = taskObj.optString("payload", "")
                        if (payloadStr.isNotEmpty()) {
                            try {
                                val pObj = JSONObject(payloadStr)
                                val subArr = pObj.optJSONArray("audio_subtitles")
                                if (subArr != null && subArr.length() > 0) {
                                    audioUrl = subArr.getJSONObject(0).optString("speech_url", "")
                                }
                                if (audioUrl.isEmpty()) {
                                    audioUrl = pObj.optString("speech_url", "")
                                }
                            } catch (e: Exception) {
                                logError("Lỗi trích xuất speech_url: ${e.message}")
                            }
                        }
                        if (audioUrl.isEmpty()) {
                            audioUrl = taskObj.optString("result_url").ifEmpty { taskObj.optString("audio_url") }
                        }

                        if (audioUrl.isNotEmpty()) {
                            val audioReq = Request.Builder().url(audioUrl).build()
                            val audioResp = client.newCall(audioReq).execute()
                            val audioBytes = audioResp.body?.bytes()
                            if (audioBytes != null && audioBytes.size > 500) {
                                logInfo("Successfully downloaded audio from CapCut: ${audioBytes.size} bytes")
                                return audioBytes
                            }
                        }
                    } else if (status == "failed") {
                        logError("Task failed on server: $qRespStr")
                        break
                    }
                }
            } catch (e: Exception) {
                logError("Polling exception: ${e.message}", e)
            }
        }
        return null
    }
}
