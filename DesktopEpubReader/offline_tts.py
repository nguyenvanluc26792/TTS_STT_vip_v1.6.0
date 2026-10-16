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
                    data_dir=data_dir
                ),
                num_threads=2,
                debug=False
            )
        )
        engine = sherpa_onnx.OfflineTts(tts_config)
        _loaded_engines[clean_id] = engine
        return engine

def synthesize_offline(text, voice_id, speed=1.0):
    clean_id = voice_id.replace("offline_", "")
    engine = get_sherpa_engine(clean_id)
    if not engine:
        raise ValueError(f"Giọng offline '{voice_id}' chưa được tải về máy hoặc không tồn tại!")

    import sherpa_onnx
    # Tốc độ đọc: speed 1.0
    safe_speed = max(0.5, min(2.0, float(speed)))
    audio = engine.generate(text, sid=0, speed=safe_speed)
    if not audio or len(audio.samples) == 0:
        return None

    # Ghi ra file WAV tạm thời rồi đọc byte dữ liệu
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_name = tmp.name

    try:
        sherpa_onnx.write_wave(tmp_name, audio.samples, audio.sample_rate)
        with open(tmp_name, "rb") as f:
            data = f.read()
        return data
    finally:
        if os.path.exists(tmp_name):
            try:
                os.remove(tmp_name)
            except Exception:
                pass
