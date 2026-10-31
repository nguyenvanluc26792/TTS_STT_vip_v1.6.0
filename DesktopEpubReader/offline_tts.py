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

try:
    from vietnamese_prosody_engine import VietnameseProsodyPlanner, VietnameseProsodyDSP, VietnamesePhonologyHelper
    _prosody_planner = VietnameseProsodyPlanner()
except Exception as _e:
    print(f"[OfflineTTS] Prosody Engine load warning: {_e}")
    _prosody_planner = None

_prosody_dsp_cache = {}
def get_prosody_dsp(sample_rate: int = 22050):
    if sample_rate not in _prosody_dsp_cache:
        try:
            from vietnamese_prosody_engine import VietnameseProsodyDSP
            _prosody_dsp_cache[sample_rate] = VietnameseProsodyDSP(sample_rate=sample_rate)
        except Exception:
            return None
    return _prosody_dsp_cache[sample_rate]

# Danh mục Subvoices trong Mô hình Đa Giọng Gốc VieNeu TTS
VIENEU_SUBVOICES = [
    {
        "sid": 0,
        "base_sid": 0,
        "id": "narrator_female",
        "name": "Ngọc Lan (Dẫn truyện - Nữ Bắc thanh tao)",
        "gender": "Nữ",
        "age": "Trưởng thành",
        "region": "Bắc",
        "desc": "Giọng nữ dẫn truyện điềm đạm, ấm áp, chuẩn phát thanh miền Bắc",
        "base_voice": "Ngọc Lan",
        "pitch_shift": 0.0,
        "speed_factor": 1.0,
        "demo_file": "csa_0.wav"
    },
    {
        "sid": 1,
        "base_sid": 1,
        "id": "minh_anh",
        "name": "Minh Anh (Nữ chính - Nữ Bắc trẻ trung)",
        "gender": "Nữ",
        "age": "Trưởng thành",
        "region": "Bắc",
        "desc": "Giọng nữ Bắc trong trẻo, tự nhiên, biểu cảm linh hoạt",
        "base_voice": "Minh Anh",
        "pitch_shift": 0.0,
        "speed_factor": 1.0,
        "demo_file": "csa_1.wav"
    },
    {
        "sid": 2,
        "base_sid": 2,
        "id": "quang_huy",
        "name": "Quang Huy (Nam chính - Nam Bắc hào sảng)",
        "gender": "Nam",
        "age": "Trưởng thành",
        "region": "Bắc",
        "desc": "Giọng nam hào sảng, mạnh mẽ, cực chuẩn vai nam chính và anh hùng",
        "base_voice": "Quang Huy",
        "pitch_shift": 0.0,
        "speed_factor": 1.0,
        "demo_file": "csa_2.wav"
    },
    {
        "sid": 3,
        "base_sid": 3,
        "id": "thu_ha",
        "name": "Thu Hà (Nữ Bắc dịu dàng, truyền cảm)",
        "gender": "Nữ",
        "age": "Trưởng thành",
        "region": "Bắc",
        "desc": "Giọng nữ nhẹ nhàng, êm dịu, hợp tự sự và lãng mạn",
        "base_voice": "Thu Hà",
        "pitch_shift": 0.0,
        "speed_factor": 1.0,
        "demo_file": "csa_3.wav"
    },
    {
        "sid": 4,
        "base_sid": 4,
        "id": "yen_nhi",
        "name": "Yến Nhi (Nữ chính - Nữ Nam Bộ dịu dàng)",
        "gender": "Nữ",
        "age": "Trưởng thành",
        "region": "Nam",
        "desc": "Giọng nữ Nam Bộ ngọt ngào, truyền cảm, tự nhiên",
        "base_voice": "Yến Nhi",
        "pitch_shift": 0.0,
        "speed_factor": 1.0,
        "demo_file": "csa_4.wav"
    },
    {
        "sid": 5,
        "base_sid": 2,
        "id": "hai_dang",
        "name": "Hải Đăng (Nam trẻ - Nam Bắc nhẹ nhàng)",
        "gender": "Nam",
        "age": "Trưởng thành",
        "region": "Bắc",
        "desc": "Giọng nam trẻ trung, nhẹ nhàng, truyền cảm",
        "base_voice": "Quang Huy",
        "pitch_shift": 1.2,
        "speed_factor": 1.0,
        "demo_file": "csa_2.wav"
    },
    {
        "sid": 6,
        "base_sid": 2,
        "id": "thai_son",
        "name": "Thái Sơn (Nam trầm ấm - Uy nghiêm)",
        "gender": "Nam",
        "age": "Trưởng thành",
        "region": "Bắc",
        "desc": "Giọng nam trầm ấm, điềm đạm, uy nghiêm",
        "base_voice": "Quang Huy",
        "pitch_shift": -1.5,
        "speed_factor": 1.0,
        "demo_file": "csa_2.wav"
    },
    {
        "sid": 7,
        "base_sid": 2,
        "id": "adam_bua",
        "name": "Adam (Nam Bắc vui vẻ, hài hước)",
        "gender": "Nam",
        "age": "Trưởng thành",
        "region": "Bắc",
        "desc": "Giọng nam hóm hỉnh, sống động, phong cách tự nhiên",
        "base_voice": "Quang Huy",
        "pitch_shift": 0.6,
        "speed_factor": 1.0,
        "demo_file": "csa_2.wav"
    },
    {
        "sid": 8,
        "base_sid": 2,
        "id": "ong_lao",
        "name": "Ông lão (Người già Nam - Trầm khàn)",
        "gender": "Nam",
        "age": "Người già",
        "region": "Bắc",
        "desc": "Giọng ông lão từng trải, chậm rãi, trầm khàn (DSP Pitch & Formant)",
        "base_voice": "Quang Huy",
        "pitch_shift": -3.8,
        "speed_factor": 0.82,
        "demo_file": "csa_ong_lao.wav"
    },
    {
        "sid": 9,
        "base_sid": 4,
        "id": "ba_lao",
        "name": "Bà lão (Người già Nữ - Ấm áp, từ tốn)",
        "gender": "Nữ",
        "age": "Người già",
        "region": "Nam",
        "desc": "Giọng bà lão hiền từ, phúc hậu, từ tốn (DSP Pitch & Formant)",
        "base_voice": "Yến Nhi",
        "pitch_shift": -2.8,
        "speed_factor": 0.90,
        "demo_file": "csa_ba_lao.wav"
    },
    {
        "sid": 10,
        "base_sid": 1,
        "id": "be_trai",
        "name": "Bé trai (Trẻ con Nam - Líu lo, lanh lợi)",
        "gender": "Nam",
        "age": "Trẻ em",
        "region": "Bắc",
        "desc": "Giọng bé trai ngây thơ, tinh nghịch, líu lo (DSP Pitch & Formant)",
        "base_voice": "Minh Anh",
        "pitch_shift": 4.5,
        "speed_factor": 1.0,
        "demo_file": "csa_be_trai.wav"
    },
    {
        "sid": 11,
        "base_sid": 1,
        "id": "be_gai",
        "name": "Bé gái (Trẻ con Nữ - Trong trẻo, ngây thơ)",
        "gender": "Nữ",
        "age": "Trẻ em",
        "region": "Bắc",
        "desc": "Giọng bé gái trong veo, dễ thương, hồn nhiên (DSP Pitch & Formant)",
        "base_voice": "Minh Anh",
        "pitch_shift": 5.0,
        "speed_factor": 1.0,
        "demo_file": "csa_be_gai.wav"
    },
    {
        "sid": 12,
        "base_sid": 1,
        "id": "bich_giao",
        "name": "Bích Giao (Nữ trẻ lanh lợi, trong trẻo - Clone)",
        "gender": "Nữ",
        "age": "Trẻ tuổi",
        "region": "Bắc",
        "desc": "Giọng Bích Giao âm sắc trong sáng, lanh lợi, tự nhiên và ngọt ngào",
        "base_voice": "Minh Anh",
        "pitch_shift": 1.2,
        "speed_factor": 1.0,
        "demo_file": "csa_12.wav"
    },
    {
        "sid": 13,
        "base_sid": 0,
        "id": "kim_tuyen",
        "name": "Kim Tuyến (Nữ đọc truyện truyền cảm, ấm áp - Clone)",
        "gender": "Nữ",
        "age": "Trưởng thành",
        "region": "Bắc",
        "desc": "Giọng Kim Tuyến chất đọc truyện chuyên nghiệp, ấm áp, sâu lắng và điềm đạm",
        "base_voice": "Ngọc Lan",
        "pitch_shift": -0.8,
        "speed_factor": 0.96,
        "demo_file": "csa_13.wav"
    },
    {
        "sid": 14,
        "base_sid": 5,
        "id": "kim_cuc",
        "name": "NSƯT Kim Cúc (Đọc Truyện Đêm Khuya VOV - Master Prosody)",
        "gender": "Nữ",
        "age": "Trưởng thành",
        "region": "Bắc",
        "desc": "Giọng đọc kinh điển Đài Tiếng nói Việt Nam (Speaker Độc Lập), diễn cảm sâu lắng, nhịp ngắt tâm tình bậc thầy",
        "base_voice": "NSƯT Kim Cúc",
        "pitch_shift": 0.0,
        "speed_factor": 0.94,
        "demo_file": "csa_14.wav"
    }
]

