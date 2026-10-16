import sys
sys.stdout.reconfigure(encoding='utf-8')
import urllib.request, json, time, hashlib, base64

_RSA_N = int('19341813084631315671282549431798655160825512801013391560750156528444287447892559220236099203022189312996509243483755654291658808631344567184378689327273259390644661930225954596968213035923198083437102535618783415692653811348862243705526699107851690693125596736080099356396803461339216527691309374959691258789927689498378878482554514874089477069000113270337080049670332556471810330214798429795238319101401506608665290167760399585652278886979131868827422701738576086077151453279247167711376399900166201302369203349172030364626191019105037101985688867268590829086107225896220811741526787405362085604352187239844583176859')
_RSA_E = 65537

def md5(s):
    return hashlib.md5(s.encode('utf-8')).hexdigest()

def rsa_enc(msg):
    m = msg.encode('utf-8')
    k = (_RSA_N.bit_length() + 7) // 8
    ps_len = k - len(m) - 3
    import secrets
    ps = bytearray()
    while len(ps) < ps_len:
        for b in secrets.token_bytes(ps_len - len(ps)):
            if b != 0: ps.append(b)
    goi = b'\x00\x02' + bytes(ps[:ps_len]) + b'\x00' + m
    c = pow(int.from_bytes(goi, 'big'), _RSA_E, _RSA_N)
    return base64.b64encode(c.to_bytes(k, 'big')).decode('ascii')

deviceId = '7828052662984453186'
voiceName = 'BV074_streaming'
cleanText = 'Xin chao ban'

babi_str = '{"feature_entrance":"editor","feature_entrance_detail":"editor-feature-text_to_speech","feature_key":"text_to_speech","scenario":"video_editor"}'
ssml = f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">\n    <voice name="{voiceName}" mock_tone_info="" platform="sami" resource_id="" emotion="" emotion_scale="0" style="" role="" moyin_emotion="" is_clone_tone="false" need_subtitle_timestamp="false">\n        <prosody rate="1.0">{cleanText}</prosody>\n    </voice>\n</speak>'
extra_info = '{"benefit_info":{}}'
s = f'appid:359289&did:{deviceId}&creditDisable:false&ssml:{md5(ssml)}&extraInfo:{extra_info}'
sign = rsa_enc(s)

pl = {
    'audio_format': 'mp3',
    'babi_param': babi_str,
    'credit_disable': False,
    'extra_info': extra_info,
    'need_merge_voice': False,
    'need_subtitle_timestamp': False,
    'scene': 'text_to_speech',
    'ssml': ssml,
    'sign': sign
}
body = json.dumps({
    'bind_id': '85a4ebaa-71ad-4b05-ab47-26d3b7c570d0',
    'can_queue': True,
    'enter_from': 'text_to_speech',
    'tasks': [{
        'context': 'e126a9d7-ba4f-494f-9e25-d74b28fd8ae7',
        'payload': json.dumps(pl, separators=(',', ':')),
        'req_key': 'sami_text_to_speech',
        'task_version': 'v3'
    }]
}, separators=(',', ':'))

deviceTime = str(int(time.time()))
pathTail = '/lv/v1/common_task/new'[-7:]
hSign = md5(f'9e2c|{pathTail}|3|8.7.0|{deviceTime}|{deviceId}|11ac')

headers = {
    'content-type': 'application/json',
    'appvr': '8.7.0',
    'ch': 'capcutpc_google',
    'device-time': deviceTime,
    'lan': 'vi-VN',
    'loc': 'VN',
    'pf': '3',
    'sign-ver': '1',
    'tdid': deviceId,
    'x-ss-stub': md5(body),
    'x-ss-dp': '359289',
    'x-khronos': deviceTime,
    'sign': hSign,
    'appid': '359289',
    'user-agent': 'Cronet/TTNetVersion:1d7cc3b1 2025-07-16 QuicVersion:52c2b40d 2025-04-03'
}

url = f'https://editor-api-sg.capcutapi.com/lv/v1/common_task/new?app_name=CapCut&device_type=Windows&os_version=10.0.19045&channel=capcutpc_google&version_name=8.7.0&device_brand=Windows&device_id={deviceId}&iid={deviceId}&version_code=8.7.0&device_platform=windows&aid=359289&region=VN&babi_param=%7B%22feature_entrance%22%3A%22editor%22%2C%22feature_entrance_detail%22%3A%22editor-feature-text_to_speech%22%2C%22feature_key%22%3A%22text_to_speech%22%2C%22scenario%22%3A%22video_editor%22%7D'

req = urllib.request.Request(url, data=body.encode('utf-8'), headers=headers)
with urllib.request.urlopen(req) as r:
    res = json.loads(r.read().decode('utf-8'))
    tasks = res.get('data', {}).get('tasks', [])
    task_id = tasks[0]['id']
    token = tasks[0]['token']
    print('Created task:', task_id)

time.sleep(1.2)
qBody = json.dumps({'tasks': [{'bind_id':'', 'id': task_id, 'req_key': 'sami_text_to_speech', 'task_version': 'v3', 'token': token}]}, separators=(',', ':'))
qTime = str(int(time.time()))
qTail = '/lv/v1/common_task/query'[-7:]
qSign = md5(f'9e2c|{qTail}|3|8.7.0|{qTime}|{deviceId}|11ac')
qHeaders = {
    'content-type': 'application/json',
    'appvr': '8.7.0',
    'ch': 'capcutpc_google',
    'device-time': qTime,
    'lan': 'vi-VN',
    'loc': 'VN',
    'pf': '3',
    'sign-ver': '1',
    'tdid': deviceId,
    'x-ss-stub': md5(qBody),
    'x-ss-dp': '359289',
    'x-khronos': qTime,
    'sign': qSign,
    'appid': '359289',
    'user-agent': 'Cronet/TTNetVersion:1d7cc3b1 2025-07-16 QuicVersion:52c2b40d 2025-04-03'
}
qUrl = f'https://editor-api-sg.capcutapi.com/lv/v1/common_task/query?app_name=CapCut&device_type=Windows&os_version=10.0.19045&channel=capcutpc_google&version_name=8.7.0&device_brand=Windows&device_id={deviceId}&iid={deviceId}&version_code=8.7.0&device_platform=windows&aid=359289'
qReq = urllib.request.Request(qUrl, data=qBody.encode('utf-8'), headers=qHeaders)
with urllib.request.urlopen(qReq) as qr:
    qRes = json.loads(qr.read().decode('utf-8'))
    task = qRes.get('data', {}).get('tasks', [{}])[0]
    status = task.get('status')
    print('Query status:', status)
    payload_str = task.get('payload')
    if payload_str:
        payload = json.loads(payload_str)
        print('Speech url:', payload['audio_subtitles'][0]['speech_url'][:70])
