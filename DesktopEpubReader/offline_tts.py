# -*- coding: utf-8 -*-
"""
Module Quản lý & Tổng hợp Giọng đọc Offline AI (Piper VITS / Sherpa-ONNX)
Dành cho DesktopEpubReader & HonorReader.
"""
import os
import io
import json
import tempfile
import urllib.request
import threading
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OFFLINE_TTS_DIR = BASE_DIR / "piper_offline_tts"
MODELS_DIR = OFFLINE_TTS_DIR / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

TOKENS_PATH = OFFLINE_TTS_DIR / "tokens.txt"
DATA_DIR = OFFLINE_TTS_DIR / "espeak-ng-data"

USER_AGENT = "Mozilla/5.0 (Linux; Android 14; Mobile)"

OFFLINE_VOICES = [
    {
        "id": "banmai",
        "name": "Ban Mai",
        "gender": "Nữ",
        "accent": "Bắc",
        "desc": "Giọng nữ miền Bắc trẻ trung, tự nhiên, truyền cảm",
        "fileName": "banmai.onnx",
        "onnxUrl": "https://cdn.ainovelreader.com/tts_model/banmai.onnx",
        "jsonUrl": "https://cdn.ainovelreader.com/tts_model/banmai.onnx.json",
        "demoUrl": "https://cdn.ainovelreader.com/demo_voice/demo_banmai.wav"
    },
    {
        "id": "ngochuyennew",
        "name": "Ngọc Huyền",
        "gender": "Nữ",
        "accent": "Bắc",
        "desc": "Giọng nữ truyền cảm, mượt mà, chuyên đọc truyện tình cảm",
        "fileName": "ngochuyennew.onnx",
        "onnxUrl": "https://cdn.ainovelreader.com/tts_model/ngochuyennew.onnx",
        "jsonUrl": "https://cdn.ainovelreader.com/tts_model/ngochuyennew.onnx.json",
        "demoUrl": "https://cdn.ainovelreader.com/demo_voice/demo_ngochuyennew.wav"
    },
    {
        "id": "deepman3909",
        "name": "Nam Trầm",
        "gender": "Nam",
        "accent": "Bắc",
        "desc": "Giọng nam trầm ấm, hào sảng, hợp truyện tiên hiệp, kiếm hiệp",
        "fileName": "deepman3909.onnx",
        "onnxUrl": "https://cdn.ainovelreader.com/tts_model/deepman3909.onnx",
        "jsonUrl": "https://cdn.ainovelreader.com/tts_model/deepman3909.onnx.json",
        "demoUrl": "https://cdn.ainovelreader.com/demo_voice/demo_deepman3909.wav"
    },
    {
        "id": "calmwoman3688",
        "name": "Nữ nhẹ nhàng",
        "gender": "Nữ",
        "accent": "Bắc",
        "desc": "Giọng nữ nhẹ nhàng, êm dịu, dễ ngủ",
        "fileName": "calmwoman3688.onnx",
        "onnxUrl": "https://cdn.ainovelreader.com/tts_model/calmwoman3688.onnx",
        "jsonUrl": "https://cdn.ainovelreader.com/tts_model/calmwoman3688.onnx.json",
        "demoUrl": "https://cdn.ainovelreader.com/demo_voice/demo_calmwoman3688.wav"
    },
    {
        "id": "manhdung",
        "name": "Mạnh Dũng",
        "gender": "Nam",
        "accent": "Bắc",
        "desc": "Giọng nam chững chạc, rõ ràng, dứt khoát",
        "fileName": "manhdung.onnx",
        "onnxUrl": "https://cdn.ainovelreader.com/tts_model/manhdung.onnx",
        "jsonUrl": "https://cdn.ainovelreader.com/tts_model/manhdung.onnx.json",
        "demoUrl": "https://cdn.ainovelreader.com/demo_voice/demo_manhdung.wav"
    },
    {
        "id": "maiphuong",
        "name": "Mai Phương",
        "gender": "Nữ",
        "accent": "Bắc",
        "desc": "Giọng nữ ấm áp, lưu loát",
        "fileName": "maiphuong.onnx",
        "onnxUrl": "https://cdn.ainovelreader.com/tts_model/maiphuong.onnx",
        "jsonUrl": "https://cdn.ainovelreader.com/tts_model/maiphuong.onnx.json",
        "demoUrl": "https://cdn.ainovelreader.com/demo_voice/demo_maiphuong.wav"
    },
    {
        "id": "minhkhang",
        "name": "Minh Khang",
        "gender": "Nam",
        "accent": "Bắc",
        "desc": "Giọng nam thanh niên hiện đại, tự nhiên",
        "fileName": "minhkhang.onnx",
        "onnxUrl": "https://cdn.ainovelreader.com/tts_model/minhkhang.onnx",
        "jsonUrl": "https://cdn.ainovelreader.com/tts_model/minhkhang.onnx.json",
        "demoUrl": "https://cdn.ainovelreader.com/demo_voice/demo_minhkhang.wav"
    },
    {
        "id": "minhquang",
        "name": "Minh Quang",
        "gender": "Nam",
        "accent": "Bắc",
        "desc": "Giọng nam đĩnh đạc, rõ từng từ",
        "fileName": "minhquang.onnx",
        "onnxUrl": "https://cdn.ainovelreader.com/tts_model/minhquang.onnx",
        "jsonUrl": "https://cdn.ainovelreader.com/tts_model/minhquang.onnx.json",
        "demoUrl": "https://cdn.ainovelreader.com/demo_voice/demo_minhquang.wav"
    },
    {
        "id": "phuongtrang",
        "name": "Phương Trang",
        "gender": "Nữ",
        "accent": "Bắc",
        "desc": "Giọng nữ trong trẻo, nhẹ nhàng",
        "fileName": "phuongtrang.onnx",
        "onnxUrl": "https://cdn.ainovelreader.com/tts_model/phuongtrang.onnx",
        "jsonUrl": "https://cdn.ainovelreader.com/tts_model/phuongtrang.onnx.json",
        "demoUrl": "https://cdn.ainovelreader.com/demo_voice/demo_phuongtrang.wav"
    },
    {
        "id": "duyoryx3175",
        "name": "Duy",
        "gender": "Nam",
        "accent": "Nam",
        "desc": "Giọng nam miền Nam gần gũi, biểu cảm",
        "fileName": "duyoryx3175.onnx",
        "onnxUrl": "https://cdn.ainovelreader.com/tts_model/duyoryx3175.onnx",
        "jsonUrl": "https://cdn.ainovelreader.com/tts_model/duyoryx3175.onnx.json",
        "demoUrl": "https://cdn.ainovelreader.com/demo_voice/demo_duyoryx3175.wav"
    },
    {
        "id": "chieuthanh",
        "name": "Chiếu Thành",
        "gender": "Nam",
        "accent": "Bắc",
        "desc": "Giọng nam truyền thống, kể chuyện đêm khuya",
        "fileName": "chieuthanh.onnx",
        "onnxUrl": "https://cdn.ainovelreader.com/tts_model/chieuthanh.onnx",
        "jsonUrl": "https://cdn.ainovelreader.com/tts_model/chieuthanh.onnx.json",
        "demoUrl": "https://cdn.ainovelreader.com/demo_voice/demo_chieuthanh.wav"
    },
    {
        "id": "ngocngan3701",
        "name": "Ngọc Ngân",
        "gender": "Nữ",
        "accent": "Nam",
        "desc": "Giọng nữ miền Nam thanh thoát, ngọt ngào",
        "fileName": "ngocngan3701.onnx",
        "onnxUrl": "https://cdn.ainovelreader.com/tts_model/ngocngan3701.onnx",
        "jsonUrl": "https://cdn.ainovelreader.com/tts_model/ngocngan3701.onnx.json",
        "demoUrl": "https://cdn.ainovelreader.com/demo_voice/demo_ngocngan3701.wav"
    },
    {
        "id": "thanhphuong2",
        "name": "Thanh Phương",
        "gender": "Nữ",
        "accent": "Bắc",
        "desc": "Giọng nữ đằm thắm, giàu cảm xúc",
        "fileName": "thanhphuong2.onnx",
        "onnxUrl": "https://cdn.ainovelreader.com/tts_model/thanhphuong2.onnx",
        "jsonUrl": "https://cdn.ainovelreader.com/tts_model/thanhphuong2.onnx.json",
        "demoUrl": "https://cdn.ainovelreader.com/demo_voice/demo_thanhphuong2.wav"
    },
    {
        "id": "vietthao3886",
        "name": "Việt Thao",
        "gender": "Nam",
        "accent": "Bắc",
        "desc": "Giọng nam trầm, lôi cuốn",
        "fileName": "vietthao3886.onnx",
        "onnxUrl": "https://cdn.ainovelreader.com/tts_model/vietthao3886.onnx",
        "jsonUrl": "https://cdn.ainovelreader.com/tts_model/vietthao3886.onnx.json",
        "demoUrl": "https://cdn.ainovelreader.com/demo_voice/demo_vietthao3886.wav"
    },
    {
        "id": "thientam",
        "name": "Thiện Tâm",
        "gender": "Nam",
        "accent": "Bắc",
        "desc": "Giọng nam ấm, thanh bình",
        "fileName": "thientam.onnx",
        "onnxUrl": "https://cdn.ainovelreader.com/tts_model/thientam.onnx",
        "jsonUrl": "https://cdn.ainovelreader.com/tts_model/thientam.onnx.json",
        "demoUrl": "https://cdn.ainovelreader.com/demo_voice/demo_thientam.wav"
    },
    {
        "id": "taian4",
        "name": "Tài An",
        "gender": "Nam",
        "accent": "Bắc",
        "desc": "Giọng nam khỏe khoắn, tươi vui",
        "fileName": "taian4.onnx",
        "onnxUrl": "https://cdn.ainovelreader.com/tts_model/taian4.onnx",
        "jsonUrl": "https://cdn.ainovelreader.com/tts_model/taian4.onnx.json",
        "demoUrl": "https://cdn.ainovelreader.com/demo_voice/demo_taian4.wav"
    },
    {
        "id": "lacphi",
        "name": "Lạc Phi",
        "gender": "Nam",
        "accent": "Bắc",
        "desc": "Giọng nam bí ẩn, hấp dẫn",
        "fileName": "lacphi.onnx",
        "onnxUrl": "https://cdn.ainovelreader.com/tts_model/lacphi.onnx",
        "jsonUrl": "https://cdn.ainovelreader.com/tts_model/lacphi.onnx.json",
        "demoUrl": "https://cdn.ainovelreader.com/demo_voice/demo_lacphi.wav"
    },
    {
        "id": "ngochuyen",
        "name": "Ngọc Chuyên",
        "gender": "Nữ",
        "accent": "Bắc",
        "desc": "Giọng nữ sâu lắng",
        "fileName": "ngochuyen.onnx",
        "onnxUrl": "https://cdn.ainovelreader.com/tts_model/ngochuyen.onnx",
        "jsonUrl": "https://cdn.ainovelreader.com/tts_model/ngochuyen.onnx.json",
        "demoUrl": "https://cdn.ainovelreader.com/demo_voice/demo_ngochuyen.wav"
    }
]

