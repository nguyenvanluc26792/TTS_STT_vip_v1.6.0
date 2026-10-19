package com.dragon.read.reader.server

import android.content.Context
import android.util.Log
import fi.iki.elonen.NanoHTTPD
import org.json.JSONArray
import org.json.JSONObject
import com.dragon.read.reader.ui.ReaderMediaService
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.io.File
import java.io.FileInputStream
import java.io.InputStream
import java.security.MessageDigest
import java.util.concurrent.Executors
import java.util.concurrent.Future
import java.util.concurrent.TimeUnit

class HonorLocalServer(
    private val context: Context,
    port: Int = 8765
) : NanoHTTPD("127.0.0.1", port) {

    companion object {
        private const val TAG = "HonorLocalServer"
    }

    private val bookManager = NativeBookManager(context)
    private val dictEngine = NativeDictionaryEngine(context)
    private val cacheDir = File(context.cacheDir, "tts_cache_v6").apply { mkdirs() }
    private val pronounceFile = File(context.filesDir, "pronounce_rules.json")
    private val customWordsFile = File(context.filesDir, "custom_english_words.json")

    @Volatile
    var isAudioPlaying: Boolean = false
    @Volatile
    private var isPreloadEnabled = true
    val preloader by lazy { ChapterAudioPreloader() }

    fun getSilentMp3(): ByteArray {
        val frame = byteArrayOf(
            0xFF.toByte(), 0xFB.toByte(), 0x90.toByte(), 0x64.toByte(),
            0x00, 0x00, 0x00, 0x00
        )
        val baos = ByteArrayOutputStream()
        for (i in 0 until 50) {
            baos.write(frame)
        }
        return baos.toByteArray()
    }

    init {
        try {
            // Xoa sach thu muc cache cu de giai phong bo nho
            context.cacheDir.listFiles()?.forEach { f ->
                if (f.name.startsWith("tts_cache") && f.name != "tts_cache_v6") {
                    f.deleteRecursively()
                }
            }
            // Neu APK moi vua duoc cai dat, xoa file ota/index.html cu de tranh che khuat code moi trong assets
            val otaFile = File(context.filesDir, "ota/index.html")
            if (otaFile.exists()) {
                val pkgInfo = context.packageManager.getPackageInfo(context.packageName, 0)
                if (otaFile.lastModified() < pkgInfo.lastUpdateTime) {
                    Log.i(TAG, "Xóa ota/index.html cũ do APK vừa được cập nhật mới hơn")
                    otaFile.delete()
                }
            }
        } catch (e: Exception) {
            Log.w(TAG, "Lỗi dọn cache audio: ${e.message}")
        }
    }

    private fun md5(input: String): String {
        val md = MessageDigest.getInstance("MD5")
        val bytes = md.digest(input.toByteArray(Charsets.UTF_8))
        return bytes.joinToString("") { "%02x".format(it) }
    }

    private fun jsonResponse(jsonStr: String, status: Response.Status = Response.Status.OK): Response {
        val resp = newFixedLengthResponse(status, "application/json; charset=utf-8", jsonStr)
        resp.addHeader("Access-Control-Allow-Origin", "*")
        resp.addHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        resp.addHeader("Access-Control-Allow-Headers", "Content-Type")
        return resp
    }

    override fun serve(session: IHTTPSession): Response {
        return try {
            handleServe(session)
        } catch (t: Throwable) {
            Log.e(TAG, "Lỗi server serve (${session.uri}): ${t.message}", t)
            jsonResponse("{\"error\":\"Lỗi máy chủ nội bộ: ${t.message}\"}", Response.Status.INTERNAL_ERROR)
        }
    }

    private fun handleServe(session: IHTTPSession): Response {
        val uri = session.uri
        val method = session.method

        if (method == Method.OPTIONS) {
            val resp = newFixedLengthResponse(Response.Status.OK, "text/plain", "OK")
            resp.addHeader("Access-Control-Allow-Origin", "*")
            resp.addHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            resp.addHeader("Access-Control-Allow-Headers", "Content-Type")
            return resp
        }

        if (uri == "/download-app" || uri == "/LReader.apk") {
            val redirectResp = newFixedLengthResponse(Response.Status.REDIRECT, "text/plain", "Redirecting to APK download...")
            redirectResp.addHeader("Location", "https://rehab-survey-clusters-joins.trycloudflare.com/download-app")
            return redirectResp
        }

        // 1. Phục vụ trang đọc sách: Ưu tiên file OTA cập nhật mới nhất, nếu chưa có thì dùng Assets gốc
        if (uri == "/" || uri == "/index.html") {
            try {
                val otaFile = File(context.filesDir, "ota/index.html")
                val input: InputStream = if (otaFile.exists() && otaFile.length() > 50000) {
                    Log.i(TAG, "Đang nạp index.html từ gói cập nhật OTA (${otaFile.length()} bytes)")
                    FileInputStream(otaFile)
                } else {
                    Log.i(TAG, "Đang nạp index.html từ assets gốc")
                    context.assets.open("index.html")
                }
                val resp = newChunkedResponse(Response.Status.OK, "text/html; charset=utf-8", input)
                resp.addHeader("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
                resp.addHeader("Pragma", "no-cache")
                resp.addHeader("Expires", "0")
                return resp
            } catch (e: Exception) {
                return newFixedLengthResponse(Response.Status.INTERNAL_ERROR, "text/plain", "Lỗi nạp index.html: ${e.message}")
            }
        }

        val ct = session.headers["content-type"] ?: ""
        if (!ct.contains("charset", ignoreCase = true)) {
            try {
                (session.headers as? MutableMap<String, String>)?.put("content-type", if (ct.isEmpty()) "application/json; charset=utf-8" else "$ct; charset=utf-8")
            } catch (e: Exception) {}
        }

        val files = mutableMapOf<String, String>()
        if (method == Method.POST || method == Method.PUT) {
            try {
                session.parseBody(files)
            } catch (e: Exception) {
                Log.w(TAG, "Lỗi parseBody: ${e.message}")
            }
        }
        val postData = files["postData"] ?: ""

        // 2. API Danh mục Sách
        if (uri == "/api/books" || uri == "/api/library") {
            return jsonResponse(bookManager.getLibraryIndex().toString())
        }

        // 2b. API Cuốn sách đọc gần nhất
        if (uri == "/api/last-book") {
            val list = bookManager.getLibraryIndex()
            return if (list.length() > 0) {
                val lastId = list.getJSONObject(0).optString("id")
                val bookRaw = bookManager.getBookRawJson(lastId)
                if (bookRaw != null) jsonResponse(bookRaw) else jsonResponse("null")
            } else {
                jsonResponse("null")
            }
        }

        // 3. API Chi tiết & Xóa Sách
        if (uri.startsWith("/api/books/")) {
            val bookId = uri.substringAfter("/api/books/")
            if (method == Method.DELETE) {
                val ok = bookManager.deleteBook(bookId)
                return jsonResponse("{\"success\":$ok}")
            }
            val bookRaw = bookManager.getBookRawJson(bookId)
            return if (bookRaw != null) {
                jsonResponse(bookRaw)
            } else {
                jsonResponse("{\"error\":\"Không tìm thấy sách\"}", Response.Status.NOT_FOUND)
            }
        }

        // 4. API Bóc tách truyện web online (Tải trước tối đa 15 chương)
        if (uri == "/api/web-novel/parse" && method == Method.POST) {
            try {
                val json = JSONObject(postData)
                val url = json.optString("url").trim()
                if (url.isEmpty()) {
                    return jsonResponse("{\"error\":\"Vui lòng nhập link truyện\"}", Response.Status.BAD_REQUEST)
                }

                val client = okhttp3.OkHttpClient.Builder()
                    .connectTimeout(15, TimeUnit.SECONDS)
                    .readTimeout(15, TimeUnit.SECONDS)
                    .followRedirects(true)
                    .build()

                val req = okhttp3.Request.Builder()
                    .url(url)
                    .header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
                    .build()

                val response = client.newCall(req).execute()
                val html = response.body?.string() ?: ""
                val doc = org.jsoup.Jsoup.parse(html, url)

                var storyTitle = doc.selectFirst("a.truyen-title, .story-title, .truyen-title, .rv-full-story-title, .rv-heading-story, .truyen-name, .book-info h1, .book-title, .novel-title, h1.title, h1")?.text()?.trim() ?: ""
                if (storyTitle.isEmpty()) {
                    storyTitle = doc.select("meta[property='og:title'], meta[name='title']").attr("content").split("-").firstOrNull()?.trim() ?: ""
                }
                if (storyTitle.isEmpty()) {
                    storyTitle = doc.title().split("-").firstOrNull()?.trim() ?: "Truyện Web"
                }

                var author = doc.selectFirst("a[href*='/tac-gia/'], .author, meta[property='og:novel:author'], meta[name='author'], .author-name")?.text()?.trim() ?: ""
                if (author.isEmpty()) author = "Tác giả Online"

                var contentEl = doc.selectFirst("#chapter-content, .chapter-c, .entry-content, .reading-content, div.content-inner, div.content, #content, .content-body, #chapter-c, .reading-detail, .box-chap, #bookContentBody, .chap-content, .txt-content, #chr-content, .chr-c, #vungdoc, .vung-doc, .vungdoc")
                var startChapUrl = url
                if (!startChapUrl.contains("/chuong-", ignoreCase = true) && !startChapUrl.contains("/chapter-", ignoreCase = true)) {
                    if (startChapUrl.contains("truyenhoan.com", ignoreCase = true)) {
                        val m = Regex("""truyenhoan\.com/([^/.]+)(?:\.\d+)?/?""", RegexOption.IGNORE_CASE).find(startChapUrl)
                        if (m != null) startChapUrl = "https://truyenhoan.com/${m.groupValues[1]}/chuong-1.html"
                    } else if (startChapUrl.contains("truyenfullmoi.net", ignoreCase = true)) {
                        val m = Regex("""truyenfullmoi\.net/([^/.]+)(?:\.\d+)?/?""", RegexOption.IGNORE_CASE).find(startChapUrl)
                        if (m != null) startChapUrl = "https://truyenfullmoi.net/${m.groupValues[1]}/chuong-1/"
                    } else if (startChapUrl.contains("xtruyen.vn/truyen/", ignoreCase = true)) {
                        val m = Regex("""xtruyen\.vn/truyen/([^/]+)/?""", RegexOption.IGNORE_CASE).find(startChapUrl)
                        if (m != null) startChapUrl = "https://xtruyen.vn/truyen/${m.groupValues[1]}/chuong-1/"
                    } else if (startChapUrl.contains("sottruyen.com/truyen/", ignoreCase = true)) {
                        val m = Regex("""sottruyen\.com/truyen/([^/]+)/?""", RegexOption.IGNORE_CASE).find(startChapUrl)
                        if (m != null) startChapUrl = "https://sottruyen.com/truyen/${m.groupValues[1]}/chuong-1"
                    }
                }

                // Nếu là trang mục lục / thông tin truyện (chưa vào thẳng nội dung chương)
                if (contentEl == null || contentEl.text().trim().length < 50) {
                    var firstChapUrl = ""
                    val ch1HrefRegex = Regex("""(?i)[/-](?:chuong|chapter|c)[-_]?0*1(?:\.html|/|\?|$)""")
                    val ch1TxtRegex = Regex("""(?i)(?:chương|chuong|chapter)\s*0*1(?:\s*[:.-]|\s+\D|$)""")
                    val actionTxtRegex = Regex("""(?i)^(?:đọc từ đầu|đọc ngay|đọc truyện)$""")

                    // 1. Quét tìm link có chữ "Đọc từ đầu", "Đọc ngay", hoặc đúng Chương 1 (không dính số phía sau như 10, 11, 1338)
                    for (a in doc.select("a[href]")) {
                        val raw = a.attr("href").trim()
                        if (raw.isEmpty() || raw == "#" || raw.startsWith("javascript")) continue
                        val txt = a.text().trim()
                        val abs = a.absUrl("href")
                        val fullUrl = if (abs.isNotEmpty()) abs else try { java.net.URI(url).resolve(raw).toString() } catch (e: Exception) { "" }
                        if (fullUrl.isEmpty() || fullUrl == url) continue

                        if (actionTxtRegex.containsMatchIn(txt) || ch1HrefRegex.containsMatchIn(raw) || ch1TxtRegex.containsMatchIn(txt)) {
                            firstChapUrl = fullUrl
                            break
                        }
                    }

                    // 2. Fallback nếu chưa thấy: thử qua các selector thông dụng có regex kiểm tra
                    if (firstChapUrl.isEmpty()) {
                        val chapLinkEl = doc.select("a[href*='chuong-1.'], a[href*='chuong-1/'], a[href*='chuong-01.'], a[href*='chuong-01/'], a[href*='chapter-1.'], a[href*='chapter-1/']").firstOrNull { el ->
                            val href = el.attr("href").trim()
                            ch1HrefRegex.containsMatchIn(href)
                        }
                        if (chapLinkEl != null) {
                            firstChapUrl = chapLinkEl.absUrl("href")
                            if (firstChapUrl.isEmpty()) {
                                val raw = chapLinkEl.attr("href").trim()
                                if (raw.isNotEmpty() && raw != "#" && !raw.startsWith("javascript")) {
                                    firstChapUrl = if (raw.startsWith("http")) raw else try { java.net.URI(url).resolve(raw).toString() } catch (e: Exception) { "" }
                                }
                            }
                        }
                    }

                    if (firstChapUrl.isNotEmpty()) {
                        startChapUrl = firstChapUrl
                    }
                }

                // Tải trước tối đa 15 chương đầu tiên theo chuỗi next_url
                val chapters = JSONArray()
                val visited = mutableSetOf<String>()
                var curChapUrl = startChapUrl
                val maxInitialChapters = 15

                while (curChapUrl.isNotEmpty() && !visited.contains(curChapUrl) && chapters.length() < maxInitialChapters) {
                    visited.add(curChapUrl)
                    val parsed = parseSingleChapter(client, curChapUrl) ?: break
                    val chIdx = chapters.length() + 1
                    val chTitle = if (parsed.title.contains("chương", ignoreCase = true)) parsed.title else "Chương $chIdx: ${parsed.title}"
                    val chObj = JSONObject().apply {
                        put("id", "ch_$chIdx")
                        put("index", chIdx - 1)
                        put("title", chTitle)
                        put("paragraphs", parsed.paragraphs)
                        put("source_url", curChapUrl)
                        if (!parsed.nextUrl.isNullOrEmpty()) put("next_url", parsed.nextUrl)
                    }
                    chapters.put(chObj)
                    curChapUrl = parsed.nextUrl ?: ""
                }

                if (chapters.length() == 0) {
                    return jsonResponse("{\"error\":\"Không thể bóc tách nội dung chương truyện từ trang này (nội dung rỗng hoặc trang bị chặn)\"}", Response.Status.BAD_REQUEST)
                }

                val md5 = MessageDigest.getInstance("MD5").digest(url.toByteArray()).joinToString("") { "%02x".format(it) }.take(10)
                val bookId = "web_" + md5

                val bookObj = JSONObject().apply {
                    put("id", bookId)
                    put("title", storyTitle)
                    put("author", author)
                    put("totalChapters", chapters.length())
                    put("lastChapter", 0)
                    put("lastParagraph", 0)
                    put("is_web", true)
                    put("source_url", url)
                    put("last_crawl_url", curChapUrl)
                    put("chapters", chapters)
                }

                bookManager.saveBookToDisk(bookObj)
                return jsonResponse(bookObj.toString())
            } catch (e: Exception) {
                Log.e(TAG, "Lỗi parse web novel: ${e.message}", e)
                return jsonResponse("{\"error\":\"Không thể tải truyện từ link này: ${e.message}\"}", Response.Status.INTERNAL_ERROR)
            }
        }

        // 4b. API Tải thêm chương tiếp theo của truyện online
        if (uri == "/api/web-novel/fetch-more" && method == Method.POST) {
            try {
                val json = JSONObject(postData)
                val bookId = json.optString("bookId")
                val count = json.optInt("count", 5).coerceIn(1, 100)
                if (bookId.isEmpty()) {
                    return jsonResponse("{\"error\":\"Thiếu bookId\"}", Response.Status.BAD_REQUEST)
                }

                val book = bookManager.getBook(bookId)
                if (book == null) {
                    return jsonResponse("{\"error\":\"Không tìm thấy truyện\"}", Response.Status.NOT_FOUND)
                }

                val (addedCount, newChapters) = fetchMoreChaptersNative(book, count, json.optString("lastUrl", ""))
                if (addedCount > 0) {
                    val resp = JSONObject().apply {
                        put("success", true)
                        put("added", addedCount)
                        put("totalChapters", book.optJSONArray("chapters")?.length() ?: 0)
                        put("newChapters", newChapters)
                    }
                    return jsonResponse(resp.toString())
                } else {
                    return jsonResponse("{\"success\":false,\"message\":\"Không có thêm chương mới hoặc đã đến chương cuối cùng\",\"added\":0}")
                }
            } catch (e: Exception) {
                Log.e(TAG, "Lỗi fetch-more: ${e.message}", e)
                return jsonResponse("{\"error\":\"${e.message}\"}", Response.Status.INTERNAL_ERROR)
            }
        }

        // 4. API Cập nhật tiến độ đọc
        if (uri == "/api/progress" && method == Method.POST) {
            try {
                val json = JSONObject(postData)
                val bookId = json.optString("bookId")
                val ch = if (json.has("chapterIndex")) json.optInt("chapterIndex", 0) else json.optInt("chapter", 0)
                val para = if (json.has("paragraphIndex")) json.optInt("paragraphIndex", 0) else json.optInt("paragraph", 0)
                if (bookId.isNotEmpty()) {
                    bookManager.updateProgress(bookId, ch, para)
                }
                return jsonResponse("{\"success\":true}")
            } catch (e: Exception) {
                return jsonResponse("{\"error\":\"${e.message}\"}", Response.Status.BAD_REQUEST)
            }
        }

        // 5. API Tải sách lên (EPUB / TXT / DOCX)
        if ((uri == "/api/upload_book" || uri == "/api/upload" || uri == "/api/parse-epub") && method == Method.POST) {
            try {
                var bookJson: JSONObject? = null
                for ((paramName, tempFilePath) in files) {
                    if (paramName != "postData") {
                        val file = File(tempFilePath)
                        val originalName = session.parameters[paramName]?.firstOrNull() ?: "book.epub"
                        FileInputStream(file).use { fis ->
                            bookJson = bookManager.parseAndSaveBook(fis, originalName)
                        }
                        break
                    }
                }
                return if (bookJson != null) {
                    jsonResponse(bookJson.toString())
                } else {
                    jsonResponse("{\"error\":\"Không có tệp tải lên\"}", Response.Status.BAD_REQUEST)
                }
            } catch (e: Exception) {
                return jsonResponse("{\"error\":\"${e.message}\"}", Response.Status.INTERNAL_ERROR)
            }
        }

        // 5b. API Quy tắc Bỏ Qua Câu (Skip Rules) - theo từng cuốn sách riêng biệt
        if (uri == "/api/skip-rules") {
            val params = session.parms
            val bookId = params["bookId"]
            if (method == Method.POST) {
                try {
                    var targetBookId = bookId
                    val contentToWrite = try {
                        val json = org.json.JSONObject(postData)
                        if (json.has("bookId") && (targetBookId == null || targetBookId.isEmpty())) {
                            targetBookId = json.optString("bookId", "")
                        }
                        if (json.has("rules")) json.getJSONArray("rules").toString() else postData
                    } catch (e: Exception) {
                        postData
                    }
                    val safeId = targetBookId?.filter { it.isLetterOrDigit() || it == '-' || it == '_' }
                    val skipFile = if (!safeId.isNullOrEmpty()) File(context.filesDir, "skip_rules_${safeId}.json") else File(context.filesDir, "skip_rules.json")
                    skipFile.writeText(contentToWrite, Charsets.UTF_8)

                    // Xóa sạch file cache TTS cũ (.mp3) để TTS không phát lại audio đã chứa từ bị bỏ qua
                    try {
                        cacheDir.listFiles()?.forEach { f ->
                            if (f.isFile && f.name.endsWith(".mp3")) {
                                f.delete()
                            }
                        }
                    } catch (e: Exception) {}

                    return jsonResponse("{\"success\":true,\"rules\":$contentToWrite,\"bookId\":\"$targetBookId\"}")
                } catch (e: Exception) {
                    return jsonResponse("{\"error\":\"${e.message}\"}", Response.Status.INTERNAL_ERROR)
                }
            } else {
                val safeId = bookId?.filter { it.isLetterOrDigit() || it == '-' || it == '_' }
                val skipFile = if (!safeId.isNullOrEmpty()) File(context.filesDir, "skip_rules_${safeId}.json") else File(context.filesDir, "skip_rules.json")
                val content = if (skipFile.exists()) {
                    skipFile.readText(Charsets.UTF_8)
                } else {
                    val defaultFile = File(context.filesDir, "skip_rules.json")
                    if (defaultFile.exists()) defaultFile.readText(Charsets.UTF_8) else "[]"
                }
                return jsonResponse(content)
            }
        }

        // 6. API Danh mục Giọng đọc (CapCut, ElevenLabs, Edge, Offline)
        if (uri == "/api/voices") {
            val catalog = JSONArray().apply {
                put(JSONObject().apply {
                    put("id", "BV421_vivn_streaming")
                    put("name", "Nhỏ Ngọt Ngào (Truyền Cảm • Audiobook)")
                    put("provider", "capcut")
                    put("lang", "vi")
                    put("desc", "CapCut AI - Nữ ấm dịu, truyền cảm, ngắt nhịp văn học cực tốt")
                })
                put(JSONObject().apply {
                    put("id", "BV075_streaming")
                    put("name", "Nam Trầm Ấm (Kể Chuyện • Tiên Hiệp)")
                    put("provider", "capcut")
                    put("lang", "vi")
                    put("desc", "CapCut AI - Nam dõng dạc, trầm hùng, hoàn hảo cho truyện tiên hiệp/hành động")
                })
                put(JSONObject().apply {
                    put("id", "multi_female_richgirl_uranus_bigtts")
                    put("name", "Review Phim (Siêu Truyền Cảm)")
                    put("provider", "capcut")
                    put("lang", "vi")
                    put("desc", "CapCut AI - Trầm ấm, siêu truyền cảm, chuyên đọc truyện và review")
                })
                put(JSONObject().apply {
                    put("id", "BV074_streaming")
                    put("name", "Cô Gái Hoạt Ngôn (Tươi Vui)")
                    put("provider", "capcut")
                    put("lang", "vi")
                    put("desc", "CapCut AI - Tự nhiên, hoạt bát, biểu cảm hội thoại")
                })
                put(JSONObject().apply {
                    put("id", "eleven_zA6D7RyKdc2EClouEMkP")
                    put("name", "Almee-Anh (ElevenLabs)")
                    put("provider", "elevenlabs")
                    put("lang", "en")
                    put("desc", "ElevenLabs - Nữ Anh Quốc (British) thanh lịch, truyền cảm")
                })
                put(JSONObject().apply {
                    put("id", "eleven_Gsndh0O5AnuI2Hj3YUlA")
                    put("name", "Adam-Anh (ElevenLabs)")
                    put("provider", "elevenlabs")
                    put("lang", "en")
                    put("desc", "ElevenLabs - Nam Anh Quốc (British) điềm tĩnh, ấm áp")
                })
                put(JSONObject().apply {
                    put("id", "eleven_IRHApOXLvnW57QJPQH2P")
                    put("name", "Adam-Mỹ (ElevenLabs)")
                    put("provider", "elevenlabs")
                    put("lang", "en")
                    put("desc", "ElevenLabs - Nam Mỹ kinh điển, kể chuyện & thuyết minh")
                })
                put(JSONObject().apply {
                    put("id", "en-US-JennyNeural")
                    put("name", "Jenny (Edge EN)")
                    put("provider", "edge")
                    put("lang", "en")
                    put("desc", "Microsoft - Nữ tiếng Anh bản xứ Mỹ")
                })
                put(JSONObject().apply {
                    put("id", "vi-VN-HoaiMyNeural")
                    put("name", "Hoài My (Edge)")
                    put("provider", "edge")
                    put("lang", "vi")
                    put("desc", "Microsoft - Nữ phát thanh viên êm đềm")
                })
            }
            return jsonResponse(catalog.toString())
        }

        // 7. API Sinh Giọng Đọc TTSọc TTS
        if (uri == "/api/tts" && method == Method.POST) {
            try {
                val json = JSONObject(postData)
                val rawText = json.optString("text", "").trim()
                val bookId = json.optString("book_id", json.optString("bookId", ""))
                val safeId = bookId.filter { it.isLetterOrDigit() || it == '-' || it == '_' }

                // Lọc bỏ các cụm từ / câu bị người dùng đánh dấu bỏ qua ở phía máy chủ
                var text = rawText
                try {
                    val skipFile = if (safeId.isNotEmpty()) File(context.filesDir, "skip_rules_${safeId}.json") else File(context.filesDir, "skip_rules.json")
                    val defaultFile = File(context.filesDir, "skip_rules.json")
                    val fileToRead = if (skipFile.exists()) skipFile else if (defaultFile.exists()) defaultFile else null
                    if (fileToRead != null && fileToRead.exists()) {
                        val rulesJson = org.json.JSONArray(fileToRead.readText(Charsets.UTF_8))
                        fun extractAlpha(s: String): String {
                            return Regex("[\\p{L}\\p{N}]+").findAll(s.lowercase()).map { it.value }.joinToString(" ")
                        }
                        val textAlpha = extractAlpha(text)
                        var shouldDropAll = false

                        for (i in 0 until rulesJson.length()) {
                            val rawRule = rulesJson.optString(i, "").trim()
                            if (rawRule.isEmpty()) continue

                            val ruleAlpha = extractAlpha(rawRule)
                            if (ruleAlpha.isNotEmpty() && textAlpha.isNotEmpty()) {
                                if (ruleAlpha == textAlpha) {
                                    shouldDropAll = true
                                    break
                                }
                                val textWords = textAlpha.split(" ")
                                if (textWords.size >= 2 && " $ruleAlpha ".contains(" $textAlpha ")) {
                                    shouldDropAll = true
                                    break
                                }
                                if (textWords.size == 1 && textAlpha.length >= 5 && " $ruleAlpha ".contains(" $textAlpha ")) {
                                    shouldDropAll = true
                                    break
                                }
                            }

                            var rule = rawRule.replace(Regex("^[\\p{P}\\p{S}\\s]+|[\\p{P}\\p{S}\\s]+$"), "").trim()
                            if (rule.isEmpty()) rule = rawRule

                            val words = rule.split(Regex("[\\s\\p{P}\\p{S}]+")).filter { it.isNotBlank() }
                            if (words.size > 1) {
                                val pattern = words.joinToString("[\\s\\p{P}\\p{S}]*") { Regex.escape(it) }
                                text = text.replace(Regex(pattern, RegexOption.IGNORE_CASE), " ")
                            } else if (words.size == 1) {
                                val w = words[0]
                                val esc = Regex.escape(w)
                                if (w.length <= 3) {
                                    text = text.replace(Regex("(?<![\\p{L}\\p{N}])$esc(?![\\p{L}\\p{N}])", RegexOption.IGNORE_CASE), " ")
                                } else {
                                    text = text.replace(Regex(esc, RegexOption.IGNORE_CASE), " ")
                                }
                            } else {
                                val esc = Regex.escape(rule)
                                text = text.replace(Regex(esc, RegexOption.IGNORE_CASE), " ")
                            }
                        }

                        if (shouldDropAll) {
                            text = ""
                        } else {
                            text = text.replace(Regex("\\s*([,;:.!?])(?:\\s*[,;:.!?])+"), "$1")
                                       .replace(Regex("\\s+"), " ")
                                       .trim()
                        }
                    }
                } catch (e: Exception) {
                    Log.w(TAG, "Lỗi server skip filter: ${e.message}")
                }

                text = normalizeSpokenText(text)

                // Nhận diện và cắt bỏ từ tượng thanh (Foley SFX Engine)
                val sfxWordsRaw = "(?:oanh\\s+long(?:\\s+long)?|oành(?:\\s+oành)?|oanh\\s+tạc|oanh\\s+kích|oanh\\s+ầm|xuy(?:\\s+xuy){1,2}|xuy(?=[!?.…~–—]|(?:\\s+một\\s+tiếng))|ầm(?:\\s+ầm){1,2}|ầm\\s+vang|ầm\\s+ào|đùng\\s+đoàng|đùng(?:\\s+đùng)?|đoàng(?:\\s+đoàng)?|bùm(?:\\s+bùm)?|nổ\\s+tung|rầm(?:\\s+rầm)?|bịch(?:\\s+bịch)?|huỵch(?:\\s+huỵch)?|bộp(?:\\s+bộp)?|bốp(?:\\s+bốp)?|chát(?:\\s+chát)?(?![a-zA-Z0-9à-ỹÀ-Ỹ\\s]*(?:chúa|ngắt))|rắc(?:\\s+rắc)?|bành\\s+bành|phanh(?:\\s+phanh)?|leng\\s+keng|keng(?:\\s+keng)?|choang(?:\\s+choang)?|xoảng(?:\\s+xoảng)?|xủng\\s+xoảng|boong(?:\\s+boong)?|coong(?:\\s+coong)?|vun\\s+vút|vút(?:\\s+vút)?|vèo(?:\\s+vèo)?|xẹt(?:\\s+xẹt)?|xoẹt(?:\\s+xoẹt)?|chéo(?:\\s+chéo)?|vù(?:\\s+vù)?|phù(?:\\s+phù)?(?![a-zA-Z0-9à-ỹÀ-Ỹ\\s]*(?:hợp|thủy|hộ|du|hiệu|chú)))"
                val sfxRegex = Regex("(?i)(?<![\\p{L}\\p{N}])$sfxWordsRaw(?:\\s+một\\s+tiếng)?(?![\\p{L}\\p{N}])")
                val sfxMatches = sfxRegex.findAll(text).toList()

                val detectedSfxType = if (sfxMatches.isNotEmpty()) {
                    val first = sfxMatches[0].value.lowercase()
                    when {
                        Regex("keng|choang|xoảng|boong|coong").containsMatchIn(first) -> "clash"
                        Regex("vút|vèo|xẹt|xoẹt|chéo|vù|phù|xuy").containsMatchIn(first) -> "whoosh"
                        Regex("rầm|bịch|huỵch|bộp|bốp|chát|rắc|bành|phanh").containsMatchIn(first) -> "impact"
                        else -> "explosion"
                    }
                } else null

                val sfxCleaned = text.replace(sfxRegex, " ")
                    .replace(Regex("[\\s,;:!?…–—]+"), " ")
                    .trim()

                if (sfxCleaned.any { it.isLetterOrDigit() }) {
                    text = sfxCleaned
                } else if (detectedSfxType != null) {
                    // Câu thuần túy là từ tượng thanh (ví dụ: "Oanh long!", "Ầm ầm ầm!", "Keng!", "Vút!", "Phanh! Phanh! Phanh!")
                    val wavBytes = SfxAudioGenerator.generateWav(detectedSfxType, sfxMatches.size)
                    val resp = newFixedLengthResponse(Response.Status.OK, "audio/wav", ByteArrayInputStream(wavBytes), wavBytes.size.toLong())
                    resp.addHeader("Cache-Control", "no-cache, no-store, must-revalidate")
                    return resp
                }

                if (text.isEmpty() || !text.any { it.isLetterOrDigit() }) {
                    return newFixedLengthResponse(Response.Status.OK, "audio/mpeg", ByteArrayInputStream(ByteArray(0)), 0)
                }

                val voiceId = json.optString("voice_id", json.optString("voice", "BV074_streaming"))
                val provider = json.optString("provider", "capcut")
                val isElevenLabs = provider == "elevenlabs" || voiceId.startsWith("eleven_") || voiceId.contains("almee", true) || voiceId.contains("adam", true)

                // Nếu người dùng chọn giọng Offline AI (offline_*), map sang giọng đọc AI chất lượng cao tương ứng
                // Tách biệt hoàn toàn: Ban Mai dùng Review Phim, Ngọc Chuyên dùng Nhỏ Ngọt Ngào, Online chuẩn dùng Cô Gái Hoạt Ngôn
                var targetVoice = voiceId
                if (targetVoice == "adam-my" || targetVoice == "adam-us") {
                    targetVoice = "eleven_IRHApOXLvnW57QJPQH2P"
                } else if (targetVoice == "adam-anh" || targetVoice == "adam") {
                    targetVoice = "eleven_Gsndh0O5AnuI2Hj3YUlA"
                } else if (provider == "offline" || targetVoice.startsWith("offline_")) {
                    val clean = targetVoice.removePrefix("offline_").lowercase()
                    targetVoice = when {
                        // Ngọc Chuyên / Ngọc Huyền / Thanh Phương -> Nhỏ Ngọt Ngào BV421 (ấm áp, tình cảm)
                        clean.contains("ngochuyen") || clean.contains("thanhphuong") -> "BV421_vivn_streaming"
                        // Ban Mai / Phương Trang -> Review Phim siêu truyền cảm (khác biệt 100% với Cô Gái Hoạt Ngôn BV074)
                        clean.contains("banmai") || clean.contains("phuongtrang") -> "multi_female_richgirl_uranus_bigtts"
                        // Nữ nhẹ nhàng / Mai Phương / Ngọc Ngân -> Giọng nữ dịu dàng Hương
                        clean.contains("calmwoman") || clean.contains("maiphuong") || clean.contains("ngocngan") -> "vi_female_huong"
                        // Tất cả giọng nam offline -> Nam trầm ấm BV075
                        else -> "BV075_streaming"
                    }
                }

                val multiVoice = json.optBoolean("multi_voice", true)
                val emotion = json.optString("emotion", "normal")
                if (emotion == "cold" && !text.endsWith("!") && !text.endsWith("?")) {
                    text = text.trimEnd(' ', ',', ';', '…', '-', '–', '—') + "!"
                }

                // Tinh chỉnh nhịp ngắt nghỉ dấu phẩy (Comma Prosody & Breath Enhancer):
                // Bổ sung nhịp ngắt hơi biểu cảm sâu lắng (~300ms) giữa các vế câu ngăn cách bởi dấu phẩy
                text = text.replace(Regex("(?<!\\d),\\s*(?!——)"), ", —— ")

                // Check cache sạch: đồng bộ khóa cache với Preloader và Web UI
                val baseVoiceId = json.optString("base_voice_id", json.optString("voice_id", targetVoice)).let {
                    if (it.isEmpty() || it == "default") "BV074_streaming" else it
                }
                val cacheKey = md5("$baseVoiceId:$multiVoice:$emotion:$text")
                val cacheFile = File(cacheDir, "$cacheKey.mp3")
                if (cacheFile.exists()) {
                    if (cacheFile.length() in 240000L..245000L) {
                        cacheFile.delete() // Lập tức xóa nếu trùng kích thước file demo wav 242KB
                    } else if (cacheFile.length() > 500) {
                        val fis = FileInputStream(cacheFile)
                        val resp = newFixedLengthResponse(Response.Status.OK, "audio/mpeg", fis, cacheFile.length())
                        resp.addHeader("Cache-Control", "no-cache, no-store, must-revalidate")
                        return resp
                    }
                }

                val audioBytes = synthesizeAudioUnified(text, targetVoice, multiVoice, isElevenLabs)

                return if (audioBytes != null && audioBytes.isNotEmpty()) {
                    try { cacheFile.writeBytes(audioBytes) } catch (e: Exception) {}
                    val resp = newFixedLengthResponse(Response.Status.OK, "audio/mpeg", ByteArrayInputStream(audioBytes), audioBytes.size.toLong())
                    resp.addHeader("Cache-Control", "no-cache, no-store, must-revalidate")
                    resp.addHeader("Pragma", "no-cache")
                    resp.addHeader("Expires", "0")
                    return resp
                } else {
                    jsonResponse("{\"error\":\"Không thể sinh âm thanh TTS\"}", Response.Status.INTERNAL_ERROR)
                }
            } catch (e: Exception) {
                return jsonResponse("{\"error\":\"${e.message}\"}", Response.Status.INTERNAL_ERROR)
            }
        }

        // 8. API Tra cứu Từ Điển & Dịch Thuật (Google ML Kit + SQLite 132K từ)
        if (uri == "/api/dictionary/translate" && method == Method.POST) {
            try {
                val json = JSONObject(postData)
                val text = json.optString("text", "").trim()
                val sourceLang = json.optString("source_lang", "auto")
                val targetLang = json.optString("target_lang", "vi")
                val mode = json.optString("mode", "auto")

                val transResult = dictEngine.translateSmart(text, sourceLang, targetLang, mode)
                return jsonResponse(transResult.toString())
            } catch (e: Exception) {
                return jsonResponse("{\"success\":false,\"error\":\"${e.message}\"}", Response.Status.INTERNAL_ERROR)
            }
        }

        // 8b. API Phát âm Từ điển
        if (uri == "/api/dictionary/tts") {
            try {
                var text = session.parameters["text"]?.firstOrNull() ?: ""
                var lang = session.parameters["lang"]?.firstOrNull() ?: "en"
                if (text.isEmpty() && postData.isNotEmpty()) {
                    val j = JSONObject(postData)
                    text = j.optString("text", "")
                    lang = j.optString("lang", "en")
                }
                if (text.isNotEmpty()) {
                    val encoded = java.net.URLEncoder.encode(text.take(200), "UTF-8")
                    val ttsUrl = "https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=$lang&q=$encoded"
                    val req = okhttp3.Request.Builder()
                        .url(ttsUrl)
                        .header("User-Agent", "Mozilla/5.0")
                        .build()
                    val client = okhttp3.OkHttpClient()
                    val resp = client.newCall(req).execute()
                    val bytes = resp.body?.bytes()
                    if (bytes != null && bytes.isNotEmpty()) {
                        return newFixedLengthResponse(Response.Status.OK, "audio/mpeg", ByteArrayInputStream(bytes), bytes.size.toLong())
                    }
                }
            } catch (e: Exception) {
                Log.w(TAG, "Lỗi phát âm từ điển: ${e.message}")
            }
            return jsonResponse("{\"error\":\"Không thể phát âm\"}", Response.Status.INTERNAL_ERROR)
        }

        // 8c. API Danh sách gói từ điển offline
        if (uri == "/api/dictionary/packages") {
            val res = JSONObject().apply {
                put("success", true)
                val pkgs = JSONArray().apply {
                    put(JSONObject().apply {
                        put("id", "dict_hh")
                        put("name", "Từ điển Anh - Việt (132.000 từ)")
                        put("description", "Cơ sở dữ liệu từ điển offline tốc độ cao tích hợp sẵn")
                        put("size", "35.8 MB")
                        put("installed", true)
                    })
                    put(JSONObject().apply {
                        put("id", "google_mlkit_en_vi")
                        put("name", "Mô hình Dịch Câu Google ML Kit Offline")
                        put("description", "Dịch toàn bộ đoạn văn ngoại tuyến không cần Internet")
                        put("size", "30 MB")
                        put("installed", true)
                    })
                }
                put("packages", pkgs)
            }
            return jsonResponse(res.toString())
        }

        if (uri == "/api/dictionary/download/start") {
            return jsonResponse("{\"success\":true,\"message\":\"Gói từ điển đã được tích hợp sẵn trên thiết bị.\"}")
        }
        if (uri == "/api/dictionary/download/progress") {
            return jsonResponse("{\"active\":false,\"progress_percent\":100,\"message\":\"Đã cài đặt sẵn\",\"completed\":true}")
        }
        if (uri == "/api/dictionary/packages/delete") {
            return jsonResponse("{\"success\":true,\"message\":\"Không cần xóa gói tích hợp mặc định.\"}")
        }

        // 9. API Quản lý Từ điển phát âm (Pronunciation Rules)
        if (uri == "/api/pronunciation-rules") {
            if (method == Method.POST) {
                try {
                    pronounceFile.writeText(postData, Charsets.UTF_8)
                    return jsonResponse("{\"success\":true}")
                } catch (e: Exception) {
                    return jsonResponse("{\"error\":\"${e.message}\"}", Response.Status.INTERNAL_ERROR)
                }
            } else {
                val content = if (pronounceFile.exists()) pronounceFile.readText(Charsets.UTF_8) else "[]"
                return jsonResponse(content)
            }
        }

        // 10. API Danh sách từ tiếng Anh tùy chỉnh
        if (uri == "/api/custom-english-words") {
            if (method == Method.POST) {
                try {
                    customWordsFile.writeText(postData, Charsets.UTF_8)
                    return jsonResponse("{\"success\":true}")
                } catch (e: Exception) {
                    return jsonResponse("{\"error\":\"${e.message}\"}", Response.Status.INTERNAL_ERROR)
                }
            } else {
                val content = if (customWordsFile.exists()) customWordsFile.readText(Charsets.UTF_8) else "[]"
                return jsonResponse(content)
            }
        }

                // 11. Preloader status
        if (uri == "/api/preload/toggle") {
            if (method == Method.POST && postData.isNotEmpty()) {
                try {
                    val j = JSONObject(postData)
                    if (j.has("enabled")) {
                        preloader.isEnabled = j.getBoolean("enabled")
                    } else {
                        preloader.isEnabled = !preloader.isEnabled
                    }
                } catch (e: Exception) {
                    preloader.isEnabled = !preloader.isEnabled
                }
            } else {
                preloader.isEnabled = !preloader.isEnabled
            }
            return jsonResponse("{\"enabled\":${preloader.isEnabled}}")
        }
        if (uri == "/api/preload/status") {
            val bookId = session.parameters["bookId"]?.firstOrNull() ?: ""
            if (bookId.isNotEmpty() && preloader.currentBookId.isNullOrEmpty()) {
                preloader.update(bookId, 0)
            }
            val wCh = if (preloader.workingChapter != null) "${preloader.workingChapter}" else "null"
            return jsonResponse("{\"enabled\":${preloader.isEnabled},\"isWorking\":${preloader.isWorking},\"cachedCount\":${preloader.cachedCount},\"windowTotal\":${preloader.windowTotal},\"workingChapter\":$wCh,\"workingPara\":${preloader.workingPara},\"totalWorkingParas\":${preloader.totalWorkingParas},\"totalBookChapters\":${preloader.totalBookChapters},\"bookId\":\"${preloader.currentBookId ?: ""}\"}")
        }
        if (uri == "/api/preload/update") {
            try {
                if (postData.isNotEmpty()) {
                    val json = JSONObject(postData)
                    val bookId = json.optString("bookId", json.optString("book_id", ""))
                    val chIdx = json.optInt("chapterIdx", json.optInt("chapterIndex", json.optInt("chapter", 0)))
                    val vId = json.optString("voiceId", json.optString("voice_id", "BV074_streaming"))
                    val tVoice = if (vId.isEmpty() || vId == "default") "BV074_streaming" else vId
                    val mVoice = json.optBoolean("multiVoice", json.optBoolean("multi_voice", true))
                    val emo = json.optString("emotion", "normal")
                    val e11 = json.optBoolean("isElevenLabs", false)
                    val winSize = json.optInt("windowSize", 30)
                    if (bookId.isNotEmpty()) {
                        preloader.update(bookId, chIdx, vId, tVoice, mVoice, emo, e11, winSize)
                    }
                }
            } catch (e: Exception) {
                Log.w(TAG, "Lỗi update preloader: ${e.message}")
            }
            return jsonResponse("{\"success\":true}")
        }
        if (uri == "/api/bilingual-mode") {
            return jsonResponse("{\"mode\":\"off\"}")
        }
        if (uri == "/api/offline_voices") {
            return jsonResponse(getOfflineVoicesCatalog().toString())
        }

        // 12. API Nghe thử giọng Offline AI
        if (uri.startsWith("/api/offline_voices/demo/")) {
            val voiceId = uri.substringAfter("/api/offline_voices/demo/")
            try {
                val demoUrl = "https://cdn.ainovelreader.com/demo_voice/demo_${voiceId}.wav"
                val req = okhttp3.Request.Builder()
                    .url(demoUrl)
                    .header("User-Agent", "Mozilla/5.0 (Linux; Android 14; Mobile)")
                    .build()
                val client = okhttp3.OkHttpClient.Builder()
                    .connectTimeout(10, java.util.concurrent.TimeUnit.SECONDS)
                    .readTimeout(20, java.util.concurrent.TimeUnit.SECONDS)
                    .build()
                val resp = client.newCall(req).execute()
                val bytes = resp.body?.bytes()
                if (bytes != null && bytes.isNotEmpty()) {
                    return newFixedLengthResponse(Response.Status.OK, "audio/wav", ByteArrayInputStream(bytes), bytes.size.toLong())
                }
            } catch (e: Exception) {
                Log.w(TAG, "Lỗi nạp audio demo cho $voiceId: ${e.message}")
            }
            return jsonResponse("{\"error\":\"Không thể phát audio demo\"}", Response.Status.INTERNAL_ERROR)
        }

        // 13. API Tải mô hình giọng Offline AI về máy
        if (uri == "/api/offline_voices/download" && method == Method.POST) {
            try {
                val json = JSONObject(postData)
                val voiceId = json.optString("voice_id", "").trim()
                if (voiceId.isNotEmpty()) {
                    startDownloadOfflineVoice(voiceId)
                    return jsonResponse("{\"status\":\"started\",\"voice_id\":\"$voiceId\"}")
                }
                return jsonResponse("{\"error\":\"Thiếu voice_id\"}", Response.Status.BAD_REQUEST)
            } catch (e: Exception) {
                return jsonResponse("{\"error\":\"${e.message}\"}", Response.Status.INTERNAL_ERROR)
            }
        }

        // 14. API Xóa mô hình giọng Offline AI giải phóng bộ nhớ
        if (uri == "/api/offline_voices/delete" && method == Method.POST) {
            try {
                val json = JSONObject(postData)
                val voiceId = json.optString("voice_id", "").trim()
                if (voiceId.isNotEmpty()) {
                    val onnxFile = File(offlineModelsDir, "$voiceId.onnx")
                    val jsonFile = File(offlineModelsDir, "$voiceId.onnx.json")
                    if (onnxFile.exists()) onnxFile.delete()
                    if (jsonFile.exists()) jsonFile.delete()
                    downloadStatusMap.remove(voiceId)
                    return jsonResponse("{\"success\":true,\"voice_id\":\"$voiceId\"}")
                }
                return jsonResponse("{\"error\":\"Thiếu voice_id\"}", Response.Status.BAD_REQUEST)
            } catch (e: Exception) {
                return jsonResponse("{\"error\":\"${e.message}\"}", Response.Status.INTERNAL_ERROR)
            }
        }

        if (uri == "/api/debug/crash-log") {
            val crashFile = File(context.filesDir, "crash_log.txt")
            val content = if (crashFile.exists()) crashFile.readText(Charsets.UTF_8) else ""
            return jsonResponse("{\"has_crash\":${crashFile.exists() && content.isNotEmpty()},\"log\":${JSONObject.quote(content)}}")
        }
        if (uri == "/api/debug/clear-crash-log") {
            val crashFile = File(context.filesDir, "crash_log.txt")
            if (crashFile.exists()) crashFile.delete()
            return jsonResponse("{\"success\":true}")
        }

        // 15. API OTA Cập nhật giao diện không cần cài lại APK
        if (uri == "/api/ota/status" && method == Method.GET) {
            val otaFile = File(context.filesDir, "ota/index.html")
            val hasOta = otaFile.exists() && otaFile.length() > 50000
            val size = if (hasOta) otaFile.length() else 0
            val mod = if (hasOta) otaFile.lastModified() else 0
            return jsonResponse("{\"has_ota\":$hasOta,\"ota_size\":$size,\"updated_at\":$mod}")
        }

        if (uri == "/api/ota/update" && method == Method.POST) {
            try {
                val json = JSONObject(postData)
                val serverUrl = json.optString("server_url", "https://unwrap-analyzed-clarke-fonts.trycloudflare.com").trimEnd('/')
                var htmlContent = json.optString("html_content", "")

                if (htmlContent.isEmpty()) {
                    val candidateUrls = mutableListOf<String>()
                    if (serverUrl.isNotEmpty()) candidateUrls.add(serverUrl)
                    val fallback3G = "https://unwrap-analyzed-clarke-fonts.trycloudflare.com"
                    val fallbackWifi = "http://192.168.1.204:5000"
                    if (!candidateUrls.contains(fallback3G)) candidateUrls.add(fallback3G)
                    if (!candidateUrls.contains(fallbackWifi)) candidateUrls.add(fallbackWifi)

                    val client = okhttp3.OkHttpClient.Builder()
                        .connectTimeout(10, TimeUnit.SECONDS)
                        .readTimeout(15, TimeUnit.SECONDS)
                        .build()

                    var lastErr = ""
                    for (candidate in candidateUrls) {
                        try {
                            val req = okhttp3.Request.Builder()
                                .url("$candidate/api/ota/bundle?t=${System.currentTimeMillis()}")
                                .build()
                            val resp = client.newCall(req).execute()
                            if (resp.isSuccessful) {
                                val bodyStr = resp.body?.string() ?: ""
                                if (bodyStr.length > 50000 && bodyStr.contains("<html")) {
                                    htmlContent = bodyStr
                                    break
                                }
                            } else {
                                lastErr = "HTTP ${resp.code} từ $candidate"
                            }
                        } catch (eReq: Exception) {
                            lastErr = "${eReq.message} từ $candidate"
                        }
                    }

                    if (htmlContent.isEmpty()) {
                        return jsonResponse("{\"error\":\"Không thể tải gói cập nhật qua 3G/Wi-Fi: $lastErr\"}", Response.Status.BAD_REQUEST)
                    }
                }

                if (htmlContent.length < 50000 || !htmlContent.contains("<html")) {
                    return jsonResponse("{\"error\":\"Gói cập nhật không hợp lệ hoặc kích thước quá nhỏ (${htmlContent.length} bytes)\"}", Response.Status.BAD_REQUEST)
                }

                val otaDir = File(context.filesDir, "ota")
                if (!otaDir.exists()) otaDir.mkdirs()
                val otaFile = File(otaDir, "index.html")
                val tmpFile = File(otaDir, "index.tmp.html")
                tmpFile.writeText(htmlContent, Charsets.UTF_8)
                if (tmpFile.length() > 50000) {
                    if (otaFile.exists()) otaFile.delete()
                    tmpFile.renameTo(otaFile)
                    return jsonResponse("{\"success\":true,\"message\":\"Cập nhật OTA thành công (${otaFile.length() / 1024} KB)\"}")
                } else {
                    return jsonResponse("{\"error\":\"Lỗi ghi tệp cập nhật OTA\"}", Response.Status.INTERNAL_ERROR)
                }
            } catch (e: Exception) {
                Log.e(TAG, "Lỗi cập nhật OTA: ${e.message}", e)
                return jsonResponse("{\"error\":\"Lỗi cập nhật OTA: ${e.message}\"}", Response.Status.INTERNAL_ERROR)
            }
        }

        if (uri == "/api/ota/reset" && method == Method.POST) {
            try {
                val otaFile = File(context.filesDir, "ota/index.html")
                if (otaFile.exists()) {
                    otaFile.delete()
                }
                return jsonResponse("{\"success\":true,\"message\":\"Đã xoá bản OTA, khôi phục giao diện gốc từ APK\"}")
            } catch (e: Exception) {
                return jsonResponse("{\"error\":\"Lỗi khôi phục: ${e.message}\"}", Response.Status.INTERNAL_ERROR)
            }
        }

        return newFixedLengthResponse(Response.Status.NOT_FOUND, "text/plain", "Not Found")
    }

    private val offlineModelsDir = File(context.filesDir, "piper_models").apply { mkdirs() }
    private val downloadStatusMap = java.util.concurrent.ConcurrentHashMap<String, String>()

    private fun getOfflineVoicesCatalog(): JSONArray {
        val list = JSONArray()
        val rawVoices = listOf(
            Triple("banmai", "Ban Mai", "Nữ" to "Bắc"),
            Triple("ngochuyennew", "Ngọc Huyền", "Nữ" to "Bắc"),
            Triple("deepman3909", "Nam Trầm", "Nam" to "Bắc"),
            Triple("calmwoman3688", "Nữ nhẹ nhàng", "Nữ" to "Bắc"),
            Triple("manhdung", "Mạnh Dũng", "Nam" to "Bắc"),
            Triple("maiphuong", "Mai Phương", "Nữ" to "Bắc"),
            Triple("minhkhang", "Minh Khang", "Nam" to "Bắc"),
            Triple("minhquang", "Minh Quang", "Nam" to "Bắc"),
            Triple("phuongtrang", "Phương Trang", "Nữ" to "Bắc"),
            Triple("duyoryx3175", "Duy", "Nam" to "Nam"),
            Triple("chieuthanh", "Chiếu Thành", "Nam" to "Bắc"),
            Triple("ngocngan3701", "Ngọc Ngân", "Nữ" to "Nam"),
            Triple("thanhphuong2", "Thanh Phương", "Nữ" to "Bắc"),
            Triple("vietthao3886", "Việt Thao", "Nam" to "Bắc"),
            Triple("thientam", "Thiện Tâm", "Nam" to "Bắc"),
            Triple("taian4", "Tài An", "Nam" to "Bắc"),
            Triple("lacphi", "Lạc Phi", "Nam" to "Bắc"),
            Triple("ngochuyen", "Ngọc Chuyên", "Nữ" to "Bắc")
        )

        val descMap = mapOf(
            "banmai" to "Giọng nữ miền Bắc trẻ trung, tự nhiên, truyền cảm",
            "ngochuyennew" to "Giọng nữ truyền cảm, mượt mà, chuyên đọc truyện tình cảm",
            "deepman3909" to "Giọng nam trầm ấm, hào sảng, hợp truyện tiên hiệp, kiếm hiệp",
            "calmwoman3688" to "Giọng nữ nhẹ nhàng, êm dịu, dễ ngủ",
            "manhdung" to "Giọng nam chững chạc, rõ ràng, dứt khoát",
            "maiphuong" to "Giọng nữ ấm áp, lưu loát",
            "minhkhang" to "Giọng nam thanh niên hiện đại, tự nhiên",
            "minhquang" to "Giọng nam đĩnh đạc, rõ từng từ",
            "phuongtrang" to "Giọng nữ trong trẻo, nhẹ nhàng",
            "duyoryx3175" to "Giọng nam miền Nam gần gũi, biểu cảm",
            "chieuthanh" to "Giọng nam truyền thống, kể chuyện đêm khuya",
            "ngocngan3701" to "Giọng nữ miền Nam thanh thoát, ngọt ngào",
            "thanhphuong2" to "Giọng nữ đằm thắm, giàu cảm xúc",
            "vietthao3886" to "Giọng nam trầm, lôi cuốn",
            "thientam" to "Giọng nam ấm, thanh bình",
            "taian4" to "Giọng nam khỏe khoắn, tươi vui",
            "lacphi" to "Giọng nam bí ẩn, hấp dẫn",
            "ngochuyen" to "Giọng nữ sâu lắng"
        )

        for ((id, name, pair) in rawVoices) {
            val gender = pair.first
            val accent = pair.second
            val onnxFile = File(offlineModelsDir, "$id.onnx")
            val isDl = onnxFile.exists() && onnxFile.length() > 5 * 1024 * 1024
            val status = downloadStatusMap[id] ?: "idle"

            list.put(JSONObject().apply {
                put("id", id)
                put("full_id", "offline_$id")
                put("name", name)
                put("gender", gender)
                put("accent", accent)
                put("desc", descMap[id] ?: "Giọng đọc AI tự nhiên")
                put("fileName", "$id.onnx")
                put("is_downloaded", isDl)
                put("download_status", status)
                put("file_size_mb", if (isDl) (onnxFile.length() / (1024.0 * 1024.0)).let { Math.round(it * 10) / 10.0 } else 63.5)
                put("onnxUrl", "https://cdn.ainovelreader.com/tts_model/$id.onnx")
                put("jsonUrl", "https://cdn.ainovelreader.com/tts_model/$id.onnx.json")
                put("demoUrl", "https://cdn.ainovelreader.com/demo_voice/demo_${id}.wav")
            })
        }
        return list
    }

    private fun startDownloadOfflineVoice(voiceId: String) {
        val cur = downloadStatusMap[voiceId]
        if (cur != null && cur.startsWith("downloading")) return

        downloadStatusMap[voiceId] = "downloading_0%"
        Thread {
            try {
                val client = okhttp3.OkHttpClient.Builder()
                    .connectTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
                    .readTimeout(120, java.util.concurrent.TimeUnit.SECONDS)
                    .build()

                // 1. Tải JSON metadata
                val jsonUrl = "https://cdn.ainovelreader.com/tts_model/$voiceId.onnx.json"
                val jsonReq = okhttp3.Request.Builder().url(jsonUrl).header("User-Agent", "Mozilla/5.0").build()
                client.newCall(jsonReq).execute().use { resp ->
                    val bytes = resp.body?.bytes()
                    if (bytes != null) {
                        File(offlineModelsDir, "$voiceId.onnx.json").writeBytes(bytes)
                    }
                }

                // 2. Tải ONNX model weights
                val onnxUrl = "https://cdn.ainovelreader.com/tts_model/$voiceId.onnx"
                val onnxReq = okhttp3.Request.Builder().url(onnxUrl).header("User-Agent", "Mozilla/5.0").build()
                client.newCall(onnxReq).execute().use { resp ->
                    val body = resp.body ?: throw Exception("Empty response body")
                    val total = body.contentLength()
                    val tmpFile = File(offlineModelsDir, "$voiceId.onnx.tmp")
                    val targetFile = File(offlineModelsDir, "$voiceId.onnx")

                    body.byteStream().use { input ->
                        tmpFile.outputStream().use { output ->
                            val buf = ByteArray(64 * 1024)
                            var read: Int
                            var downloaded: Long = 0
                            while (input.read(buf).also { read = it } != -1) {
                                output.write(buf, 0, read)
                                downloaded += read
                                if (total > 0) {
                                    val pct = (downloaded * 100 / total).toInt()
                                    downloadStatusMap[voiceId] = "downloading_${pct}%"
                                }
                            }
                        }
                    }
                    if (tmpFile.exists()) {
                        if (targetFile.exists()) targetFile.delete()
                        tmpFile.renameTo(targetFile)
                    }
                }
                downloadStatusMap[voiceId] = "completed"
                Log.i(TAG, "Tải thành công giọng offline $voiceId")
            } catch (e: Exception) {
                downloadStatusMap[voiceId] = "error: ${e.message}"
                Log.e(TAG, "Lỗi tải giọng offline $voiceId: ${e.message}")
            }
        }.start()
    }

    private data class StorySegment(val text: String, val isDialogue: Boolean, val gender: String)

    private fun parseStorySegments(text: String): List<StorySegment> {
        val regex = Regex("[“\"«「『](.*?)[”\"»」』]")
        val segments = mutableListOf<StorySegment>()
        var lastIdx = 0
        val matches = regex.findAll(text).toList()

        // Nếu không có ngoặc kép nhưng bắt đầu bằng gạch đầu dòng (- / – / —)
        if (matches.isEmpty() && Regex("^[\\s]*[\\-–—]").containsMatchIn(text)) {
            val dashRegex = Regex("^[\\s]*[\\-–—]\\s*(.+?[!?.…])(?:[\\s\\-–—,:]+([A-ZÀ-Ỹa-zà-ỹ].*))?$", RegexOption.DOT_MATCHES_ALL)
            val dashMatch = dashRegex.find(text)
            if (dashMatch != null) {
                val dText = dashMatch.groupValues[1].trim()
                val rest = dashMatch.groupValues[2].trim()
                val gender = analyzeSegmentGender("", dText, rest)
                segments.add(StorySegment(dText, true, gender))
                if (rest.isNotEmpty()) {
                    segments.add(StorySegment(rest, false, "neutral"))
                }
                return segments
            } else {
                val dText = text.replace(Regex("^[\\s]*[\\-–—]\\s*"), "").trim()
                val gender = analyzeSegmentGender("", dText, "")
                return listOf(StorySegment(dText, true, gender))
            }
        }

        if (matches.isEmpty()) {
            return listOf(StorySegment(text, false, "neutral"))
        }

        for (m in matches) {
            val start = m.range.first
            val end = m.range.last + 1
            if (start > lastIdx) {
                val nar = text.substring(lastIdx, start).trim()
                if (nar.isNotEmpty()) segments.add(StorySegment(nar, false, "neutral"))
            }
            val quoteText = m.groupValues[1].trim()
            if (quoteText.isNotEmpty()) {
                val ctxBefore = text.substring(maxOf(0, start - 90), start).lowercase()
                val ctxAfter = if (end < text.length) text.substring(end, minOf(text.length, end + 90)).lowercase() else ""
                val gender = analyzeSegmentGender(ctxBefore, quoteText, ctxAfter)
                segments.add(StorySegment(quoteText, true, gender))
            }
            lastIdx = end
        }
        if (lastIdx < text.length) {
            val nar = text.substring(lastIdx).trim()
            if (nar.isNotEmpty()) segments.add(StorySegment(nar, false, "neutral"))
        }
        return segments
    }

    private fun analyzeSegmentGender(leadIn: String, dialogueText: String, leadOut: String): String {
        val femaleTitlesRegex = "(?:nàng|cô|cô ấy|cô gái|ả|thị|bà|tiểu thư|cô nương|tiểu nha đầu|sư muội|sư tỷ|tỷ tỷ|muội muội|tiên tử|thánh nữ|mẫu thân|mẹ|nữ tử|công chúa|nương tử|thiếu nữ|phu nhân|nha hoàn|bà lão|mỹ phụ|nữ nhi|sư nương)"
        val maleTitlesRegex = "(?:hắn|chàng|y|gã|anh|anh ấy|ông|công tử|sư huynh|sư đệ|huynh đệ|phụ thân|cha|nam tử|huynh trưởng|thiếu niên|đại ca|lão giả|đạo nhân|lão tổ|môn chủ|chưởng môn|tông chủ|tiểu tử|trượng phu|nam nhân|lão quái|lão ma|thiếu gia)"
        val speechVerbsRegex = "(?:lên\\s+tiếng|nói|hỏi|đáp|cười|thì\\s+thào|thỏ\\s+thẻ|than|lẩm\\s+bẩm|thốt\\s+lên|bảo|quát|thét|gầm|rống|la|hô|trầm\\s+giọng|khẽ\\s+nói|khẽ\\s+thở\\s+dài|thở\\s+dài|nhủ|nghĩ|nghĩ\\s+thầm|thầm\\s+nghĩ|trong\\s+(?:lòng|nội\\s+tâm))"

        val femaleNames = setOf(
            "tuyết", "liên", "như", "yến", "nhược", "mộng", "tiên", "linh", "cầm",
            "nghiên", "thiến", "điệp", "mai", "lan", "cúc", "trúc", "hương", "vy", "my", "thảo",
            "uyên", "uyển", "diễm", "trâm", "quỳnh", "châu", "tú", "phượng",
            "thục", "huyên", "thiền", "nga", "loan", "kiều", "hân", "thùy", "trang",
            "hằng", "huyền", "nhạn", "khuê", "oanh", "bích", "thúy", "nhã"
        )
        val maleNames = setOf(
            "phong", "viêm", "hàn", "phàm", "hạo", "kiệt", "dũng", "cường", "tuấn",
            "khang", "thắng", "vĩnh", "đức", "tráng", "mãnh", "thạch", "trần", "bá",
            "lâm", "quang", "hoàng", "bảo", "huy", "minh", "sơn", "long", "thiên",
            "trung", "hiếu", "nghĩa", "trí", "trọng", "hùng", "ngạo", "cương"
        )

        // 1. Khớp LeadOut
        if (leadOut.isNotEmpty()) {
            val fSubjObj = Regex("^[\\s\\-–—,:]*$femaleTitlesRegex\\s+(?:nhìn|hướng|quay sang|đối|với)\\s+$maleTitlesRegex\\s*$speechVerbsRegex", RegexOption.IGNORE_CASE)
            val mSubjObj = Regex("^[\\s\\-–—,:]*$maleTitlesRegex\\s+(?:nhìn|hướng|quay sang|đối|với)\\s+$femaleTitlesRegex\\s*$speechVerbsRegex", RegexOption.IGNORE_CASE)
            if (fSubjObj.containsMatchIn(leadOut)) return "female"
            if (mSubjObj.containsMatchIn(leadOut)) return "male"

            val fTag = Regex("^[\\s\\-–—,:]*$femaleTitlesRegex\\s+(?:[a-zà-ỹ\\s]*?)$speechVerbsRegex", RegexOption.IGNORE_CASE)
            val mTag = Regex("^[\\s\\-–—,:]*$maleTitlesRegex\\s+(?:[a-zà-ỹ\\s]*?)$speechVerbsRegex", RegexOption.IGNORE_CASE)
            val fMatch = fTag.containsMatchIn(leadOut)
            val mMatch = mTag.containsMatchIn(leadOut)
            if (fMatch && !mMatch) return "female"
            if (mMatch && !fMatch) return "male"

            val nameMatch = Regex("^[\\s\\-–—,:]*([A-ZÀ-Ỹ][a-zà-ỹ]+(?:\\s+[A-ZÀ-Ỹ][a-zà-ỹ]+)*)(?:\\s+(.*?))?\\s*$speechVerbsRegex").find(leadOut)
            if (nameMatch != null) {
                val givenName = nameMatch.groupValues[1].trim().lowercase().split(Regex("\\s+")).lastOrNull() ?: ""
                if (femaleNames.contains(givenName)) return "female"
                if (maleNames.contains(givenName)) return "male"
            }
        }

        // 2. Khớp LeadIn
        if (leadIn.isNotEmpty()) {
            val fInSubjObj = Regex("$femaleTitlesRegex\\s+(?:nhìn|hướng|quay sang|đối|với)\\s+$maleTitlesRegex\\s*$speechVerbsRegex[:]\\s*$", RegexOption.IGNORE_CASE)
            val mInSubjObj = Regex("$maleTitlesRegex\\s+(?:nhìn|hướng|quay sang|đối|với)\\s+$femaleTitlesRegex\\s*$speechVerbsRegex[:]\\s*$", RegexOption.IGNORE_CASE)
            if (fInSubjObj.containsMatchIn(leadIn)) return "female"
            if (mInSubjObj.containsMatchIn(leadIn)) return "male"

            val fInTag = Regex("$femaleTitlesRegex\\s+(?:[a-zà-ỹ\\s]*?)$speechVerbsRegex[:]\\s*$", RegexOption.IGNORE_CASE)
            val mInTag = Regex("$maleTitlesRegex\\s+(?:[a-zà-ỹ\\s]*?)$speechVerbsRegex[:]\\s*$", RegexOption.IGNORE_CASE)
            val fMatch = fInTag.containsMatchIn(leadIn)
            val mMatch = mInTag.containsMatchIn(leadIn)
            if (fMatch && !mMatch) return "female"
            if (mMatch && !fMatch) return "male"

            val inNameMatch = Regex("([A-ZÀ-Ỹ][a-zà-ỹ]+(?:\\s+[A-ZÀ-Ỹ][a-zà-ỹ]+)*)\\s+(?:.*?)\\s*$speechVerbsRegex[:]\\s*$").find(leadIn)
            if (inNameMatch != null) {
                val givenName = inNameMatch.groupValues[1].trim().lowercase().split(Regex("\\s+")).lastOrNull() ?: ""
                if (femaleNames.contains(givenName)) return "female"
                if (maleNames.contains(givenName)) return "male"
            }
        }

        // 3. Đại từ tự xưng trong thoại
        val dWords = dialogueText.lowercase().split(Regex("\\s+")).take(8).joinToString(" ")
        val femaleSelf = listOf("tiểu nữ", "thiếp", "thiếp thân", "nô gia", "nô tỳ", "bản cung", "tiểu muội", "bần ni", "lão thân", "bản cô nương")
        val maleSelf = listOf("tại hạ", "lão phu", "bản tọa", "bổn tọa", "bần đạo", "lão nạp", "bản công tử", "tiểu sinh", "mỗ", "vi sư", "mạt tướng", "bản vương", "bổn vương", "trẫm", "bản tôn", "bổn tôn", "tiểu tử", "vi huynh", "lão hủ")
        val femaleToMale = listOf("phu quân", "tướng công", "chàng à", "chàng ơi", "sư huynh của muội")
        val maleToFemale = listOf("nương tử", "tiểu thư", "cô nương", "tiểu nha đầu", "ái phi", "nàng ơi", "sư muội của ta")

        if (femaleSelf.any { dWords.contains(it) } || femaleToMale.any { dWords.contains(it) }) return "female"
        if (maleSelf.any { dWords.contains(it) } || maleToFemale.any { dWords.contains(it) }) return "male"

        return "neutral"
    }

    private fun synthesizeAudioUnified(
        text: String,
        targetVoice: String,
        multiVoice: Boolean,
        isElevenLabs: Boolean
    ): ByteArray? {
        var audioBytes: ByteArray? = null
        val hasQuotes = text.contains("“") || text.contains("\"") || text.contains("«") || text.contains("”") || text.contains("»")

        // Phương án 3: Kịch truyền thanh AI phân vai đối thoại Nam - Nữ
        if (multiVoice && hasQuotes && !isElevenLabs) {
            try {
                val segments = parseStorySegments(text)
                if (segments.size > 1 && segments.any { it.isDialogue }) {
                    val baos = java.io.ByteArrayOutputStream()
                    var allSuccess = true
                    for (seg in segments) {
                        val segVoice = if (seg.isDialogue) {
                            if (seg.gender == "female") {
                                if (targetVoice.contains("BV421") || targetVoice.contains("huong")) "multi_female_richgirl_uranus_bigtts"
                                else "BV421_vivn_streaming"
                            } else if (seg.gender == "male") {
                                if (targetVoice.contains("BV075")) "BV074_streaming"
                                else "BV075_streaming"
                            } else targetVoice
                        } else {
                            targetVoice
                        }
                        val partBytes = CapCutTtsHelper.synthesize(seg.text, segVoice, false)
                        if (partBytes != null && partBytes.size > 500) {
                            baos.write(partBytes)
                        } else {
                            allSuccess = false
                            break
                        }
                    }
                    if (allSuccess && baos.size() > 500) {
                        audioBytes = baos.toByteArray()
                    }
                }
            } catch (e: Exception) {
                Log.w(TAG, "Lỗi phân vai kịch truyền thanh: ${e.message}")
            }
        }

        if (audioBytes == null || audioBytes.isEmpty()) {
            try {
                audioBytes = CapCutTtsHelper.synthesize(text, targetVoice, isElevenLabs)
            } catch (e: Exception) {
                Log.w(TAG, "Lỗi CapCut synthesize: ${e.message}")
            }
        }

        // Dự phòng 1: Nếu CapCut giọng được chọn bị lỗi, thử lại với giọng chuẩn
        if (audioBytes == null || audioBytes.isEmpty()) {
            if (isElevenLabs) {
                try {
                    audioBytes = CapCutTtsHelper.synthesize(text, "en_us_006", false)
                } catch (e: Exception) {
                    Log.w(TAG, "Lỗi CapCut fallback en_us_006: ${e.message}")
                }
            } else if (targetVoice != "BV074_streaming") {
                try {
                    audioBytes = CapCutTtsHelper.synthesize(text, "BV074_streaming", false)
                } catch (e: Exception) {
                    Log.w(TAG, "Lỗi CapCut fallback BV074: ${e.message}")
                }
            }
        }

        // Kiểm tra loại trừ file demo wav 242KB nếu vô tình bị lẫn
        if (audioBytes != null && audioBytes.size in 240000..245000) {
            audioBytes = null
        }

        // Dự phòng 2: Google TTS trực tiếp với cơ chế chia nhỏ câu (<100 ký tự)
        if (audioBytes == null || audioBytes.isEmpty()) {
            try {
                val lang = if (targetVoice.contains("en", true) || targetVoice.contains("Jenny", true) || targetVoice.contains("Adam", true) || targetVoice.contains("IRHApOXLvnW57QJPQH2P", true) || targetVoice.contains("Gsndh0O5AnuI2Hj3YUlA", true)) "en" else "vi"
                audioBytes = fetchGoogleTtsChunked(text, lang)
            } catch (e: Exception) {
                Log.w(TAG, "Lỗi Google TTS chunked fallback: ${e.message}")
            }
        }
        return audioBytes
    }

    fun splitIntoSentences(rawText: String): List<String> {
        if (rawText.isBlank()) return emptyList()
        var text = rawText.trim().replace(Regex("\\.{3,}"), "…")
        if (text.isBlank()) return emptyList()

        // Tránh ngắt câu tên miền
        text = text.replace(Regex("\\.\\s*([a-zA-Z]{2,6})\\b"), "\uE000$1")

        // DIALOGUE MASKING: Bảo vệ toàn bộ dấu kết câu bên trong ngoặc kép
        val quoteRegex = Regex("([“\"«「『][^”\"»」』]+[”\"»」』])")
        text = quoteRegex.replace(text) { m ->
            m.value
                .replace(".", "\uE001")
                .replace("!", "\uE002")
                .replace("?", "\uE003")
                .replace("…", "\uE004")
        }

        val sentRegex = Regex("([^.!?…\\n]+(?:[.!?…]+[\"\'”’»)]*|[\\n]+|$))")
        val matches = sentRegex.findAll(text).map { it.value.trim() }.filter { it.isNotEmpty() }.toList()
        if (matches.isEmpty()) {
            return listOf(
                text.replace("\uE000", ".")
                    .replace("\uE001", ".")
                    .replace("\uE002", "!")
                    .replace("\uE003", "?")
                    .replace("\uE004", "…")
            )
        }

        val result = mutableListOf<String>()
        var buffer = ""

        for (m in matches) {
            var part = m.replace("\uE000", ".")
                .replace("\uE001", ".")
                .replace("\uE002", "!")
                .replace("\uE003", "?")
                .replace("\uE004", "…")
                .trim()
            if (part.isEmpty()) continue

            if (part.matches(Regex("^\\d+\\.$")) || part.matches(Regex("^\\$\\d+\\.$"))) {
                buffer = if (buffer.isEmpty()) part else "$buffer $part"
                continue
            }

            if (buffer.isNotEmpty()) {
                part = "$buffer $part"
                buffer = ""
            }

            if (part.length > 220) {
                val subParts = part.split(Regex("(?<=[,;:—])\\s+"))
                var subBuf = ""
                for (s in subParts) {
                    if (subBuf.length + s.length > 160 && subBuf.length > 30) {
                        result.add(subBuf.trim())
                        subBuf = s
                    } else {
                        subBuf = if (subBuf.isEmpty()) s else "$subBuf $s"
                    }
                }
                if (subBuf.isNotBlank()) result.add(subBuf.trim())
            } else {
                result.add(part)
            }
        }
        if (buffer.isNotBlank()) result.add(buffer.trim())
        return result
    }

    private fun fetchGoogleTtsChunked(text: String, lang: String): ByteArray? {
        val clean = text.trim()
        if (clean.isEmpty()) return null

        val chunks = mutableListOf<String>()
        val sentences = clean.split(Regex("(?<=[.?!,;:\n\r])\\s*"))
        var current = StringBuilder()
        for (s in sentences) {
            val part = s.trim()
            if (part.isEmpty()) continue
            if (part.length > 100) {
                if (current.isNotEmpty()) {
                    chunks.add(current.toString().trim())
                    current = StringBuilder()
                }
                val words = part.split(Regex("\\s+"))
                for (w in words) {
                    if (current.length + w.length + 1 > 100) {
                        if (current.isNotEmpty()) {
                            chunks.add(current.toString().trim())
                            current = StringBuilder()
                        }
                        if (w.length > 100) {
                            var longW = w
                            while (longW.length > 100) {
                                chunks.add(longW.take(100))
                                longW = longW.drop(100)
                            }
                            if (longW.isNotEmpty()) current.append(longW).append(" ")
                        } else {
                            current.append(w).append(" ")
                        }
                    } else {
                        current.append(w).append(" ")
                    }
                }
            } else if (current.length + part.length + 1 > 100) {
                chunks.add(current.toString().trim())
                current = StringBuilder(part).append(" ")
            } else {
                current.append(part).append(" ")
            }
        }
        if (current.isNotEmpty()) {
            val rem = current.toString().trim()
            if (rem.isNotEmpty()) chunks.add(rem)
        }

        if (chunks.isEmpty()) return null

        val client = okhttp3.OkHttpClient.Builder()
            .connectTimeout(8, TimeUnit.SECONDS)
            .readTimeout(10, TimeUnit.SECONDS)
            .build()

        val out = ByteArrayOutputStream()
        for (chunk in chunks) {
            if (chunk.isBlank()) continue
            val encoded = java.net.URLEncoder.encode(chunk, "UTF-8")
            val googleUrl = "https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=$lang&q=$encoded"
            val req = okhttp3.Request.Builder()
                .url(googleUrl)
                .header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
                .build()
            try {
                val resp = client.newCall(req).execute()
                val gBytes = resp.body?.bytes()
                if (gBytes != null && gBytes.size > 100) {
                    out.write(gBytes)
                }
            } catch (e: Exception) {
                Log.w(TAG, "Lỗi tải đoạn Google TTS: ${e.message}")
            }
        }
        val result = out.toByteArray()
        return if (result.size > 200) result else null
    }

    private data class ParsedWebChapter(
        val title: String,
        val paragraphs: JSONArray,
        val nextUrl: String?
    )

    private fun parseSingleChapter(client: okhttp3.OkHttpClient, chapUrl: String): ParsedWebChapter? {
        try {
            val req = okhttp3.Request.Builder()
                .url(chapUrl)
                .header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
                .build()
            val resp = client.newCall(req).execute()
            if (!resp.isSuccessful) return null
            val html = resp.body?.string() ?: return null
            val doc = org.jsoup.Jsoup.parse(html, chapUrl)

            var chapTitle = doc.selectFirst("a.chapter-title, .chapter-title, .chapter-name, .rv-chapt-title, .rv-heading-chapter, h2.chapter-title, .chr-title")?.text()?.trim() ?: ""
            if (chapTitle.isEmpty() || (!chapTitle.contains("chương", ignoreCase = true) && !chapTitle.contains("chuong", ignoreCase = true))) {
                val hWithChap = doc.select("h1, h2, h3, .title").firstOrNull { 
                    val t = it.text().trim()
                    t.length <= 90 && (t.contains("chương", ignoreCase = true) || t.contains("chuong", ignoreCase = true) || t.contains("chapter", ignoreCase = true))
                }
                if (hWithChap != null) {
                    chapTitle = hWithChap.text().trim()
                }
            }
            if (chapTitle.isEmpty() || chapTitle.length > 90 || chapTitle.split("chương", ignoreCase = true).size > 2) {
                chapTitle = doc.selectFirst("h1, h2")?.text()?.trim() ?: ""
            }
            if (chapTitle.isEmpty() || chapTitle.length > 90) {
                chapTitle = "Chương"
            }

            val contentEl = doc.selectFirst("#chapter-content, .chapter-c, .entry-content, .reading-content, div.content-inner, div.content, #content, .content-body, #chapter-c, .reading-detail, .box-chap, #bookContentBody, .chap-content, .txt-content, #chr-content, .chr-c, #vungdoc, .vung-doc, .vungdoc")
                ?: return null

            contentEl.select("script, style, ins, iframe, noscript, .ads, .ads-holder").remove()
            for (br in contentEl.select("br, hr")) {
                br.replaceWith(org.jsoup.nodes.TextNode("\n"))
            }

            val parasList = mutableListOf<String>()
            val pTags = contentEl.select("p, div.line, .paragraph")
            for (p in pTags) {
                val t = p.text().trim()
                if (t.length > 2 && !t.contains("quảng cáo", ignoreCase = true) && !t.contains("tải app", ignoreCase = true) && !t.contains("download app", ignoreCase = true)) {
                    parasList.add(t)
                }
            }
            if (parasList.size < 3) {
                parasList.clear()
                val text = contentEl.wholeText()
                for (line in text.lines()) {
                    val l = line.trim()
                    if (l.length > 1 && !l.contains("quảng cáo", ignoreCase = true) && !l.contains("tải app", ignoreCase = true) && !l.contains("download app", ignoreCase = true)) {
                        parasList.add(l)
                    }
                }
            }
            if (parasList.size < 3) {
                parasList.clear()
                val cleanHtml = contentEl.html().replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n").replace("</p>", "\n")
                val cleanDoc = org.jsoup.Jsoup.parse(cleanHtml)
                for (line in cleanDoc.text().lines()) {
                    val l = line.trim()
                    if (l.length > 1 && !l.contains("quảng cáo", ignoreCase = true) && !l.contains("tải app", ignoreCase = true) && !l.contains("download app", ignoreCase = true)) {
                        parasList.add(l)
                    }
                }
            }

            val paragraphs = JSONArray()
            for (p in parasList) {
                paragraphs.put(p)
            }

            val totalChars = (0 until paragraphs.length()).sumOf { paragraphs.optString(it).trim().length }
            if (paragraphs.length() == 0 || (paragraphs.length() < 3 && totalChars < 120)) {
                return null
            }

            // Tìm link chương tiếp theo
            var nextChapUrl = ""
            val nextBtn = doc.selectFirst("#next_chap, a#next_chap, a[rel='next'], .btn-next, .chapter-next, .next-chap, #btn-next, #next-chapter, a.next-page, a:contains(Chương tiếp), a:contains(Chương sau), a:contains(Tiếp theo), a:contains(Next)")
            if (nextBtn != null) {
                nextChapUrl = nextBtn.absUrl("href")
                if (nextChapUrl.isEmpty()) {
                    val raw = nextBtn.attr("href").trim()
                    if (raw.isNotEmpty() && raw != "#" && !raw.startsWith("javascript")) {
                        nextChapUrl = if (raw.startsWith("http")) raw else try { java.net.URI(chapUrl).resolve(raw).toString() } catch (e: Exception) { "" }
                    }
                }
            }
            if (nextChapUrl.isEmpty() || nextChapUrl == chapUrl) {
                for (a in doc.select("a[href]")) {
                    val raw = a.attr("href").trim()
                    if (raw.isEmpty() || raw == "#" || raw.startsWith("javascript")) continue
                    val txt = a.text().trim().lowercase()
                    if (txt.contains("chương tiếp") || txt.contains("tiếp theo") || txt.contains("chương sau") || txt == "tiếp" || txt == "next") {
                        val abs = a.absUrl("href")
                        val candidate = if (abs.isNotEmpty()) abs else try { java.net.URI(chapUrl).resolve(raw).toString() } catch (e: Exception) { "" }
                        if (candidate.isNotEmpty() && candidate != chapUrl && candidate.startsWith("http")) {
                            nextChapUrl = candidate
                            break
                        }
                    }
                }
            }

            return ParsedWebChapter(
                title = if (chapTitle.isNotEmpty()) chapTitle else "Chương",
                paragraphs = paragraphs,
                nextUrl = if (nextChapUrl.isNotEmpty() && nextChapUrl != chapUrl) nextChapUrl else null
            )
        } catch (e: Exception) {
            Log.e(TAG, "Lỗi parseSingleChapter ($chapUrl): ${e.message}")
            return null
        }
    }

    fun fetchMoreChaptersNative(book: JSONObject, count: Int, lastUrlParam: String = ""): Pair<Int, JSONArray> {
        val newChapters = JSONArray()
        try {
            val chapters = book.optJSONArray("chapters") ?: JSONArray()
            val visited = mutableSetOf<String>()
            for (i in 0 until chapters.length()) {
                val c = chapters.getJSONObject(i)
                val sUrl = c.optString("source_url")
                if (sUrl.isNotEmpty()) visited.add(sUrl)
            }

            var curChapUrl = ""
            if (chapters.length() > 0) {
                val lastCh = chapters.getJSONObject(chapters.length() - 1)
                curChapUrl = lastCh.optString("next_url", "")
            }
            if (curChapUrl.isEmpty()) {
                curChapUrl = book.optString("last_crawl_url", "")
            }
            if (curChapUrl.isEmpty()) {
                curChapUrl = lastUrlParam
            }

            if (curChapUrl.isEmpty()) return Pair(0, newChapters)

            val client = okhttp3.OkHttpClient.Builder()
                .connectTimeout(15, TimeUnit.SECONDS)
                .readTimeout(15, TimeUnit.SECONDS)
                .followRedirects(true)
                .build()

            var addedCount = 0
            while (curChapUrl.isNotEmpty() && !visited.contains(curChapUrl) && addedCount < count) {
                visited.add(curChapUrl)
                val parsed = parseSingleChapter(client, curChapUrl) ?: break
                val chIdx = chapters.length() + 1
                val chTitle = if (parsed.title.contains("chương", ignoreCase = true)) parsed.title else "Chương $chIdx: ${parsed.title}"
                val chObj = JSONObject().apply {
                    put("id", "ch_$chIdx")
                    put("index", chIdx - 1)
                    put("title", chTitle)
                    put("paragraphs", parsed.paragraphs)
                    put("source_url", curChapUrl)
                    if (!parsed.nextUrl.isNullOrEmpty()) put("next_url", parsed.nextUrl)
                }
                chapters.put(chObj)
                newChapters.put(chObj)
                addedCount++
                curChapUrl = parsed.nextUrl ?: ""
            }

            if (addedCount > 0) {
                book.put("chapters", chapters)
                book.put("totalChapters", chapters.length())
                book.put("last_crawl_url", curChapUrl)
                bookManager.saveBookToDisk(book)
            }
            return Pair(addedCount, newChapters)
        } catch (e: Exception) {
            Log.e(TAG, "Lỗi fetchMoreChaptersNative: ${e.message}")
            return Pair(0, newChapters)
        }
    }

// =====================================================================
    // BỘ ĐỆM TẢI TRƯỚC ÂM THANH CHẠY NỀN LIÊN TỤC 30 CHƯƠNG (WAKELOCK)
    // Giữ CPU chạy tải trước cho đến khi đủ đệm 30 chương ngay cả khi tắt màn hình
    // =====================================================================
    fun normalizeSpokenText(raw: String): String {
        var text = raw
        text = text.replace(Regex("^[—–-]+\\s*(?=[\\p{L}\\p{N}“\"'])"), "“")
        text = text.replace(Regex("([\\p{L}\\p{N}])~+"), "$1… ")
                   .replace(Regex("\\?{2,}"), "?")
                   .replace(Regex("!{2,}"), "!")
                   .replace(Regex("\\?!\\?+"), "?!")
                   .replace(Regex("!\\?+"), "!?")
                   .replace(Regex("\\.{2,}"), "…")

        text = text.replace(Regex("(?i)(?<=^|[\\s.!?…“\"—])(Ồ|Hừ|Ôi|Hơ|Chao ôi|Trời ơi|Ha ha|Hì hì|Hừm|Ô kìa|Ô hay)(?=\\s+[\\p{L}\\p{N}])"), "$1,")

        text = text.replace(Regex("(?i)(?<![\\p{L}\\p{N}])(chương|hồi|tập|phần|mục)\\s+VI(?![\\p{L}\\p{N}])"), "$1 6")
                   .replace(Regex("(?i)(?<![\\p{L}\\p{N}])(chương|hồi|tập|phần|mục)\\s+XI(?![\\p{L}\\p{N}])"), "$1 11")
                   .replace(Regex("(?<![\\p{L}\\p{N}])vi(?![\\p{L}\\p{N}])"), "vy")
                   .replace(Regex("(?<![\\p{L}\\p{N}])Vi(?![\\p{L}\\p{N}])"), "Vy")
                   .replace(Regex("(?<![\\p{L}\\p{N}])VI(?![\\p{L}\\p{N}])"), "Vy")
                   .replace(Regex("(?<![\\p{L}\\p{N}])xi(?![\\p{L}\\p{N}])"), "xy")
                   .replace(Regex("(?<![\\p{L}\\p{N}])Xi(?![\\p{L}\\p{N}])"), "Xy")
                   .replace(Regex("(?<![\\p{L}\\p{N}])XI(?![\\p{L}\\p{N}])"), "Xy")
                   .replace(Regex("(?<![\\p{L}\\p{N}])[Ôô](?![\\p{L}\\p{N}])"), "Ôh")
                   .replace(Regex("(?<![\\p{L}\\p{N}])A(?![\\p{L}\\p{N}])"), "Ah")
                   .replace(Regex("(?<![\\p{L}\\p{N}])a(?![\\p{L}\\p{N}])"), "ah")

        text = text.replace(Regex("\\s*([;:.!?…])\\s*"), "$1 ")
                   .replace(Regex("(?<!\\d),\\s*(?!——)"), ", —— ")
                   .replace(Regex("[^\\S\\r\\n]{3,}"), "  ")
                   .trim()
        return text
    }


    inner class ChapterAudioPreloader {
        private val lock = Any()
        var isEnabled = true
        var currentBookId: String? = null
        var currentChapter: Int = 0
        var windowSize: Int = 30
        var voiceId: String = "BV074_streaming"
        var targetVoice: String = "BV074_streaming"
        var multiVoice: Boolean = true
        var emotion: String = "normal"
        var isElevenLabs: Boolean = false

        var isWorking: Boolean = false
        var cachedCount: Int = 0
        var windowTotal: Int = 0
        var workingChapter: Int? = null
        var workingPara: Int = 0
        var totalWorkingParas: Int = 0
        var totalBookChapters: Int = 0

        private var wakeLock: android.os.PowerManager.WakeLock? = null
        private var workerThread: Thread? = null
        private val pool = Executors.newFixedThreadPool(3)
        @Volatile private var isRunning = true

        init {
            try {
                val pm = context.getSystemService(Context.POWER_SERVICE) as? android.os.PowerManager
                wakeLock = pm?.newWakeLock(android.os.PowerManager.PARTIAL_WAKE_LOCK, "HonorReader:AudioPreloaderWakeLock")
            } catch (e: Exception) {
                Log.w(TAG, "Không thể khởi tạo WakeLock cho Preloader: ${e.message}")
            }
            startWorker()
        }

        fun update(bId: String, chIdx: Int, vId: String? = null, tVoice: String? = null, mVoice: Boolean? = null, emo: String? = null, e11: Boolean? = null, winSize: Int? = null) {
            synchronized(lock) {
                currentBookId = bId
                currentChapter = chIdx
                if (!vId.isNullOrEmpty()) voiceId = vId
                if (!tVoice.isNullOrEmpty()) targetVoice = tVoice
                if (mVoice != null) multiVoice = mVoice
                if (emo != null) emotion = emo
                if (e11 != null) isElevenLabs = e11
                if (winSize != null) windowSize = minOf(winSize, 30)
                (lock as java.lang.Object).notifyAll()
            }
        }

        fun stop() {
            isRunning = false
            synchronized(lock) {
                (lock as java.lang.Object).notifyAll()
            }
            try { pool.shutdownNow() } catch (e: Exception) {}
            releaseWakeLock()
        }

        private fun acquireWakeLock() {
            try {
                if (wakeLock?.isHeld == false) {
                    wakeLock?.acquire(30 * 60 * 1000L) // 30 phút tối đa cho phiên tải đệm 30 chương
                }
            } catch (e: Exception) {}
        }

        private fun releaseWakeLock() {
            try {
                if (wakeLock?.isHeld == true) {
                    wakeLock?.release()
                }
            } catch (e: Exception) {}
        }

        private fun startWorker() {
            workerThread = Thread({
                while (isRunning) {
                    var bId: String? = null
                    var startCh = 0
                    var win = 30
                    var vId = "BV074_streaming"
                    var tVoice = "BV074_streaming"
                    var mVoice = true
                    var emo = "normal"
                    var e11 = false

                    synchronized(lock) {
                        while (isRunning && (!isEnabled || currentBookId.isNullOrEmpty())) {
                            isWorking = false
                            workingChapter = null
                            workingPara = 0
                            releaseWakeLock()
                            try {
                                (lock as java.lang.Object).wait(2000)
                            } catch (e: InterruptedException) { break }
                        }
                        if (!isRunning) return@Thread
                        bId = currentBookId
                        startCh = currentChapter
                        win = windowSize
                        vId = voiceId
                        tVoice = targetVoice
                        mVoice = multiVoice
                        emo = emotion
                        e11 = isElevenLabs
                    }

                    if (bId.isNullOrEmpty()) continue

                    val book = bookManager.getBook(bId!!)
                    if (book == null) {
                        Thread.sleep(1000)
                        continue
                    }

                    // Tự động tải thêm chương từ web nếu còn dưới 30 chương phía trước
                    if (book.optBoolean("is_web", false)) {
                        val currentTotal = book.optJSONArray("chapters")?.length() ?: 0
                        val remainingAhead = currentTotal - 1 - startCh
                        if (remainingAhead < win) {
                            val needed = win - remainingAhead
                            val toFetch = minOf(needed, 5)
                            try {
                                val (added, _) = fetchMoreChaptersNative(book, toFetch)
                                if (added > 0) {
                                    Log.i(TAG, "[Preloader] Tự động nạp thêm $added chương web mới. Tổng: ${book.optJSONArray("chapters")?.length()}")
                                }
                            } catch (e: Exception) {
                                Log.w(TAG, "[Preloader] Lỗi nạp thêm chương web: ${e.message}")
                            }
                        }
                    }

                    val chapters = book.optJSONArray("chapters")
                    if (chapters == null || chapters.length() == 0) {
                        Thread.sleep(1000)
                        continue
                    }

                    val totalCh = chapters.length()
                    synchronized(lock) {
                        totalBookChapters = totalCh
                    }
                    val endCh = minOf(startCh + win, totalCh)
                    val winTotal = maxOf(0, endCh - startCh)

                    synchronized(lock) {
                        windowTotal = winTotal
                    }

                    val bookTitle = book.optString("title", "LReader")
                    var fullyCachedChapters = 0
                    var hasMissingAudio = false

                    for (chIdx in startCh until endCh) {
                        synchronized(lock) {
                            if (!isRunning || !isEnabled || currentBookId != bId || currentChapter != startCh) {
                                break
                            }
                        }

                        val chObj = chapters.optJSONObject(chIdx) ?: continue
                        val paras = chObj.optJSONArray("paragraphs") ?: continue

                        val sentenceList = mutableListOf<String>()
                        for (p in 0 until paras.length()) {
                            val pText = paras.optString(p, "").trim()
                            if (pText.isEmpty()) continue
                            val sentences = splitIntoSentences(pText)
                            if (sentences.isEmpty()) sentenceList.add(pText) else sentenceList.addAll(sentences)
                        }

                        if (sentenceList.isEmpty()) {
                            fullyCachedChapters++
                            synchronized(lock) { cachedCount = fullyCachedChapters }
                            continue
                        }

                        synchronized(lock) {
                            workingChapter = chIdx
                            totalWorkingParas = sentenceList.size
                            workingPara = 0
                        }

                        // Kiểm tra câu nào còn thiếu audio
                        data class MissingSent(val index: Int, val text: String, val cacheFile: File)
                        val missingList = mutableListOf<MissingSent>()
                        var alreadyCachedCount = 0

                        for ((sIdx, rawSent) in sentenceList.withIndex()) {
                            var text = normalizeSpokenText(rawSent)
                            if (emo == "cold" && !text.endsWith("!") && !text.endsWith("?")) {
                                text = text.trimEnd(' ', ',', ';', '…', '-', '–', '—') + "!"
                            }
                            text = text.replace(Regex("(?<!\\d),\\s*(?!——)"), ", —— ")

                            val cacheKey = md5("$vId:$mVoice:$emo:$text")
                            val cFile = File(cacheDir, "$cacheKey.mp3")
                            if (cFile.exists() && cFile.length() > 500) {
                                alreadyCachedCount++
                            } else {
                                missingList.add(MissingSent(sIdx, text, cFile))
                            }
                        }

                        synchronized(lock) {
                            workingPara = alreadyCachedCount
                        }

                        if (missingList.isEmpty()) {
                            fullyCachedChapters++
                            synchronized(lock) {
                                cachedCount = fullyCachedChapters
                            }
                            continue
                        }

                        // Có câu cần tải audio -> Bật Foreground Service & WakeLock
                        hasMissingAudio = true
                        synchronized(lock) {
                            isWorking = true
                        }
                        acquireWakeLock()

                        // Giữ ứng dụng chạy ngầm liên tục không bao giờ bị Android tắt
                        try {
                            ReaderMediaService.startOrUpdate(
                                context,
                                bookTitle,
                                "⚡ Đang tải đệm Ch.${chIdx + 1} ($workingPara/$totalWorkingParas câu) • $fullyCachedChapters/$winTotal chương",
                                isAudioPlaying,
                                bookTitle
                            )
                        } catch (e: Exception) {}

                        // Tải song song tối đa 3 câu cùng lúc để tăng tốc độ gấp 3 lần
                        val futures = mutableListOf<Future<*>>()
                        var stopMissing = false
                        for (item in missingList) {
                            synchronized(lock) {
                                if (!isRunning || !isEnabled || currentBookId != bId || currentChapter != startCh) {
                                    stopMissing = true
                                }
                            }
                            if (stopMissing) break

                            val f = pool.submit {
                                try {
                                    val aBytes = synthesizeAudioUnified(item.text, tVoice, mVoice, e11)
                                    if (aBytes != null && aBytes.size > 500) {
                                        item.cacheFile.writeBytes(aBytes)
                                    } else {
                                        try {
                                            item.cacheFile.writeBytes(getSilentMp3())
                                        } catch (e: Exception) {}
                                    }
                                } catch (e: Exception) {
                                    Log.w(TAG, "Preload error sentence: ${e.message}")
                                } finally {
                                    synchronized(lock) {
                                        workingPara++
                                    }
                                }
                            }
                            futures.add(f)
                            if (futures.size >= 3) {
                                for (fut in futures) {
                                    try { fut.get(15, TimeUnit.SECONDS) } catch (e: Exception) {}
                                }
                                futures.clear()
                                try {
                                    ReaderMediaService.startOrUpdate(
                                        context,
                                        bookTitle,
                                        "⚡ Đang tải đệm Ch.${chIdx + 1} ($workingPara/$totalWorkingParas câu) • $fullyCachedChapters/$winTotal chương",
                                        isAudioPlaying,
                                        bookTitle
                                    )
                                } catch (e: Exception) {}
                            }
                        }

                        for (fut in futures) {
                            try { fut.get(15, TimeUnit.SECONDS) } catch (e: Exception) {}
                        }

                        // Kiểm tra lại toàn bộ câu của chương
                        var chSuccess = true
                        for (rawSent in sentenceList) {
                            var text = normalizeSpokenText(rawSent)
                            if (emo == "cold" && !text.endsWith("!") && !text.endsWith("?")) {
                                text = text.trimEnd(' ', ',', ';', '…', '-', '–', '—') + "!"
                            }
                            text = text.replace(Regex("(?<!\\d),\\s*(?!——)"), ", —— ")
                            val cacheKey = md5("$vId:$mVoice:$emo:$text")
                            val cFile = File(cacheDir, "$cacheKey.mp3")
                            if (!cFile.exists() || cFile.length() < 300) {
                                chSuccess = false
                                break
                            }
                        }

                        if (chSuccess) {
                            fullyCachedChapters++
                        }
                        synchronized(lock) {
                            cachedCount = fullyCachedChapters
                        }
                        Thread.sleep(50)
                    }

                    if (!hasMissingAudio) {
                        synchronized(lock) {
                            isWorking = false
                            cachedCount = windowTotal
                            workingChapter = null
                            workingPara = 0
                        }
                        releaseWakeLock()
                        try {
                            if (isAudioPlaying) {
                                ReaderMediaService.startOrUpdate(context, bookTitle, "🎧 Đã đệm đủ 30 chương", true, bookTitle)
                            } else {
                                ReaderMediaService.stop(context)
                            }
                        } catch (e: Exception) {}
                        Thread.sleep(2000)
                    }
                }
            }, "ChapterAudioPreloaderThread")
            workerThread?.isDaemon = true
            workerThread?.start()
        }
    }

    override fun stop() {
        try {
            preloader.stop()
        } catch (e: Exception) {}
        super.stop()
    }
}

/**
 * Bộ sinh âm thanh hiệu ứng (Foley SFX Engine) độc lập:
 * Tự động tạo file âm thanh chuẩn 16-bit PCM WAV 22050Hz mono
 * cho các hiệu ứng nổ sấm sét, quyền cước, đao kiếm va chạm, kiếm khí xé gió.
 */
object SfxAudioGenerator {
    fun generateWav(type: String, count: Int = 1): ByteArray {
        val sampleRate = 22050
        val dur = when (type) {
            "explosion" -> 0.85
            "clash" -> 0.50
            "whoosh" -> 0.28
            else -> 0.40 // impact
        }
        val gapSec = when (type) {
            "explosion" -> 0.15
            "clash" -> 0.10
            "whoosh" -> 0.08
            else -> 0.10
        }
        val numSamples = (sampleRate * dur).toInt()
        val oneChunk = ShortArray(numSamples)
        val random = java.util.Random()

        when (type) {
            "explosion" -> {
                for (i in 0 until numSamples) {
                    val t = i.toDouble() / sampleRate
                    val freq = 90.0 * Math.exp(-t * 3.5) + 35.0
                    val phase = 2.0 * Math.PI * freq * t
                    val sub = Math.sin(phase) * Math.exp(-t * 3.5)
                    val noise = (random.nextDouble() * 2.0 - 1.0) * Math.exp(-t * 4.5)
                    val sample = (sub * 0.65 + noise * 0.35) * 0.95
                    val clamped = sample.coerceIn(-1.0, 1.0)
                    oneChunk[i] = (clamped * 32767.0).toInt().toShort()
                }
            }
            "clash" -> {
                for (i in 0 until numSamples) {
                    val t = i.toDouble() / sampleRate
                    val b1 = Math.sin(2.0 * Math.PI * 2350.0 * t) * Math.exp(-t * 7.0)
                    val b2 = Math.sin(2.0 * Math.PI * 3400.0 * t) * Math.exp(-t * 9.0)
                    val b3 = Math.sin(2.0 * Math.PI * 5100.0 * t) * Math.exp(-t * 14.0)
                    val click = (random.nextDouble() * 2.0 - 1.0) * Math.exp(-t * 70.0)
                    val sample = (b1 * 0.35 + b2 * 0.3 + b3 * 0.2 + click * 0.15) * 0.9
                    val clamped = sample.coerceIn(-1.0, 1.0)
                    oneChunk[i] = (clamped * 32767.0).toInt().toShort()
                }
            }
            "whoosh" -> {
                for (i in 0 until numSamples) {
                    val t = i.toDouble() / sampleRate
                    val env = Math.pow(Math.sin(Math.PI * t / dur), 2.0)
                    val noise = random.nextDouble() * 2.0 - 1.0
                    val carrier = Math.sin(2.0 * Math.PI * (600.0 + 1400.0 * Math.sin(Math.PI * t / dur)) * t)
                    val sample = (noise * 0.4 + carrier * 0.6) * env * 0.9
                    val clamped = sample.coerceIn(-1.0, 1.0)
                    oneChunk[i] = (clamped * 32767.0).toInt().toShort()
                }
            }
            else -> { // impact
                for (i in 0 until numSamples) {
                    val t = i.toDouble() / sampleRate
                    val freq = 120.0 * Math.exp(-t * 8.0) + 40.0
                    val phase = 2.0 * Math.PI * freq * t
                    val sub = Math.sin(phase) * Math.exp(-t * 9.0)
                    val noise = (random.nextDouble() * 2.0 - 1.0) * Math.exp(-t * 25.0)
                    val sample = (sub * 0.75 + noise * 0.25) * 0.95
                    val clamped = sample.coerceIn(-1.0, 1.0)
                    oneChunk[i] = (clamped * 32767.0).toInt().toShort()
                }
            }
        }

        val repeatCount = count.coerceIn(1, 4)
        val pcm = if (repeatCount <= 1) {
            oneChunk
        } else {
            val gapSamples = (sampleRate * gapSec).toInt()
            val totalSamples = numSamples * repeatCount + gapSamples * (repeatCount - 1)
            val combined = ShortArray(totalSamples)
            var destPos = 0
            for (r in 0 until repeatCount) {
                System.arraycopy(oneChunk, 0, combined, destPos, numSamples)
                destPos += numSamples
                if (r < repeatCount - 1) {
                    destPos += gapSamples
                }
            }
            combined
        }

        val totalAudioLen = pcm.size * 2
        val totalDataLen = totalAudioLen + 36
        val header = ByteArray(44)
        val channels = 1
        val byteRate = sampleRate * channels * 2

        header[0] = 'R'.code.toByte(); header[1] = 'I'.code.toByte(); header[2] = 'F'.code.toByte(); header[3] = 'F'.code.toByte()
        header[4] = (totalDataLen and 0xff).toByte()
        header[5] = ((totalDataLen shr 8) and 0xff).toByte()
        header[6] = ((totalDataLen shr 16) and 0xff).toByte()
        header[7] = ((totalDataLen shr 24) and 0xff).toByte()
        header[8] = 'W'.code.toByte(); header[9] = 'A'.code.toByte(); header[10] = 'V'.code.toByte(); header[11] = 'E'.code.toByte()
        header[12] = 'f'.code.toByte(); header[13] = 'm'.code.toByte(); header[14] = 't'.code.toByte(); header[15] = ' '.code.toByte()
        header[16] = 16; header[17] = 0; header[18] = 0; header[19] = 0
        header[20] = 1; header[21] = 0 // PCM
        header[22] = channels.toByte(); header[23] = 0
        header[24] = (sampleRate and 0xff).toByte()
        header[25] = ((sampleRate shr 8) and 0xff).toByte()
        header[26] = ((sampleRate shr 16) and 0xff).toByte()
        header[27] = ((sampleRate shr 24) and 0xff).toByte()
        header[28] = (byteRate and 0xff).toByte()
        header[29] = ((byteRate shr 8) and 0xff).toByte()
        header[30] = ((byteRate shr 16) and 0xff).toByte()
        header[31] = ((byteRate shr 24) and 0xff).toByte()
        header[32] = (channels * 2).toByte(); header[33] = 0
        header[34] = 16; header[35] = 0
        header[36] = 'd'.code.toByte(); header[37] = 'a'.code.toByte(); header[38] = 't'.code.toByte(); header[39] = 'a'.code.toByte()
        header[40] = (totalAudioLen and 0xff).toByte()
        header[41] = ((totalAudioLen shr 8) and 0xff).toByte()
        header[42] = ((totalAudioLen shr 16) and 0xff).toByte()
        header[43] = ((totalAudioLen shr 24) and 0xff).toByte()

        val out = ByteArray(44 + totalAudioLen)
        System.arraycopy(header, 0, out, 0, 44)
        var offset = 44
        for (sample in pcm) {
            out[offset++] = (sample.toInt() and 0xff).toByte()
            out[offset++] = ((sample.toInt() shr 8) and 0xff).toByte()
        }
        return out
    }
}
