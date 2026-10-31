import sys
sys.stdout.reconfigure(encoding='utf-8')
with open(r'D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\templates\index.html', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")
for j in range(len(lines)-30, len(lines)):
    print(f"{j+1}: {lines[j].rstrip()}")
