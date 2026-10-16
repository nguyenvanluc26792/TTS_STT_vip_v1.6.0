import re
import zlib

with open(r"c:\Users\VANLUC\Downloads\Share tool -20261010T221918Z-1-001\Share tool\TTS_STT_vip_v1.6.0\TTS_STT_vip_v1.6.0\TTS_STT.exe", "rb") as f:
    data = f.read()

print("File size:", len(data))

# Search for zlib compressed chunks
urls = set()
pattern = re.compile(rb"https?://[a-zA-Z0-9\.\-_/:\?=%&]+")

# Direct search
for m in pattern.findall(data):
    try:
        s = m.decode('ascii')
        if any(k in s for k in ['capcut', 'bytedance', 'tiktok', 'tts', 'speech', 'api']):
            urls.add(s)
    except:
        pass

print("Direct URLs found:", len(urls))
for u in sorted(urls)[:20]:
    print("  ", u)

# Search inside zlib streams
pos = 0
found_zlib = 0
while True:
    pos = data.find(b"\x78\x9c", pos)
    if pos == -1:
        break
    try:
        decomp = zlib.decompress(data[pos:pos+100000])
        for m in pattern.findall(decomp):
            s = m.decode('ascii')
            if any(k in s for k in ['capcut', 'bytedance', 'tiktok', 'tts', 'speech', 'api']):
                urls.add(s)
    except:
        pass
    pos += 1

print("Total URLs after zlib decomp:", len(urls))
for u in sorted(urls)[:30]:
    print("  ->", u)