# Bộ đệm instance Sherpa-ONNX trong bộ nhớ (tránh tải lại model mỗi câu)
_loaded_engines = {}
_engine_lock = threading.Lock()

# Trạng thái tiến trình tải
_download_status = {}

def get_voice_info(voice_id):
    for v in OFFLINE_VOICES:
        if v["id"] == voice_id or f"offline_{v['id']}" == voice_id:
            return v
    return None

def is_voice_downloaded(voice_id):
    v = get_voice_info(voice_id)
    if not v:
        return False
    onnx_file = MODELS_DIR / v["fileName"]
    json_file = MODELS_DIR / f"{v['fileName']}.json"
    return onnx_file.exists() and onnx_file.stat().st_size > 10 * 1024 * 1024 and json_file.exists()

def get_all_voices_status():
    result = []
    for v in OFFLINE_VOICES:
        item = dict(v)
        item["full_id"] = f"offline_{v['id']}"
        item["is_downloaded"] = is_voice_downloaded(v["id"])
        item["download_status"] = _download_status.get(v["id"], "idle")
        if item["is_downloaded"]:
            onnx_file = MODELS_DIR / v["fileName"]
            item["file_size_mb"] = round(onnx_file.stat().st_size / (1024 * 1024), 1)
        else:
            item["file_size_mb"] = 63.5
        result.append(item)
    return result

