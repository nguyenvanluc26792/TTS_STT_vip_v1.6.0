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

# 1. Update #honorReaderTopStatus: place at top: 4px, height: 22px so C11 and Tắt đệm sit directly in the empty space horizontally level with the pill notch
old_top_re = r"#honorReaderTopStatus,\s*\.honor-status-top\s*\{[^}]+\}"
new_top_css = """#honorReaderTopStatus,
    .honor-status-top {
      position: absolute !important;
      top: 4px !important;
      left: 0 !important;
      right: 0 !important;
      height: 22px !important;
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
print(f"1. Updated #honorReaderTopStatus to top: 4px, height: 22px level with pill (count={c_top})")

# 2. Update scroll area top to 70% of 32px -> 22px (max 22px, calc(env * 0.7))
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
      top: 22px !important;
      top: max(22px, calc(env(safe-area-inset-top, 0px) * 0.7)) !important;
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
print(f"2. Reduced #readerScrollArea top to 70% (22px) (count={c_sc})")

# 3. Bump version to v1.6.7 (build 167)
content = content.replace("v1.6.6", "v1.6.7")
content = content.replace("CURRENT_APP_BUILD = 166;", "CURRENT_APP_BUILD = 167;")
print("3. Bumped index.html to v1.6.7 (build 167)")

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

# 4. Bump server.py version to v1.6.7, build 167
for s_path in [desktop_server_d, desktop_server_c]:
    with open(s_path, "r", encoding="utf-8", errors="ignore") as f:
        s_code = f.read()
    s_code = re.sub(r'"version":\s*"[^"]+"', '"version": "v1.6.7"', s_code, count=1)
    s_code = re.sub(r'"version_code":\s*\d+', '"version_code": 167', s_code, count=1)
    old_cl = r'"changelog":\s*\[[^\]]+\]'
    new_cl = '''"changelog": [
                "Giảm độ rộng viền trên xuống còn 70% (22px)",
                "Đưa chữ C11 và trạng thái đệm nằm trong khoảng trống ngang hàng với viên thuốc notch",
                "Tối ưu hoàn hảo không gian đọc sách chuẩn Honor Reader"
            ]'''
    s_code = re.sub(old_cl, new_cl, s_code, count=1)
    with open(s_path, "w", encoding="utf-8") as f:
        f.write(s_code)
    print(f"4. Updated {s_path} with v1.6.7 & changelog")

print("\nALL FILES UPDATED SUCCESSFULLY!")
