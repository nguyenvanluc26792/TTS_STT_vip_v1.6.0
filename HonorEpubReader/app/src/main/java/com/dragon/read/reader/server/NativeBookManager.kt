package com.dragon.read.reader.server

import android.content.Context
import android.util.Log
import org.json.JSONArray
import org.json.JSONObject
import org.jsoup.Jsoup
import com.tom_roush.pdfbox.android.PDFBoxResourceLoader
import com.tom_roush.pdfbox.pdmodel.PDDocument
import com.tom_roush.pdfbox.text.PDFTextStripper
import java.io.File
import java.io.InputStream
import java.util.zip.ZipFile
import java.util.zip.ZipInputStream

class NativeBookManager(private val context: Context) {
    companion object {
        private const val TAG = "NativeBookManager"
        private const val MAX_SAVED_BOOKS = 10
        private var pdfBoxInitialized = false
    }

    private val booksDir = File(context.filesDir, "saved_books").apply { mkdirs() }
    private val indexFile = File(booksDir, "library_index.json")

    init {
        if (!pdfBoxInitialized) {
            try {
                PDFBoxResourceLoader.init(context.applicationContext)
                pdfBoxInitialized = true
            } catch (e: Exception) {
                Log.w(TAG, "Lỗi khởi tạo PDFBoxResourceLoader: ${e.message}")
            }
        }
    }

    fun getLibraryIndex(): JSONArray {
        if (indexFile.exists()) {
            try {
                val content = indexFile.readText(Charsets.UTF_8)
                return JSONArray(content)
            } catch (e: Exception) {
                Log.w(TAG, "Lỗi đọc library_index.json: ${e.message}")
            }
        }
        val entries = JSONArray()
        val files = booksDir.listFiles { f -> f.extension == "json" && f.name != "library_index.json" }
            ?.sortedByDescending { it.lastModified() } ?: emptyList()

        for (f in files) {
            try {
                val json = JSONObject(f.readText(Charsets.UTF_8))
                val entry = JSONObject().apply {
                    put("id", json.optString("id", f.nameWithoutExtension))
                    put("title", json.optString("title", f.nameWithoutExtension))
                    put("author", json.optString("author", "Không rõ"))
                    put("totalChapters", json.optJSONArray("chapters")?.length() ?: 0)
                    put("lastChapter", json.optInt("lastChapter", 0))
                    put("lastParagraph", json.optInt("lastParagraph", 0))
                    put("is_web", json.optBoolean("is_web", false))
                }
                entries.put(entry)
            } catch (e: Exception) {
                // ignore corrupted book
            }
        }
        saveLibraryIndex(entries)
        return entries
    }

    private fun saveLibraryIndex(indexData: JSONArray) {
        try {
            indexFile.writeText(indexData.toString(2), Charsets.UTF_8)
        } catch (e: Exception) {
            Log.e(TAG, "Lỗi lưu library_index.json: ${e.message}")
        }
    }

    @Volatile
    private var cachedBookId: String? = null
    @Volatile
    private var cachedBookRaw: String? = null

    fun getTotalChapters(bookId: String): Int {
        if (indexFile.exists()) {
            try {
                val content = indexFile.readText(Charsets.UTF_8)
                val arr = JSONArray(content)
                for (i in 0 until arr.length()) {
                    val item = arr.optJSONObject(i) ?: continue
                    if (item.optString("id") == bookId) {
                        return item.optInt("totalChapters", 0)
                    }
                }
            } catch (e: Exception) {
                Log.w(TAG, "Lỗi đọc getTotalChapters: ${e.message}")
            }
        }
        return 0
    }

    fun getBookRawJson(bookId: String): String? {
        if (cachedBookId == bookId && cachedBookRaw != null) {
            return cachedBookRaw
        }
        val file = File(booksDir, "$bookId.json")
        if (file.exists()) {
            try {
                val raw = file.readText(Charsets.UTF_8)
                cachedBookId = bookId
                cachedBookRaw = raw
                return raw
            } catch (e: Exception) {
                Log.e(TAG, "Lỗi đọc getBookRawJson: ${e.message}")
            }
        }
        return null
    }

