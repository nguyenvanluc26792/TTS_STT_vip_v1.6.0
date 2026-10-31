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
    proc = subprocess.Popen([edge_path, '--headless', '--remote-debugging-port=9444', '--disable-gpu', 'about:blank'])
    try:
        time.sleep(2)
        tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9444/json').read().decode())
        ws_url = tabs[0]['webSocketDebuggerUrl']
        async with websockets.connect(ws_url) as ws:
            await ws.send(json.dumps({'id': 1, 'method': 'Runtime.enable'}))
            await ws.send(json.dumps({'id': 2, 'method': 'Page.enable'}))
            await ws.send(json.dumps({'id': 3, 'method': 'Page.navigate', 'params': {'url': file_url}}))
            
            start = time.time()
            while time.time() - start < 5:
                raw = await ws.recv()
                msg = json.loads(raw)
                method = msg.get('method')
                if method == 'Runtime.exceptionThrown':
                    print("EXCEPTION THROWN:", json.dumps(msg, ensure_ascii=False, indent=2))
                elif method == 'Runtime.consoleAPICalled':
                    params = msg.get('params', {})
                    if params.get('type') == 'error':
                        print("CONSOLE ERROR:", [a.get('value') or a.get('description') for a in params.get('args', [])])
    finally:
        proc.terminate()

if __name__ == '__main__':
    asyncio.run(test_func())
