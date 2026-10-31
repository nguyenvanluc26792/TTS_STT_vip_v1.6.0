import urllib.request
import json
import base64
import time

def test_tts(text):
    url = "https://openspeech.bytedance.com/api/v1/tts"
    # Or test via local server /api/tts
    req_data = {
        "text": text,
        "voice_id": "BV074_streaming",
        "provider": "capcut"
    }
    req = urllib.request.Request(
        "http://127.0.0.1:5000/api/tts",
        data=json.dumps(req_data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req) as resp:
            data = resp.read()
            return len(data)
    except Exception as e:
        return str(e)

tests = [
    "Hắn quay đầu lại nhìn nàng.",
    "Hắn quay đầu lại, nhìn nàng.",
    "Hắn quay đầu lại, — nhìn nàng.",
    "Hắn quay đầu lại, —— nhìn nàng.",
    "Hắn quay đầu lại... nhìn nàng.",
    "Hắn quay đầu lại. Nhìn nàng.",
    "Hắn quay đầu lại, ... nhìn nàng.",
]

for i, t in enumerate(tests):
    size = test_tts(t)
    print(f"Test {i}: {size:6d} bytes")