def download_voice_thread(voice_id):
    v = get_voice_info(voice_id)
    if not v:
        _download_status[voice_id] = "error: Không tìm thấy giọng"
        return

    _download_status[voice_id] = "downloading"
    try:
        onnx_file = MODELS_DIR / v["fileName"]
        json_file = MODELS_DIR / f"{v['fileName']}.json"
        headers = {"User-Agent": USER_AGENT}

        # 1. Tải file JSON cấu hình
        req_json = urllib.request.Request(v["jsonUrl"], headers=headers)
        with urllib.request.urlopen(req_json, timeout=15) as resp:
            with open(json_file, "wb") as f:
                f.write(resp.read())

        # 2. Tải file ONNX trọng số mô hình
        req_onnx = urllib.request.Request(v["onnxUrl"], headers=headers)
        tmp_onnx = MODELS_DIR / f"{v['fileName']}.tmp"
        with urllib.request.urlopen(req_onnx, timeout=60) as resp:
            total_size = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            with open(tmp_onnx, "wb") as f:
                while True:
                    chunk = resp.read(1024 * 512)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        pct = int((downloaded / total_size) * 100)
                        _download_status[voice_id] = f"downloading_{pct}%"

        if tmp_onnx.exists():
            if onnx_file.exists():
                onnx_file.unlink()
            tmp_onnx.rename(onnx_file)

        _download_status[voice_id] = "completed"
        print(f"[OfflineTTS] Tải thành công giọng {v['name']} ({voice_id})!")
    except Exception as e:
        _download_status[voice_id] = f"error: {str(e)}"
        print(f"[OfflineTTS Error] Lỗi tải giọng {voice_id}: {e}")

