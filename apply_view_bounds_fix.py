# -*- coding: utf-8 -*-
import os, sys

path = r"D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\templates\index.html"
with open(path, "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

# 1. Remove corrupted center hint span if present
idx_hint = content.find('<span id="honorEyeTrackingHint"')
if idx_hint != -1:
    idx_hint_end = content.find('</span>', idx_hint) + 7
    content = content[:idx_hint] + content[idx_hint_end:]
    print("1. Removed corrupted center hint span")

# 2. Add high-specificity bounding rules for #nrViewReader.honor-reader-mode #readerScrollArea
old_scroll_rule_start = "/* Vùng cuộn / lật trang sách"
if old_scroll_rule_start not in content:
    old_scroll_rule_start = ".honor-scroll-area {"

idx_s1 = content.find(old_scroll_rule_start)
idx_s2 = content.find(".honor-container {", idx_s1)
if idx_s1 != -1 and idx_s2 != -1:
    new_scroll_rule = """/* VÙNG CUỘN / LẬT TRANG SÁCH CHUẨN HONOR READER GỐC:
       - Phần trên: chữ hiển thị ngay bên dưới hình viên thuốc (top: 62px, phần trên không hiển thị chữ)
       - Phần dưới: bỏ dòng cuối cùng, làm phần để trống không hiển thị nội dung (bottom: 50px)
       - Chân trang: giữ lại giờ, pin và số trang */
    #nrViewReader.honor-reader-mode #readerScrollArea,
    #nrViewReader.honor-reader-mode .honor-scroll-area,
    #nrViewReader #readerScrollArea.honor-scroll-area,
    .honor-reader-mode #readerScrollArea,
    .honor-scroll-area {
      position: absolute !important;
      top: 62px !important;
      top: max(62px, calc(env(safe-area-inset-top, 0px) + 16px)) !important;
      bottom: 50px !important;
      bottom: max(50px, calc(env(safe-area-inset-bottom, 0px) + 16px)) !important;
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
    body.honor-light-mode .honor-reader-mode #readerScrollArea {
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
    }

    """
    content = content[:idx_s1] + new_scroll_rule + content[idx_s2:]
    print("2. High-specificity #nrViewReader.honor-reader-mode #readerScrollArea rules installed")
else:
    print("2. Warning: could not locate scroll rule range!")

# 3. Update top and bottom status CSS
old_top_status = """.honor-status-top {
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 28px;
      padding: 6px 18px 0 18px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      z-index: 55;
      pointer-events: none;
      box-sizing: border-box;
    }"""
new_top_status = """.honor-status-top {
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 38px;
      padding: 8px 18px 0 18px;
      padding-top: max(8px, env(safe-area-inset-top, 0px));
      display: flex;
      justify-content: space-between;
      align-items: center;
      z-index: 55;
      pointer-events: none;
      box-sizing: border-box;
    }"""
if old_top_status in content:
    content = content.replace(old_top_status, new_top_status, 1)
    print("3. honor-status-top updated")

old_bottom_status = """.honor-status-bottom {
      position: absolute;
      bottom: 0; left: 0; right: 0;
      height: 28px;
      padding: 0 18px 6px 18px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      z-index: 860;
      pointer-events: auto !important;
      cursor: pointer;
      box-sizing: border-box;
      -webkit-tap-highlight-color: transparent;
    }"""
new_bottom_status = """.honor-status-bottom {
      position: absolute;
      bottom: 0; left: 0; right: 0;
      height: 38px;
      padding: 0 18px 10px 18px;
      padding-bottom: max(10px, env(safe-area-inset-bottom, 0px));
      display: flex;
      justify-content: space-between;
      align-items: center;
      z-index: 860;
      pointer-events: auto !important;
      cursor: pointer;
      box-sizing: border-box;
      -webkit-tap-highlight-color: transparent;
    }"""
if old_bottom_status in content:
    content = content.replace(old_bottom_status, new_bottom_status, 1)
    print("3b. honor-status-bottom updated")

# 4. Update honor-bottom-tap-zone to 50px height
idx_tap = content.find(".honor-bottom-tap-zone {")
if idx_tap != -1:
    idx_tap_end = content.find("}", idx_tap) + 1
    new_tap_block = """.honor-bottom-tap-zone {
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      height: 50px;
      z-index: 850;
      background: transparent;
      cursor: pointer;
      -webkit-tap-highlight-color: transparent;
      touch-action: manipulation;
    }"""
    content = content[:idx_tap] + new_tap_block + content[idx_tap_end:]
    print("4. honor-bottom-tap-zone updated to 50px")

# 5. Ensure JS turnDistance and click coordinates
content = content.replace("Math.max(260, (sc.clientHeight || window.innerHeight) - 20)", "Math.max(260, sc.clientHeight)")
content = content.replace("(sc.scrollHeight - 20) / turnDistance", "sc.scrollHeight / turnDistance")
content = content.replace("clickY >= h - 80", "clickY >= h - 50")
content = content.replace("clickY >= h * 0.70", "clickY >= h - 50")
print("5. JS turnDistance and click checks updated")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("SUCCESS: index.html fully updated!")
