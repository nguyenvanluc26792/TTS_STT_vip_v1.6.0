# -*- coding: utf-8 -*-
import os, sys, re, shutil

assets_html = r"c:\Users\VANLUC\Downloads\Share tool -20261010T221918Z-1-001\Share tool\TTS_STT_vip_v1.6.0\HonorEpubReader\app\src\main\assets\index.html"
desktop_html_d = r"D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\templates\index.html"
desktop_html_c = r"c:\Users\VANLUC\Downloads\Share tool -20261010T221918Z-1-001\Share tool\DesktopEpubReader\templates\index.html"
desktop_server_d = r"D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\server.py"
desktop_server_c = r"c:\Users\VANLUC\Downloads\Share tool -20261010T221918Z-1-001\Share tool\DesktopEpubReader\server.py"

print("Reading assets index.html...")
with open(assets_html, "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

# 1. Update top status CSS: restore compact height (28px), level with camera pill
old_top_status_css = """    #honorReaderTopStatus,
    .honor-status-top {
      position: absolute !important;
      top: 0 !important;
      left: 0 !important;
      right: 0 !important;
      height: 46px !important;
      height: max(46px, calc(env(safe-area-inset-top, 0px) + 22px)) !important;
      padding: 0 16px !important;
      padding-top: max(0px, env(safe-area-inset-top, 0px)) !important;
      padding-left: max(16px, env(safe-area-inset-left, 0px)) !important;
      display: flex !important;
      justify-content: flex-start !important;
      align-items: center !important;
      z-index: 860 !important;
      pointer-events: none !important;
      box-sizing: border-box !important;
      background: transparent !important;
      -webkit-tap-highlight-color: transparent !important;
    }"""

new_top_status_css = """    #honorReaderTopStatus,
    .honor-status-top {
      position: absolute !important;
      top: max(4px, env(safe-area-inset-top, 0px)) !important;
      left: 0 !important;
      right: 0 !important;
      height: 28px !important;
      padding: 0 16px !important;
      padding-left: max(16px, env(safe-area-inset-left, 0px)) !important;
      display: flex !important;
      justify-content: flex-start !important;
      align-items: center !important;
      z-index: 860 !important;
      pointer-events: none !important;
      box-sizing: border-box !important;
      background: transparent !important;
      -webkit-tap-highlight-color: transparent !important;
    }"""

if old_top_status_css in content:
    content = content.replace(old_top_status_css, new_top_status_css, 1)
    print("1. Restored #honorReaderTopStatus to compact 28px level with pill")
else:
    print("1. Warning: old_top_status_css not matched verbatim, using regex")
    content = re.sub(
        r'#honorReaderTopStatus,\s*\.honor-status-top\s*\{[^}]+\}',
        new_top_status_css.strip(),
        content,
        count=1
    )

# 2. Update scroll area CSS: strictly constrained below the top border (top: 32px) and above the bottom border (bottom: 28px)
old_scroll_area_css = """    #nrViewReader.honor-reader-mode #readerScrollArea,
    #nrViewReader.honor-reader-mode .honor-scroll-area,
    #nrViewReader #readerScrollArea.honor-scroll-area,
    #nrViewReader #readerScrollArea,
    .nr-view-reader.honor-reader-mode #readerScrollArea,
    .nr-view-reader #readerScrollArea.honor-scroll-area,
    .honor-reader-mode #readerScrollArea,
    .honor-scroll-area {
      position: absolute !important;
      top: 52px !important;
      top: max(52px, calc(env(safe-area-inset-top, 0px) + 26px)) !important;
      bottom: 34px !important;
      bottom: calc(max(34px, calc(env(safe-area-inset-bottom, 0px) + 22px)) + var(--honor-viewport-extra-bottom, 0px)) !important;
      left: 0 !important;
      right: 0 !important;
      width: auto !important;
      height: auto !important;
      flex: none !important;
      background: #000000 !important;
      color: #a3a3a3 !important;
      padding: 0 var(--honor-margin-horizontal, 18px) !important;
      margin: 0 !important;
      box-sizing: border-box !important;
      overflow-y: hidden !important;
      overflow-x: hidden !important;
      touch-action: pan-y !important;
    }"""

new_scroll_area_css = """    #nrViewReader.honor-reader-mode #readerScrollArea,
    #nrViewReader.honor-reader-mode .honor-scroll-area,
    #nrViewReader #readerScrollArea.honor-scroll-area,
    #nrViewReader #readerScrollArea,
    .nr-view-reader.honor-reader-mode #readerScrollArea,
    .nr-view-reader #readerScrollArea.honor-scroll-area,
    .honor-reader-mode #readerScrollArea,
    .honor-scroll-area {
      position: absolute !important;
      top: 32px !important;
      top: max(32px, calc(env(safe-area-inset-top, 0px) + 28px)) !important;
      bottom: 28px !important;
      bottom: max(28px, calc(env(safe-area-inset-bottom, 0px) + 20px)) !important;
      left: 0 !important;
      right: 0 !important;
      width: auto !important;
      height: auto !important;
      flex: none !important;
      background: #000000 !important;
      color: #a3a3a3 !important;
      padding: 0 var(--honor-margin-horizontal, 18px) !important;
      margin: 0 !important;
      box-sizing: border-box !important;
      overflow-y: hidden !important;
      overflow-x: hidden !important;
      touch-action: pan-y !important;
    }"""

if old_scroll_area_css in content:
    content = content.replace(old_scroll_area_css, new_scroll_area_css, 1)
    print("2. Constrained #readerScrollArea strictly between top: 32px and bottom: 28px")
else:
    print("2. Warning: old_scroll_area_css not matched verbatim, using regex")
    content = re.sub(
        r'#nrViewReader\.honor-reader-mode #readerScrollArea[\s\S]*?touch-action: pan-y !important;\s*\}',
        new_scroll_area_css.strip(),
        content,
        count=1
    )

# 3. Replace snapViewportToLastFullLine, adjustHonorViewportLines, and getOptimalPageTurnTarget
old_snapping_block = """    // Tự động căn chỉnh chiều cao hiển thị để không bao giờ bị cắt nửa chiều cao chữ
    function adjustHonorViewportLines() {
      const sc = document.getElementById('readerScrollArea');
      if (!sc) return;
      document.documentElement.style.setProperty('--honor-viewport-extra-bottom', '0px');

      let lh = 32;
      const p = sc.querySelector('.paragraph-item') || sc.querySelector('.honor-content');
      if (p) {
        const cs = window.getComputedStyle(p);
        const parsed = parseFloat(cs.lineHeight);
        if (!isNaN(parsed) && parsed > 12) lh = parsed;
      } else {
        const fs = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--honor-font-size')) || 18;
        const lhm = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--honor-line-height')) || 1.6;
        lh = fs * lhm;
      }

      const scStyle = window.getComputedStyle(sc);
      const padTop = parseFloat(scStyle.paddingTop) || 4;
      const padBottom = parseFloat(scStyle.paddingBottom) || 4;
      const clientH = sc.clientHeight;
      const innerH = clientH - padTop - padBottom;

      if (innerH > 100 && lh > 10) {
        const lines = Math.floor(innerH / lh);
        const fittedInnerH = lines * lh;
        const remainder = innerH - fittedInnerH;
        if (remainder >= 1 && remainder < lh) {
          document.documentElement.style.setProperty('--honor-viewport-extra-bottom', `${Math.floor(remainder)}px`);
        } else {
          document.documentElement.style.setProperty('--honor-viewport-extra-bottom', '0px');
        }
      }

      if (typeof updateHonorPageCounter === 'function') {
        updateHonorPageCounter();
      }
    }

    // Tính toán đích lật trang chuẩn xác khớp với từng dòng chữ nguyên vẹn bằng DOM Rects
    function getOptimalPageTurnTarget(sc, direction) {
      if (!sc) return 0;
      const scRect = sc.getBoundingClientRect();
      const maxScroll = Math.max(0, sc.scrollHeight - sc.clientHeight);
      const curScroll = sc.scrollTop;

      // Thu thập toàn bộ các dòng chữ đang hiển thị thực tế
      const lineRects = [];
      const textBlocks = sc.querySelectorAll('.chapter-title-heading, .paragraph-item');
      textBlocks.forEach(block => {
        try {
          const range = document.createRange();
          range.selectNodeContents(block);
          const rects = range.getClientRects();
          for (let i = 0; i < rects.length; i++) {
            const r = rects[i];
            if (r.height > 6 && r.width > 10) {
              lineRects.push(r);
            }
          }
        } catch (_) {}
      });

      if (lineRects.length === 0) {
        const turnDist = Math.max(160, sc.clientHeight - 20);
        return direction === 'next' ? Math.min(curScroll + turnDist, maxScroll) : Math.max(0, curScroll - turnDist);
      }

      if (direction === 'next') {
        // Tìm dòng đầu tiên mà đáy của nó vượt ra ngoài đáy của khung đọc hiện tại (hoặc bị cắt ngang)
        let nextStartLine = null;
        for (let i = 0; i < lineRects.length; i++) {
          const r = lineRects[i];
          if (r.bottom > scRect.bottom - 4) {
            nextStartLine = r;
            break;
          }
        }

        if (!nextStartLine) {
          return maxScroll;
        }

        // Độ dịch chuyển chính xác để đưa đỉnh của dòng mới (nextStartLine.top) khớp đúng đỉnh khung đọc (scRect.top)
        const delta = nextStartLine.top - scRect.top;
        if (delta <= 10) {
          return Math.min(curScroll + Math.max(160, sc.clientHeight - 20), maxScroll);
        }
        return Math.min(Math.max(0, Math.round(curScroll + delta)), maxScroll);
      } else {
        // Lật về trang trước: Tìm dòng chữ cách đỉnh hiện tại khoảng 1 trang
        const targetTop = scRect.top - (scRect.height - 20);
        let prevStartLine = null;
        for (let i = 0; i < lineRects.length; i++) {
          const r = lineRects[i];
          if (r.top >= targetTop - 4) {
            prevStartLine = r;
            break;
          }
        }

        if (!prevStartLine || prevStartLine.top >= scRect.top - 10) {
          return 0;
        }

        const delta = scRect.top - prevStartLine.top;
        return Math.max(0, Math.round(curScroll - delta));
      }
    }

    // Ẩn lập tức bất kỳ dòng chữ nào bị cắt nửa ở mép dưới cùng để chuyển trọn vẹn sang trang sau
    function snapViewportToLastFullLine() {
      const sc = document.getElementById('readerScrollArea');
      if (!sc) return;
      const scRect = sc.getBoundingClientRect();
      const textBlocks = sc.querySelectorAll('.chapter-title-heading, .paragraph-item');
      let peekCut = 0;
      textBlocks.forEach(block => {
        try {
          const range = document.createRange();
          range.selectNodeContents(block);
          const rects = range.getClientRects();
          for (let i = 0; i < rects.length; i++) {
            const r = rects[i];
            // Dòng bị cắt ngang ở mép đáy: đỉnh nằm trong viewport nhưng đáy vượt quá viewport
            if (r.top < scRect.bottom - 2 && r.bottom > scRect.bottom - 1) {
              const peek = Math.ceil(scRect.bottom - r.top) + 2;
              if (peek > 0 && peek < r.height && peek > peekCut) {
                peekCut = peek;
              }
            }
          }
        } catch (_) {}
      });

      if (peekCut > 0) {
        document.documentElement.style.setProperty('--honor-viewport-extra-bottom', `${peekCut}px`);
      } else {
        document.documentElement.style.setProperty('--honor-viewport-extra-bottom', '0px');
      }
    }"""

new_snapping_block = """    // Tự động căn chỉnh và khóa trọn vẹn các dòng chữ trong khung đọc
    function adjustHonorViewportLines() {
      snapViewportToLastFullLine();
      if (typeof updateHonorPageCounter === 'function') {
        updateHonorPageCounter();
      }
    }

    // Tính toán đích lật trang chuẩn xác khớp với từng dòng chữ nguyên vẹn bằng DOM Rects
    function getOptimalPageTurnTarget(sc, direction) {
      if (!sc) return 0;
      const scRect = sc.getBoundingClientRect();
      const maxScroll = Math.max(0, sc.scrollHeight - sc.clientHeight);
      const curScroll = sc.scrollTop;

      // Xác định đáy hiển thị thực tế (nếu đáy đang bị clip-path giấu dòng cắt)
      let visibleBottom = scRect.bottom - 2;
      if (sc.style.clipPath) {
        const m = sc.style.clipPath.match(/(\\d+)px\\s*0px\\)$/);
        if (m) visibleBottom -= parseInt(m[1], 10);
      }

      // Thu thập toàn bộ các dòng chữ đang hiển thị thực tế
      const lineRects = [];
      const textBlocks = sc.querySelectorAll('.chapter-title-heading, .paragraph-item');
      textBlocks.forEach(block => {
        try {
          const range = document.createRange();
          range.selectNodeContents(block);
          const rects = range.getClientRects();
          for (let i = 0; i < rects.length; i++) {
            const r = rects[i];
            if (r.height > 6 && r.width > 10) {
              lineRects.push(r);
            }
          }
        } catch (_) {}
      });

      if (lineRects.length === 0) {
        const turnDist = Math.max(160, sc.clientHeight - 20);
        return direction === 'next' ? Math.min(curScroll + turnDist, maxScroll) : Math.max(0, curScroll - turnDist);
      }

      if (direction === 'next') {
        // Tìm dòng đầu tiên mà đáy của nó vượt ra ngoài đáy của khung đọc hiện tại (hoặc bị cắt ngang mép đáy)
        let nextStartLine = null;
        for (let i = 0; i < lineRects.length; i++) {
          const r = lineRects[i];
          if (r.bottom > visibleBottom) {
            nextStartLine = r;
            break;
          }
        }

        if (!nextStartLine) {
          return maxScroll;
        }

        // Độ dịch chuyển chính xác để đưa đỉnh của dòng mới khớp đúng đỉnh khung đọc (không bị cắt đỉnh)
        const delta = nextStartLine.top - scRect.top;
        if (delta <= 5) {
          return Math.min(curScroll + Math.max(160, sc.clientHeight - 20), maxScroll);
        }
        return Math.min(Math.max(0, Math.floor(curScroll + delta)), maxScroll);
      } else {
        // Lật về trang trước: Tìm dòng chữ cách đỉnh hiện tại khoảng 1 trang
        const targetTop = scRect.top - (scRect.height - 20);
        let prevStartLine = null;
        for (let i = 0; i < lineRects.length; i++) {
          const r = lineRects[i];
          if (r.top >= targetTop - 4) {
            prevStartLine = r;
            break;
          }
        }

        if (!prevStartLine || prevStartLine.top >= scRect.top - 10) {
          return 0;
        }

        const delta = scRect.top - prevStartLine.top;
        return Math.max(0, Math.floor(curScroll - delta));
      }
    }

    // Ẩn triệt để bất kỳ dòng chữ nào bị cắt nửa ở mép dưới cùng bằng clip-path không gây giật layout
    function snapViewportToLastFullLine() {
      const sc = document.getElementById('readerScrollArea');
      if (!sc) return;
      const scRect = sc.getBoundingClientRect();
      const textBlocks = sc.querySelectorAll('.chapter-title-heading, .paragraph-item');
      let cutBottomPx = 0;

      for (let b = 0; b < textBlocks.length; b++) {
        const block = textBlocks[b];
        const bRect = block.getBoundingClientRect();
        if (bRect.bottom < scRect.top || bRect.top > scRect.bottom) continue;

        try {
          const range = document.createRange();
          range.selectNodeContents(block);
          const rects = range.getClientRects();
          for (let i = 0; i < rects.length; i++) {
            const r = rects[i];
            // Dòng bị cắt ngang ở mép đáy: đỉnh nằm trong viewport nhưng đáy vượt quá viewport
            if (r.top < scRect.bottom - 1 && r.bottom > scRect.bottom - 1) {
              const peek = Math.ceil(scRect.bottom - r.top) + 1;
              if (peek > cutBottomPx) {
                cutBottomPx = peek;
              }
            }
          }
        } catch (_) {}
      }

      if (cutBottomPx > 0) {
        sc.style.clipPath = `inset(0px 0px ${cutBottomPx}px 0px)`;
      } else {
        sc.style.clipPath = '';
      }
    }"""

if old_snapping_block in content:
    content = content.replace(old_snapping_block, new_snapping_block, 1)
    print("3. Replaced snapViewportToLastFullLine with rock-solid clipPath mechanism")
else:
    print("3. Error: old_snapping_block pattern not found!")
    sys.exit(1)

# 4. Update clone handling in nextPage and prevPage to maintain clipPath
content = content.replace(
    "clone.id = 'pageTurnClone';",
    "clone.id = 'pageTurnClone';\n          if (sc.style.clipPath) clone.style.clipPath = sc.style.clipPath;"
)
print("4. Updated clone handling to preserve clipPath")

# 5. Update scrollSentenceToView for instant jump and clipPath awareness
old_scroll_sentence = """    function scrollSentenceToView(activeEl, isInstant = false) {
      if (!activeEl) return;
      const sc = document.getElementById('readerScrollArea') || document.querySelector('main');
      if (!sc) return;

      const elRect = activeEl.getBoundingClientRect();
      const scRect = sc.getBoundingClientRect();

      // Kiểm tra câu đang đọc có nằm trọn vẹn trong trang sách hiện tại không
      const isVisibleOnPage = (elRect.top >= scRect.top - 2) && (elRect.bottom <= scRect.bottom - 4);
      if (isVisibleOnPage) {
        // Câu đang đọc nằm trọn vẹn trên trang hiện tại -> GIỮ NGUYÊN TRANG, TUYỆT ĐỐI KHÔNG CUỘN để không làm lệch dòng chữ!
        return;
      }

      // Nếu câu nằm ở trang tiếp theo (bị khuất ở đáy trang hoặc nằm bên dưới) -> LẬT SANG TRANG MỚI
      if (elRect.bottom > scRect.bottom - 4) {
        if (typeof window.nextPage === 'function') {
          window.nextPage();
        }
        return;
      }

      // Nếu câu nằm ở trang trước (ở trên đỉnh) -> LẬT VỀ TRANG TRƯỚC
      if (elRect.top < scRect.top - 2) {
        if (typeof window.prevPage === 'function') {
          window.prevPage();
        }
        return;
      }
    }"""

new_scroll_sentence = """    function scrollSentenceToView(activeEl, isInstant = false) {
      if (!activeEl) return;
      const sc = document.getElementById('readerScrollArea') || document.querySelector('main');
      if (!sc) return;

      if (isInstant) {
        const targetScroll = Math.max(0, activeEl.offsetTop - sc.offsetTop);
        sc.scrollTop = targetScroll;
        snapViewportToLastFullLine();
        if (typeof updateHonorPageCounter === 'function') updateHonorPageCounter();
        return;
      }

      const elRect = activeEl.getBoundingClientRect();
      const scRect = sc.getBoundingClientRect();

      let visibleBottom = scRect.bottom - 4;
      if (sc.style.clipPath) {
        const m = sc.style.clipPath.match(/(\\d+)px\\s*0px\\)$/);
        if (m) visibleBottom -= parseInt(m[1], 10);
      }

      // Kiểm tra câu đang đọc có nằm trọn vẹn trong trang sách hiện tại không
      const isVisibleOnPage = (elRect.top >= scRect.top - 2) && (elRect.bottom <= visibleBottom);
      if (isVisibleOnPage) {
        // Câu đang đọc nằm trọn vẹn trên trang hiện tại -> GIỮ NGUYÊN TRANG, TUYỆT ĐỐI KHÔNG CUỘN để không làm lệch dòng chữ!
        return;
      }

      // Nếu câu nằm ở trang tiếp theo (bị khuất ở đáy trang hoặc nằm bên dưới) -> LẬT SANG TRANG MỚI
      if (elRect.bottom > visibleBottom) {
        if (typeof window.nextPage === 'function') {
          window.nextPage();
        }
        return;
      }

      // Nếu câu nằm ở trang trước (ở trên đỉnh) -> LẬT VỀ TRANG TRƯỚC
      if (elRect.top < scRect.top - 2) {
        if (typeof window.prevPage === 'function') {
          window.prevPage();
        }
        return;
      }
    }"""

if old_scroll_sentence in content:
    content = content.replace(old_scroll_sentence, new_scroll_sentence, 1)
    print("5. Updated scrollSentenceToView with instant jump & clipPath awareness")
else:
    print("5. Warning: old_scroll_sentence not found verbatim!")

# 6. Call snapViewportToLastFullLine in loadChapter
if "reader.appendChild(endIndicator);" in content and "snapViewportToLastFullLine();" not in content[:content.find("reader.appendChild(endIndicator);") + 200]:
    content = content.replace(
        "reader.appendChild(endIndicator);",
        "reader.appendChild(endIndicator);\n      setTimeout(() => { if (typeof snapViewportToLastFullLine === 'function') snapViewportToLastFullLine(); }, 60);"
    )
    print("6. Added snapViewportToLastFullLine call on chapter render")

# 7. Bump app version to v1.6.5, build 165 in index.html
content = content.replace("v1.6.4", "v1.6.5")
content = content.replace("CURRENT_APP_BUILD = 164;", "CURRENT_APP_BUILD = 165;")
print("7. Bumped version to v1.6.5 (build 165) in index.html")

# Write to assets index.html
with open(assets_html, "w", encoding="utf-8") as f:
    f.write(content)
print(f"Saved {assets_html}")

# Write to desktop templates
with open(desktop_html_d, "w", encoding="utf-8") as f:
    f.write(content)
print(f"Saved {desktop_html_d}")

with open(desktop_html_c, "w", encoding="utf-8") as f:
    f.write(content)
print(f"Saved {desktop_html_c}")

# 8. Bump server.py version to v1.6.5, build 165
for s_path in [desktop_server_d, desktop_server_c]:
    with open(s_path, "r", encoding="utf-8", errors="ignore") as f:
        s_code = f.read()
    s_code = re.sub(r'"version":\s*"[^"]+"', '"version": "v1.6.5"', s_code, count=1)
    s_code = re.sub(r'"version_code":\s*\d+', '"version_code": 165', s_code, count=1)
    # Update changelog
    old_cl = r'"changelog":\s*\[[^\]]+\]'
    new_cl = '''"changelog": [
                "Trả lại độ rộng viền trên nhỏ gọn ngang tầm viên thuốc notch",
                "Ép dòng chữ hiển thị trọn vẹn nằm dưới viền trên và trên viền dưới",
                "Chấm dứt triệt để tình trạng che nửa chiều cao chữ bằng khóa dòng clip-path nguyên vẹn",
                "Tự động chuyển trang mượt mà không bao giờ bị cắt chữ dù đọc tay hay nghe TTS"
            ]'''
    s_code = re.sub(old_cl, new_cl, s_code, count=1)
    with open(s_path, "w", encoding="utf-8") as f:
        f.write(s_code)
    print(f"8. Updated {s_path} with v1.6.5 & changelog")

print("\nALL FILES UPDATED SUCCESSFULLY!")
