# -*- coding: utf-8 -*-
import json, sys

sys.stdout.reconfigure(encoding="utf-8")

path = r"D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\saved_books\b83da51179c8.json"
with open(path, "r", encoding="utf-8", errors="ignore") as f:
    data = json.load(f)

print("Title:", data.get("title"))
print("Total chapters:", len(data.get("chapters", [])))
print("lastChapter:", data.get("lastChapter"))

chapters = data.get("chapters", [])
for i in range(min(20, len(chapters))):
    ch = chapters[i]
    t = ch.get("title", "")
    p_len = len(ch.get("paragraphs", []))
    first_p = ch.get("paragraphs", [""])[0][:60] if ch.get("paragraphs") else ""
    print(f"Chapter Index {i}: Title: '{t}' | Paras: {p_len} | First para: '{first_p}'")
