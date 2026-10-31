# -*- coding: utf-8 -*-
import os, sys, re

assets_html = r"c:\Users\VANLUC\Downloads\Share tool -20261010T221918Z-1-001\Share tool\TTS_STT_vip_v1.6.0\HonorEpubReader\app\src\main\assets\index.html"
desktop_html_d = r"D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\templates\index.html"
desktop_html_c = r"c:\Users\VANLUC\Downloads\Share tool -20261010T221918Z-1-001\Share tool\DesktopEpubReader\templates\index.html"
desktop_server_d = r"D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\server.py"
desktop_server_c = r"c:\Users\VANLUC\Downloads\Share tool -20261010T221918Z-1-001\Share tool\DesktopEpubReader\server.py"

print("Reading assets index.html...")
with open(assets_html, "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

# Replace honor-media-pill rules with True Liquid Glass
old_pill_block = r"\.honor-media-pill\s*\{[\s\S]*?\.honor-media-pill\.with-toolbar\s*\{\s*bottom:\s*120px;\s*\}"
new_liquid_glass_css = """.honor-media-pill {
      position: absolute;
      left: 18px;
      bottom: 26px;
      height: 46px;
      border-radius: 9999px;
      background: rgba(255, 255, 255, 0.08) !important;
      backdrop-filter: blur(25px) saturate(200%) !important;
      -webkit-backdrop-filter: blur(25px) saturate(200%) !important;
      border: 1px solid rgba(255, 255, 255, 0.3) !important;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.12), inset 0 1px 1px rgba(255, 255, 255, 0.4) !important;
      display: flex;
      align-items: center;
      padding: 0 8px 0 10px;
      gap: 8px;
      z-index: 1050;
      transform: translateY(20px) scale(0.9);
      opacity: 0;
      pointer-events: none;
      transition: transform 0.28s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.22s ease, bottom 0.28s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .honor-media-pill.open {
      transform: translateY(0) scale(1) !important;
      opacity: 0.9 !important;
      pointer-events: auto !important;
    }
    body.honor-light-mode .honor-media-pill {
      background: rgba(0, 0, 0, 0.04) !important;
      border: 1px solid rgba(0, 0, 0, 0.1) !important;
      box-shadow: 0 8px 25px rgba(0, 0, 0, 0.06), inset 0 1px 1px rgba(255, 255, 255, 0.8) !important;
    }
    body.honor-light-mode .honor-pill-skip-btn,
    body.honor-light-mode .honor-pill-close-btn {
      color: #1f2937 !important;
    }
    body.honor-light-mode .honor-pill-divider {
      background: rgba(0, 0, 0, 0.12) !important;
    }
    .honor-bottom-toolbar.open ~ .honor-media-pill,
    .honor-media-pill.with-toolbar {
      bottom: 120px;
    }"""

content, c_p = re.subn(old_pill_block, new_liquid_glass_css, content, count=1)
print(f"1. Replaced honor-media-pill with Liquid Glass CSS (count={c_p})")

# Bump version to v1.6.10 (build 170)
content = content.replace("v1.6.9", "v1.6.10")
content = content.replace("CURRENT_APP_BUILD = 169;", "CURRENT_APP_BUILD = 170;")
print("2. Bumped version to v1.6.10 (build 170)")

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

# Update server.py in both places
for s_path in [desktop_server_d, desktop_server_c]:
    with open(s_path, "r", encoding="utf-8", errors="ignore") as f:
        s_code = f.read()
    s_code = re.sub(r'"version":\s*"[^"]+"', '"version": "v1.6.10"', s_code, count=1)
    s_code = re.sub(r'"version_code":\s*\d+', '"version_code": 170', s_code, count=1)
    old_cl = r'"changelog":\s*\[[^\]]+\]'
    new_cl = '''"changelog": [
                "Pop-up Media chuyển sang hiệu ứng Liquid Glass siêu trong suốt nhìn xuyên thấu chữ bên dưới",
                "Loại bỏ màu trắng đục, kính mờ nước cao cấp chuẩn iOS / VisionOS",
                "Bỏ gạch chân màu xanh ở chữ đang đọc, giữ nền nhạt dịu mắt"
            ]'''
    s_code = re.sub(old_cl, new_cl, s_code, count=1)
    with open(s_path, "w", encoding="utf-8") as f:
        f.write(s_code)
    print(f"3. Updated {s_path} with v1.6.10 & changelog")

print("\nALL FILES UPDATED WITH LIQUID GLASS EFFECT SUCCESSFULLY!")