def start_download_voice(voice_id):
    if _download_status.get(voice_id) == "downloading" or str(_download_status.get(voice_id, "")).startswith("downloading_"):
        return {"status": "already_downloading"}
    
    t = threading.Thread(target=download_voice_thread, args=(voice_id,), daemon=True)
    t.start()
    return {"status": "started"}

def delete_voice(voice_id):
    v = get_voice_info(voice_id)
    if not v:
        return False
    with _engine_lock:
        if voice_id in _loaded_engines:
            del _loaded_engines[voice_id]
        if f"offline_{voice_id}" in _loaded_engines:
            del _loaded_engines[f"offline_{voice_id}"]

    onnx_file = MODELS_DIR / v["fileName"]
    json_file = MODELS_DIR / f"{v['fileName']}.json"
    if onnx_file.exists():
        onnx_file.unlink()
    if json_file.exists():
        json_file.unlink()
    _download_status[voice_id] = "idle"
    return True

def get_demo_audio_bytes(voice_id):
    v = get_voice_info(voice_id)
    if not v:
        return None
    req = urllib.request.Request(v["demoUrl"], headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.read()

def get_sherpa_engine(voice_id):
    clean_id = voice_id.replace("offline_", "")
    v = get_voice_info(clean_id)
    if not v or not is_voice_downloaded(clean_id):
        return None

    with _engine_lock:
        if clean_id in _loaded_engines:
            return _loaded_engines[clean_id]

        import sherpa_onnx
        onnx_file = str(MODELS_DIR / v["fileName"])
        tokens_file = str(TOKENS_PATH)
        data_dir = str(DATA_DIR)

        tts_config = sherpa_onnx.OfflineTtsConfig(
            model=sherpa_onnx.OfflineTtsModelConfig(
                vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                    model=onnx_file,
                    tokens=tokens_file,
                    data_dir=data_dir,
                    noise_scale=0.78,    # Phương án 1: Tăng biến thiên cao độ biểu cảm tự nhiên
                    noise_scale_w=0.85,  # Phương án 1: Tăng biến thiên nhịp thở & trường độ âm tiết
                    length_scale=1.0
                ),
                num_threads=2,
                debug=False
            )
        )
        engine = sherpa_onnx.OfflineTts(tts_config)
        _loaded_engines[clean_id] = engine
        return engine

def find_best_downloaded_voice(gender_preference, exclude_id=None):
    """Tìm giọng offline đã tải về máy phù hợp nhất theo giới tính (Nam/Nữ)"""
    for v in OFFLINE_VOICES:
        if v["id"] == exclude_id:
            continue
        if v.get("gender", "") == gender_preference and is_voice_downloaded(v["id"]):
            return v["id"]
    return None

