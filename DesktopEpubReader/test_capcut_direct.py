import json
import time
import uuid
import base64
import secrets
import hashlib
import requests

_RSA_N = 19341813084631315671282549431798655160825512801013391560750156528444287447892559220236099203022189312996509243483755654291658808631344567184378689327273259390644661930225954596968213035923198083437102535618783415692653811348862243705526699107851690693125596736080099356396803461339216527691309374959691258789927689498378878482554514874089477069000113270337080049670332556471810330214798429795238319101401506608665290167760399585652278886979131868827422701738576086077151453279247167711376399900166201302369203349172030364626191019105037101985688867268590829086107225896220811741526787405362085604352187239844583176859
_RSA_E = 65537
_AID = "359289"
_APPVR = "8.7.0"
BASE_URL = "https://editor-api-sg.capcutapi.com"
_PATH_NEW = "/lv/v1/common_task/new"
_PATH_QUERY = "/lv/v1/common_task/query"

_BABI = {
    "feature_entrance": "editor",
    "feature_entrance_detail": "editor-feature-text_to_speech",
    "feature_key": "text_to_speech",
    "scenario": "video_editor"
}

def _rsa_ma_hoa(msg: str) -> str:
    m = msg.encode("utf-8")
    k = (_RSA_N.bit_length() + 7) // 8
    ps_len = k - len(m) - 3
    if ps_len < 0:
        raise ValueError("Văn bản quá dài so với khóa RSA")
    ps = bytearray()
    while len(ps) < ps_len:
        b = secrets.token_bytes(1)[0]
        if b != 0:
            ps.append(b)
    goi = b"\x00\x02" + bytes(ps) + b"\x00" + m
    c = pow(int.from_bytes(goi, "big"), _RSA_E, _RSA_N)
    return base64.b64encode(c.to_bytes(k, "big")).decode("ascii")

def _ky_payload(ssml: str, extra_info: str, device_id: str) -> str:
    md5_ssml = hashlib.md5(ssml.encode("utf-8")).hexdigest()
    s = f"appid:{_AID}&did:{device_id}&creditDisable:false&ssml:{md5_ssml}&extraInfo:{extra_info}"
    return _rsa_ma_hoa(s)

def _ky_header(path: str, device_time: int, tdid: str) -> str:
    raw = f"9e2c|{_APPVR[-7:]}|3|{path}|{device_time}|{tdid}|11ac"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()

def _escape_xml(text: str) -> str:
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;"))

def generate_device():
    did = str(secrets.randbelow(1000000000000000000) + 7000000000000000000)
    return {
        "aid": _AID,
        "app_name": "CapCut",
        "appvr": _APPVR,
        "version_name": _APPVR,
        "version_code": _APPVR,
        "channel": "capcutpc_google",
        "device_platform": "windows",
        "device_type": "Windows",
        "device_brand": "Windows",
        "os_version": "10.0.19045",
        "device_id": did,
        "iid": did,
        "tdid": did,
        "region": "VN",
        "loc": "VN",
        "lan": "vi-VN",
        "pf": "3"
    }

