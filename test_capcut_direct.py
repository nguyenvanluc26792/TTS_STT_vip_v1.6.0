import json
import base64
import urllib.request
import time

def call_capcut_direct(text, voice="BV074_streaming"):
    url = "https://openspeech.bytedance.com/api/v1/tts"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer M_vXp2zPzQ4kQ5eL"
    }
    payload = {
        "app": {
            "appid": "348187",
            "token": "M_vXp2zPzQ4kQ5eL",
            "cluster": "volcano_tts"
        },
        "user": {
            "uid": "388808088185083"
        },
        "audio": {
            "voice_type": voice,
            "encoding": "mp3",
            "speed_ratio": 1.0,
            "volume_ratio": 1.0,
            "pitch_ratio": 1.0
        },
        "request": {
            "reqid": f"test_{int(time.time()*1000)}",
            "text": text,
            "text_type": "plain",
            "operation": "query"
        }
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        if "data" in res:
            audio_bytes = base64.b64decode(res["data"])
            return len(audio_bytes)
        return res

tests = [
    ("No punctuation", "Hắn quay đầu lại nhìn nàng"),
    ("Normal comma", "Hắn quay đầu lại, nhìn nàng"),
    ("Comma em-dash", "Hắn quay đầu lại, — nhìn nàng"),
    ("Comma double em-dash", "Hắn quay đầu lại, —— nhìn nàng"),
    ("Triple comma", "Hắn quay đầu lại, , , nhìn nàng"),
    ("Dot pause", "Hắn quay đầu lại. Nhìn nàng"),
    ("Ellipsis pause", "Hắn quay đầu lại... Nhìn nàng"),
    ("Hyphen pause", "Hắn quay đầu lại - nhìn nàng"),
    ("Semicolon pause", "Hắn quay đầu lại; nhìn nàng"),
]

for label, t in tests:
    size = call_capcut_direct(t)
    print(f"{label:22s}: {size} bytes")
