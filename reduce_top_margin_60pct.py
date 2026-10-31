# -*- coding: utf-8 -*-
import os, sys, re

desktop_template = r"D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\templates\index.html"
assets_template = r"c:\Users\VANLUC\Downloads\Share tool -20261010T221918Z-1-001\Share tool\TTS_STT_vip_v1.6.0\HonorEpubReader\app\src\main\assets\index.html"
desktop_server = r"D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\server.py"

print(f"Loading {desktop_template}...")
with open(desktop_template, "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

# 1. Reduce top margin to 60% of 54px -> 32px to align flush with pill notch
old_top_pattern = r"top:\s*54px\s*!important;\s*top:\s*max\(54px,\s*calc\(var\(--safe-cutout-top,\s*40px\)\s*\+\s*14px\),\s*calc\(env\(safe-area-inset-top,\s*0px\)\s*\+\s*14px\)\)\s*!important;"
new_top_rule = "top: 32px !important;\n      top: max(32px, calc(env(safe-area-inset-top, 0px) + 6px)) !important;"

content, count_t = re.subn(old_top_pattern, new_top_rule, content)
print(f"1. Updated scroll area top to 32px (count={count_t})")

# Save to desktop template
with open(desktop_template, "w", encoding="utf-8") as f:
    f.write(content)
print(f"2. Saved to {desktop_template}")

# Sync to Android Assets template
with open(assets_template, "w", encoding="utf-8") as f:
    f.write(content)
print(f"3. Synced to {assets_template}")

# Bump server.py version
with open(desktop_server, "r", encoding="utf-8", errors="ignore") as f:
    server_code = f.read()

server_code = re.sub(r'"version":\s*"[^"]+"', '"version": "v1.6.15-honor-top-margin-level-pill"', server_code, count=1)
with open(desktop_server, "w", encoding="utf-8") as f:
    f.write(server_code)
print("4. Bumped server.py version to v1.6.15-honor-top-margin-level-pill")

print("SUCCESS: Top margin reduced to 60% (32px) to level with pill notch!")
