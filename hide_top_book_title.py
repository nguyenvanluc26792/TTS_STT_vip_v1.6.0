# -*- coding: utf-8 -*-
import os, sys, re

desktop_template = r"D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\templates\index.html"
assets_template = r"c:\Users\VANLUC\Downloads\Share tool -20261010T221918Z-1-001\Share tool\TTS_STT_vip_v1.6.0\HonorEpubReader\app\src\main\assets\index.html"
desktop_server = r"D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\server.py"

print(f"Loading {desktop_template}...")
with open(desktop_template, "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

# 1. Update CSS for honor-status-title and honor-status-subtitle
old_title_css = r"\.honor-status-title\s*\{[^}]+\}"
new_title_css = """#honorTopBookTitle,
    .honor-status-title {
      display: none !important;
    }
    .honor-status-subtitle {
      margin-left: auto !important;
      font-size: 11px;
      color: #666666;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 65%;
    }"""

content, count_c = re.subn(old_title_css, new_title_css, content, count=1)
print(f"1. Updated CSS to hide honor-status-title (count={count_c})")

# 2. Update HTML markup for honorTopBookTitle
old_html = r'<span id="honorTopBookTitle" class="honor-status-title">[^<]*</span>'
new_html = r'<span id="honorTopBookTitle" class="honor-status-title" style="display: none !important;"></span>'
content, count_h = re.subn(old_html, new_html, content, count=1)
print(f"2. Updated HTML markup (count={count_h})")

# 3. Update JS in updateHonorTopStatusBar
old_js = r"if \(topBook\) topBook\.textContent = bTitle;"
new_js = r"if (topBook) { topBook.textContent = ''; topBook.style.display = 'none'; }"
content, count_j = re.subn(old_js, new_js, content, count=1)
print(f"3. Updated JS updateHonorTopStatusBar (count={count_j})")

# Save to desktop template
with open(desktop_template, "w", encoding="utf-8") as f:
    f.write(content)
print(f"4. Saved to {desktop_template}")

# Sync to Android Assets template
with open(assets_template, "w", encoding="utf-8") as f:
    f.write(content)
print(f"5. Synced to {assets_template}")

# Bump server.py version
with open(desktop_server, "r", encoding="utf-8", errors="ignore") as f:
    server_code = f.read()

server_code = re.sub(r'"version":\s*"[^"]+"', '"version": "v1.6.12-honor-hide-book-title"', server_code, count=1)
with open(desktop_server, "w", encoding="utf-8") as f:
    f.write(server_code)
print("6. Bumped server.py version to v1.6.12-honor-hide-book-title")

print("SUCCESS: Book title removed from top border!")
