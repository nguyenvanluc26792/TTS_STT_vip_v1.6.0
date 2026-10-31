import json
import subprocess
import time
import urllib.request
import asyncio
import sys

async def check_page():
    edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
    file_url = 'file:///' + r'D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\templates\index.html'.replace('\\', '/')
    proc = subprocess.Popen([
        edge_path,
        '--headless',
        '--remote-debugging-port=9333',
        '--disable-gpu',
        file_url
    ])
    try:
        time.sleep(2)
        req = urllib.request.urlopen('http://127.0.0.1:9333/json')
        tabs = json.loads(req.read().decode())
        ws_url = None
        for t in tabs:
            if 'index.html' in t.get('url', ''):
                ws_url = t.get('webSocketDebuggerUrl')
                break
        if not ws_url and tabs:
            ws_url = tabs[0].get('webSocketDebuggerUrl')
        
        print(f"Target tab: {ws_url}")
        if not ws_url:
            print("No websocket url found")
            return

        try:
            import websockets
        except ImportError:
            print("websockets module not installed, trying pip or alternative")
            return

        async with websockets.connect(ws_url) as ws:
            # Enable Runtime
            await ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
            res = await ws.recv()
            
            exprs = [
                "typeof togglePlay",
                "typeof analyzeDialogueAttribution",
                "typeof playParagraph",
                "CURRENT_APP_VERSION",
                "CURRENT_APP_BUILD"
            ]
            for i, expr in enumerate(exprs, 2):
                await ws.send(json.dumps({
                    "id": i,
                    "method": "Runtime.evaluate",
                    "params": {"expression": expr}
                }))
                reply = await ws.recv()
                print(f"Eval '{expr}': {reply}")
    finally:
        proc.terminate()

if __name__ == '__main__':
    asyncio.run(check_page())