def synthesize_capcut(text: str, voice_type="BV074_streaming", resource_id="7102355709945188865"):
    dev = generate_device()
    ts = str(int(time.time()))
    ssml = f'''<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
    <voice name="{voice_type}" mock_tone_info="" platform="sami" resource_id="{resource_id}" emotion="" emotion_scale="0" style="" role="" moyin_emotion="" is_clone_tone="false" need_subtitle_timestamp="false">
        <prosody rate="1.0">{_escape_xml(text)}</prosody>
    </voice>
</speak>'''
    
    sign = _ky_payload(ssml, "", dev["device_id"])
    
    payload = {
        "audio_format": "mp3",
        "babi_param": json.dumps(_BABI, ensure_ascii=False, separators=(",", ":")),
        "credit_disable": False,
        "extra_info": "",
        "need_merge_voice": False,
        "need_subtitle_timestamp": False,
        "scene": "text_to_speech",
        "ssml": ssml,
        "sign": sign
    }
    
    body = {
        "bind_id": str(uuid.uuid4()),
        "can_queue": True,
        "enter_from": "text_to_speech",
        "tasks": [{
            "context": {"benefit_info": ""},
            "payload": json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            "req_key": "sami_text_to_speech",
            "task_version": "v3"
        }]
    }
    
    body_json = json.dumps(body, ensure_ascii=False, separators=(",", ":"))
    device_time = int(time.time())
    
    headers = {
        "content-type": "application/json",
        "appvr": _APPVR,
        "ch": "capcutpc_google",
        "channel": "capcutpc_google",
        "device-time": str(device_time),
        "lan": "vi-VN",
        "loc": "VN",
        "pf": "3",
        "sign-ver": "1",
        "tdid": dev["tdid"],
        "device_id": dev["device_id"],
        "x-ss-stub": hashlib.md5(body_json.encode("utf-8")).hexdigest(),
        "x-ss-dp": _AID,
        "sign": _ky_header(_PATH_NEW, device_time, dev["tdid"]),
        "x-khronos": str(device_time),
        "x-tt-trace-id": f"00-{secrets.token_hex(16)}-{secrets.token_hex(8)}-01",
        "user-agent": "Cronet/TTNetVersion:1d7cc3b1 2025-07-16 QuicVersion:52c2b40d 2025-04-03"
    }
    
    query_keys = ["app_name", "device_type", "os_version", "channel", "version_name", "device_brand", "device_id", "iid", "version_code", "device_platform", "aid"]
    query_params = {k: dev[k] for k in query_keys}
    query_params["region"] = "VN"
    query_params["babi_param"] = json.dumps(_BABI, ensure_ascii=False, separators=(",", ":"))
    
    url = f"{BASE_URL}{_PATH_NEW}?" + requests.compat.urlencode(query_params)
    resp = requests.post(url, data=body_json.encode("utf-8"), headers=headers, timeout=15)
    data = resp.json()
    print("New Task Resp:", data)
    
    tasks = data.get("data", {}).get("tasks", [])
    if not tasks:
        raise Exception(f"Tạo task thất bại: {data}")
    
    task_id = tasks[0]["id"]
    token = tasks[0]["token"]
    
    # Poll query task
    poll_body = {
        "tasks": [{
            "bind_id": "",
            "id": task_id,
            "req_key": "sami_text_to_speech",
            "task_version": "v3",
            "token": token
        }]
    }
    poll_json = json.dumps(poll_body, ensure_ascii=False, separators=(",", ":"))
    
    for _ in range(15):
        time.sleep(1.0)
        p_time = int(time.time())
        p_headers = {
            "content-type": "application/json",
            "appvr": _APPVR,
            "channel": "capcutpc_google",
            "device-time": str(p_time),
            "lan": "vi-VN",
            "loc": "VN",
            "pf": "3",
            "sign-ver": "1",
            "tdid": dev["tdid"],
            "device_id": dev["device_id"],
            "x-ss-stub": hashlib.md5(poll_json.encode("utf-8")).hexdigest(),
            "x-ss-dp": _AID,
            "sign": _ky_header(_PATH_QUERY, p_time, dev["tdid"]),
            "x-khronos": str(p_time),
            "user-agent": "Cronet/TTNetVersion:1d7cc3b1 2025-07-16 QuicVersion:52c2b40d 2025-04-03"
        }
        poll_url = f"{BASE_URL}{_PATH_QUERY}?" + requests.compat.urlencode(query_params)
        p_resp = requests.post(poll_url, data=poll_json.encode("utf-8"), headers=p_headers, timeout=15)
        p_data = p_resp.json()
        print("Poll Resp:", p_data)
        res_tasks = p_data.get("data", {}).get("tasks", [])
        if res_tasks and res_tasks[0].get("status") == "succeed":
            payload_str = res_tasks[0].get("payload", "{}")
            payload_obj = json.loads(payload_str)
            speech_url = payload_obj.get("speech_url")
            print("FOUND AUDIO URL:", speech_url)
            audio_data = requests.get(speech_url).content
            return audio_data

if __name__ == "__main__":
    audio = synthesize_capcut("Xin chào các bạn, tôi là Cô Gái Hoạt Ngôn đến từ CapCut!")
    with open("test_capcut_success.mp3", "wb") as f:
        f.write(audio)
    print("SUCCESS! File size:", len(audio))