def generate_sfx_samples(sfx_type, sample_rate=22050):
    """
    Sinh tín hiệu âm thanh hiệu ứng thực tế (Foley SFX Synthesis) bằng thuật toán DSP:
    - impact: Va chạm quyền cước, nện đòn trầm đục (phanh, bịch, bộp, rầm, rắc)
    - explosion: Tiếng sấm sét, vụ nổ rền (ầm, bùm, đùng, đoàng, oành, nổ)
    - clash: Va chạm binh khí kim loại tóe lửa (keng, choang, xoảng, leng keng)
    - whoosh: Kiếm khí, phi kiếm, ám khí xé rách không gian (vút, vèo, xẹt, chéo)
    """
    import math, random
    samples = []
    if sfx_type == 'impact':
        dur = 0.35
        n_samples = int(sample_rate * dur)
        for i in range(n_samples):
            t = i / sample_rate
            freq = 110.0 * math.exp(-t * 9.0) + 40.0
            phase = 2.0 * math.pi * freq * t
            sub = math.sin(phase) * math.exp(-t * 10.0)
            noise = random.uniform(-1.0, 1.0) * math.exp(-t * 30.0)
            val = (sub * 0.75 + noise * 0.25) * 0.95
            samples.append(val)
    elif sfx_type == 'explosion':
        dur = 0.75
        n_samples = int(sample_rate * dur)
        for i in range(n_samples):
            t = i / sample_rate
            freq = 85.0 * math.exp(-t * 4.0) + 30.0
            phase = 2.0 * math.pi * freq * t
            sub = math.sin(phase) * math.exp(-t * 4.0)
            noise = random.uniform(-1.0, 1.0) * math.exp(-t * 5.0)
            val = (sub * 0.6 + noise * 0.4) * 0.95
            samples.append(val)
    elif sfx_type == 'clash':
        dur = 0.55
        n_samples = int(sample_rate * dur)
        for i in range(n_samples):
            t = i / sample_rate
            bell1 = math.sin(2.0 * math.pi * 2350.0 * t) * math.exp(-t * 6.5)
            bell2 = math.sin(2.0 * math.pi * 3180.0 * t) * math.exp(-t * 8.5)
            bell3 = math.sin(2.0 * math.pi * 4820.0 * t) * math.exp(-t * 13.0)
            click = random.uniform(-1.0, 1.0) * math.exp(-t * 65.0)
            val = (bell1 * 0.4 + bell2 * 0.3 + bell3 * 0.2 + click * 0.2) * 0.9
            samples.append(val)
    elif sfx_type == 'whoosh':
        dur = 0.32
        n_samples = int(sample_rate * dur)
        for i in range(n_samples):
            t = i / sample_rate
            env = (math.sin(math.pi * t / dur)) ** 2
            noise = random.uniform(-1.0, 1.0)
            carrier = math.sin(2.0 * math.pi * (700.0 + 1300.0 * math.sin(math.pi * t / dur)) * t)
            val = (noise * 0.45 + carrier * 0.55) * env * 0.85
            samples.append(val)
    return samples

def generate_sfx_wav_bytes(sfx_type, sample_rate=22050):
    """
    Sinh file WAV âm thanh hiệu ứng (SFX) 16-bit PCM mono chuẩn.
    """
    samples = generate_sfx_samples(sfx_type, sample_rate)
    if not samples:
        return None
    import io, wave, struct
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        raw = bytearray()
        for s in samples:
            val = max(-32767, min(32767, int(s * 32767)))
            raw.extend(struct.pack('<h', val))
        wf.writeframes(raw)
    return buf.getvalue()

