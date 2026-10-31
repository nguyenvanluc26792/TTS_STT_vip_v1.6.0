# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")

path = r"D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\saved_books\b83da51179c8.json"
with open(path, "r", encoding="utf-8", errors="ignore") as f:
    data = json.load(f)

for i, ch in enumerate(data.get("chapters", [])):
    content = " ".join(ch.get("paragraphs", []))
    if "Luân Hồi Kính" in content and "Hiên Viên Vấn Thiên" in content:
        print(f"MATCH FOUND! Chapter Index: {i}, Title: '{ch.get('title')}'")
        for p in ch.get("paragraphs", [])[:8]:
            print("  Para:", p[:80])
        break
