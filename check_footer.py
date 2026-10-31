import sys
sys.stdout.reconfigure(encoding='utf-8')
with open(r'D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\templates\index.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('honorReaderBottomStatus')
print(text[idx-40:idx+450])