# Chỉ giữ duy nhất Mô hình Đa Giọng Gốc VieNeu

KOKORO_SUBVOICES = [
    {
        "sid": 14,
        "base_sid": 13,
        "id": "kim_cuc",
        "name": "NSƯT Kim Cúc (Đọc Truyện Đêm Khuya VOV)",
        "gender": "Nữ",
        "age": "Trưởng thành",
        "region": "Bắc",
        "desc": "Giọng đọc vàng huyền thoại, trầm ấm, truyền cảm, ngân nga diễn cảm đỉnh cao",
        "demo_file": "turn_0_sid13.wav"
    },
    {
        "sid": 1,
        "base_sid": 0,
        "id": "diem_trinh",
        "name": "Diễm Trinh (Nữ miền Nam)",
        "gender": "Nữ",
        "age": "Trưởng thành",
        "region": "Nam",
        "desc": "Giọng nữ miền Nam dịu dàng, trong trẻo, tự nhiên",
        "demo_file": "turn_1_sid0.wav"
    },
    {
        "sid": 2,
        "base_sid": 4,
        "id": "manh_dung",
        "name": "Mạnh Dũng (Nam miền Bắc)",
        "gender": "Nam",
        "age": "Trưởng thành",
        "region": "Bắc",
        "desc": "Giọng nam miền Bắc dõng dạc, khí chất, đĩnh đạc",
        "demo_file": "turn_2_sid4.wav"
    },
    {
        "sid": 3,
        "base_sid": 6,
        "id": "ngoc_huyen",
        "name": "Ngọc Huyền (Nữ trẻ miền Bắc)",
        "gender": "Nữ",
        "age": "Thanh niên",
        "region": "Bắc",
        "desc": "Giọng nữ Bắc thanh tú, nhẹ nhàng, biểu cảm",
        "demo_file": "turn_3_sid13.wav"
    },
    {
        "sid": 4,
        "base_sid": 1,
        "id": "hung_thinh",
        "name": "Hưng Thịnh (Nam miền Nam)",
        "gender": "Nam",
        "age": "Trưởng thành",
        "region": "Nam",
        "desc": "Giọng nam miền Nam ấm áp, hào sảng, chân thành",
        "demo_file": "csa_2.wav"
    },
    {
        "sid": 13,
        "base_sid": 3,
        "id": "mai_loan",
        "name": "Mai Loan (Nữ miền Bắc)",
        "gender": "Nữ",
        "age": "Trưởng thành",
        "region": "Bắc",
        "desc": "Giọng nữ truyền cảm, ấm áp, sâu lắng",
        "demo_file": "csa_3.wav"
    },
    {
        "sid": 5,
        "base_sid": 8,
        "id": "thanh_dat",
        "name": "Thành Đạt (Nam trẻ năng động)",
        "gender": "Nam",
        "age": "Thanh niên",
        "region": "Bắc",
        "desc": "Giọng nam trẻ năng động, tự tin",
        "demo_file": "hai_dang.wav"
    },
    {
        "sid": 6,
        "base_sid": 10,
        "id": "tuan_ngoc",
        "name": "Tuấn Ngọc (Nam trầm ấm)",
        "gender": "Nam",
        "age": "Trưởng thành",
        "region": "Bắc",
        "desc": "Giọng nam điềm đạm, ấm áp, từng trải",
        "demo_file": "thai_son.wav"
    },
    {
        "sid": 7,
        "base_sid": 7,
        "id": "phat_tai",
        "name": "Phát Tài (Nam Nam Bộ)",
        "gender": "Nam",
        "age": "Trưởng thành",
        "region": "Nam",
        "desc": "Giọng nam vui tươi, thân thiện, phóng khoáng",
        "demo_file": "adam_bua.wav"
    },
    {
        "sid": 8,
        "base_sid": 4,
        "id": "ong_lao",
        "name": "Ông lão (Trầm khàn, chậm rãi)",
        "gender": "Nam",
        "age": "Người già",
        "region": "Bắc",
        "desc": "Giọng cụ ông từng trải, trầm ấm, chậm rãi",
        "pitch_shift": -3.5,
        "speed_factor": 0.82,
        "demo_file": "csa_ong_lao.wav"
    },
    {
        "sid": 9,
        "base_sid": 3,
        "id": "ba_lao",
        "name": "Bà lão (Hiền từ, từ tốn)",
        "gender": "Nữ",
        "age": "Người già",
        "region": "Bắc",
        "desc": "Giọng bà cụ hiền từ, phúc hậu, từ tốn",
        "pitch_shift": -2.5,
        "speed_factor": 0.90,
        "demo_file": "csa_ba_lao.wav"
    },
    {
        "sid": 10,
        "base_sid": 6,
        "id": "be_trai",
        "name": "Bé trai (Lanh lợi, tinh nghịch)",
        "gender": "Nam",
        "age": "Trẻ em",
        "region": "Bắc",
        "desc": "Giọng bé trai ngây thơ, líu lo, tinh nghịch",
        "pitch_shift": 4.2,
        "speed_factor": 1.0,
        "demo_file": "csa_be_trai.wav"
    },
    {
        "sid": 11,
        "base_sid": 6,
        "id": "be_gai",
        "name": "Bé gái (Trong trẻo, ngọt ngào)",
        "gender": "Nữ",
        "age": "Trẻ em",
        "region": "Bắc",
        "desc": "Giọng bé gái dễ thương, ngọt ngào, trong trẻo",
        "pitch_shift": 5.0,
        "speed_factor": 1.0,
        "demo_file": "csa_be_gai.wav"
    }
]


