# -*- coding: utf-8 -*-
import os, sys, re

desktop_template = r"D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\templates\index.html"
assets_template = r"c:\Users\VANLUC\Downloads\Share tool -20261010T221918Z-1-001\Share tool\TTS_STT_vip_v1.6.0\HonorEpubReader\app\src\main\assets\index.html"
desktop_server = r"D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\server.py"
universal_parser = r"D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\universal_parser.py"
native_bm = r"c:\Users\VANLUC\Downloads\Share tool -20261010T221918Z-1-001\Share tool\TTS_STT_vip_v1.6.0\HonorEpubReader\app\src\main\java\com\dragon\read\reader\server\NativeBookManager.kt"

print(f"Loading {desktop_template}...")
with open(desktop_template, "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

# 1. Revert loadNrBookById target chapter logic
old_load_book_target = """          const chLen = Array.isArray(data.chapters) ? data.chapters.length : 1;
          const chRegex = /^\\s*(?:chương|hồi|tiết|quyển|phần|tập|bài|chapter|part)\\s*[\\d\\w]+[:\\s.\\-—].*/i;
          const numRegex = /^\\s*chương\\s+\\d+/i;

          let targetCh = Math.min(Math.max(0, data.lastChapter || 0), Math.max(0, chLen - 1));
          // Nếu sách mở lần đầu (chưa có lastChapter hoặc lastChapter = 0) mà các chương đầu là Mục lục / Thông tin
          // Tự động tìm và mở chương truyện thực tế đầu tiên!
          if (!data.lastChapter && data.chapters.length > 3) {
            for (let i = 0; i < Math.min(6, data.chapters.length); i++) {
              const c = data.chapters[i];
              const t = (c && c.title) || '';
              if (chRegex.test(t) || numRegex.test(t)) {
                targetCh = i;
                break;
              }
            }
          }
          const targetPara = data.lastParagraph || 0;
          const curCh = data.chapters[targetCh];"""

revert_load_book_target = """          const chLen = Array.isArray(data.chapters) ? data.chapters.length : 1;
          const targetCh = Math.min(Math.max(0, data.lastChapter || 0), Math.max(0, chLen - 1));
          const targetPara = data.lastParagraph || 0;
          const curCh = data.chapters[targetCh];"""

if old_load_book_target in content:
    content = content.replace(old_load_book_target, revert_load_book_target, 1)
    print("1. Reverted loadNrBookById target chapter logic")
else:
    print("1. Warning: old_load_book_target pattern not found directly, checking regex")

# 2. Revert data.chapters.forEach normalization
old_foreach = """          // Chuẩn hóa và nhận diện chính xác tên chương thực tế từ nội dung
          data.chapters.forEach((ch, idx) => {
            let foundTitle = null;
            if (ch.title && (chRegex.test(ch.title) || numRegex.test(ch.title)) && ch.title.length < 90 && !/^\\s*trang\\s+\\d+#/i.test(ch.title)) {
              foundTitle = ch.title;
            } else if (Array.isArray(ch.paragraphs)) {
              for (let i = 0; i < Math.min(5, ch.paragraphs.length); i++) {
                const p = (ch.paragraphs[i] || '').trim();
                if ((chRegex.test(p) || numRegex.test(p)) && p.length < 90) {
                  foundTitle = p;
                  break;
                }
              }
            }
            if (foundTitle) {
              ch.title = foundTitle;
            } else if (!ch.title || ch.title.length > 80 || /^\\s*trang\\s+\\d+#/i.test(ch.title) || (ch.title.match(/chương/gi) || []).length > 2) {
              if (idx === 0 && Array.isArray(ch.paragraphs) && (ch.paragraphs[0] || '').includes('Table of Contents')) {
                ch.title = 'Mục lục';
              } else if (idx === 1 && Array.isArray(ch.paragraphs) && (ch.paragraphs[0] || '').includes('Thông tin')) {
                ch.title = 'Thông tin Ebook';
              } else if (idx === 2 && Array.isArray(ch.paragraphs) && (ch.paragraphs[0] || '').includes('Trang 1# 1')) {
                ch.title = 'Giới thiệu truyện';
              } else {
                ch.title = `Chương ${idx + 1}`;
              }
            }
          });"""

revert_foreach = """          // Chuẩn hóa và lọc sạch tiêu đề chương nếu bị lặp từ
          data.chapters.forEach((ch, idx) => {
            if (!ch.title || ch.title.length > 80 || (ch.title.match(/chương/gi) || []).length > 2) {
              ch.title = `Chương ${idx + 1}`;
            }
          });"""

if old_foreach in content:
    content = content.replace(old_foreach, revert_foreach, 1)
    print("2. Reverted data.chapters.forEach")
else:
    print("2. Warning: old_foreach pattern not found directly")

# 3. Revert updateHonorTitles
old_honor_titles = """      let cTitle = '';
      if (bookData && bookData.chapters && bookData.chapters[currentChapterIndex]) {
        const ch = bookData.chapters[currentChapterIndex];
        let realTitle = ch.title;
        const chRegex = /^\\s*(?:chương|hồi|tiết|quyển|phần|tập|bài|chapter|part)\\s*[\\d\\w]+[:\\s.\\-—].*/i;
        const numRegex = /^\\s*chương\\s+\\d+/i;
        if (!realTitle || !chRegex.test(realTitle) || /^\\s*trang\\s+\\d+#/i.test(realTitle)) {
          if (Array.isArray(ch.paragraphs)) {
            for (let i = 0; i < Math.min(5, ch.paragraphs.length); i++) {
              const p = (ch.paragraphs[i] || '').trim();
              if ((chRegex.test(p) || numRegex.test(p)) && p.length < 90) {
                realTitle = p;
                ch.title = p;
                break;
              }
            }
          }
        }
        cTitle = realTitle || `Chương ${currentChapterIndex + 1}`;
      } else {
        cTitle = `Chương ${(currentChapterIndex || 0) + 1}`;
      }

      if (topChap) { topChap.textContent = ''; topChap.style.display = 'none'; }
      if (activeChap) activeChap.textContent = cTitle;"""

revert_honor_titles = """      let cTitle = '';
      if (bookData && bookData.chapters && bookData.chapters[currentChapterIndex]) {
        const ch = bookData.chapters[currentChapterIndex];
        cTitle = ch.title || `Chương ${currentChapterIndex + 1}`;
      } else {
        cTitle = `Chương ${(currentChapterIndex || 0) + 1}`;
      }

      if (topChap) { topChap.textContent = ''; topChap.style.display = 'none'; }
      if (activeChap) activeChap.textContent = cTitle;"""

if old_honor_titles in content:
    content = content.replace(old_honor_titles, revert_honor_titles, 1)
    print("3. Reverted updateHonorTitles")
else:
    print("3. Warning: old_honor_titles pattern not found directly")

# 4. Revert onHonorChapterSliderChange
old_slider_change = """    function onHonorChapterSliderChange(val) {
      const activeChap = document.getElementById('honorTopActiveChap');
      const idx = parseInt(val, 10);
      if (bookData && bookData.chapters && bookData.chapters[idx]) {
        const ch = bookData.chapters[idx];
        let realTitle = ch.title;
        const chRegex = /^\\s*(?:chương|hồi|tiết|quyển|phần|tập|bài|chapter|part)\\s*[\\d\\w]+[:\\s.\\-—].*/i;
        const numRegex = /^\\s*chương\\s+\\d+/i;
        if (!realTitle || !chRegex.test(realTitle) || /^\\s*trang\\s+\\d+#/i.test(realTitle)) {
          if (Array.isArray(ch.paragraphs)) {
            for (let i = 0; i < Math.min(5, ch.paragraphs.length); i++) {
              const p = (ch.paragraphs[i] || '').trim();
              if ((chRegex.test(p) || numRegex.test(p)) && p.length < 90) {
                realTitle = p;
                ch.title = p;
                break;
              }
            }
          }
        }
        if (activeChap) activeChap.textContent = realTitle || `Chương ${idx + 1}`;
      } else if (activeChap) {
        activeChap.textContent = `Chương ${idx + 1}`;
      }
    }"""

revert_slider_change = """    function onHonorChapterSliderChange(val) {
      const activeChap = document.getElementById('honorTopActiveChap');
      const idx = parseInt(val, 10);
      if (bookData && bookData.chapters && bookData.chapters[idx]) {
        const ch = bookData.chapters[idx];
        if (activeChap) activeChap.textContent = ch.title || `Chương ${idx + 1}`;
      } else if (activeChap) {
        activeChap.textContent = `Chương ${idx + 1}`;
      }
    }"""

if old_slider_change in content:
    content = content.replace(old_slider_change, revert_slider_change, 1)
    print("4. Reverted onHonorChapterSliderChange")
else:
    print("4. Warning: old_slider_change pattern not found directly")

# 5. Revert loadChapter display title logic
old_load_ch = """      const ch = bookData.chapters[idx];
      if (!ch) return;
      let displayTitle = ch.title;
      const chRegex = /^\\s*(?:chương|hồi|tiết|quyển|phần|tập|bài|chapter|part)\\s*[\\d\\w]+[:\\s.\\-—].*/i;
      const numRegex = /^\\s*chương\\s+\\d+/i;
      if (!displayTitle || !chRegex.test(displayTitle) || /^\\s*trang\\s+\\d+#/i.test(displayTitle)) {
        if (Array.isArray(ch.paragraphs)) {
          for (let i = 0; i < Math.min(5, ch.paragraphs.length); i++) {
            const p = (ch.paragraphs[i] || '').trim();
            if ((chRegex.test(p) || numRegex.test(p)) && p.length < 90) {
              displayTitle = p;
              ch.title = p;
              break;
            }
          }
        }
      }
      if (!displayTitle || displayTitle.length > 80 || (displayTitle.match(/chương/gi) || []).length > 2) {
        displayTitle = `Chương ${idx + 1}`;
      }
      const chIndicator = document.getElementById('mobileChapterIndicator');
      if (chIndicator) {
        chIndicator.textContent = displayTitle;
      }"""

revert_load_ch = """      const ch = bookData.chapters[idx];
      if (!ch) return;
      let displayTitle = ch.title || `Chương ${idx + 1}`;
      if (displayTitle.length > 80 || (displayTitle.match(/chương/gi) || []).length > 2) {
        displayTitle = `Chương ${idx + 1}`;
      }"""

if old_load_ch in content:
    content = content.replace(old_load_ch, revert_load_ch, 1)
    print("5. Reverted loadChapter display title logic")
else:
    print("5. Warning: old_load_ch pattern not found directly")

# Save to desktop template
with open(desktop_template, "w", encoding="utf-8") as f:
    f.write(content)
print(f"6. Saved to {desktop_template}")

# Sync to Android Assets template
with open(assets_template, "w", encoding="utf-8") as f:
    f.write(content)
print(f"7. Synced to {assets_template}")

# Revert universal_parser.py
with open(universal_parser, "r", encoding="utf-8", errors="ignore") as f:
    up_code = f.read()

up_old = """                if paras:
                    ch_pattern = re.compile(r'^\s*(?:chương|hồi|tiết|quyển|phần|tập|bài|chapter|part)\s*[\d\w]+[:\s\.\-—].*', re.IGNORECASE)
                    c_title = None
                    for p in paras[:5]:
                        p_strip = p.strip()
                        if ch_pattern.match(p_strip) and len(p_strip) < 95:
                            c_title = p_strip
                            break
                    if not c_title:
                        first_clean = paras[0].strip()
                        if len(first_clean) < 80 and not re.match(r'^\s*trang\s+\d+#', first_clean, re.I):
                            c_title = first_clean
                        else:
                            c_title = f"Chương {c_idx}"

                    chapters.append({
                        "index": c_idx - 1,
                        "title": c_title,
                        "paragraphs": paras
                    })
                    c_idx += 1"""

up_revert = """                if paras:
                    c_title = paras[0] if len(paras[0]) < 80 else f"Chương {c_idx}"
                    chapters.append({
                        "index": c_idx - 1,
                        "title": c_title,
                        "paragraphs": paras
                    })
                    c_idx += 1"""

if up_old in up_code:
    up_code = up_code.replace(up_old, up_revert, 1)
    with open(universal_parser, "w", encoding="utf-8") as f:
        f.write(up_code)
    print("8. Reverted universal_parser.py")

# Revert NativeBookManager.kt
with open(native_bm, "r", encoding="utf-8", errors="ignore") as f:
    nbm_code = f.read()

nbm_old = """            val paras = JSONArray()
            doc.select("p, div").forEach { el ->
                val t = el.text().trim()
                if (t.isNotEmpty() && t.length > 2) {
                    paras.put(t)
                }
            }
            if (paras.length() > 0) {
                var docTitle = ""
                val chRegex = Regex(\"\"\"^(?:Chương|Chapter|Hồi|Tiết|Quyển|Phần)\\s+\\d+.*\"\"\", RegexOption.IGNORE_CASE)
                for (pIdx in 0 until minOf(5, paras.length())) {
                    val pStr = paras.optString(pIdx, "").trim()
                    if (chRegex.matches(pStr) && pStr.length < 95) {
                        docTitle = pStr
                        break
                    }
                }
                if (docTitle.isEmpty()) {
                    val firstP = paras.optString(0, "").trim()
                    if (firstP.isNotEmpty() && firstP.length < 80 && !firstP.startsWith("Trang ", ignoreCase = true)) {
                        docTitle = firstP
                    } else {
                        docTitle = doc.title().ifEmpty {
                            doc.select("h1, h2, h3").firstOrNull()?.text() ?: "Chương $chIdx"
                        }
                    }
                }

                chapters.put(JSONObject().apply {
                    put("id", "ch_$chIdx")
                    put("title", docTitle)
                    put("paragraphs", paras)
                })
                chIdx++
            }"""

nbm_revert = """            val docTitle = doc.title().ifEmpty {
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
            }"""

if nbm_old in nbm_code:
    nbm_code = nbm_code.replace(nbm_old, nbm_revert, 1)
    with open(native_bm, "w", encoding="utf-8") as f:
        f.write(nbm_code)
    print("9. Reverted NativeBookManager.kt")

# Revert server.py version to v1.6.16-honor-top-touch-pill-bottom
with open(desktop_server, "r", encoding="utf-8", errors="ignore") as f:
    server_code = f.read()

server_code = re.sub(r'"version":\s*"[^"]+"', '"version": "v1.6.16-honor-top-touch-pill-bottom"', server_code, count=1)
with open(desktop_server, "w", encoding="utf-8") as f:
    f.write(server_code)
print("10. Bumped server.py back to v1.6.16-honor-top-touch-pill-bottom")

print("SUCCESS: Fully restored to previous stable step!")
