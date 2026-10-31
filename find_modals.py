with open(r'D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\templates\index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'class="[^"]*(?:modal|drawer|overlay)[^"]*"', text, re.IGNORECASE)
for m in sorted(set(matches)):
    print(m)