# ─── VITS Single-Speaker Voices ─────────────────────────
VITS_SINGLE_VOICES = [
    {
        "id": "banmai",
        "name": "Ban Mai (Nữ Bắc - Trong trẻo, rõ ràng)",
        "gender": "Nữ",
        "accent": "Bắc",
        "desc": "Giọng nữ Bắc chuẩn phát thanh, trong trẻo, rõ ràng",
        "fileName": "banmai.onnx",
        "onnxUrl": "https://invitation-aaa-compute-fantastic.trycloudflare.com/static/banmai.onnx",
        "jsonUrl": "https://invitation-aaa-compute-fantastic.trycloudflare.com/static/banmai.onnx.json",
        "demoUrl": "",
        "group": "vits"
    },
    {
        "id": "manhdung",
        "name": "Mạnh Dũng (Nam Bắc - Dõng dạc, khí chất)",
        "gender": "Nam",
        "accent": "Bắc",
        "desc": "Giọng nam Bắc khỏe khoắn, dõng dạc, đĩnh đạc",
        "fileName": "manhdung.onnx",
        "onnxUrl": "https://invitation-aaa-compute-fantastic.trycloudflare.com/static/manhdung.onnx",
        "jsonUrl": "https://invitation-aaa-compute-fantastic.trycloudflare.com/static/manhdung.onnx.json",
        "demoUrl": "",
        "group": "vits"
    },
    {
        "id": "calmwoman3688",
        "name": "Thùy Dung (Nữ - Nhẹ nhàng, điềm đạm)",
        "gender": "Nữ",
        "accent": "Bắc",
        "desc": "Giọng nữ nhẹ nhàng, điềm đạm, tự nhiên",
        "fileName": "calmwoman3688.onnx",
        "onnxUrl": "https://invitation-aaa-compute-fantastic.trycloudflare.com/static/calmwoman3688.onnx",
        "jsonUrl": "https://invitation-aaa-compute-fantastic.trycloudflare.com/static/calmwoman3688.onnx.json",
        "demoUrl": "",
        "group": "vits"
    },
    {
        "id": "ngochuyennew",
        "name": "Ngọc Huyền (Nữ Bắc - Thanh tú, biểu cảm)",
        "gender": "Nữ",
        "accent": "Bắc",
        "desc": "Giọng nữ Bắc thanh tú, nhẹ nhàng, biểu cảm linh hoạt",
        "fileName": "ngochuyennew.onnx",
        "onnxUrl": "https://invitation-aaa-compute-fantastic.trycloudflare.com/static/ngochuyennew.onnx",
        "jsonUrl": "https://invitation-aaa-compute-fantastic.trycloudflare.com/static/ngochuyennew.onnx.json",
        "demoUrl": "",
        "group": "vits"
    },
    {
        "id": "deepman3909",
        "name": "Trọng Nghĩa (Nam - Trầm sâu, uy nghiêm)",
        "gender": "Nam",
        "accent": "Bắc",
        "desc": "Giọng nam trầm sâu, uy nghiêm, phù hợp phản diện hoặc nhân vật uy quyền",
        "fileName": "deepman3909.onnx",
        "onnxUrl": "https://invitation-aaa-compute-fantastic.trycloudflare.com/static/deepman3909.onnx",
        "jsonUrl": "https://invitation-aaa-compute-fantastic.trycloudflare.com/static/deepman3909.onnx.json",
        "demoUrl": "",
        "group": "vits"
    }
]

OFFLINE_VOICES = [
    {
        "id": "kokoro_vietnamese",
        "name": "Kokoro-Vietnamese (NSƯT Kim Cúc & 14 Giọng Cao Cấp 24kHz)",
        "gender": "Đa giọng",
        "accent": "Bắc - Trung - Nam",
        "desc": "Mô hình Kokoro Neural thế hệ mới 24kHz: NSƯT Kim Cúc (Đọc Truyện Đêm Khuya VOV), Diễm Trinh, Mạnh Dũng, Ngọc Huyền, Mai Loan, Hưng Thịnh... Zero delay khi chuyển giọng thoại (~310 MB)",
        "fileName": "kokoro_vi.onnx",
        "onnxUrl": "https://invitation-aaa-compute-fantastic.trycloudflare.com/static/kokoro_vi_package.zip",
        "jsonUrl": "",
        "demoUrl": "https://invitation-aaa-compute-fantastic.trycloudflare.com/static/turn_0_sid13.wav",
        "subvoices": KOKORO_SUBVOICES
    },
    {
        "id": "vieneu_multispeaker",
        "name": "VieNeu Multi-Speaker (15 Giọng Gốc, Độ Tuổi & NSƯT Kim Cúc)",
        "gender": "Đa giọng",
        "accent": "Bắc - Trung - Nam",
        "desc": "Mô hình đa giọng gốc chuẩn VITS tích hợp 15 giọng: Dẫn truyện, Nam/Nữ chính, Ông lão, Bà lão, Trẻ em, Bích Giao, Kim Tuyến & NSƯT Kim Cúc VOV (~73.5 MB)",
        "fileName": "vieneu_v3_turbo.onnx",
        "onnxUrl": "https://invitation-aaa-compute-fantastic.trycloudflare.com/api/offline_voices/models/vieneu_v3_turbo.onnx",
        "jsonUrl": "https://invitation-aaa-compute-fantastic.trycloudflare.com/api/offline_voices/models/vieneu_v3_turbo.onnx.json",
        "demoUrl": "https://invitation-aaa-compute-fantastic.trycloudflare.com/api/offline_voices/models/vieneu_v3_turbo_demo.wav",
        "subvoices": VIENEU_SUBVOICES
    }
] + VITS_SINGLE_VOICES

