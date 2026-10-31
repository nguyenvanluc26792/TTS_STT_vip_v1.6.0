import asyncio
import websockets
import json
import subprocess
import time
import urllib.request
import sys

sys.stdout.reconfigure(encoding='utf-8')

async def test_func():
    edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
    file_url = 'file:///' + r'D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\templates\index.html'.replace('\\', '/')
    proc = subprocess.Popen([edge_path, '--headless', '--remote-debugging-port=9444', '--disable-gpu', file_url])
    try:
        time.sleep(2)
        tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9444/json').read().decode())
        ws_url = tabs[0]['webSocketDebuggerUrl']
        async with websockets.connect(ws_url) as ws:
            tc = "- không có hứng thú! Lữ Tuyết lạnh lùng lên tiếng."
            expr = f"analyzeDialogueAttribution({json.dumps(tc)})"
            await ws.send(json.dumps({'id': 100, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}))
            while True:
                raw = await ws.recv()
                msg = json.loads(raw)
                if msg.get('id') == 100:
                    print("RAW:", json.dumps(msg, ensure_ascii=False, indent=2))
                    break
    finally:
        proc.terminate()

if __name__ == '__main__':
    asyncio.run(test_func())