    fun getBook(bookId: String): JSONObject? {
        val raw = getBookRawJson(bookId)
        if (raw != null) {
            try {
                val book = JSONObject(raw)
                val index = getLibraryIndex()
                for (i in 0 until index.length()) {
                    val item = index.optJSONObject(i) ?: continue
                    if (item.optString("id") == bookId) {
                        book.put("lastChapter", item.optInt("lastChapter", 0))
                        book.put("lastParagraph", item.optInt("lastParagraph", 0))
                        break
                    }
                }
                return book
            } catch (e: Exception) {
                Log.e(TAG, "Lỗi parse getBook: ${e.message}")
            }
        }
        return null
    }

    fun updateProgress(bookId: String, chapter: Int, paragraph: Int) {
        try {
            val index = getLibraryIndex()
            var updatedItem: JSONObject? = null
            val newIndex = JSONArray()

            for (i in 0 until index.length()) {
                val item = index.getJSONObject(i)
                if (item.optString("id") == bookId) {
                    item.put("lastChapter", chapter)
                    item.put("lastParagraph", paragraph)
                    updatedItem = item
                } else {
                    newIndex.put(item)
                }
            }
            // Đưa cuốn sách đang đọc lên đầu danh sách để /api/last-book luôn lấy đúng cuốn đang đọc
            if (updatedItem != null) {
                val finalIndex = JSONArray()
                finalIndex.put(updatedItem)
                for (i in 0 until newIndex.length()) {
                    finalIndex.put(newIndex.getJSONObject(i))
                }
                saveLibraryIndex(finalIndex)
            } else {
                saveLibraryIndex(newIndex)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Lỗi cập nhật tiến độ đọc: ${e.message}")
        }
    }

    fun deleteBook(bookId: String): Boolean {
        if (cachedBookId == bookId) {
            cachedBookId = null
            cachedBookRaw = null
        }
        val file = File(booksDir, "$bookId.json")
        val deleted = file.delete()
        val index = getLibraryIndex()
        val newIndex = JSONArray()
        for (i in 0 until index.length()) {
            val item = index.getJSONObject(i)
            if (item.optString("id") != bookId) {
                newIndex.put(item)
            }
        }
        saveLibraryIndex(newIndex)
        return deleted
    }

    fun parseAndSaveBook(inputStream: InputStream, filename: String): JSONObject {
        val lower = filename.lowercase()
        return when {
            lower.endsWith(".epub") -> parseEpub(inputStream, filename)
            lower.endsWith(".pdf") -> parsePdf(inputStream, filename)
            else -> parseTxt(inputStream, filename)
        }
    }

    private fun parsePdf(inputStream: InputStream, filename: String): JSONObject {
        val chapters = JSONArray()
        val title = filename.substringBeforeLast(".")
        try {
            val doc = PDDocument.load(inputStream)
            val totalPages = doc.numberOfPages
            val stripper = PDFTextStripper()

            // Chia tài liệu PDF thành các chương đọc hợp lý (mỗi chương 3-5 trang hoặc theo cấu trúc)
            val pagesPerChapter = 5
            var chIdx = 1

            for (startPage in 1..totalPages step pagesPerChapter) {
                val endPage = Math.min(startPage + pagesPerChapter - 1, totalPages)
                stripper.startPage = startPage
                stripper.endPage = endPage
                val text = stripper.getText(doc) ?: ""

                val rawLines = text.lines()
                    .map { it.trim() }
                    .filter { it.isNotEmpty() && !it.matches(Regex("""^\d+$""")) }

                // Gom dòng thành đoạn văn đọc tự nhiên
                val paras = JSONArray()
                var currentBlock = StringBuilder()

                for (line in rawLines) {
                    if (currentBlock.isNotEmpty() && (line.endsWith(".") || line.endsWith("!") || line.endsWith("?") || line.endsWith(":") || line.length > 80)) {
                        currentBlock.append(" ").append(line)
                        paras.put(currentBlock.toString().trim())
                        currentBlock = StringBuilder()
                    } else if (currentBlock.isNotEmpty()) {
                        currentBlock.append(" ").append(line)
                    } else {
                        currentBlock.append(line)
                    }
                }
                if (currentBlock.isNotEmpty()) {
                    paras.put(currentBlock.toString().trim())
                }

                if (paras.length() > 0) {
                    val chTitle = if (totalPages <= pagesPerChapter) {
                        title
                    } else {
                        "Trang $startPage - $endPage"
                    }
                    chapters.put(JSONObject().apply {
                        put("id", "ch_$chIdx")
                        put("title", chTitle)
                        put("paragraphs", paras)
                    })
                    chIdx++
                }
            }
            doc.close()
        } catch (e: Exception) {
            Log.e(TAG, "Lỗi trích xuất văn bản PDF: ${e.message}", e)
            chapters.put(JSONObject().apply {
                put("id", "ch_1")
                put("title", title)
                put("paragraphs", JSONArray().apply {
                    put("Lỗi trích xuất văn bản PDF: ${e.message}. Tệp PDF có thể được bảo vệ bằng mật khẩu hoặc chứa trang quét dạng ảnh.")
                })
            })
        }

        if (chapters.length() == 0) {
            chapters.put(JSONObject().apply {
                put("id", "ch_1")
                put("title", title)
                put("paragraphs", JSONArray().apply {
                    put("Tài liệu PDF không có nội dung chữ trích xuất được (có thể là tài liệu scan dạng hình ảnh).")
                })
            })
        }

        val bookId = "book_" + System.currentTimeMillis()
        val book = JSONObject().apply {
            put("id", bookId)
            put("title", title)
            put("author", "Tài liệu PDF")
            put("totalChapters", chapters.length())
            put("lastChapter", 0)
            put("lastParagraph", 0)
            put("chapters", chapters)
        }

        saveBookToDisk(book)
        return book
    }

    private fun parseTxt(inputStream: InputStream, filename: String): JSONObject {
        val text = inputStream.bufferedReader(Charsets.UTF_8).use { it.readText() }
        val lines = text.lines().map { it.trim() }.filter { it.isNotEmpty() }

        val chapters = JSONArray()
        var curParas = JSONArray()
        var curTitle = "Chương 1"
        var chIdx = 1

        val chRegex = Regex("""^(Chương|Chapter|Hồi|Tiết)\s+\d+.*""", RegexOption.IGNORE_CASE)

        for (line in lines) {
            if (chRegex.matches(line) && curParas.length() > 0) {
                chapters.put(JSONObject().apply {
                    put("id", "ch_$chIdx")
                    put("title", curTitle)
                    put("paragraphs", curParas)
                })
                chIdx++
                curTitle = line
                curParas = JSONArray()
            } else {
                curParas.put(line)
            }
        }
        if (curParas.length() > 0) {
            chapters.put(JSONObject().apply {
                put("id", "ch_$chIdx")
                put("title", curTitle)
                put("paragraphs", curParas)
            })
        }

        val bookId = "book_" + System.currentTimeMillis()
        val title = filename.substringBeforeLast(".")
        val book = JSONObject().apply {
            put("id", bookId)
            put("title", title)
            put("author", "Tài liệu tải lên")
            put("totalChapters", chapters.length())
            put("lastChapter", 0)
            put("lastParagraph", 0)
            put("chapters", chapters)
        }

        saveBookToDisk(book)
        return book
    }

    private fun parseEpub(inputStream: InputStream, filename: String): JSONObject {
        val tempFile = File.createTempFile("epub_parse_", ".epub", context.cacheDir)
        try {
            tempFile.outputStream().use { out ->
                inputStream.copyTo(out)
            }
            val zipFile = ZipFile(tempFile)
            try {
                return parseEpubFromZip(zipFile, filename)
            } finally {
                try { zipFile.close() } catch (_: Exception) {}
            }
        } finally {
            try { tempFile.delete() } catch (_: Exception) {}
        }
    }

    private fun normalizeZipPath(path: String): String {
        val clean = path.replace("\\", "/").trimStart('/')
        val parts = clean.split("/")
        val stack = mutableListOf<String>()
        for (p in parts) {
            if (p.isEmpty() || p == ".") continue
            if (p == "..") {
                if (stack.isNotEmpty()) stack.removeAt(stack.size - 1)
            } else {
                stack.add(p)
            }
        }
        return stack.joinToString("/")
    }

    private object NaturalOrderComparator : Comparator<String> {
        private val SPLIT_REGEX = Regex("(?<=\\D)(?=\\d)|(?<=\\d)(?=\\D)")
        override fun compare(s1: String, s2: String): Int {
            val chunks1 = s1.split(SPLIT_REGEX)
            val chunks2 = s2.split(SPLIT_REGEX)
            val len = minOf(chunks1.size, chunks2.size)
            for (i in 0 until len) {
                val c1 = chunks1[i]
                val c2 = chunks2[i]
                val n1 = c1.toLongOrNull()
                val n2 = c2.toLongOrNull()
                if (n1 != null && n2 != null) {
                    val numComp = n1.compareTo(n2)
                    if (numComp != 0) return numComp
                } else {
                    val strComp = c1.compareTo(c2, ignoreCase = true)
                    if (strComp != 0) return strComp
                }
            }
            return chunks1.size.compareTo(chunks2.size)
        }
    }

    private fun parseEpubFromZip(zipFile: ZipFile, filename: String): JSONObject {
        var opfPath = ""
        val containerEntry = zipFile.getEntry("META-INF/container.xml") ?: zipFile.getEntry("meta-inf/container.xml")
        if (containerEntry != null) {
            try {
                val xml = zipFile.getInputStream(containerEntry).bufferedReader(Charsets.UTF_8).readText()
                val doc = Jsoup.parse(xml, "", org.jsoup.parser.Parser.xmlParser())
                opfPath = doc.select("rootfile").attr("full-path").trim()
            } catch (e: Exception) {
                Log.w(TAG, "Lỗi đọc container.xml: ${e.message}")
            }
        }
        if (opfPath.isEmpty()) {
            val opfEntry = zipFile.entries().asSequence().firstOrNull { it.name.endsWith(".opf", ignoreCase = true) }
            if (opfEntry != null) opfPath = opfEntry.name
        }

        val opfDir = if (opfPath.contains("/")) opfPath.substringBeforeLast("/") + "/" else ""
        var bookTitle = filename.substringBeforeLast(".")
        var bookAuthor = "Ebook EPUB"
        val manifest = mutableMapOf<String, String>()
        val spine = mutableListOf<String>()
        var tocHref = ""

        if (opfPath.isNotEmpty()) {
            val opfEntry = zipFile.getEntry(opfPath)
            if (opfEntry != null) {
                try {
                    val opfXml = zipFile.getInputStream(opfEntry).bufferedReader(Charsets.UTF_8).readText()
                    val opfDoc = Jsoup.parse(opfXml, "", org.jsoup.parser.Parser.xmlParser())

                    val parsedTitle = opfDoc.select("dc|title, title").firstOrNull()?.text()?.trim() ?: ""
                    if (parsedTitle.isNotEmpty()) bookTitle = parsedTitle

                    val parsedAuthor = opfDoc.select("dc|creator, creator").firstOrNull()?.text()?.trim() ?: ""
                    if (parsedAuthor.isNotEmpty()) bookAuthor = parsedAuthor

                    for (item in opfDoc.select("item")) {
                        val id = item.attr("id").trim()
                        val href = item.attr("href").trim()
                        val mediaType = item.attr("media-type").trim()
                        if (id.isNotEmpty() && href.isNotEmpty()) {
                            val decoded = try { java.net.URLDecoder.decode(href, "UTF-8") } catch (_: Exception) { href }
                            val fullPath = normalizeZipPath(opfDir + decoded)
                            manifest[id] = fullPath
                            if (mediaType.contains("x-dtbncx") || href.endsWith(".ncx", ignoreCase = true)) {
                                tocHref = fullPath
                            }
                        }
                    }

                    for (itemref in opfDoc.select("itemref")) {
                        val idref = itemref.attr("idref").trim()
                        if (idref.isNotEmpty()) {
                            spine.add(idref)
                        }
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "Lỗi phân tích OPF: ${e.message}", e)
                }
            }
        }

        val tocTitleMap = mutableMapOf<String, String>()
        if (tocHref.isEmpty()) {
            val ncxEntry = zipFile.entries().asSequence().firstOrNull { it.name.endsWith(".ncx", ignoreCase = true) }
            if (ncxEntry != null) tocHref = ncxEntry.name
        }
        if (tocHref.isNotEmpty()) {
            val ncxEntry = zipFile.getEntry(tocHref)
            if (ncxEntry != null) {
                try {
                    val ncxXml = zipFile.getInputStream(ncxEntry).bufferedReader(Charsets.UTF_8).readText()
                    val ncxDoc = Jsoup.parse(ncxXml, "", org.jsoup.parser.Parser.xmlParser())
                    val ncxDir = if (tocHref.contains("/")) tocHref.substringBeforeLast("/") + "/" else ""
                    for (navPoint in ncxDoc.select("navPoint")) {
                        val label = navPoint.select("navLabel > text").firstOrNull()?.text()?.trim() ?: ""
                        val src = navPoint.select("content").attr("src").substringBefore("#").trim()
                        if (label.isNotEmpty() && src.isNotEmpty()) {
                            val decoded = try { java.net.URLDecoder.decode(src, "UTF-8") } catch (_: Exception) { src }
                            val fullSrc = normalizeZipPath(ncxDir + decoded)
                            if (!tocTitleMap.containsKey(fullSrc)) {
                                tocTitleMap[fullSrc] = label
                            }
                        }
                    }
                } catch (e: Exception) {
                    Log.w(TAG, "Lỗi đọc toc.ncx: ${e.message}")
                }
            }
        }

        val orderedEntryPaths = mutableListOf<String>()
        val seenPaths = mutableSetOf<String>()

        // 1. Thứ tự đọc theo spine chuẩn EPUB
        for (idref in spine) {
            val path = manifest[idref] ?: continue
            if (!seenPaths.contains(path)) {
                val lower = path.lowercase()
                if (lower.endsWith(".html") || lower.endsWith(".xhtml") || lower.endsWith(".htm")) {
                    orderedEntryPaths.add(path)
                    seenPaths.add(path)
                }
            }
        }

        // 2. Fallback nếu spine rỗng: Thu thập tất cả file HTML và sắp xếp tự nhiên
        if (orderedEntryPaths.isEmpty()) {
            val allHtml = zipFile.entries().asSequence()
                .map { it.name }
                .filter {
                    val l = it.lowercase()
                    l.endsWith(".html") || l.endsWith(".xhtml") || l.endsWith(".htm")
                }
                .toList()
            orderedEntryPaths.addAll(allHtml.sortedWith(NaturalOrderComparator))
        }

        val chapters = JSONArray()
        var chIdx = 1
        val chapterPattern = Regex("^(?:chương|hồi|tiết|quyển|bài|tập|phần|volume|chapter)\\s*\\d+", RegexOption.IGNORE_CASE)

        for (entryPath in orderedEntryPaths) {
            val entry = zipFile.getEntry(entryPath) ?: continue
            val html = try {
                zipFile.getInputStream(entry).bufferedReader(Charsets.UTF_8).readText()
            } catch (e: Exception) {
                continue
            }
            val doc = Jsoup.parse(html)
            doc.select("script, style, noscript").remove()

            val paraList = mutableListOf<String>()
            doc.select("p, div, h1, h2, h3, h4, h5, h6").forEach { el ->
                if (el.tagName().startsWith("h") || el.children().none { it.tagName() in listOf("p", "div") }) {
                    val t = el.text().trim()
                    if (t.isNotEmpty() && t.length > 1) {
                        paraList.add(t)
                    }
                }
            }
            if (paraList.isEmpty()) {
                doc.select("p, div").forEach { el ->
                    val t = el.text().trim()
                    if (t.isNotEmpty() && t.length > 2) {
                        paraList.add(t)
                    }
                }
            }

            if (paraList.isEmpty()) continue

            // Xác định tiêu đề chương
            var chTitle = tocTitleMap[entryPath] ?: ""
            if (chTitle.isEmpty() && entryPath.contains("/")) {
                chTitle = tocTitleMap[entryPath.substringAfterLast("/")] ?: ""
            }

            if (chTitle.isEmpty()) {
                val hText = doc.select("h1, h2, h3").firstOrNull()?.text()?.trim() ?: ""
                if (hText.isNotEmpty() && hText.length <= 90) {
                    chTitle = hText
                }
            }

            if (chTitle.isEmpty()) {
                val dTitle = doc.title().trim()
                if (dTitle.isNotEmpty() && dTitle.length <= 90 && !dTitle.equals(bookTitle, ignoreCase = true)) {
                    chTitle = dTitle
                }
            }

            if (chTitle.isEmpty() || !chapterPattern.containsMatchIn(chTitle)) {
                for (i in 0 until minOf(5, paraList.size)) {
                    val p = paraList[i]
                    if (p.length <= 90 && chapterPattern.containsMatchIn(p)) {
                        chTitle = p
                        break
                    }
                }
            }

            if (chTitle.isEmpty()) {
                chTitle = if (paraList[0].length <= 70) paraList[0] else "Chương $chIdx"
            }

            val paras = JSONArray()
            paraList.forEach { paras.put(it) }

            chapters.put(JSONObject().apply {
                put("id", "ch_$chIdx")
                put("title", chTitle)
                put("paragraphs", paras)
            })
            chIdx++
        }

        val bookId = "book_" + System.currentTimeMillis()
        val book = JSONObject().apply {
            put("id", bookId)
            put("title", bookTitle)
            put("author", bookAuthor)
            put("totalChapters", chapters.length())
            put("lastChapter", 0)
            put("lastParagraph", 0)
            put("chapters", chapters)
        }

        repairChaptersIfScrambled(book)
        saveBookToDisk(book)
        return book
    }

    fun repairChaptersIfScrambled(book: JSONObject): Boolean {
        val chapters = book.optJSONArray("chapters") ?: return false
        val total = chapters.length()
        if (total < 4) return false

        val chapRegex = Regex("(?:chương|hồi|tiết|quyển|bài|tập|phần|chapter|chap)\\s*(\\d+)", RegexOption.IGNORE_CASE)

        data class ChapItem(val originalIndex: Int, var title: String, var chapterNum: Int?, val rawJson: JSONObject)
        val items = mutableListOf<ChapItem>()

        for (i in 0 until total) {
            val chObj = chapters.getJSONObject(i)
            var title = chObj.optString("title", "").trim()
            val paras = chObj.optJSONArray("paragraphs")

            var match = chapRegex.find(title)
            // Nếu tiêu đề không có số chương hoặc là generic như "Chương 3" trong khi đoạn văn có số thực
            if (paras != null && paras.length() > 0) {
                for (pIdx in 0 until minOf(5, paras.length())) {
                    val pText = paras.optString(pIdx, "").trim()
                    val pMatch = chapRegex.find(pText)
                    if (pMatch != null && pText.length <= 95) {
                        val pNum = pMatch.groupValues[1].toIntOrNull()
                        val curNum = match?.groupValues?.get(1)?.toIntOrNull()
                        if (curNum == null || (pNum != null && pNum != curNum && title.length < 15)) {
                            title = pText
                            chObj.put("title", title)
                            match = pMatch
                        }
                        break
                    }
                }
            }

            val num = match?.groupValues?.get(1)?.toIntOrNull()
            items.add(ChapItem(i, title, num, chObj))
        }

        val numberedList = items.filter { it.chapterNum != null }
        if (numberedList.size < total * 0.4) {
            return false
        }

        var inversions = 0
        for (i in 0 until numberedList.size - 1) {
            if (numberedList[i].chapterNum!! > numberedList[i + 1].chapterNum!!) {
                inversions++
            }
        }

        if (inversions < 2) {
            return false
        }

        Log.i(TAG, "Phát hiện $inversions vị trí nhảy lộn xộn trong $total chương sách '${book.optString("title")}'. Đang sắp xếp lại theo thứ tự số tự nhiên...")

        val frontMatter = mutableListOf<ChapItem>()
        val numberedMatter = mutableListOf<ChapItem>()
        val endMatter = mutableListOf<ChapItem>()

        var seenFirstNumbered = false
        for (item in items) {
            if (item.chapterNum == null) {
                if (!seenFirstNumbered) {
                    frontMatter.add(item)
                } else {
                    endMatter.add(item)
                }
            } else {
                seenFirstNumbered = true
                numberedMatter.add(item)
            }
        }

        numberedMatter.sortBy { it.chapterNum }

        val newChapters = JSONArray()
        var newIdx = 0
        val allSorted = frontMatter + numberedMatter + endMatter
        for (item in allSorted) {
            item.rawJson.put("index", newIdx)
            item.rawJson.put("id", "ch_${newIdx + 1}")
            newChapters.put(item.rawJson)
            newIdx++
        }

        book.put("chapters", newChapters)
        book.put("totalChapters", newChapters.length())
        return true
    }

    fun saveBookToDisk(book: JSONObject) {
        val bookId = book.getString("id")
        val file = File(booksDir, "$bookId.json")
        val raw = book.toString()
        file.writeText(raw, Charsets.UTF_8)
        cachedBookId = bookId
        cachedBookRaw = raw

        val index = getLibraryIndex()
        val newIndex = JSONArray()
        newIndex.put(JSONObject().apply {
            put("id", bookId)
            put("title", book.getString("title"))
            put("author", book.optString("author", "Không rõ"))
            put("totalChapters", book.optJSONArray("chapters")?.length() ?: 0)
            put("lastChapter", book.optInt("lastChapter", 0))
            put("lastParagraph", book.optInt("lastParagraph", 0))
            put("is_web", book.optBoolean("is_web", false))
        })

        for (i in 0 until index.length()) {
            val item = index.getJSONObject(i)
            if (item.optString("id") != bookId && newIndex.length() < MAX_SAVED_BOOKS) {
                newIndex.put(item)
            }
        }
        saveLibraryIndex(newIndex)
    }
}
