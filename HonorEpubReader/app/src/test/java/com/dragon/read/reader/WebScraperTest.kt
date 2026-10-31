package com.dragon.read.reader

import okhttp3.OkHttpClient
import okhttp3.Request
import org.jsoup.Jsoup
import org.junit.Test
import java.util.concurrent.TimeUnit

class WebScraperTest {
    @Test
    fun testScrapeThanMo2() {
        val url = "https://truyenhoan.com/than-mo-2.648/"
        val client = OkHttpClient.Builder()
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(15, TimeUnit.SECONDS)
            .build()

        val req = Request.Builder()
            .url(url)
            .header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            .build()

        val response = client.newCall(req).execute()
        val html = response.body?.string() ?: ""
        val doc = Jsoup.parse(html, url)

        var contentEl = doc.selectFirst("#chapter-content, .chapter-c, .entry-content, .reading-content, div.content-inner, div.content, #content, .content-body, #chapter-c, .reading-detail, .box-chap, #bookContentBody, .chap-content, .txt-content, #chr-content, .chr-c, #vungdoc, .vung-doc, .vungdoc")
        var activeDoc = doc

        println("Initial contentEl: " + (contentEl != null) + ", text len: " + (contentEl?.text()?.length ?: 0))

        if (contentEl == null || contentEl.text().trim().length < 50) {
            var firstChapUrl = ""
            val chapLinkEl = doc.select("a[href*='chuong-1.'], a[href*='chuong-1/'], a[href*='chuong-1-'], a[href*='chuong-01'], a[href*='chapter-1'], a[href*='chuong_1'], a[href*='/c1-'], a:contains(Đọc từ đầu), a:contains(Đọc ngay), a:contains(Chương 1), .list-chapter a, #list-chapter a, .chapter-list a, .list-truyen a, ul.list-chapters a, .ul-list-chaps a").firstOrNull()
            if (chapLinkEl != null) {
                firstChapUrl = chapLinkEl.absUrl("href")
                if (firstChapUrl.isEmpty()) {
                    val raw = chapLinkEl.attr("href").trim()
                    if (raw.isNotEmpty() && raw != "#" && !raw.startsWith("javascript")) {
                        firstChapUrl = if (raw.startsWith("http")) raw else try { java.net.URI(url).resolve(raw).toString() } catch (e: Exception) { "" }
                    }
                }
            }
            println("Found firstChapUrl: $firstChapUrl")

            if (firstChapUrl.isNotEmpty() && firstChapUrl != url) {
                val chReq = Request.Builder()
                    .url(firstChapUrl)
                    .header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
                    .build()
                val chResp = client.newCall(chReq).execute()
                val chHtml = chResp.body?.string() ?: ""
                val chDoc = Jsoup.parse(chHtml, firstChapUrl)
                val chContentEl = chDoc.selectFirst("#chapter-content, .chapter-c, .entry-content, .reading-content, div.content-inner, div.content, #content, .content-body, #chapter-c, .reading-detail, .box-chap, #bookContentBody, .chap-content, .txt-content, #chr-content, .chr-c, #vungdoc, .vung-doc, .vungdoc")
                println("chContentEl: " + (chContentEl != null) + ", tag: " + chContentEl?.tagName() + ", class: " + chContentEl?.className())
                if (chContentEl != null) {
                    contentEl = chContentEl
                    activeDoc = chDoc
                }
            }
        }

        if (contentEl != null) {
            contentEl.select("script, style, ins, iframe, noscript, .ads, .ads-holder").remove()
            for (br in contentEl.select("br, hr")) {
                br.replaceWith(org.jsoup.nodes.TextNode("\n"))
            }
            val parasList = mutableListOf<String>()
            val pTags = contentEl.select("p, div.line, .paragraph")
            println("pTags count: " + pTags.size)
            for (p in pTags) {
                val t = p.text().trim()
                if (t.length > 2 && !t.contains("quảng cáo", ignoreCase = true) && !t.contains("tải app", ignoreCase = true)) {
                    parasList.add(t)
                }
            }
            println("parasList after pTags: " + parasList.size)
            if (parasList.size < 3) {
                parasList.clear()
                val text = contentEl.wholeText()
                println("wholeText length: " + text.length + ", lines: " + text.lines().size)
                for (line in text.lines()) {
                    val l = line.trim()
                    if (l.length > 1 && !l.contains("quảng cáo", ignoreCase = true) && !l.contains("tải app", ignoreCase = true)) {
                        parasList.add(l)
                    }
                }
            }
            println("FINAL parasList count: " + parasList.size)
            if (parasList.isNotEmpty()) {
                println("First para: " + parasList[0].take(60))
            }
        }
    }
}
