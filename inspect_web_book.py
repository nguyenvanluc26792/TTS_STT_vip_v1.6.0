# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")

path = r"D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\saved_books\web_7319d7d62d.json"
with open(path, "r", encoding="utf-8", errors="ignore") as f:
    data = json.load(f)

print("Title:", data.get("title"))
print("Source URL:", data.get("source_url"))
print("Last Crawl URL:", data.get("last_crawl_url"))
print("Total chapters:", len(data.get("chapters", [])))
print("lastChapter:", data.get("lastChapter"))

chapters = data.get("chapters", [])
for i in range(min(15, len(chapters))):
    ch = chapters[i]
    t = ch.get("title", "")
    p_len = len(ch.get("paragraphs", []))
    first_p = ch.get("paragraphs", [""])[0][:80] if ch.get("paragraphs") else ""
    print(f"Index {i}: Title: '{t}' | Paras: {p_len} | First: '{first_p}'")
