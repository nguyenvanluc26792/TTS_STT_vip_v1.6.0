import sys
sys.stdout.reconfigure(encoding='utf-8')
with open(r'D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\templates\index.html', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if '.sentence-item' in line:
        print(f"{i+1}: {line.strip()[:100]}")
