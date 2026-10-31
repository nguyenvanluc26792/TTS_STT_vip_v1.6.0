# -*- coding: utf-8 -*-
import os, sys, re

desktop_template = r"D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\templates\index.html"
assets_template = r"c:\Users\VANLUC\Downloads\Share tool -20261010T221918Z-1-001\Share tool\TTS_STT_vip_v1.6.0\HonorEpubReader\app\src\main\assets\index.html"
desktop_server = r"D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\server.py"

print(f"Loading {desktop_template}...")
with open(desktop_template, "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

# 1. Reduce top margin to 1/3 (from 86px / 42px offset down to 54px / 14px offset)
old_top_pattern = r"top:\s*86px\s*!important;\s*top:\s*max\(86px,\s*calc\(var\(--safe-cutout-top,\s*40px\)\s*\+\s*42px\),\s*calc\(env\(safe-area-inset-top,\s*0px\)\s*\+\s*42px\)\)\s*!important;"
new_top_rule = "top: 54px !important;\n      top: max(54px, calc(var(--safe-cutout-top, 40px) + 14px), calc(env(safe-area-inset-top, 0px) + 14px)) !important;"

content, count_t = re.subn(old_top_pattern, new_top_rule, content)
print(f"1. Updated scroll area top to 54px (count={count_t})")

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

server_code = re.sub(r'"version":\s*"[^"]+"', '"version": "v1.6.14-honor-top-margin-one-third"', server_code, count=1)
with open(desktop_server, "w", encoding="utf-8") as f:
    f.write(server_code)
print("4. Bumped server.py version to v1.6.14-honor-top-margin-one-third")

print("SUCCESS: Top margin reduced to 1/3 (54px / 14px offset below cutout)!")