# Bộ đệm instance Sherpa-ONNX trong bộ nhớ (tránh tải lại model mỗi câu)
_loaded_engines = {}
_engine_lock = threading.Lock()

# Trạng thái tiến trình tải
_download_status = {}


def extract_subvoice_sid(voice_id, speaker_id=0):
    try:
        s_int = int(speaker_id)
        if s_int > 0:
            return s_int
    except Exception:
        pass
    if voice_id:
        v_str = str(voice_id).strip()
        if ":" in v_str:
            parts = v_str.split(":")
            if parts[-1].isdigit():
                return int(parts[-1])
        clean = v_str.replace("offline_vieneu_", "").replace("offline_vieneu:", "").replace("offline_", "").lower()
        if clean.isdigit():
            return int(clean)
        for sv in VIENEU_SUBVOICES:
            if sv["id"].lower() == clean:
                return sv["sid"]
    try:
        return int(speaker_id)
    except Exception:
        return 0

def normalize_offline_voice_id(voice_id):
    if not voice_id:
        return "kokoro_vietnamese"
    v = str(voice_id).strip().lower().replace("offline_", "")
    # VITS single-speaker: nhận dạng trực tiếp, không route sang vieneu_multispeaker
    _vits_ids = {"banmai", "manhdung", "calmwoman3688", "ngochuyennew", "deepman3909"}
    if v in _vits_ids:
        return v
    if "kokoro" in v:
        return "kokoro_vietnamese"
    v = v.replace("vietneu", "vieneu")
    if "vieneu" in v or "vietneu" in v or v in ("vieneu_multispeaker", "multispeaker", "vieneu_v3_turbo", "vieneu", "vietneu", "turbo", "diemdam", "vieneu_v3_nano", "nano", "altotram", "alto", "mailinh"):
        return "vieneu_multispeaker"
    return v

def get_voice_info(voice_id):
    clean_id = normalize_offline_voice_id(voice_id)
    for v in OFFLINE_VOICES:
        if v["id"] == clean_id or v["id"] == voice_id or f"offline_{v['id']}" == voice_id:
            return v
    for v in OFFLINE_VOICES:
        if clean_id in v["id"] or v["id"] in clean_id:
            return v
    return None

def is_voice_downloaded(voice_id):
    v = get_voice_info(voice_id)
    if not v:
        # Thử tìm trong VITS_SINGLE_VOICES
        clean = str(voice_id).strip().lower().replace("offline_", "")
        for sv in VITS_SINGLE_VOICES:
            if sv["id"] == clean:
                f = MODELS_DIR / sv["fileName"]
                j = MODELS_DIR / f"{sv['fileName']}.json"
                return f.exists() and f.stat().st_size > 10 * 1024 * 1024 and j.exists()
        return False
    onnx_file = MODELS_DIR / v["fileName"]
    if v["id"] == "kokoro_vietnamese":
        voices_file = MODELS_DIR / "voices.bin"
        tokens_file = MODELS_DIR / "tokens.txt"
        lexicon_file = MODELS_DIR / "lexicon-vi.txt"
        return onnx_file.exists() and onnx_file.stat().st_size > 10 * 1024 * 1024 and voices_file.exists() and tokens_file.exists() and lexicon_file.exists()
    json_file = MODELS_DIR / f"{v['fileName']}.json"
    return onnx_file.exists() and onnx_file.stat().st_size > 10 * 1024 * 1024 and json_file.exists()