def detect_and_prune_sfx(text):
    """
    Phát hiện từ tượng thanh độc lập và cắt bỏ (Prune) khỏi văn bản đọc để TTS không đọc thô:
    - 1. Nổ / Sấm: oanh long, oanh long long, ầm, ầm ầm, bùm, đùng, đoàng, oành, oanh, nổ tung
    - 2. Va chạm / Quyền cước: rầm, bịch, huỵch, bộp, bốp, chát, rắc, bành
    - 3. Binh khí: keng, choang, xoảng, leng keng, xủng xoảng, boong, coong
    - 4. Kiếm khí / Xé gió: vun vút, vút, vèo, xẹt, xoẹt, chéo, vù, phù
    Hỗ trợ kèm cụm 'một tiếng' (ví dụ: 'oanh long một tiếng', 'keng một tiếng', 'rầm một tiếng')
    """
    import re
    # 1. Nổ / Sấm sét: oanh long (long), oành, ầm ầm, bùm, đùng đoàng, nổ tung
    m = re.search(r'(?i)(?:^|[\s“"«\'–—])(oanh\s+long(?:\s+long)?|oành(?:\s+oành)?|oanh|ầm(?:\s+ầm){1,2}|ầm\s+vang|ầm|đùng\s+đoàng|đùng(?:\s+đùng)?|đoàng|bùm(?:\s+bùm)?|nổ\s+tung)(?:\s+một\s+tiếng)?(?=[!?.…,”"»\'–—\s]|$)', text)
    if m:
        pruned = re.sub(r'(?i)(?:^|[\s“"«\'–—])(?:oanh\s+long(?:\s+long)?|oành(?:\s+oành)?|oanh|ầm(?:\s+ầm){1,2}|ầm\s+vang|ầm|đùng\s+đoàng|đùng(?:\s+đùng)?|đoàng|bùm(?:\s+bùm)?|nổ\s+tung)(?:\s+một\s+tiếng)?[!?.…,”"»\'–—\s]*', ' ', text).strip()
        return 'explosion', pruned
    # 2. Va chạm / Quyền cước: rầm, bịch, huỵch, bộp, bốp, chát, rắc, bành
    m = re.search(r'(?i)(?:^|[\s“"«\'–—])(rầm(?:\s+rầm)?|bịch(?:\s+bịch)?|huỵch|bộp(?:\s+bộp)?|bốp(?:\s+bốp)?|chát|rắc(?:\s+rắc)?|bành)(?:\s+một\s+tiếng)?(?=[!?.…,”"»\'–—\s]|$)', text)
    if m:
        pruned = re.sub(r'(?i)(?:^|[\s“"«\'–—])(?:rầm(?:\s+rầm)?|bịch(?:\s+bịch)?|huỵch|bộp(?:\s+bộp)?|bốp(?:\s+bốp)?|chát|rắc(?:\s+rắc)?|bành)(?:\s+một\s+tiếng)?[!?.…,”"»\'–—\s]*', ' ', text).strip()
        return 'impact', pruned
    # 3. Binh khí: leng keng, keng, choang, xoảng, xủng xoảng, boong, coong
    m = re.search(r'(?i)(?:^|[\s“"«\'–—])(leng\s+keng|keng(?:\s+keng)?|choang(?:\s+choang)?|xoảng(?:\s+xoảng)?|xủng\s+xoảng|boong|coong)(?:\s+một\s+tiếng)?(?=[!?.…,”"»\'–—\s]|$)', text)
    if m:
        pruned = re.sub(r'(?i)(?:^|[\s“"«\'–—])(?:leng\s+keng|keng(?:\s+keng)?|choang(?:\s+choang)?|xoảng(?:\s+xoảng)?|xủng\s+xoảng|boong|coong)(?:\s+một\s+tiếng)?[!?.…,”"»\'–—\s]*', ' ', text).strip()
        return 'clash', pruned
    # 4. Kiếm khí / Xé gió: vun vút, vút, vèo, xẹt, xoẹt, chéo, vù, phù
    m = re.search(r'(?i)(?:^|[\s“"«\'–—])(vun\s+vút|vút(?:\s+vút)?|vèo(?:\s+vèo)?|xẹt(?:\s+xẹt)?|xoẹt(?:\s+xoẹt)?|chéo|vù(?:\s+vù)?|phù)(?:\s+một\s+tiếng)?(?=[!?.…,”"»\'–—\s]|$)', text)
    if m:
        pruned = re.sub(r'(?i)(?:^|[\s“"«\'–—])(?:vun\s+vút|vút(?:\s+vút)?|vèo(?:\s+vèo)?|xẹt(?:\s+xẹt)?|xoẹt(?:\s+xoẹt)?|chéo|vù(?:\s+vù)?|phù)(?:\s+một\s+tiếng)?[!?.…,”"»\'–—\s]*', ' ', text).strip()
        return 'whoosh', pruned
    return None, text

