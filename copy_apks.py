import shutil
import os

built_apk = r'c:\Users\VANLUC\Downloads\Share tool -20261010T221918Z-1-001\Share tool\TTS_STT_vip_v1.6.0\HonorEpubReader\app\build\outputs\apk\debug\app-debug.apk'

targets = [
    r'c:\Users\VANLUC\Downloads\Share tool -20261010T221918Z-1-001\Share tool\TTS_STT_vip_v1.6.0\LReader.apk',
    r'c:\Users\VANLUC\Downloads\Share tool -20261010T221918Z-1-001\Share tool\TTS_STT_vip_v1.6.0\HonorReader_v1.6.38_debug.apk',
    r'c:\Users\VANLUC\Downloads\Share tool -20261010T221918Z-1-001\Share tool\TTS_STT_vip_v1.6.0\HonorReader_VIP_v1.0.apk',
    r'D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\LReader.apk',
    r'D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\HonorReader_VIP_v1.0.apk',
    r'D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\app-debug.apk'
]

print(f"Source APK exists: {os.path.exists(built_apk)} ({os.path.getsize(built_apk)} bytes)")

for t in targets:
    shutil.copy2(built_apk, t)
    print(f"Copied to {t}: {os.path.getsize(t)} bytes")

print("All APK targets updated successfully for v1.6.38!")