def get_all_voices_status():
    result = []
    for v in OFFLINE_VOICES:
        item = dict(v)
        item["full_id"] = f"offline_{v['id']}"
        item["is_downloaded"] = is_voice_downloaded(v["id"])
        item["download_status"] = _download_status.get(v["id"], "idle")
        item["group"] = v.get("group", "multispeaker")
        if item["is_downloaded"]:
            onnx_file = MODELS_DIR / v["fileName"]
            item["file_size_mb"] = round(onnx_file.stat().st_size / (1024 * 1024), 1)
        else:
            if "mailinh" in v["id"]:
                item["file_size_mb"] = 60.5
            elif "turbo" in v["id"]:
                item["file_size_mb"] = 235.0
            elif "nano" in v["id"]:
                item["file_size_mb"] = 180.0
            elif v.get("group") == "vits":
                item["file_size_mb"] = 60.6
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

        # 1. Tải file JSON cấu hình (nếu có)
        if v.get("jsonUrl"):
            req_json = urllib.request.Request(v["jsonUrl"], headers=headers)
            with urllib.request.urlopen(req_json, timeout=20) as resp:
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
    # Hỗ trợ nghe thử trực tiếp từng subvoice trong 12 giọng VieNeu
    sub_sample_dir = BASE_DIR / "static" / "vieneu_samples"
    clean_sub = str(voice_id).replace("offline_vieneu:", "").replace("offline_vieneu_", "").replace("offline_", "").strip().lower()
    
    # 1. Tìm theo sid số (0..11) hoặc mã id của subvoice
    matched_sub = None
    if clean_sub.isdigit():
        target_sid = int(clean_sub)
        matched_sub = next((sv for sv in VIENEU_SUBVOICES if sv["sid"] == target_sid), None)
    else:
        matched_sub = next((sv for sv in VIENEU_SUBVOICES if sv["id"].lower() == clean_sub), None)
        
    if matched_sub and matched_sub.get("demo_file"):
        demo_path = sub_sample_dir / matched_sub["demo_file"]
        if demo_path.exists() and demo_path.stat().st_size > 1024:
            return demo_path.read_bytes()

    v = get_voice_info(voice_id)
    if not v or not v.get("demoUrl"):
        return None
    demo_url = v["demoUrl"]
    ext = "mp3" if "mp3" in demo_url else "wav"
    cache_file = MODELS_DIR / f"{v['id']}_demo.{ext}"
    if cache_file.exists() and cache_file.stat().st_size > 1024:
        return cache_file.read_bytes()
    try:
        req = urllib.request.Request(demo_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
            if data and len(data) > 1024:
                try:
                    cache_file.write_bytes(data)
                except Exception:
                    pass
            return data
    except Exception as e:
        logger.warning(f"Lỗi tải demo audio cho {voice_id}: {e}")
        return None

def _ensure_model_tokens_file(file_name):
    """Tạo file tokens riêng biệt chuẩn 100% từ phoneme_id_map trong .onnx.json của từng model để tránh lệch ID gây rè/tạch"""
    json_path = MODELS_DIR / f"{file_name}.json"
    custom_tokens_path = MODELS_DIR / f"{file_name}.tokens.txt"
    noise_scale = 0.667
    noise_w = 0.8
    length_scale = 1.15

    if json_path.exists():
        try:
            cfg = json.loads(json_path.read_text(encoding="utf-8"))
            inf = cfg.get("inference", {})
            noise_scale = float(inf.get("noise_scale", 0.667))
            noise_w = float(inf.get("noise_w", 0.8))
            length_scale = float(inf.get("length_scale", 1.15))

            pmap = cfg.get("phoneme_id_map")
            if pmap and isinstance(pmap, dict):
                lines = []
                for sym, ids in pmap.items():
                    # Sherpa-ONNX piper-phonemize yêu cầu mỗi token là đúng 1 ký tự Unicode (UTF-32 length == 1)
                    if ids and len(sym) == 1:
                        lines.append(f"{sym} {ids[0]}")
                if lines:
                    custom_tokens_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
                    return str(custom_tokens_path), noise_scale, noise_w, length_scale
        except Exception as e:
            logger.warning(f"Lỗi tạo tokens riêng cho {file_name}: {e}")

    return str(TOKENS_PATH), noise_scale, noise_w, length_scale

def get_sherpa_engine(voice_id):
    clean_id = normalize_offline_voice_id(voice_id)
    v = get_voice_info(clean_id)
    if not v or not is_voice_downloaded(clean_id):
        return None

    with _engine_lock:
        if clean_id in _loaded_engines:
            return _loaded_engines[clean_id]

        import sherpa_onnx
        onnx_file = str(MODELS_DIR / v["fileName"])
        tokens_file, noise_scale, noise_w, length_scale = _ensure_model_tokens_file(v["fileName"])
        data_dir = str(DATA_DIR)

        if clean_id == "kokoro_vietnamese":
            voices_file = str(MODELS_DIR / "voices.bin")
            tokens_file = str(MODELS_DIR / "tokens.txt")
            lexicon_file = str(MODELS_DIR / "lexicon-vi.txt")
            tts_config = sherpa_onnx.OfflineTtsConfig(
                model=sherpa_onnx.OfflineTtsModelConfig(
                    kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(
                        model=onnx_file,
                        voices=voices_file,
                        tokens=tokens_file,
                        data_dir=data_dir,
                        lexicon=lexicon_file
                    ),
                    num_threads=4,
                    debug=False
                )
            )
        else:
            tts_config = sherpa_onnx.OfflineTtsConfig(
                model=sherpa_onnx.OfflineTtsModelConfig(
                    vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                        model=onnx_file,
                        tokens=tokens_file,
                        data_dir=data_dir,
                        noise_scale=noise_scale,
                        noise_scale_w=noise_w,
                        length_scale=length_scale
                    ),
                    num_threads=4,
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

def generate_sfx_samples(sfx_type, count=1, sample_rate=22050):
    """
    Sinh tín hiệu âm thanh hiệu ứng thực tế (Foley SFX Synthesis) bằng thuật toán DSP:
    - impact: Va chạm quyền cước, nện đòn trầm đục (phanh, bịch, bộp, rầm, rắc)
    - explosion: Tiếng sấm sét, vụ nổ rền (ầm, bùm, đùng, đoàng, oành, nổ)
    - clash: Va chạm binh khí kim loại tóe lửa (keng, choang, xoảng, leng keng)
    - whoosh: Kiếm khí, phi kiếm, ám khí xé rách không gian (vút, vèo, xẹt, chéo)
    Hỗ trợ phát lặp lại tự nhiên theo số lần xuất hiện (ví dụ: Vèo, vèo, vèo -> count=3)
    """
    import math, random
    one_chunk = []
    gap_sec = 0.10

    if sfx_type == 'impact':
        dur = 0.32
        gap_sec = 0.12
        n_samples = int(sample_rate * dur)
        for i in range(n_samples):
            t = i / sample_rate
            freq = 120.0 * math.exp(-t * 8.0) + 40.0
            phase = 2.0 * math.pi * freq * t
            sub = math.sin(phase) * math.exp(-t * 9.0)
            noise = random.uniform(-1.0, 1.0) * math.exp(-t * 25.0)
            val = (sub * 0.75 + noise * 0.25) * 0.95
            one_chunk.append(val)
    elif sfx_type == 'explosion':
        dur = 0.75
        gap_sec = 0.18
        n_samples = int(sample_rate * dur)
        for i in range(n_samples):
            t = i / sample_rate
            freq = 90.0 * math.exp(-t * 3.5) + 35.0
            phase = 2.0 * math.pi * freq * t
            sub = math.sin(phase) * math.exp(-t * 3.5)
            noise = random.uniform(-1.0, 1.0) * math.exp(-t * 4.5)
            val = (sub * 0.65 + noise * 0.35) * 0.95
            one_chunk.append(val)
    elif sfx_type == 'clash':
        dur = 0.50
        gap_sec = 0.10
        n_samples = int(sample_rate * dur)
        for i in range(n_samples):
            t = i / sample_rate
            b1 = math.sin(2.0 * math.pi * 2350.0 * t) * math.exp(-t * 7.0)
            b2 = math.sin(2.0 * math.pi * 3400.0 * t) * math.exp(-t * 9.0)
            b3 = math.sin(2.0 * math.pi * 5100.0 * t) * math.exp(-t * 14.0)
            click = random.uniform(-1.0, 1.0) * math.exp(-t * 70.0)
            val = (b1 * 0.35 + b2 * 0.3 + b3 * 0.2 + click * 0.15) * 0.9
            one_chunk.append(val)
    elif sfx_type == 'whoosh':
        dur = 0.28
        gap_sec = 0.08
        n_samples = int(sample_rate * dur)
        for i in range(n_samples):
            t = i / sample_rate
            env = (math.sin(math.pi * t / dur)) ** 2
            noise = random.uniform(-1.0, 1.0)
            carrier = math.sin(2.0 * math.pi * (600.0 + 1400.0 * math.sin(math.pi * t / dur)) * t)
            val = (noise * 0.4 + carrier * 0.6) * env * 0.9
            one_chunk.append(val)
    else:
        return []

    repeat_count = max(1, min(int(count or 1), 4))
    if repeat_count == 1:
        return one_chunk

    gap_samples = int(sample_rate * gap_sec)
    all_samples = []
    for c in range(repeat_count):
        all_samples.extend(one_chunk)
        if c < repeat_count - 1:
            all_samples.extend([0.0] * gap_samples)
    return all_samples

def generate_sfx_wav_bytes(sfx_type, count=1, sample_rate=22050):
    """
    Sinh file WAV âm thanh hiệu ứng (SFX) 16-bit PCM mono chuẩn.
    """
    samples = generate_sfx_samples(sfx_type, count=count, sample_rate=sample_rate)
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

SFX_WORDS_RAW = r'(?:oanh\s+long(?:\s+long)?|oành(?:\s+oành)?|oanh|phanh(?:\s+phanh)?|xuy(?:\s+xuy){1,2}|xuy(?=[!?.…~–—]|(?:\s+một\s+tiếng))|ầm(?:\s+ầm){1,2}|ầm\s+vang|ầm|đùng\s+đoàng|đùng(?:\s+đùng)?|đoàng|bùm(?:\s+bùm)?|nổ\s+tung|rầm(?:\s+rầm)?|bịch(?:\s+bịch)?|huỵch|bộp(?:\s+bộp)?|bốp(?:\s+bốp)?|chát|rắc(?:\s+rắc)?|bành|leng\s+keng|keng(?:\s+keng)?|choang(?:\s+choang)?|xoảng(?:\s+xoảng)?|xủng\s+xoảng|boong|coong|vun\s+vút|vút(?:\s+vút)?|vèo(?:\s+vèo)?|xẹt(?:\s+xẹt)?|xoẹt(?:\s+xoẹt)?|chéo|vù(?:\s+vù)?|phù)'
SFX_REGEX_ZERO_WIDTH = None

def get_sfx_regex():
    global SFX_REGEX_ZERO_WIDTH
    if SFX_REGEX_ZERO_WIDTH is None:
        import re
        SFX_REGEX_ZERO_WIDTH = re.compile(rf'(?i)(?<![\w\u00C0-\u1EF9]){SFX_WORDS_RAW}(?:\s+một\s+tiếng)?(?![\w\u00C0-\u1EF9])')
    return SFX_REGEX_ZERO_WIDTH

def detect_and_prune_sfx(text):
    """
    Phát hiện từ tượng thanh độc lập và cắt bỏ (Prune) khỏi văn bản đọc để TTS không đọc thô:
    - 1. Nổ / Sấm: oanh long, oanh long long, ầm, ầm ầm, bùm, đùng, đoàng, oành, oanh, nổ tung
    - 2. Va chạm / Quyền cước: rầm, bịch, huỵch, bộp, bốp, chát, rắc, bành, phanh
    - 3. Binh khí: keng, choang, xoảng, leng keng, xủng xoảng, boong, coong
    - 4. Kiếm khí / Xé gió: vun vút, vút, vèo, xẹt, xoẹt, chéo, vù, phù, xuy, xuy xuy
    Hỗ trợ lặp lại nhiều lần liên tiếp (Vèo, vèo, vèo / Keng, keng, keng / Phanh, phanh, phanh / Xuy, xuy, xuy) bằng Zero-width assertions.
    Trả về (sfx_type, cleaned_text, count)
    """
    if not text:
        return None, text, 0
    import re
    pat = get_sfx_regex()
    matches = pat.findall(text)
    if not matches:
        return None, text, 0

    first = matches[0].lower()
    if re.search(r'keng|choang|xoảng|boong|coong', first):
        sfx_type = 'clash'
    elif re.search(r'vút|vèo|xẹt|xoẹt|chéo|vù|phù|xuy', first):
        sfx_type = 'whoosh'
    elif re.search(r'rầm|bịch|huỵch|bộp|bốp|chát|rắc|bành|phanh', first):
        sfx_type = 'impact'
    else:
        sfx_type = 'explosion'

    pruned = pat.sub('', text)
    cleaned = re.sub(r'[\s,;:!?.\-–—]+', ' ', pruned).strip()
    return sfx_type, cleaned, len(matches)

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
    male_titles = r'\b(chàng|hắn|hắn ta|công tử|sư huynh|huynh đệ|phụ thân|cha|nam tử|huynh trưởng|thiếu niên|đại ca|lão giả|đạo nhân|lão tổ|môn chủ|chưởng môn|tông chủ|tiểu tử|gã|y|trượng phu|nam nhân|hoàng thượng|vương gia|Lý Phong|Phong|Minh|Quang|Dũng|Huy|Vương Võ|Võ|Lâm Tiêu|Tiêu|Hàn Lập)\b'
    verbs = r'\b(nói|đáp|hỏi|than|cười|thầm|bảo|nghẹn ngào|thì thào|thỏ thẻ|quát|thét|gầm|rống|la|cười lạnh|hừ lạnh|trầm giọng|lẩm bẩm|thốt lên|hô|nhủ|nghĩ|truyền âm|tiếp lời|khẽ nói|trong nội tâm|trong lòng|đáy lòng|tâm niệm|thầm nghĩ|nghĩ thầm|thầm than|thầm nhủ|thầm mắng|kinh ngạc|kinh hãi|hoảng sợ|chấn động|chấn kinh|biến sắc|ngẩn người|bàng hoàng|trầm ngâm|tự nhủ|nhíu mày|thở dài|nhếch miệng|cười nhạt|cười gằn)\b'
    
    for i, p in enumerate(raw_parts):
        p_clean = p.strip()
        if not p_clean:
            continue
        is_dialogue = bool(re.match(r'^[“"«「『].+[”"»」』]$', p_clean))
        clean_text = re.sub(r'^[“"«「『]\s*|\s*[”"»」』]$', '', p_clean).strip()
        if not clean_text:
            continue
            
        # Kiểm tra từ tượng thanh độc lập
        sfx_res = detect_and_prune_sfx(clean_text)
        sfx_type, pruned_text = sfx_res[0], sfx_res[1]
        if sfx_type and pruned_text:
            clean_text = pruned_text
            
        # Tinh chỉnh nhịp ngắt nghỉ dấu phẩy (Comma Prosody & Breath Enhancer):
        clean_text = re.sub(r'[\s\u00A0\u1680\u2000-\u200a\u202f\u205f\u3000—–-]*[,，、﹐][\s\u00A0\u1680\u2000-\u200a\u202f\u205f\u3000—–-]*(?:…|\.{3})?', ', ', clean_text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
            
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

def _apply_smooth_fade(samples, sample_rate=22050, fade_ms=25, is_trailing=False):
    """
    Làm mượt biên âm thanh tự nhiên bằng đường dốc cosine nhẹ nhàng:
    - Giữ đệm đuôi hào phóng 120ms (hoặc 180ms với câu ngập ngừng) để tuyệt đối không cắt cụt đuôi chữ, âm gió hay tiếng thở.
    - Fade out 25ms siêu mịn màng, loại bỏ hoàn toàn mọi tiếng lách cách (click/pop) hoặc rè rè cuối câu.
    """
    if not samples or len(samples) < 64:
        return samples
    import numpy as np
    arr = np.asarray(samples, dtype=np.float32).copy()
    # Ngưỡng phát hiện âm: Giữ đệm đuôi an toàn 120ms (hoặc 180ms nếu trailing)
    non_silent = np.where(np.abs(arr) > 0.001)[0]
    if len(non_silent) > 0:
        pad_start = int(sample_rate * 0.020)
        pad_end = int(sample_rate * (0.180 if is_trailing else 0.120))
        start_idx = max(0, int(non_silent[0]) - pad_start)
        end_idx = min(len(arr), int(non_silent[-1]) + pad_end)
        arr = arr[start_idx:end_idx]

    fade_len = min(int(sample_rate * (fade_ms / 1000.0)), len(arr) // 4)
    if fade_len > 4:
        fade_in = 0.5 * (1.0 - np.cos(np.linspace(0, np.pi, fade_len, dtype=np.float32)))
        fade_out = 0.5 * (1.0 + np.cos(np.linspace(0, np.pi, fade_len, dtype=np.float32)))
        arr[:fade_len] *= fade_in
        arr[-fade_len:] *= fade_out
    return arr.tolist()

def apply_dsp_voice_profile(samples, sample_rate, pitch_shift=0.0, speed_factor=1.0):
    """
    Biến đổi giọng nói Formant/Pitch shift bằng thuật toán DSP thời gian thực:
    - n_semitones: độ cao/trầm (âm số = già/trầm hơn, dương số = trẻ con/líu lo)
    - speed_factor: tốc độ nói (già chậm hơn 0.88, trẻ nhanh hơn 1.15)
    """
    if pitch_shift == 0.0 and speed_factor == 1.0:
        return samples
    import numpy as np
    import scipy.signal
    arr = np.asarray(samples, dtype=np.float32)
    if pitch_shift != 0.0:
        factor = 2.0 ** (pitch_shift / 12.0)
        new_len = int(len(arr) / factor)
        resampled = scipy.signal.resample(arr, new_len)
        orig_indices = np.linspace(0, len(resampled) - 1, len(arr))
        arr = np.interp(orig_indices, np.arange(len(resampled)), resampled).astype(np.float32)
    if speed_factor != 1.0:
        target_len = int(len(arr) / speed_factor)
        arr = scipy.signal.resample(arr, target_len).astype(np.float32)
    return arr.tolist()


def synthesize_vits_single_speaker(voice_id, text, speed=1.0, sample_rate=22050):
    """Tổng hợp giọng VITS đơn giọng (banmai, manhdung, calmwoman3688, ngochuyennew, deepman3909)"""
    import sherpa_onnx
    import numpy as np
    import io
    import wave

    clean_id = str(voice_id).strip().lower().replace("offline_", "")
    vits_info = None
    for sv in VITS_SINGLE_VOICES:
        if sv["id"] == clean_id:
            vits_info = sv
            break
    if not vits_info:
        raise ValueError(f"Không tìm thấy VITS voice: {voice_id}")

    onnx_path = str(MODELS_DIR / vits_info["fileName"])
    tokens_file, noise_scale, noise_w, length_scale = _ensure_model_tokens_file(vits_info["fileName"])

    cache_key = f"vits_{clean_id}"
    with _engine_lock:
        if cache_key not in _loaded_engines:
            tts_config = sherpa_onnx.OfflineTtsConfig(
                model=sherpa_onnx.OfflineTtsModelConfig(
                    vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                        model=onnx_path,
                        lexicon="",
                        tokens=tokens_file,
                        data_dir=str(DATA_DIR) if DATA_DIR.exists() else "",
                        noise_scale=noise_scale,
                        noise_scale_w=noise_w,
                        length_scale=length_scale,
                        dict_dir="",
                    ),
                    provider="cpu",
                    num_threads=2,
                    debug=0,
                ),
                rule_fsts="",
                max_num_sentences=1,
            )
            _loaded_engines[cache_key] = sherpa_onnx.OfflineTts(tts_config)
        engine = _loaded_engines[cache_key]

    result = engine.generate(text, sid=0, speed=float(speed))
    audio_data = np.array(result.samples, dtype=np.float32)
    audio_int16 = (audio_data * 32767).clip(-32768, 32767).astype(np.int16)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(result.sample_rate)
        wf.writeframes(audio_int16.tobytes())
    return buf.getvalue()

def synthesize_offline(text, voice_id="vieneu_multispeaker", speed=1.0, multi_voice=False, speaker_id=0):
    """
    Tổng hợp âm thanh giọng đọc Offline AI Đa Giọng Gốc VieNeu TTS:
    1. Mô hình duy nhất: VieNeu Multi-Speaker (14 Giọng Gốc & Độ Tuổi).
    2. Hỗ trợ chọn subvoice trực tiếp qua speaker_id (0-11) hoặc voice_id.
    3. Hỗ trợ tự động phân vai thoại: Nam chính, Nữ chính, Ông lão, Bà lão, Bé trai, Bé gái khi bật multi_voice.
    4. Áp dụng biến đổi DSP Formant/Pitch mượt mà không độ trễ.
    """
    # VITS single-speaker route: banmai, manhdung, calmwoman3688, ngochuyennew, deepman3909
    _vits_ids = {"banmai", "manhdung", "calmwoman3688", "ngochuyennew", "deepman3909"}
    _clean_vid = str(voice_id).strip().lower().replace("offline_", "")
    if _clean_vid in _vits_ids:
        return synthesize_vits_single_speaker(voice_id, text, speed=speed, sample_rate=22050)

    clean_id = normalize_offline_voice_id(voice_id)
    story_segments = parse_contextual_story_segments(text)
    if not story_segments:
        return None

    import sherpa_onnx
    safe_speed = max(0.5, min(2.2, float(speed)))
    all_samples = []
    final_sample_rate = 22050

    is_kokoro = (clean_id == "kokoro_vietnamese" or "kokoro" in str(voice_id).lower())
    engine_id = "kokoro_vietnamese" if is_kokoro else "vieneu_multispeaker"
    engine = get_sherpa_engine(engine_id)
    if not engine:
        # Fallback to the other engine if available
        fallback_id = "vieneu_multispeaker" if is_kokoro else "kokoro_vietnamese"
        engine = get_sherpa_engine(fallback_id)
        if engine:
            engine_id = fallback_id
            is_kokoro = (engine_id == "kokoro_vietnamese")
        else:
            raise ValueError(f"Mô hình giọng offline ({engine_id}) chưa được tải về máy!")

    # Tra cứu profile subvoice theo speaker_id hoặc subvoice_id
    current_sid = extract_subvoice_sid(voice_id, speaker_id)
    if is_kokoro:
        # Kokoro SID mapping:
        # 14 -> 13 (Kim Cúc), 0 -> 13 (Dẫn chuyện mặc định: Kim Cúc), 1 -> 0 (Diễm Trinh), 2 -> 4 (Mạnh Dũng)...
        kokoro_map = {14: 13, 0: 13, 1: 0, 2: 4, 3: 6, 4: 1, 5: 8, 6: 10, 7: 7, 8: 4, 9: 3, 10: 6, 11: 6, 12: 2, 13: 3}
        current_sid = kokoro_map.get(current_sid, current_sid if current_sid < 14 else 13)

    for idx, s_seg in enumerate(story_segments):
        seg_text = s_seg["text"].strip()
        if not seg_text:
            continue

        target_sid = current_sid
        pitch_shift = 0.0
        dsp_speed = 1.0

        if multi_voice and s_seg["is_dialogue"]:
            gender = s_seg.get("gender", "neutral")
            seg_lower = seg_text.lower()

            # Phân vai chỉ đúng 2 giọng nhân vật thoại theo giới tính (Nam & Nữ):
            # Tuyệt đối không đột biến sang giọng người già/trẻ em
            if gender == "female":
                target_sid = 1  # Minh Anh (Nữ chính)
            elif gender == "male":
                target_sid = 2  # Quang Huy (Nam chính)
            else:
                target_sid = 2 if any(w in seg_lower for w in ("ta", "huynh", "anh", "hắn", "chàng", "đệ", "ông")) else 1

        # Lấy thông số DSP theo target_sid
        if is_kokoro:
            sub_info = next((sv for sv in KOKORO_SUBVOICES if sv["sid"] == target_sid or sv.get("base_sid") == target_sid), None)
            if sub_info:
                pitch_shift = sub_info.get("pitch_shift", 0.0)
                dsp_speed = sub_info.get("speed_factor", 1.0)
                model_sid = sub_info.get("base_sid", target_sid)
            else:
                model_sid = target_sid if target_sid < 14 else 13
        else:
            sub_info = next((sv for sv in VIENEU_SUBVOICES if sv["sid"] == target_sid), None)
            if sub_info:
                pitch_shift = sub_info.get("pitch_shift", 0.0)
                dsp_speed = sub_info.get("speed_factor", 1.0)
            model_sid = sub_info.get("base_sid", target_sid) if sub_info else (target_sid if target_sid in (0, 1, 2, 3, 4) else 0)

        is_trailing = (s_seg.get("emotion") == "trailing" or seg_text.endswith("…") or seg_text.endswith("..."))
        base_speed = safe_speed
        if s_seg["is_dialogue"]:
            if s_seg["emotion"] == "excited":
                base_speed = min(2.2, base_speed * 1.05)
            elif s_seg["emotion"] == "trailing":
                base_speed = max(0.5, base_speed * 0.93)
            elif s_seg["emotion"] == "question":
                base_speed = base_speed * 1.02
        else:
            base_speed = base_speed * 0.99
        part_audio = engine.generate(seg_text, sid=model_sid, speed=base_speed)
        if part_audio and len(part_audio.samples) > 0:
            final_sample_rate = part_audio.sample_rate
            # Giữ trọn vẹn độ ngân đuôi câu không bị cắt cụt
            clean_samples = _apply_smooth_fade(part_audio.samples, final_sample_rate, fade_ms=8, is_trailing=is_trailing)
            # Áp dụng DSP Pitch Shift và Time-Stretching chuyên sâu (ví dụ: ông lão chậm rãi 0.76x)
            if pitch_shift != 0.0 or dsp_speed != 1.0:
                clean_samples = apply_dsp_voice_profile(clean_samples, final_sample_rate, pitch_shift=pitch_shift, speed_factor=dsp_speed)
            all_samples.extend(clean_samples)

        # Khoảng nghỉ tự nhiên
        if idx < len(story_segments) - 1:
            next_seg = story_segments[idx + 1]
            pause_sec = 0.16 if (s_seg["is_dialogue"] != next_seg["is_dialogue"]) else 0.10
            all_samples.extend([0.0] * int(final_sample_rate * pause_sec))

    if not all_samples:
        return None

    # BẢO TỒN ĐỘ TRONG TRẺO NGUYÊN BẢN (CRYSTAL CLEAR BIT-PERFECT SCALING):
    # Dùng chuẩn hóa đỉnh tuyến tính (Linear Peak 0.84) giống hệt các file mẫu Master
    # Tuyệt đối không can thiệp dải nén (knee compression) để âm sắc trong vắt, không rè, không đục
    import numpy as np
    arr = np.asarray(all_samples, dtype=np.float32)
    if len(arr) > 0:
        peak = float(np.max(np.abs(arr)))
        if peak > 1e-4:
            target_peak = 0.84
            arr = arr * (target_peak / peak)
        arr = np.clip(arr, -0.98, 0.98)
        norm_samples = arr.tolist()
    else:
        norm_samples = all_samples

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_name = tmp.name
    try:
        sherpa_onnx.write_wave(tmp_name, norm_samples, final_sample_rate)
        with open(tmp_name, "rb") as f:
            data = f.read()
        return data
    finally:
        if os.path.exists(tmp_name):
            try:
                os.remove(tmp_name)
            except Exception:
                pass

def _warmup_background():
    """Tải trước mô hình đa giọng VieNeu vào RAM"""
    try:
        if is_voice_downloaded("vieneu_multispeaker"):
            get_sherpa_engine("vieneu_multispeaker")
    except Exception:
        pass

threading.Thread(target=_warmup_background, daemon=True).start()

