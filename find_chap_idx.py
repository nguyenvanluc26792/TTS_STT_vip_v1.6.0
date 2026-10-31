# -*- coding: utf-8 -*-
import sys, re
sys.stdout.reconfigure(encoding="utf-8")

with open(r"D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\templates\index.html", "r", encoding="utf-8", errors="ignore") as f:
    text = f.read()

for m in re.finditer(r"currentChapterIndex\s*=\s*[^;\n]+", text):
    s = max(0, m.start() - 40)
    e = min(len(text), m.end() + 60)
    print(text[s:e].replace('\n', ' '))
