# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
path = r"D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\saved_books\b83da51179c8.json"
with open(path, "r", encoding="utf-8", errors="ignore") as f:
    data = json.load(f)

for i in [2, 3, 4, 5]:
    ch = data["chapters"][i]
    print(f"=== CH {i} ({ch.get('title')}) ===")
    for p in ch.get("paragraphs", [])[:8]:
        print("  ", p[:100])
