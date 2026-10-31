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

# 1. Update .honor-fab-listen to be translucent glass
old_fab_re = r"\.honor-fab-listen\s*\{[\s\S]*?transition:[^;]+;\s*\}"
new_fab_css = """.honor-fab-listen {
      position: absolute;
      right: 18px;
      bottom: 30px;
      width: 46px;
      height: 46px;
      border-radius: 50%;
      background: rgba(56, 189, 248, 0.28) !important;
      backdrop-filter: blur(12px) !important;
      -webkit-backdrop-filter: blur(12px) !important;
      color: #0284c7 !important;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
      font-weight: 700;
      border: 1px solid rgba(56, 189, 248, 0.45) !important;
      box-shadow: 0 4px 14px rgba(56, 189, 248, 0.2), inset 0 1px 1px rgba(255, 255, 255, 0.5) !important;
      cursor: pointer;
      z-index: 995;
      transition: transform 0.28s cubic-bezier(0.16, 1, 0.3, 1), bottom 0.28s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.2s;
    }"""
content, c_fab = re.subn(old_fab_re, new_fab_css, content, count=1)
print(f"1. Updated .honor-fab-listen to translucent glass (count={c_fab})")

# 2. Update .honor-media-pill, .honor-pill-play-btn, .honor-pill-skip-btn to Ultra-Translucent
old_media_block = r"\.honor-media-pill\s*\{[\s\S]*?\.honor-pill-close-btn:active\s*\{\s*color:\s*#ffffff;\s*\}"
new_media_block = """.honor-media-pill {
      position: absolute;
      left: 18px;
      bottom: 26px;
      height: 46px;
      border-radius: 9999px;
      background: rgba(255, 255, 255, 0.03) !important;
      backdrop-filter: blur(16px) !important;
      -webkit-backdrop-filter: blur(16px) !important;
      border: 1px solid rgba(255, 255, 255, 0.2) !important;
      box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08), inset 0 1px 1px rgba(255, 255, 255, 0.35) !important;
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
      opacity: 0.82 !important;
      pointer-events: auto !important;
    }
    body.honor-light-mode .honor-media-pill {
      background: rgba(0, 0, 0, 0.02) !important;
      border: 1px solid rgba(0, 0, 0, 0.08) !important;
      box-shadow: 0 4px 18px rgba(0, 0, 0, 0.05), inset 0 1px 1px rgba(255, 255, 255, 0.8) !important;
    }
    body.honor-light-mode .honor-pill-skip-btn,
    body.honor-light-mode .honor-pill-close-btn {
      color: #334155 !important;
    }
    body.honor-light-mode .honor-pill-divider {
      background: rgba(0, 0, 0, 0.1) !important;
    }
    .honor-bottom-toolbar.open ~ .honor-media-pill,
    .honor-media-pill.with-toolbar {
      bottom: 120px;
    }
    .honor-pill-skip-btn {
      background: transparent !important;
      border: none !important;
      color: #94a3b8;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      padding: 8px 6px;
      border-radius: 50%;
      opacity: 0.75;
      transition: color 0.15s, transform 0.15s, opacity 0.15s;
    }
    .honor-pill-skip-btn:active {
      color: #0284c7;
      opacity: 1;
      transform: scale(0.88);
    }
    .honor-pill-play-btn {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      background: rgba(56, 189, 248, 0.26) !important;
      backdrop-filter: blur(8px) !important;
      -webkit-backdrop-filter: blur(8px) !important;
      border: 1.5px solid rgba(56, 189, 248, 0.48) !important;
      color: #0284c7 !important;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      box-shadow: 0 2px 8px rgba(56, 189, 248, 0.18), inset 0 1px 2px rgba(255, 255, 255, 0.6) !important;
      transition: transform 0.15s, background 0.15s, border-color 0.15s;
    }
    body:not(.honor-light-mode) .honor-pill-play-btn {
      color: #38bdf8 !important;
    }
    .honor-pill-play-btn:active {
      transform: scale(0.9);
      background: rgba(56, 189, 248, 0.45) !important;
    }
    .honor-pill-divider {
      width: 1px;
      height: 18px;
      background: rgba(255, 255, 255, 0.15);
      margin: 0 2px;
    }
    .honor-pill-close-btn {
      background: transparent !important;
      border: none !important;
      color: #64748b;
      opacity: 0.6;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      padding: 6px;
      border-radius: 50%;
      transition: opacity 0.15s;
    }
    .honor-pill-close-btn:active {
      opacity: 1;
      color: #0f172a;
    }"""

content, c_m = re.subn(old_media_block, new_media_block, content, count=1)
print(f"2. Updated media pill & play button to ultra-translucent liquid glass (count={c_m})")

# 3. Bump version to v1.6.11 (build 171)
content = content.replace("v1.6.10", "v1.6.11")
content = content.replace("CURRENT_APP_BUILD = 170;", "CURRENT_APP_BUILD = 171;")
print("3. Bumped version to v1.6.11 (build 171)")

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
    s_code = re.sub(r'"version":\s*"[^"]+"', '"version": "v1.6.11"', s_code, count=1)
    s_code = re.sub(r'"version_code":\s*\d+', '"version_code": 171', s_code, count=1)
    old_cl = r'"changelog":\s*\[[^\]]+\]'
    new_cl = '''"changelog": [
                "Nút điều khiển Media siêu trong suốt nhìn xuyên thấu toàn bộ chữ bên dưới",
                "Nút phát/dừng chuyển sang dạng kính phát sáng mờ nước (Ultra-translucent liquid glass)",
                "Loại bỏ hoàn toàn các mảng màu đặc che chữ"
            ]'''
    s_code = re.sub(old_cl, new_cl, s_code, count=1)
    with open(s_path, "w", encoding="utf-8") as f:
        f.write(s_code)
    print(f"4. Updated {s_path} with v1.6.11 & changelog")

print("\nALL FILES UPDATED WITH ULTRA-TRANSLUCENT MEDIA BUTTONS SUCCESSFULLY!")
