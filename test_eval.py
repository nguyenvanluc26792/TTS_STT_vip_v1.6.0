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
            test_cases = [
                "- không có hứng thú! Lữ Tuyết lạnh lùng lên tiếng.",
                "\"Không thể nào!\" Lâm Tiêu giận dữ quát lớn.",
                "Nàng dịu dàng mỉm cười nói: Đừng sợ.",
                "Vèo, vèo, vèo"
            ]
            for tc in test_cases:
                expr = f"analyzeDialogueAttribution({json.dumps(tc)})"
                await ws.send(json.dumps({'id': 100, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}))
                while True:
                    msg = json.loads(await ws.recv())
                    if msg.get('id') == 100:
                        val = msg.get('result', {}).get('result', {}).get('value')
                        print(f"{tc}\n => {json.dumps(val, ensure_ascii=False)}\n")
                        break
    finally:
        proc.terminate()

if __name__ == '__main__':
    asyncio.run(test_func())
