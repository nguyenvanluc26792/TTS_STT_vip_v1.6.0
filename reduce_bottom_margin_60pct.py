# -*- coding: utf-8 -*-
import os, sys, re

desktop_template = r"D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\templates\index.html"
assets_template = r"c:\Users\VANLUC\Downloads\Share tool -20261010T221918Z-1-001\Share tool\TTS_STT_vip_v1.6.0\HonorEpubReader\app\src\main\assets\index.html"
desktop_server = r"D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\server.py"

print(f"Loading {desktop_template}...")
with open(desktop_template, "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

# 1. Reduce bottom margin to 60% of 58px -> 35px
old_bottom_pattern = r"bottom:\s*58px\s*!important;\s*bottom:\s*max\(58px,\s*calc\(env\(safe-area-inset-bottom,\s*0px\)\s*\+\s*38px\)\)\s*!important;"
new_bottom_rule = "bottom: 35px !important;\n      bottom: max(35px, calc(env(safe-area-inset-bottom, 0px) + 23px)) !important;"

content, count_b = re.subn(old_bottom_pattern, new_bottom_rule, content)
print(f"1. Updated scroll area bottom to 35px (count={count_b})")

# 2. Update .honor-bottom-tap-zone height to 35px
old_tap_re = r"\.honor-bottom-tap-zone\s*\{[^}]+\}"
new_tap_css = """.honor-bottom-tap-zone {
      position: absolute !important;
      bottom: 0 !important;
      left: 0 !important;
      right: 0 !important;
      height: 35px !important;
      height: max(35px, calc(env(safe-area-inset-bottom, 0px) + 23px)) !important;
      z-index: 850 !important;
      background: transparent !important;
      cursor: pointer !important;
      -webkit-tap-highlight-color: transparent !important;
      touch-action: manipulation !important;
    }"""
content = re.sub(old_tap_re, new_tap_css, content, count=1)
print("2. Updated .honor-bottom-tap-zone to 35px")

# 3. Update .honor-status-bottom height to 28px, padding-bottom: max(4px, ...)
old_bot_re = r"\.honor-status-bottom\s*\{[^}]+\}"
new_bot_css = """.honor-status-bottom {
      position: absolute !important;
      bottom: 0 !important;
      left: 0 !important;
      right: 0 !important;
      height: 28px !important;
      padding: 0 18px 4px 18px !important;
      padding-bottom: max(4px, env(safe-area-inset-bottom, 0px)) !important;
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
print("3. Updated .honor-status-bottom to compact 28px")

# 4. Update JS clickY checks
content = re.sub(r"clickY >= h - 58", "clickY >= h - 35", content)
content = re.sub(r"clickY >= h - 50", "clickY >= h - 35", content)
print("4. Updated JS clickY checks to h - 35")

# Save to desktop template
with open(desktop_template, "w", encoding="utf-8") as f:
    f.write(content)
print(f"5. Saved to {desktop_template}")

# Sync to Android Assets template
with open(assets_template, "w", encoding="utf-8") as f:
    f.write(content)
print(f"6. Synced to {assets_template}")

# 7. Bump server.py version
with open(desktop_server, "r", encoding="utf-8", errors="ignore") as f:
    server_code = f.read()

server_code = re.sub(r'"version":\s*"[^"]+"', '"version": "v1.6.10-honor-bottom-margin-60pct"', server_code, count=1)
with open(desktop_server, "w", encoding="utf-8") as f:
    f.write(server_code)
print("7. Bumped server.py version to v1.6.10-honor-bottom-margin-60pct")

print("SUCCESS: Bottom margin reduced to 60% (35px) in all files!")
