# -*- coding: utf-8 -*-
import os, sys, re, shutil

desktop_template = r"D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\templates\index.html"
assets_template = r"c:\Users\VANLUC\Downloads\Share tool -20261010T221918Z-1-001\Share tool\TTS_STT_vip_v1.6.0\HonorEpubReader\app\src\main\assets\index.html"
desktop_server = r"D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\server.py"

print(f"Loading {desktop_template}...")
with open(desktop_template, "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

# 1. Clean corrupted center hint span if present
idx_hint = content.find('<span id="honorEyeTrackingHint"')
if idx_hint != -1:
    idx_hint_end = content.find('</span>', idx_hint) + 7
    content = content[:idx_hint] + content[idx_hint_end:]
    print("1. Cleaned center hint span")
else:
    print("1. Center hint span already absent")

# 2. Update scroll area bounding rules
new_scroll_rules = """/* VÙNG CUỘN / LẬT TRANG SÁCH CHUẨN HONOR READER GỐC:
       - Phần trên: chữ hiển thị ngay bên dưới hình viên thuốc và header (top: 78px, phần trên không hiển thị chữ)
       - Phần dưới: bỏ dòng cuối cùng, làm phần để trống không hiển thị nội dung (bottom: 58px)
       - Chân trang: giữ lại giờ, pin và số trang, khoảng trống để nhìn lên lật trang */
    #nrViewReader.honor-reader-mode #readerScrollArea,
    #nrViewReader.honor-reader-mode .honor-scroll-area,
    #nrViewReader #readerScrollArea.honor-scroll-area,
    #nrViewReader #readerScrollArea,
    .nr-view-reader.honor-reader-mode #readerScrollArea,
    .nr-view-reader #readerScrollArea.honor-scroll-area,
    .honor-reader-mode #readerScrollArea,
    .honor-scroll-area {
      position: absolute !important;
      top: 78px !important;
      top: max(78px, calc(var(--safe-cutout-top, 40px) + 38px), calc(env(safe-area-inset-top, 0px) + 38px)) !important;
      bottom: 58px !important;
      bottom: max(58px, calc(env(safe-area-inset-bottom, 0px) + 38px)) !important;
      left: 0 !important;
      right: 0 !important;
      width: auto !important;
      height: auto !important;
      flex: none !important;
      background: #000000 !important;
      color: #a3a3a3 !important;
      padding: 0 18px 0 18px !important;
      margin: 0 !important;
      box-sizing: border-box !important;
      overflow-y: hidden !important;
      overflow-x: hidden !important;
      touch-action: pan-y !important;
    }

    body.honor-light-mode #nrViewReader.honor-reader-mode #readerScrollArea,
    body.honor-light-mode #nrViewReader.honor-reader-mode .honor-scroll-area,
    body.honor-light-mode #nrViewReader #readerScrollArea.honor-scroll-area,
    body.honor-light-mode #nrViewReader #readerScrollArea,
    body.honor-light-mode .nr-view-reader #readerScrollArea,
    body.honor-light-mode .honor-reader-mode #readerScrollArea,
    body.honor-light-mode .honor-scroll-area {
      background: #f6f3eb !important;
      color: #2c2c2c !important;
    }

    #nrViewReader.honor-reader-mode .main-container,
    #nrViewReader.honor-reader-mode .honor-container {
      display: block !important;
      flex: none !important;
      height: auto !important;
      min-height: 100% !important;
      padding: 0 !important;
      margin: 0 auto !important;
      max-width: 760px !important;
    }
    #nrViewReader.honor-reader-mode .reader-content,
    #nrViewReader.honor-reader-mode .honor-content {
      padding: 0 !important;
      margin: 0 !important;
    }"""

# Locate old rules
idx_s1 = content.find("/* VÙNG CUỘN / LẬT TRANG SÁCH")
if idx_s1 == -1:
    idx_s1 = content.find("/* V?NG CU?N / L?T TRANG S?CH")
if idx_s1 == -1:
    idx_s1 = content.find("#nrViewReader.honor-reader-mode #readerScrollArea")
if idx_s1 == -1:
    idx_s1 = content.find(".honor-scroll-area {")

idx_s2 = content.find(".honor-container {", idx_s1)
if idx_s1 != -1 and idx_s2 != -1:
    content = content[:idx_s1] + new_scroll_rules + "\n\n    " + content[idx_s2:]
    print("2. Updated scroll area bounding rules")
else:
    print("2. Warning: could not locate scroll rule boundaries!")

# 3. Update top & bottom status CSS
old_top_re = r"\.honor-status-top\s*\{[^}]+\}"
new_top_css = """.honor-status-top {
      position: absolute !important;
      top: 0 !important;
      left: 0 !important;
      right: 0 !important;
      height: 38px !important;
      padding: 8px 18px 0 18px !important;
      padding-top: max(8px, env(safe-area-inset-top, 0px), var(--android-cutout-top, 34px)) !important;
      display: flex !important;
      justify-content: space-between !important;
      align-items: center !important;
      z-index: 55 !important;
      pointer-events: none !important;
      box-sizing: border-box !important;
    }"""
content = re.sub(old_top_re, new_top_css, content, count=1)
print("3a. Updated .honor-status-top")

old_bot_re = r"\.honor-status-bottom\s*\{[^}]+\}"
new_bot_css = """.honor-status-bottom {
      position: absolute !important;
      bottom: 0 !important;
      left: 0 !important;
      right: 0 !important;
      height: 38px !important;
      padding: 0 18px 10px 18px !important;
      padding-bottom: max(10px, env(safe-area-inset-bottom, 0px)) !important;
      display: flex !important;
      justify-content: space-between !important;
      align-items: center !important;
      z-index: 860 !important;
      pointer-events: auto !important;
      cursor: pointer !important;
      box-sizing: border-box !important;
      -webkit-tap-highlight-color: transparent !important;
    }"""
content = re.sub(old_bot_re, new_bot_css, content, count=1)
print("3b. Updated .honor-status-bottom")

# 4. Update honor-bottom-tap-zone
old_tap_re = r"\.honor-bottom-tap-zone\s*\{[^}]+\}"
new_tap_css = """.honor-bottom-tap-zone {
      position: absolute !important;
      bottom: 0 !important;
      left: 0 !important;
      right: 0 !important;
      height: 58px !important;
      height: max(58px, calc(env(safe-area-inset-bottom, 0px) + 38px)) !important;
      z-index: 850 !important;
      background: transparent !important;
      cursor: pointer !important;
      -webkit-tap-highlight-color: transparent !important;
      touch-action: manipulation !important;
    }"""
content = re.sub(old_tap_re, new_tap_css, content, count=1)
print("4. Updated .honor-bottom-tap-zone")

# 5. JS click coordinate checks to h - 58
content = re.sub(r"clickY >= h - \d+", "clickY >= h - 58", content)
content = re.sub(r"clickY >= h \* 0\.\d+", "clickY >= h - 58", content)
print("5. Updated JS clickY checks")

# Write to desktop template
with open(desktop_template, "w", encoding="utf-8") as f:
    f.write(content)
print(f"6. Saved to {desktop_template}")

# Sync to Android Assets template
with open(assets_template, "w", encoding="utf-8") as f:
    f.write(content)
print(f"7. Synced to {assets_template}")

# 8. Bump server.py version
with open(desktop_server, "r", encoding="utf-8", errors="ignore") as f:
    server_code = f.read()

server_code = re.sub(r'"version":\s*"[^"]+"', '"version": "v1.6.9-honor-bounds-fixed"', server_code, count=1)
with open(desktop_server, "w", encoding="utf-8") as f:
    f.write(server_code)
print("8. Bumped server.py version to v1.6.9-honor-bounds-fixed")

print("ALL UPDATES SUCCESSFULLY APPLIED!")
