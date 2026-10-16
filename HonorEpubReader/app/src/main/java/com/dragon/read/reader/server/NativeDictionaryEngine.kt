package com.dragon.read.reader.server

import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.util.Log
import com.google.mlkit.common.model.DownloadConditions
import com.google.mlkit.nl.translate.TranslateLanguage
import com.google.mlkit.nl.translate.Translation
import com.google.mlkit.nl.translate.Translator
import com.google.mlkit.nl.translate.TranslatorOptions
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.io.FileOutputStream
import java.net.URLEncoder
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit

class NativeDictionaryEngine(private val context: Context) {
    companion object {
        private const val TAG = "NativeDictEngine"
        private const val DB_NAME = "dict_hh.db"
    }

    private var db: SQLiteDatabase? = null
    private var enToViTranslator: Translator? = null
    private var viToEnTranslator: Translator? = null
    private var isMlKitEnViReady = false
    private var isMlKitViEnReady = false

    private val httpClient = OkHttpClient.Builder()
        .connectTimeout(8, TimeUnit.SECONDS)
        .readTimeout(10, TimeUnit.SECONDS)
        .build()

    init {
        initDatabase()
        initMlKitTranslators()
    }

    private fun initDatabase() {
        try {
            val dbFile = context.getDatabasePath(DB_NAME)
            if (!dbFile.exists() || dbFile.length() < 1000) {
                dbFile.parentFile?.mkdirs()
                context.assets.open(DB_NAME).use { input ->
                    FileOutputStream(dbFile).use { output ->
                        input.copyTo(output)
                    }
                }
                Log.i(TAG, "Đã sao chép dict_hh.db từ assets thành công: ${dbFile.length()} bytes")
            }
            if (dbFile.exists()) {
                db = SQLiteDatabase.openDatabase(dbFile.absolutePath, null, SQLiteDatabase.OPEN_READONLY)
                Log.i(TAG, "Đã mở CSDL SQLite từ điển 132K từ thành công!")
            }
        } catch (e: Exception) {
            Log.e(TAG, "Lỗi nạp database dict_hh.db: ${e.message}")
        }
    }

    private fun initMlKitTranslators() {
        try {
            val enViOptions = TranslatorOptions.Builder()
                .setSourceLanguage(TranslateLanguage.ENGLISH)
                .setTargetLanguage(TranslateLanguage.VIETNAMESE)
                .build()
            enToViTranslator = Translation.getClient(enViOptions)

            val viEnOptions = TranslatorOptions.Builder()
                .setSourceLanguage(TranslateLanguage.VIETNAMESE)
                .setTargetLanguage(TranslateLanguage.ENGLISH)
                .build()
            viToEnTranslator = Translation.getClient(viEnOptions)

            val conditions = DownloadConditions.Builder().build()
            enToViTranslator?.downloadModelIfNeeded(conditions)
                ?.addOnSuccessListener {
                    isMlKitEnViReady = true
                    Log.i(TAG, "Mô hình Google ML Kit Dịch Ngoại Tuyến (Anh -> Việt) đã sẵn sàng!")
                }
                ?.addOnFailureListener { e ->
                    Log.w(TAG, "Chưa tải xong mô hình ML Kit Anh->Việt: ${e.message}")
                }

            viToEnTranslator?.downloadModelIfNeeded(conditions)
                ?.addOnSuccessListener {
                    isMlKitViEnReady = true
                    Log.i(TAG, "Mô hình Google ML Kit Dịch Ngoại Tuyến (Việt -> Anh) đã sẵn sàng!")
                }
        } catch (e: Exception) {
            Log.e(TAG, "Lỗi khởi tạo Google ML Kit Translator: ${e.message}")
        }
    }

