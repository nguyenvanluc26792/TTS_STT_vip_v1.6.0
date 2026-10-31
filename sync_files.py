import shutil
import os

src_html = r'D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\templates\index.html'

destinations = [
    r'c:\Users\VANLUC\Downloads\Share tool -20261010T221918Z-1-001\Share tool\TTS_STT_vip_v1.6.0\HonorEpubReader\app\src\main\assets\index.html',
    r'D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\HonorEpubReader\app\src\main\assets\index.html',
    r'D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\index.html'
]

for dst in destinations:
    try:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src_html, dst)
        print(f"Copied to: {dst} ({os.path.getsize(dst)} bytes)")
    except Exception as e:
        print(f"Failed {dst}: {e}")

src_server = r'D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\server.py'
dst_server = r'c:\Users\VANLUC\Downloads\Share tool -20261010T221918Z-1-001\Share tool\TTS_STT_vip_v1.6.0\server.py'
if os.path.exists(dst_server):
    shutil.copy2(src_server, dst_server)
    print("Updated root server.py")