def parse_contextual_story_segments(text):
    """
    Động cơ Kịch truyền thanh AI & Tiên Hiệp (Xianxia Audio Drama Engine):
    - Áp dụng Dialogue Masking giữ nguyên trọn vẹn câu thoại qua các dấu chấm
    - Phân vai Nam - Nữ đa chiều: Đại từ tự xưng trong thoại (Tầng 1) + Dẫn nhập ngoài thoại + Turn-taking
    - Tách và chuyển hóa từ tượng thanh thành SFX thật (Prune & Replace)
    """
    import re
    # Hỗ trợ toàn bộ ký tự thoại: “...”, "...", «...», 「...」, 『...』
    pattern = r'([“"«「『][^”"»」』]+[”"»」』])'
    raw_parts = re.split(pattern, text)
    
    # Nếu không có ngoặc kép nhưng bắt đầu bằng gạch đầu dòng (- / – / —)
    if len(raw_parts) <= 1 and re.match(r'^[\s]*[-–—]', text):
        m_dash = re.search(r'^[\s]*[-–—]\s*(.+?)(?=\s*[-–—]|\s*$)', text)
        if m_dash:
            d_text = m_dash.group(1).strip()
            rest = text[m_dash.end():].strip()
            raw_parts = [f'“{d_text}”']
            if rest:
                raw_parts.append(rest)

    segments = []
    female_titles = r'\b(nàng|nàng ấy|cô ấy|cô|tiểu thư|sư muội|tỷ tỷ|mẫu thân|mẹ|nữ tử|công chúa|nương tử|thiếu nữ|phu nhân|muội muội|tiên tử|thánh nữ|nha hoàn|bà lão|mỹ phụ|nữ nhi|sư tôn|sư nương|Ngọc|Mai|Hương|Lan|Linh|Trang|Nhi)\b'
    male_titles = r'\b(chàng|hắn|hắn ta|công tử|sư huynh|huynh đệ|phụ thân|cha|nam tử|huynh trưởng|thiếu niên|đại ca|lão giả|đạo nhân|lão tổ|môn chủ|chưởng môn|tông chủ|tiểu tử|gã|y|trượng phu|nam nhân|hoàng thượng|vương gia|Lý Phong|Phong|Minh|Quang|Dũng|Huy)\b'
    verbs = r'\b(nói|đáp|hỏi|than|cười|thầm|bảo|nghẹn ngào|thì thào|thỏ thẻ|quát|thét|gầm|rống|la|cười lạnh|hừ lạnh|trầm giọng|lẩm bẩm|thốt lên|hô|nhủ|nghĩ|truyền âm|tiếp lời|khẽ nói)\b'
    
    for i, p in enumerate(raw_parts):
        p_clean = p.strip()
        if not p_clean:
            continue
        is_dialogue = bool(re.match(r'^[“"«「『].+[”"»」』]$', p_clean))
        clean_text = re.sub(r'^[“"«「『]\s*|\s*[”"»」』]$', '', p_clean).strip()
        if not clean_text:
            continue
            
        # Kiểm tra từ tượng thanh độc lập
        sfx_type, pruned_text = detect_and_prune_sfx(clean_text)
        if sfx_type and pruned_text:
            clean_text = pruned_text
            
        prev_ctx = raw_parts[i-1] if i > 0 else ""
        next_ctx = raw_parts[i+1] if i + 1 < len(raw_parts) else ""
        
        gender = "neutral"
        if is_dialogue:
            f_score = 0
            m_score = 0
            
            # 1. Phân giải đại từ tự xưng nội bộ (Xianxia Pronoun Lexicon - Trọng số cao nhất +4)
            first_words = ' '.join(clean_text.split()[:8])
            if re.search(r'\b(tiểu nữ|thiếp|nô gia|bản cung|tiểu muội|bần ni|lão thân|muội muội|muội|nhi thần)\b', first_words, re.I):
                f_score += 4
            if re.search(r'\b(chàng|huynh|sư huynh|công tử|đại ca|phu quân|tướng công|phụ thân|lão gia|vương gia|hoàng thượng)\b', first_words, re.I):
                f_score += 3
                
            if re.search(r'\b(tại hạ|lão phu|bản tọa|bần đạo|lão nạp|bản công tử|tiểu sinh|mỗ|vi sư|mạt tướng|huynh đệ|bản vương|trẫm|bản tôn)\b', first_words, re.I):
                m_score += 4
            if re.search(r'\b(nàng|nương tử|tiểu thư|cô nương|tiểu nha đầu|mẫu thân|sư muội|nương|ái phi|tiên tử|thánh nữ)\b', first_words, re.I):
                m_score += 3

            # 2. Ngữ cảnh bên ngoài (Dẫn nhập lead_in & Thoát thoại lead_out)
            lead_in = prev_ctx[-90:] if prev_ctx else ""
            lead_out = next_ctx[:90] if next_ctx else ""
            
            if re.search(female_titles, lead_in, re.I):
                f_score += 2
                if re.search(verbs, lead_in, re.I):
                    f_score += 1
            if re.search(female_titles + r'\s+' + verbs, lead_out, re.I):
                f_score += 3
                
            if re.search(male_titles, lead_in, re.I):
                m_score += 2
                if re.search(verbs, lead_in, re.I):
                    m_score += 1
            if re.search(male_titles + r'\s+' + verbs, lead_out, re.I):
                m_score += 3

            if f_score > m_score:
                gender = "female"
            elif m_score > f_score:
                gender = "male"
            else:
                gender = "neutral"

        # Sắc thái câu & nhịp điệu cảm xúc
        emotion = "normal"
        if clean_text.endswith("!") or "!" in clean_text:
            emotion = "excited"
        elif clean_text.endswith("?") or "?" in clean_text:
            emotion = "question"
        elif clean_text.endswith("…") or clean_text.endswith("..."):
            emotion = "trailing"
            
        segments.append({
            "text": clean_text,
            "raw": p_clean,
            "is_dialogue": is_dialogue,
            "gender": gender,
            "emotion": emotion,
            "sfx": sfx_type
        })
    return segments

