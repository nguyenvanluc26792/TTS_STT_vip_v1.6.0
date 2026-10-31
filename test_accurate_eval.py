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
    proc = subprocess.Popen([edge_path, '--headless', '--remote-debugging-port=9555', '--disable-gpu', file_url])
    try:
        time.sleep(2)
        tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9555/json').read().decode())
        ws_url = tabs[0]['webSocketDebuggerUrl']
        async with websockets.connect(ws_url) as ws:
            # Enable Runtime
            await ws.send(json.dumps({'id': 1, 'method': 'Runtime.enable'}))
            
            exprs = [
                "typeof togglePlay",
                "typeof analyzeDialogueAttribution",
                "CURRENT_APP_VERSION",
                "CURRENT_APP_BUILD",
                "JSON.stringify(analyzeDialogueAttribution('- không có hứng thú! Lữ Tuyết lạnh lùng lên tiếng.'))",
                "JSON.stringify(analyzeDialogueAttribution('\"Đi thôi!\" Lữ Tuyết lạnh lùng lên tiếng.'))",
                "JSON.stringify(analyzeDialogueAttribution('\"Đồ hỗn xược!\" Lâm Tiêu giận dữ quát lớn.'))",
                "JSON.stringify(analyzeDialogueAttribution('Nàng khẽ nói: Huynh đi đâu đấy?'))"
            ]
            
            req_id = 10
            pending = {}
            for expr in exprs:
                req_id += 1
                pending[req_id] = expr
                await ws.send(json.dumps({
                    'id': req_id,
                    'method': 'Runtime.evaluate',
                    'params': {'expression': expr, 'returnByValue': True}
                }))
            
            while pending:
                msg = json.loads(await ws.recv())
                mid = msg.get('id')
                if mid in pending:
                    expr = pending.pop(mid)
                    val = msg.get('result', {}).get('result', {}).get('value')
                    err = msg.get('result', {}).get('exceptionDetails')
                    if err:
                        print(f"[FAIL] {expr} -> {err}")
                    else:
                        print(f"[OK] {expr} -> {val}")
    finally:
        proc.terminate()

if __name__ == '__main__':
    asyncio.run(check())
