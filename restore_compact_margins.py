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

# 1. Restore scroll area top and bottom to original compact values:
# top: 32px (max 32px, env + 6px)
# bottom: 28px (max 28px, env + 18px)
old_scroll_re = r"#nrViewReader\.honor-reader-mode #readerScrollArea[\s\S]*?touch-action: pan-y !important;\s*\}"
new_scroll_css = """#nrViewReader.honor-reader-mode #readerScrollArea,
    #nrViewReader.honor-reader-mode .honor-scroll-area,
    #nrViewReader #readerScrollArea.honor-scroll-area,
    #nrViewReader #readerScrollArea,
    .nr-view-reader.honor-reader-mode #readerScrollArea,
    .nr-view-reader #readerScrollArea.honor-scroll-area,
    .honor-reader-mode #readerScrollArea,
    .honor-scroll-area {
      position: absolute !important;
      top: 32px !important;
      top: max(32px, calc(env(safe-area-inset-top, 0px) + 6px)) !important;
      bottom: 28px !important;
      bottom: max(28px, calc(env(safe-area-inset-bottom, 0px) + 18px)) !important;
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

content, c_sc = re.subn(old_scroll_re, new_scroll_css, content, count=1)
print(f"1. Restored #readerScrollArea top & bottom to compact size (count={c_sc})")

# 2. Restore .honor-status-bottom to compact 24px
old_bot_re = r"\.honor-status-bottom\s*\{[^}]+\}"
new_bot_css = """.honor-status-bottom {
      position: absolute !important;
      bottom: 0 !important;
      left: 0 !important;
      right: 0 !important;
      height: 24px !important;
      padding: 0 16px 2px 16px !important;
      padding-bottom: max(2px, env(safe-area-inset-bottom, 0px)) !important;
      display: flex !important;
      justify-content: space-between !important;
      align-items: center !important;
      z-index: 860 !important;
      pointer-events: auto !important;
      cursor: pointer !important;
      box-sizing: border-box !important;
      -webkit-tap-highlight-color: transparent !important;
    }"""
content, c_bot = re.subn(old_bot_re, new_bot_css, content, count=1)
print(f"2. Restored .honor-status-bottom to compact 24px (count={c_bot})")

# 3. Restore .honor-bottom-tap-zone to 28px
old_tap_re = r"\.honor-bottom-tap-zone\s*\{[^}]+\}"
new_tap_css = """.honor-bottom-tap-zone {
      position: absolute !important;
      bottom: 0 !important;
      left: 0 !important;
      right: 0 !important;
      height: 28px !important;
      height: max(28px, calc(env(safe-area-inset-bottom, 0px) + 18px)) !important;
      z-index: 850 !important;
      background: transparent !important;
      cursor: pointer !important;
      -webkit-tap-highlight-color: transparent !important;
      touch-action: manipulation !important;
    }"""
content, c_tap = re.subn(old_tap_re, new_tap_css, content, count=1)
print(f"3. Restored .honor-bottom-tap-zone to 28px (count={c_tap})")

# 4. Restore #honorReaderTopStatus
old_top_re = r"#honorReaderTopStatus,\s*\.honor-status-top\s*\{[^}]+\}"
new_top_css = """#honorReaderTopStatus,
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
content, c_top = re.subn(old_top_re, new_top_css, content, count=1)
print(f"4. Verified #honorReaderTopStatus (count={c_top})")

# 5. Clean up clipPath logic: remove clipPath setting so no extra blank space is created
content = re.sub(
    r'// Ẩn triệt để bất kỳ dòng chữ nào[\s\S]*?function snapViewportToLastFullLine\(\)\s*\{[\s\S]*?\n    \}',
    '''function snapViewportToLastFullLine() {
      const sc = document.getElementById('readerScrollArea');
      if (sc && sc.style.clipPath) sc.style.clipPath = '';
    }''',
    content,
    count=1
)
print("5. Reset snapViewportToLastFullLine to avoid any extra blank margin clipping")

# Clean up clipPath references in clone, getOptimalPageTurnTarget and scrollSentenceToView
content = content.replace("if (sc.style.clipPath) clone.style.clipPath = sc.style.clipPath;", "")
content = re.sub(r'let visibleBottom = scRect\.bottom - 2;[\s\S]*?visibleBottom -= parseInt\(m\[1\], 10\);\s*\}', 'const visibleBottom = scRect.bottom - 4;', content)
content = re.sub(r'let visibleBottom = scRect\.bottom - 4;[\s\S]*?visibleBottom -= parseInt\(m\[1\], 10\);\s*\}', 'const visibleBottom = scRect.bottom - 4;', content)

# 6. Bump app version to v1.6.6 (build 166)
content = content.replace("v1.6.5", "v1.6.6")
content = content.replace("CURRENT_APP_BUILD = 165;", "CURRENT_APP_BUILD = 166;")
print("6. Bumped index.html to v1.6.6 (build 166)")

# Save files
with open(assets_html, "w", encoding="utf-8") as f:
    f.write(content)
print(f"Saved {assets_html}")

with open(desktop_html_d, "w", encoding="utf-8") as f:
    f.write(content)
print(f"Saved {desktop_html_d}")

with open(desktop_html_c, "w", encoding="utf-8") as f:
    f.write(content)
print(f"Saved {desktop_html_c}")

# 7. Bump server.py version to v1.6.6, build 166
for s_path in [desktop_server_d, desktop_server_c]:
    with open(s_path, "r", encoding="utf-8", errors="ignore") as f:
        s_code = f.read()
    s_code = re.sub(r'"version":\s*"[^"]+"', '"version": "v1.6.6"', s_code, count=1)
    s_code = re.sub(r'"version_code":\s*\d+', '"version_code": 166', s_code, count=1)
    old_cl = r'"changelog":\s*\[[^\]]+\]'
    new_cl = '''"changelog": [
                "Giảm kích thước viền trên và viền dưới về kích thước nhỏ gọn như cũ",
                "Viền trên ngang tầm viên thuốc notch (32px), viền dưới 28px chuẩn Honor Reader",
                "Loại bỏ hoàn toàn khoảng trống thừa, tối đa hóa không gian đọc sách"
            ]'''
    s_code = re.sub(old_cl, new_cl, s_code, count=1)
    with open(s_path, "w", encoding="utf-8") as f:
        f.write(s_code)
    print(f"7. Updated {s_path} with v1.6.6 & changelog")

print("\nALL FILES RESTORED TO COMPACT SIZE SUCCESSFULLY!")
