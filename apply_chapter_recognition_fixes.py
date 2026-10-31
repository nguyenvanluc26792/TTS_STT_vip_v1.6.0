# -*- coding: utf-8 -*-
import os, sys, re

desktop_template = r"D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\templates\index.html"
assets_template = r"c:\Users\VANLUC\Downloads\Share tool -20261010T221918Z-1-001\Share tool\TTS_STT_vip_v1.6.0\HonorEpubReader\app\src\main\assets\index.html"
desktop_server = r"D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\server.py"

print(f"Loading {desktop_template}...")
with open(desktop_template, "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

# 1. Update loadNrBookById chapter normalization & auto-jump to first real chapter
old_load_book_target = """          const chLen = Array.isArray(data.chapters) ? data.chapters.length : 1;
          const targetCh = Math.min(Math.max(0, data.lastChapter || 0), Math.max(0, chLen - 1));
          const targetPara = data.lastParagraph || 0;
          const curCh = data.chapters[targetCh];"""

new_load_book_target = """          const chLen = Array.isArray(data.chapters) ? data.chapters.length : 1;
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

content = content.replace(old_load_book_target, new_load_book_target, 1)
print("1. Updated loadNrBookById target chapter logic")

# 2. Update data.chapters.forEach normalization
old_foreach = """          // Chuẩn hóa và lọc sạch tiêu đề chương nếu bị lặp từ
          data.chapters.forEach((ch, idx) => {
            if (!ch.title || ch.title.length > 80 || (ch.title.match(/chương/gi) || []).length > 2) {
              ch.title = `Chương ${idx + 1}`;
            }
          });"""

new_foreach = """          // Chuẩn hóa và nhận diện chính xác tên chương thực tế từ nội dung
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

content = content.replace(old_foreach, new_foreach, 1)
print("2. Updated data.chapters.forEach smart chapter title detection")

# 3. Update updateHonorTitles and onHonorChapterSliderChange
old_honor_titles = """      let cTitle = '';
      if (bookData && bookData.chapters && bookData.chapters[currentChapterIndex]) {
        const ch = bookData.chapters[currentChapterIndex];
        cTitle = ch.title || `Chương ${currentChapterIndex + 1}`;
      } else {
        cTitle = `Chương ${(currentChapterIndex || 0) + 1}`;
      }

      if (topChap) { topChap.textContent = ''; topChap.style.display = 'none'; }
      if (activeChap) activeChap.textContent = cTitle;"""

new_honor_titles = """      let cTitle = '';
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

content = content.replace(old_honor_titles, new_honor_titles, 1)
print("3. Updated updateHonorTitles")

old_slider_change = """    function onHonorChapterSliderChange(val) {
      const activeChap = document.getElementById('honorTopActiveChap');
      const idx = parseInt(val, 10);
      if (bookData && bookData.chapters && bookData.chapters[idx]) {
        const ch = bookData.chapters[idx];
        if (activeChap) activeChap.textContent = ch.title || `Chương ${idx + 1}`;
      } else if (activeChap) {
        activeChap.textContent = `Chương ${idx + 1}`;
      }
    }"""

new_slider_change = """    function onHonorChapterSliderChange(val) {
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

content = content.replace(old_slider_change, new_slider_change, 1)
print("4. Updated onHonorChapterSliderChange")

# 4. Update loadChapter title indicator
old_load_ch = """      const ch = bookData.chapters[idx];
      if (!ch) return;
      let displayTitle = ch.title || `Chương ${idx + 1}`;
      if (displayTitle.length > 80 || (displayTitle.match(/chương/gi) || []).length > 2) {
        displayTitle = `Chương ${idx + 1}`;
      }"""

new_load_ch = """      const ch = bookData.chapters[idx];
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

content = content.replace(old_load_ch, new_load_ch, 1)
print("5. Updated loadChapter display title logic")

# Save to desktop template
with open(desktop_template, "w", encoding="utf-8") as f:
    f.write(content)
print(f"6. Saved to {desktop_template}")

# Sync to Android Assets template
with open(assets_template, "w", encoding="utf-8") as f:
    f.write(content)
print(f"7. Synced to {assets_template}")

# Bump server.py version
with open(desktop_server, "r", encoding="utf-8", errors="ignore") as f:
    server_code = f.read()

server_code = re.sub(r'"version":\s*"[^"]+"', '"version": "v1.6.17-honor-real-chapter-detection"', server_code, count=1)
with open(desktop_server, "w", encoding="utf-8") as f:
    f.write(server_code)
print("8. Bumped server.py version to v1.6.17-honor-real-chapter-detection")

print("SUCCESS: Chapter recognition fixes applied everywhere!")