def synthesize_offline(text, voice_id, speed=1.0, multi_voice=True):
    """
    Tổng hợp âm thanh giọng đọc Offline AI kết hợp:
    1. Emotion Scales VITS: noise_scale 0.78, noise_scale_w 0.85
    2. Contextual Prosody Engine: Ngắt nghỉ tự nhiên & điều biến tốc độ
    3. Multi-Voice Drama: Tự động phân vai Nam - Nữ theo ngữ cảnh Tiên Hiệp
    4. Foley Audio Drama: Chèn âm thanh thực tế (Nổ, Quyền cước, Binh khí, Kiếm khí)
    """
    clean_id = voice_id.replace("offline_", "")
    default_info = get_voice_info(clean_id) or {}
    default_gender = default_info.get("gender", "Nam")
    
    # Phân tích các phân đoạn câu chuyện
    segments = parse_contextual_story_segments(text)
    if not segments:
        return None

    # Tìm sẵn giọng đối ứng nếu cần phân vai Nam - Nữ (Phương án 3)
    female_voice_id = find_best_downloaded_voice("Nữ") if multi_voice else None
    male_voice_id = find_best_downloaded_voice("Nam") if multi_voice else None

    import sherpa_onnx
    safe_speed = max(0.5, min(2.0, float(speed)))
    all_samples = []
    final_sample_rate = 22050

    for idx, seg in enumerate(segments):
        # 4. Chèn hiệu ứng âm thanh thực tế (SFX) nếu có
        if seg.get("sfx"):
            sfx_samples = generate_sfx_samples(seg["sfx"], final_sample_rate)
            if sfx_samples:
                all_samples.extend(sfx_samples)
                all_samples.extend([0.0] * int(final_sample_rate * 0.08))

        seg_text = seg["text"].strip()
        if not seg_text:
            continue
            
        # Xác định giọng đọc cho phân đoạn này (Phương án 3: Kịch truyền thanh)
        chosen_voice_id = clean_id
        if multi_voice and seg["is_dialogue"]:
            if seg["gender"] == "female" and default_gender == "Nam" and female_voice_id:
                chosen_voice_id = female_voice_id
            elif seg["gender"] == "male" and default_gender == "Nữ" and male_voice_id:
                chosen_voice_id = male_voice_id
                
        engine = get_sherpa_engine(chosen_voice_id) or get_sherpa_engine(clean_id)
        if not engine:
            engine = get_sherpa_engine(clean_id)
            if not engine:
                raise ValueError(f"Giọng offline '{voice_id}' chưa được tải về máy!")

        # Phương án 2: Tinh chỉnh nhịp điệu theo ngữ cảnh & cảm xúc
        seg_speed = safe_speed
        if seg["is_dialogue"]:
            if seg["emotion"] == "excited":
                seg_speed = min(2.0, safe_speed * 1.06)
            elif seg["emotion"] == "trailing":
                seg_speed = max(0.5, safe_speed * 0.94)
            elif seg["emotion"] == "question":
                seg_speed = safe_speed * 1.02
        else:
            seg_speed = safe_speed * 0.98

        part_audio = engine.generate(seg_text, sid=0, speed=seg_speed)
        if part_audio and len(part_audio.samples) > 0:
            final_sample_rate = part_audio.sample_rate
            all_samples.extend(part_audio.samples)
            
            # Khoảng nghỉ ngữ cảnh tự nhiên (Contextual Pause)
            if idx < len(segments) - 1:
                next_seg = segments[idx + 1]
                if seg["is_dialogue"] != next_seg["is_dialogue"]:
                    pause_ms = 0.12
                elif seg["emotion"] == "trailing":
                    pause_ms = 0.25
                else:
                    pause_ms = 0.08
                all_samples.extend([0.0] * int(final_sample_rate * pause_ms))

    if not all_samples:
        return None

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_name = tmp.name
    try:
        sherpa_onnx.write_wave(tmp_name, all_samples, final_sample_rate)
        with open(tmp_name, "rb") as f:
            data = f.read()
        return data
    finally:
        if os.path.exists(tmp_name):
            try:
                os.remove(tmp_name)
            except Exception:
                pass


