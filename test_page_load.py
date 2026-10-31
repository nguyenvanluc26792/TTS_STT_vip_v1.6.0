import asyncio
import websockets
import json
import subprocess
import time
import urllib.request
import sys

sys.stdout.reconfigure(encoding='utf-8')

async def check():
    edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
    file_url = 'file:///' + r'D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\templates\index.html'.replace('\\', '/')
    proc = subprocess.Popen([edge_path, '--headless', '--remote-debugging-port=9888', '--disable-gpu', 'about:blank'])
    try:
        time.sleep(2)
        tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9888/json').read().decode())
        ws_url = tabs[0]['webSocketDebuggerUrl']
        async with websockets.connect(ws_url, max_size=50_000_000) as ws:
            await ws.send(json.dumps({'id': 1, 'method': 'Runtime.enable'}))
            await ws.send(json.dumps({'id': 2, 'method': 'Page.enable'}))
            
            # Navigate to file_url
            await ws.send(json.dumps({'id': 3, 'method': 'Page.navigate', 'params': {'url': file_url}}))
            
            # Wait for Page.loadEventFired or 4 seconds
            loaded = False
            start = time.time()
            while time.time() - start < 4:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=1.0)
                    msg = json.loads(raw)
                    method = msg.get('method')
                    if method == 'Runtime.exceptionThrown':
                        print("EXCEPTION ON PAGE:", json.dumps(msg['params']['exceptionDetails'], ensure_ascii=False))
                    elif method == 'Runtime.consoleAPICalled':
                        args = [str(a.get('value', a.get('description', ''))) for a in msg['params'].get('args', [])]
                        if msg['params'].get('type') == 'error':
                            print("CONSOLE ERROR:", " ".join(args))
                    elif method == 'Page.loadEventFired':
                        print("Page load event fired!")
                        loaded = True
                except asyncio.TimeoutError:
                    pass
            
            # Now evaluate functions
            tests = [
                "typeof togglePlay",
                "typeof analyzeDialogueAttribution",
                "CURRENT_APP_VERSION",
                "JSON.stringify(analyzeDialogueAttribution('- không có hứng thú! Lữ Tuyết lạnh lùng lên tiếng.'))",
                "JSON.stringify(analyzeDialogueAttribution('Vèo, vèo, vèo'))"
            ]
            for i, t in enumerate(tests, 100):
                await ws.send(json.dumps({'id': i, 'method': 'Runtime.evaluate', 'params': {'expression': t, 'returnByValue': True}}))
                while True:
                    msg = json.loads(await ws.recv())
                    if msg.get('id') == i:
                        val = msg.get('result', {}).get('result', {}).get('value')
                        err = msg.get('result', {}).get('exceptionDetails')
                        if err:
                            print(f"[FAIL] {t} -> {err}")
                        else:
                            print(f"[SUCCESS] {t} -> {val}")
                        break
    finally:
        proc.terminate()

if __name__ == '__main__':
    asyncio.run(check())
