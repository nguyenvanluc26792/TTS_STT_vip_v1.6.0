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

# 1. Remove border-bottom on sentence-item.active and keep gentle background
old_sent_rule = r"border-bottom:\s*2px solid var\(--highlight-border,\s*#e45c65\)\s*!important;"
new_sent_rule = "border-bottom: none !important;\n      text-decoration: none !important;"

content, c_sent = re.subn(old_sent_rule, new_sent_rule, content)
print(f"1. Removed border-bottom on active sentences (count={c_sent})")

# Add specific rule for honor-content active sentence to ensure no underline and soft background
honor_active_css = """
    .honor-content .sentence-item.active,
    .sentence-item.active {
      background-color: rgba(99, 102, 241, 0.16) !important;
      border-bottom: none !important;
      text-decoration: none !important;
      box-shadow: none !important;
      border-radius: 4px;
    }
    body.honor-light-mode .honor-content .sentence-item.active,
    body.honor-light-mode .sentence-item.active {
      background-color: rgba(99, 102, 241, 0.15) !important;
      border-bottom: none !important;
      text-decoration: none !important;
      box-shadow: none !important;
      color: #1a1a1a !important;
    }
"""

if ".honor-content .sentence-item.active" not in content:
    content = content.replace(
        ".honor-content .sentence-item {",
        honor_active_css + "\n    .honor-content .sentence-item {"
    )
    print("2. Added honor-content active sentence soft background CSS")

# 2. Make popup media translucent (85% transparency with glassmorphism)
old_pill_css = r"\.honor-media-pill\s*\{[\s\S]*?opacity:\s*0;[\s\S]*?\}"
new_pill_css = """.honor-media-pill {
      position: absolute;
      left: 18px;
      bottom: 26px;
      height: 48px;
      border-radius: 9999px;
      background: rgba(30, 30, 34, 0.45);
      backdrop-filter: blur(18px);
      -webkit-backdrop-filter: blur(18px);
      border: 1px solid rgba(255, 255, 255, 0.18);
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
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
      transform: translateY(0) scale(1);
      opacity: 0.85;
      pointer-events: auto;
    }
    body.honor-light-mode .honor-media-pill {
      background: rgba(255, 255, 255, 0.65);
      border: 1px solid rgba(0, 0, 0, 0.12);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
    }
    body.honor-light-mode .honor-pill-skip-btn,
    body.honor-light-mode .honor-pill-close-btn {
      color: #374151;
    }
    body.honor-light-mode .honor-pill-divider {
      background: rgba(0, 0, 0, 0.15);
    }"""

content, c_pill = re.subn(old_pill_css, new_pill_css, content, count=1)
print(f"3. Updated honor-media-pill to 85% translucent glassmorphism (count={c_pill})")

# 3. Bump version to v1.6.9 (build 169)
content = content.replace("v1.6.8", "v1.6.9")
content = content.replace("CURRENT_APP_BUILD = 168;", "CURRENT_APP_BUILD = 169;")
print("4. Bumped version to v1.6.9 (build 169)")

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

# 4. Bump server.py version to v1.6.9, build 169
for s_path in [desktop_server_d, desktop_server_c]:
    with open(s_path, "r", encoding="utf-8", errors="ignore") as f:
        s_code = f.read()
    s_code = re.sub(r'"version":\s*"[^"]+"', '"version": "v1.6.9"', s_code, count=1)
    s_code = re.sub(r'"version_code":\s*\d+', '"version_code": 169', s_code, count=1)
    old_cl = r'"changelog":\s*\[[^\]]+\]'
    new_cl = '''"changelog": [
                "Popup điều khiển Media dạng trong suốt 85% mượt mà chuẩn Glassmorphism",
                "Bỏ phần gạch chân màu xanh ở câu đang đọc theo giọng nói, giữ màu nền nhạt dịu mắt",
                "Đồng bộ tên giọng đọc ra ngoài giao diện theo thời gian thực"
            ]'''
    s_code = re.sub(old_cl, new_cl, s_code, count=1)
    with open(s_path, "w", encoding="utf-8") as f:
        f.write(s_code)
    print(f"5. Updated {s_path} with v1.6.9 & changelog")

print("\nALL FILES UPDATED WITH TRANSLUCENT MEDIA PILL AND UNDERLINE REMOVAL!")
