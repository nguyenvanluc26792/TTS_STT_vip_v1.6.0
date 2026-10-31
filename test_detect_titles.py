# -*- coding: utf-8 -*-
import json, sys, re
sys.stdout.reconfigure(encoding="utf-8")

path = r"D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\saved_books\b83da51179c8.json"
with open(path, "r", encoding="utf-8", errors="ignore") as f:
    data = json.load(f)

chs = data["chapters"]
found_real_titles = 0
ch_pattern = re.compile(r"^\s*(?:chương|hồi|tiết|quyển|phần|tập|bài|chapter|part)\s*[\d\w]+[:\s\.\-—].*$", re.IGNORECASE)

for i, ch in enumerate(chs[:30]):
    paras = ch.get("paragraphs", [])
    real_title = None
    for p in paras[:4]:
        p_strip = p.strip()
        if ch_pattern.match(p_strip) and len(p_strip) < 100:
            real_title = p_strip
            break
    print(f"Index {i} | Old: '{ch.get('title')}' | Detected: '{real_title}'")
