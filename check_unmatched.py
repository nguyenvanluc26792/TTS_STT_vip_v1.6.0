# -*- coding: utf-8 -*-
import json, re, sys
sys.stdout.reconfigure(encoding="utf-8")

path = r"D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\saved_books\b83da51179c8.json"
with open(path, "r", encoding="utf-8", errors="ignore") as f:
    data = json.load(f)

ch_pattern = re.compile(r"^\s*(?:chương|hồi|tiết|quyển|phần|tập|bài|chapter|part)\s*[\d\w]+[:\s\.\-—].*", re.IGNORECASE)
chs = data["chapters"]
for i, ch in enumerate(chs):
    paras = ch.get("paragraphs", [])
    found = None
    for p in paras[:5]:
        p_strip = p.strip()
        if ch_pattern.match(p_strip) and len(p_strip) < 90:
            found = p_strip
            break
    if not found:
        print(f"Unmatched Ch {i}: Old='{ch.get('title')}' | First='{paras[0][:40] if paras else ''}'")