    fun lookupWord(word: String): JSONObject? {
        val cleanWord = word.trim()
        if (cleanWord.isEmpty() || db == null) return null

        try {
            val cursor = db?.rawQuery(
                "SELECT word, html, description, pronounce FROM av WHERE word = ? COLLATE NOCASE LIMIT 1",
                arrayOf(cleanWord)
            )
            cursor?.use {
                if (it.moveToFirst()) {
                    val foundWord = it.getString(0) ?: cleanWord
                    val html = it.getString(1) ?: ""
                    val description = it.getString(2) ?: ""
                    val pronounce = it.getString(3) ?: ""

                    return JSONObject().apply {
                        put("found", true)
                        put("word", foundWord)
                        put("html", html)
                        put("description", description)
                        put("pronounce", pronounce)
                    }
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Lỗi tra từ SQLite: ${e.message}")
        }
        return null
    }

    fun translateMlKitOffline(text: String, sourceLang: String = "en", targetLang: String = "vi"): String? {
        val translator = if (sourceLang == "en" && targetLang == "vi") enToViTranslator else viToEnTranslator
        if (translator == null) return null

        val latch = CountDownLatch(1)
        var result: String? = null

        translator.translate(text)
            .addOnSuccessListener { translatedText ->
                result = translatedText
                latch.countDown()
            }
            .addOnFailureListener { e ->
                Log.w(TAG, "ML Kit offline translate failed: ${e.message}")
                latch.countDown()
            }

        try {
            latch.await(3500, TimeUnit.MILLISECONDS)
        } catch (e: Exception) {
            Log.e(TAG, "Timeout chờ dịch ML Kit: ${e.message}")
        }
        return result
    }

    fun translateOnline(text: String, sourceLang: String = "auto", targetLang: String = "vi"): String? {
        try {
            val encoded = URLEncoder.encode(text, "UTF-8")
            val url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=$sourceLang&tl=$targetLang&dt=t&q=$encoded"
            val req = Request.Builder().url(url).build()
            val resp = httpClient.newCall(req).execute()
            val body = resp.body?.string() ?: ""
            val jsonArray = JSONArray(body)
            val sentences = jsonArray.optJSONArray(0)
            if (sentences != null) {
                val sb = StringBuilder()
                for (i in 0 until sentences.length()) {
                    val s = sentences.optJSONArray(i)
                    if (s != null && s.length() > 0) {
                        sb.append(s.getString(0))
                    }
                }
                return sb.toString().trim()
            }
        } catch (e: Exception) {
            Log.e(TAG, "Lỗi dịch Google Online: ${e.message}")
        }
        return null
    }

    fun translateSmart(text: String, sourceLang: String = "auto", targetLang: String = "vi", mode: String = "auto"): JSONObject {
        val clean = text.trim()
        val isSingleWord = !clean.contains(" ") && clean.length <= 40

        var dictDetails: JSONObject? = null
        var ipa = ""
        var shortTranslation = ""
        var detectedLang = if (sourceLang == "auto") "en" else sourceLang
        var engineUsed = "online"

        // 1. Nếu là từ đơn: Tra cứu từ điển SQLite trước
        if (isSingleWord && (targetLang == "vi" || targetLang == "en")) {
            val dictEntry = lookupWord(clean)
            if (dictEntry != null) {
                dictDetails = dictEntry
                ipa = dictEntry.optString("pronounce")
                val desc = dictEntry.optString("description")
                shortTranslation = desc.ifEmpty { clean }
                engineUsed = "offline_dict"
            }
        }

        // 2. Nếu là câu hoặc từ chưa có trong từ điển: Dịch bằng Google ML Kit Offline hoặc Online
        if (shortTranslation.isEmpty()) {
            if (mode == "offline" || mode == "auto") {
                val sLang = if (sourceLang == "auto") "en" else sourceLang
                val offlineText = translateMlKitOffline(clean, sLang, targetLang)
                if (!offlineText.isNullOrEmpty()) {
                    shortTranslation = offlineText
                    engineUsed = "offline_nmt"
                }
            }

            // Fallback Online nếu cần
            if (shortTranslation.isEmpty() && mode != "offline") {
                val onlineText = translateOnline(clean, sourceLang, targetLang)
                if (!onlineText.isNullOrEmpty()) {
                    shortTranslation = onlineText
                    engineUsed = "online"
                }
            }
        }

        return JSONObject().apply {
            put("success", true)
            put("original_text", clean)
            put("translated_text", shortTranslation.ifEmpty { clean })
            put("detected_lang", detectedLang)
            put("target_lang", targetLang)
            put("engine", engineUsed)
            put("source_label", if (engineUsed.startsWith("offline")) "Google ML Kit Offline" else "Google Online")
            put("ipa", ipa)
            if (dictDetails != null) {
                put("dict_details", dictDetails)
            }
        }
    }
}
