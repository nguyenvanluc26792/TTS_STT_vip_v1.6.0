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
    proc = subprocess.Popen([edge_path, '--headless', '--remote-debugging-port=9999', '--disable-gpu', 'http://127.0.0.1:5000'])
    try:
        time.sleep(3)
        tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9999/json').read().decode())
        ws_url = None
        for t in tabs:
            if '127.0.0.1:5000' in t.get('url', ''):
                ws_url = t.get('webSocketDebuggerUrl')
                print(f"FOUND TARGET TAB: {t.get('url')} -> {ws_url}")
                break
        
        if not ws_url:
            print("ERROR: http://127.0.0.1:5000 tab not found!")
            return

        async with websockets.connect(ws_url, max_size=50_000_000) as ws:
            await ws.send(json.dumps({'id': 1, 'method': 'Runtime.enable'}))
            
            exprs = [
                "typeof togglePlay",
                "typeof analyzeDialogueAttribution",
                "CURRENT_APP_VERSION",
                "CURRENT_APP_BUILD",
                "JSON.stringify(analyzeDialogueAttribution('Bạch Tiểu Thuần vỗ ngực, hắn cười lớn nói: \"Ta chính là thiên tài!\"'))",
                "JSON.stringify(analyzeDialogueAttribution('\"Sư đệ đừng làm càn!\" - Nam Cung Uyển khẽ nói.'))",
                "JSON.stringify(analyzeDialogueAttribution('- không có hứng thú! Lữ Tuyết lạnh lùng lên tiếng.'))",
                "JSON.stringify(analyzeDialogueAttribution('\"Diệp Phàm, ngươi dám!\" - Vương Đằng giận dữ hét lên.'))",
                "JSON.stringify(analyzeDialogueAttribution('Bạch Tiểu Thuần lại tiếp lời: \"Mau giao linh thạch ra!\"'))",
                "JSON.stringify(loadCharacterRegistry())"
            ]
            
            for i, expr in enumerate(exprs, 10):
                await ws.send(json.dumps({
                    'id': i,
                    'method': 'Runtime.evaluate',
                    'params': {'expression': expr, 'returnByValue': True}
                }))
                while True:
                    msg = json.loads(await ws.recv())
                    if msg.get('id') == i:
                        val = msg.get('result', {}).get('result', {}).get('value')
                        err = msg.get('result', {}).get('exceptionDetails')
                        if err:
                            print(f"[ERROR] {expr} -> {err}")
                        else:
                            print(f"[OK] {expr} -> {val}")
                        break
    finally:
        proc.terminate()

if __name__ == '__main__':
    asyncio.run(check())
