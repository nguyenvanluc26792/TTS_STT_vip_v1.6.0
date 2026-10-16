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

    fun getBook(bookId: String): JSONObject? {
        val file = File(booksDir, "$bookId.json")
        if (file.exists()) {
            try {
                return JSONObject(file.readText(Charsets.UTF_8))
            } catch (e: Exception) {
                Log.e(TAG, "Lỗi đọc sách $bookId: ${e.message}")
            }
        }
        return null
    }

    fun updateProgress(bookId: String, chapter: Int, paragraph: Int) {
        val file = File(booksDir, "$bookId.json")
        if (file.exists()) {
            try {
                val book = JSONObject(file.readText(Charsets.UTF_8))
                book.put("lastChapter", chapter)
                book.put("lastParagraph", paragraph)
                file.writeText(book.toString(), Charsets.UTF_8)

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
    }

    fun deleteBook(bookId: String): Boolean {
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
        val chapters = JSONArray()
        val zip = ZipInputStream(inputStream)
        var entry = zip.nextEntry
        var title = filename.substringBeforeLast(".")
        var chIdx = 1

        val htmlEntries = mutableListOf<Pair<String, String>>()

        while (entry != null) {
            val name = entry.name.lowercase()
            if (name.endsWith(".html") || name.endsWith(".xhtml") || name.endsWith(".htm")) {
                val content = zip.bufferedReader(Charsets.UTF_8).readText()
                htmlEntries.add(Pair(entry.name, content))
            }
            zip.closeEntry()
            entry = zip.nextEntry
        }

        for ((entryName, html) in htmlEntries) {
            val doc = Jsoup.parse(html)
            doc.select("script, style").remove()
            val docTitle = doc.title().ifEmpty {
                doc.select("h1, h2, h3").firstOrNull()?.text() ?: "Chương $chIdx"
            }
            val paras = JSONArray()
            doc.select("p, div").forEach { el ->
                val t = el.text().trim()
                if (t.isNotEmpty() && t.length > 2) {
                    paras.put(t)
                }
            }
            if (paras.length() > 0) {
                chapters.put(JSONObject().apply {
                    put("id", "ch_$chIdx")
                    put("title", docTitle)
                    put("paragraphs", paras)
                })
                chIdx++
            }
        }

        val bookId = "book_" + System.currentTimeMillis()
        val book = JSONObject().apply {
            put("id", bookId)
            put("title", title)
            put("author", "Ebook EPUB")
            put("totalChapters", chapters.length())
            put("lastChapter", 0)
            put("lastParagraph", 0)
            put("chapters", chapters)
        }

        saveBookToDisk(book)
        return book
    }

    fun saveBookToDisk(book: JSONObject) {
        val bookId = book.getString("id")
        val file = File(booksDir, "$bookId.json")
        file.writeText(book.toString(2), Charsets.UTF_8)

        val index = getLibraryIndex()
        val newIndex = JSONArray()
        newIndex.put(JSONObject().apply {
            put("id", bookId)
            put("title", book.getString("title"))
            put("author", book.optString("author", "Không rõ"))
            put("totalChapters", book.optJSONArray("chapters")?.length() ?: 0)
            put("lastChapter", 0)
            put("lastParagraph", 0)
            put("is_web", false)
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
