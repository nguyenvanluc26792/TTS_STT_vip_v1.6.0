import asyncio
import websockets
import json
import subprocess
import time
import urllib.request
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read JS code from index.html
with open(r'D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\templates\index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Extract script
match = re.search(r'<script.*?>([\s\S]*?)<\/script>', html)
if not match:
    print("No script found!")
    sys.exit(1)

js_code = match.group(1)
print(f"Extracted JS code length: {len(js_code)} chars")

async def test_syntax():
    edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
    proc = subprocess.Popen([edge_path, '--headless', '--remote-debugging-port=9666', '--disable-gpu', 'about:blank'])
    try:
        time.sleep(2)
        tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9666/json').read().decode())
        ws_url = tabs[0]['webSocketDebuggerUrl']
        async with websockets.connect(ws_url, max_size=50_000_000) as ws:
            await ws.send(json.dumps({'id': 1, 'method': 'Runtime.enable'}))
            await ws.recv() # ack
            
            # Use Runtime.compileScript to find EXACT syntax error line & col
            await ws.send(json.dumps({
                'id': 2,
                'method': 'Runtime.compileScript',
                'params': {
                    'expression': js_code,
                    'sourceURL': 'index_extracted.js',
                    'persistScript': False
                }
            }))
            
            msg = json.loads(await ws.recv())
            print("CompileScript result:", json.dumps(msg, ensure_ascii=False, indent=2))
    finally:
        proc.terminate()

if __name__ == '__main__':
    asyncio.run(test_syntax())
