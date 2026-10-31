# -*- coding: utf-8 -*-
import os, sys, re

desktop_template = r"D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\templates\index.html"
assets_template = r"c:\Users\VANLUC\Downloads\Share tool -20261010T221918Z-1-001\Share tool\TTS_STT_vip_v1.6.0\HonorEpubReader\app\src\main\assets\index.html"
desktop_server = r"D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\server.py"

print(f"Loading {desktop_template}...")
with open(desktop_template, "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

# 1. Hide honor-status-top completely
old_top_re = r"\.honor-status-top\s*\{[^}]+\}"
new_top_css = """#honorReaderTopStatus,
    .honor-status-top,
    #honorTopBookTitle,
    .honor-status-title,
    #honorTopChapterTitle,
    .honor-status-subtitle {
      display: none !important;
      visibility: hidden !important;
      opacity: 0 !important;
      height: 0 !important;
      min-height: 0 !important;
      max-height: 0 !important;
      padding: 0 !important;
      margin: 0 !important;
      overflow: hidden !important;
      pointer-events: none !important;
    }"""
content = re.sub(old_top_re, new_top_css, content, count=1)
print("1. Set .honor-status-top and children to display: none !important")

# 2. Adjust top margin of #readerScrollArea to 86px for flawless clearance below pill notch
old_top_rule = r"top:\s*78px\s*!important;\s*top:\s*max\(78px,\s*calc\(var\(--safe-cutout-top,\s*40px\)\s*\+\s*38px\),\s*calc\(env\(safe-area-inset-top,\s*0px\)\s*\+\s*38px\)\)\s*!important;"
new_top_rule = "top: 86px !important;\n      top: max(86px, calc(var(--safe-cutout-top, 40px) + 42px), calc(env(safe-area-inset-top, 0px) + 42px)) !important;"
content, count_t = re.subn(old_top_rule, new_top_rule, content)
print(f"2. Adjusted scroll area top margin to 86px (count={count_t})")

# 3. Update HTML markup to explicitly hide the top status container
old_html = r'<div id="honorReaderTopStatus"[^>]*>[\s\S]*?</div>'
new_html = r'<div id="honorReaderTopStatus" class="honor-status-top" style="display: none !important;"></div>'
content, count_h = re.subn(old_html, new_html, content, count=1)
print(f"3. Replaced top status HTML container (count={count_h})")

# 4. Clear text in JS updateHonorTopStatusBar
js_block_old = r"if \(topChap\) topChap\.textContent = cTitle;"
js_block_new = r"if (topChap) { topChap.textContent = ''; topChap.style.display = 'none'; }"
content, count_j = re.subn(js_block_old, js_block_new, content)
print(f"4. Updated JS to suppress topChap text (count={count_j})")

# Save to desktop template
with open(desktop_template, "w", encoding="utf-8") as f:
    f.write(content)
print(f"5. Saved to {desktop_template}")

# Sync to Android Assets template
with open(assets_template, "w", encoding="utf-8") as f:
    f.write(content)
print(f"6. Synced to {assets_template}")

# Bump server.py version
with open(desktop_server, "r", encoding="utf-8", errors="ignore") as f:
    server_code = f.read()

server_code = re.sub(r'"version":\s*"[^"]+"', '"version": "v1.6.13-honor-remove-top-header"', server_code, count=1)
with open(desktop_server, "w", encoding="utf-8") as f:
    f.write(server_code)
print("7. Bumped server.py version to v1.6.13-honor-remove-top-header")

print("SUCCESS: Top status bar completely removed and scroll area top perfected!")
