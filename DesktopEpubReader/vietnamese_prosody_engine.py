import re
import unicodedata
import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Set, Callable, Any

try:
    from scipy.signal import lfilter as _scipy_lfilter
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


# ==============================================================================
# PHẦN 1: HẰNG SỐ ĐỊNH DANH VAI ĐỌC & CẤU HÌNH PRESET MASTERING PHÒNG THU
# ==============================================================================
VOICE_NARRATOR_ID = "VOICE_NARRATOR"      # Mã giọng dành riêng cho Lời Dẫn Truyện
VOICE_DIALOGUE_ID = "VOICE_DIALOGUE"      # Mã giọng dành riêng cho Lời Thoại Nhân Vật
ENABLE_GENDER_GUESSING = False            # Khóa đoán Nam/Nữ để đạt độ chính xác phân tách Thoại vs Kể >= 99.5%


@dataclass
class VocalClarityPreset:
    """Cấu hình tham số Mastering làm ấm, mượt & trong giọng chuẩn Podcast / ElevenLabs / CapCut (V9.0)."""
    name: str = "SOULFUL_PODCAST_WARMTH"
    stft_debuzz_strength: float = 0.48
    formant_contrast_boost: float = 0.13
    chest_warmth_db: float = 2.8
    mud_cut_db: float = -3.5
    nasal_cut_db: float = -1.9
    harsh_cut_db: float = -2.3
    ear_soothe_strength: float = 0.58
    clarity_presence_db: float = 2.0
    brilliance_shelf_db: float = 2.5
    consonant_transient_db: float = 1.4
    air_exciter_mix: float = 0.15
    even_tube_harmonic_weight: float = 0.70
    odd_aphex_harmonic_weight: float = 0.30
    de_esser_rel_threshold: float = 0.36
    multiband_upward_lift_db: float = 1.8
    studio_ambience_mix: float = 0.060
    velvet_breath_tail_mix: float = 0.020


CLARITY_PRESETS: Dict[str, VocalClarityPreset] = {
    "SOULFUL_PODCAST_WARMTH": VocalClarityPreset(
        name="SOULFUL_PODCAST_WARMTH",
        stft_debuzz_strength=0.48,
        formant_contrast_boost=0.13,
        chest_warmth_db=2.8,
        mud_cut_db=-3.5,
        nasal_cut_db=-1.9,
        harsh_cut_db=-2.3,
        ear_soothe_strength=0.58,
        clarity_presence_db=2.0,
        brilliance_shelf_db=2.5,
        consonant_transient_db=1.4,
        air_exciter_mix=0.15,
        even_tube_harmonic_weight=0.70,
        odd_aphex_harmonic_weight=0.30,
        de_esser_rel_threshold=0.36,
        multiband_upward_lift_db=1.8,
        studio_ambience_mix=0.060,
        velvet_breath_tail_mix=0.020,
    ),
    "ELEVENLABS_WARM_INTIMATE": VocalClarityPreset(
        name="ELEVENLABS_WARM_INTIMATE",
        stft_debuzz_strength=0.46,
        formant_contrast_boost=0.14,
        chest_warmth_db=2.4,
        mud_cut_db=-3.5,
        nasal_cut_db=-1.8,
        harsh_cut_db=-1.9,
        ear_soothe_strength=0.52,
        clarity_presence_db=2.5,
        brilliance_shelf_db=3.0,
        consonant_transient_db=1.8,
        air_exciter_mix=0.17,
        even_tube_harmonic_weight=0.62,
        odd_aphex_harmonic_weight=0.38,
        de_esser_rel_threshold=0.38,
        multiband_upward_lift_db=1.9,
        studio_ambience_mix=0.056,
        velvet_breath_tail_mix=0.016,
    ),
    "GEMINI_NATURAL_SILK": VocalClarityPreset(
        name="GEMINI_NATURAL_SILK",
        stft_debuzz_strength=0.45,
        formant_contrast_boost=0.12,
        chest_warmth_db=2.0,
        mud_cut_db=-3.4,
        nasal_cut_db=-1.9,
        harsh_cut_db=-2.0,
        ear_soothe_strength=0.56,
        clarity_presence_db=2.3,
        brilliance_shelf_db=2.8,
        consonant_transient_db=1.6,
        air_exciter_mix=0.15,
        even_tube_harmonic_weight=0.62,
        odd_aphex_harmonic_weight=0.38,
        de_esser_rel_threshold=0.36,
        multiband_upward_lift_db=1.6,
        studio_ambience_mix=0.048,
        velvet_breath_tail_mix=0.015,
    ),
    "CAPCUT_CRISP_STUDIO": VocalClarityPreset(
        name="CAPCUT_CRISP_STUDIO",
        stft_debuzz_strength=0.50,
        formant_contrast_boost=0.15,
        chest_warmth_db=1.6,
        mud_cut_db=-3.8,
        nasal_cut_db=-2.0,
        harsh_cut_db=-1.6,
        ear_soothe_strength=0.45,
        clarity_presence_db=3.0,
        brilliance_shelf_db=3.5,
        consonant_transient_db=2.2,
        air_exciter_mix=0.20,
        even_tube_harmonic_weight=0.45,
        odd_aphex_harmonic_weight=0.55,
        de_esser_rel_threshold=0.38,
        multiband_upward_lift_db=1.8,
        studio_ambience_mix=0.048,
        velvet_breath_tail_mix=0.012,
    ),
    "XIANXIA_EPIC_NARRATOR": VocalClarityPreset(
        name="XIANXIA_EPIC_NARRATOR",
        stft_debuzz_strength=0.49,
        formant_contrast_boost=0.15,
        chest_warmth_db=2.6,
        mud_cut_db=-3.8,
        nasal_cut_db=-2.0,
        harsh_cut_db=-1.8,
        ear_soothe_strength=0.50,
        clarity_presence_db=2.7,
        brilliance_shelf_db=3.2,
        consonant_transient_db=2.0,
        air_exciter_mix=0.18,
        even_tube_harmonic_weight=0.58,
        odd_aphex_harmonic_weight=0.42,
        de_esser_rel_threshold=0.38,
        multiband_upward_lift_db=1.9,
        studio_ambience_mix=0.062,
        velvet_breath_tail_mix=0.016,
    ),
}


# ==============================================================================
# PHẦN 2: CẤU TRÚC DỮ LIỆU ĐỒNG BỘ HÓA V8.1 & V7.1 (UNIFIED DATA STRUCTURES)
# ==============================================================================
@dataclass
class TextRoleSpan:
    """
    Đơn vị văn bản cấp độ Đoạn/Mệnh đề đã được khóa cứng Vai (NARRATION vs DIALOGUE)
    và Cảm xúc kế thừa từ câu dẫn TRƯỚC KHI đưa vào bộ lập kịch bản 7 tầng.
    """
    paragraph_index: int
    role: str                             # "NARRATION" | "DIALOGUE"
    voice_id: str                         # VOICE_NARRATOR_ID | VOICE_DIALOGUE_ID
    text: str                             # Nội dung văn bản sạch
    inherited_emotion: Optional[str] = None   # Cảm xúc hút từ câu dẫn (vd: "SHOUT_ROAR", "COLD_THREAT")
    inherited_confidence: float = 0.0
    detection_reason: str = ""            # Lý do nhận diện (để debug/audit)


@dataclass
class SyllableSpan:
    """Thông tin tọa độ và năng lượng của từng âm tiết thực tế trên mảng sóng âm."""
    index: int
    start_sample: int
    peak_sample: int
    end_sample: int
    rms_energy: float


@dataclass
class SyllableFilterProfile:
    """
    Hồ sơ phân tích chi tiết của từng âm tiết sau khi đi qua 6 tầng bộ lọc ngôn ngữ học
    và đồng bộ hóa với hệ số biểu cảm thoại (1.35x).
    """
    index: int
    word: str
    clean_lower: str
    viet_tone: str = "NGANG"                 # NGANG | HUYEN | SAC | HOI | NGA | NANG
    coda_type: str = "OPEN_VOWEL"            # OPEN_VOWEL | NASAL_SONORANT | GLIDE_DIPHTHONG | STOP_CODA
    syntactic_role: str = "CONTENT_NORMAL"   # PICKUP_FUNCTION | RESULTATIVE_PARTICLE | INTENSIFIER | EMOTIONAL_ANCHOR | CONTENT_NORMAL | MODAL_PARTICLE
    stretch_factor: float = 1.0              # Hệ số co giãn thời lượng WSOLA riêng cho chữ này (0.83x -> 1.85x)
    f0_offset_st: float = 0.0                # Độ lệch tần số cơ bản riêng của chữ này (semitones)
    tone_sandhi_scale: float = 1.0           # Hệ số điều hòa biến âm khi 2 thanh điệu đứng cạnh nhau
    gain_offset_db: float = 0.0              # Độ lệch âm lượng riêng của chữ này (dB)
    pause_after_ms: int = 0                  # Thời gian ngắt nhịp ý ngay sau chữ này (ms)
    no_split_after: bool = False             # True nếu bị khóa cú pháp cấm tách cụm ngay sau chữ này
    expected_dur_weight: float = 1.0         # Trọng số thời lượng kỳ vọng dùng cho Bộ lọc Tầng 7 (Khớp sóng âm 1:1)


@dataclass
class ProsodicSegment:
    """
    Kịch bản điều khiển 16 tình huống ngữ điệu, hợp nhất 100% thông tin Phân vai Lời thoại (V8.1)
    và Hồ sơ từng âm tiết (V7.1).
    """
    text: str
    role: str = "NARRATION"                  # "NARRATION" | "DIALOGUE"
    voice_id: str = "VOICE_NARRATOR"         # "VOICE_NARRATOR" | "VOICE_DIALOGUE"
    paragraph_index: int = 0                 # Chỉ số đoạn văn gốc
    detection_reason: str = ""               # Lý do nhận diện vai từ bộ phân loại
    inherited_emotion: Optional[str] = None  # Cảm xúc kế thừa từ câu dẫn
    dialogue_expressive_boost: float = 1.0   # 1.35x cho DIALOGUE, 1.0x cho NARRATION
    words: List[str] = field(default_factory=list)
    syllable_count: int = 0
    effort_mode: str = "SOULFUL_CONTEMPLATION"
    emotion_confidence: float = 1.0
    length_scale: float = 1.0
    noise_scale: float = 0.580
    noise_w: float = 0.72
    gain_db: float = 0.0
    presence_boost_db: float = 0.0
    warmth_boost_db: float = 0.0
    grit_drive: float = 0.0
    pitch_shift_st: float = 0.0
    luyen_lay_curve: str = "NONE"
    tail_stretch: float = 1.0
    syllable_profiles: List[SyllableFilterProfile] = field(default_factory=list)
    pickup_fast_syl_indices: List[int] = field(default_factory=list)
    mid_elongate_syl_indices: List[int] = field(default_factory=list)
    focal_stress_syl_indices: List[int] = field(default_factory=list)
    contrast_high_syl_indices: List[int] = field(default_factory=list)
    contrast_low_syl_indices: List[int] = field(default_factory=list)
    idiom_rhythm_syl_indices: List[int] = field(default_factory=list)
    intra_pauses_map: Dict[int, int] = field(default_factory=dict)
    intra_pause_after_syl: Optional[int] = None
    has_detached_particle_a: bool = False
    pre_particle_pause_ms: int = 0
    particle_a_syl_indices: List[int] = field(default_factory=list)
    coda_type: str = "OPEN_VOWEL"
    staccato_tail: bool = False
    soft_consonant_attack: bool = True
    enable_velvet_breath_tail: bool = True
    is_comma_end: bool = False
    is_ellipsis_end: bool = False
    is_sentence_end: bool = False
    is_question_end: bool = False
    is_exclamation_end: bool = False
    pause_after_ms: int = 380
    applied_rules: List[str] = field(default_factory=list)


# ==============================================================================
# PHẦN 3: BỘ LÀM SẠCH VĂN BẢN, PHÂN TÁCH THOẠI VS KỂ & CẢM XÚC 2 CHIỀU (V8.1)
# ==============================================================================
class ChapterTextSanitizerV8:
    """
    BỘ LÀM SẠCH VĂN BẢN TRUYỆN CONVERT CHUYÊN SÂU:
    - Xóa sạch khoảng trắng kép sau dấu phẩy (",  " -> ", ").
    - Chuẩn hóa mọi dấu gạch ngang đầu dòng về "- " để không sót bất kỳ đoạn thoại nào.
    - Chuẩn hóa các cặp dấu ngoặc kép dị biệt về “...”.
    """

    @staticmethod
    def sanitize_chapter(raw_text: str) -> str:
        if not raw_text:
            return ""

        # 1. Chuẩn hóa Unicode dựng sẵn NFC
        text = unicodedata.normalize("NFC", raw_text)

        # 2. Xóa các ký tự ẩn (Zero-width space, BOM, soft hyphen)
        text = re.sub(r"[\u200B-\u200D\uFEFF\u00AD]", "", text)

        # 3. Chuẩn hóa xuống dòng về \n
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # 4. Biến mọi khoảng trắng dị biệt trên cùng 1 dòng (\u3000, \u00A0, tab) thành dấu cách thường
        text = re.sub(r"[^\S\n]+", " ", text)

        # 5. Chuẩn hóa mọi biến thể dấu gạch đầu dòng thoại (-, –, —, ―, −, •) thành "- "
        text = re.sub(r"(?m)^\s*[-–—―‒−•]+\s*", "- ", text)

        # 6. Chuẩn hóa các loại ngoặc kép tiếng Trung/Pháp về “...”
        text = text.replace("『", "“").replace("』", "”").replace("«", "“").replace("»", "”")

        # 7. Xóa khoảng trắng thừa đứng TRƯỚC dấu câu ("hắn , nói" -> "hắn, nói")
        text = re.sub(r" +([,.;:!?\)\]”’])", r"\1", text)

        # 8. Gộp dấu phẩy lặp và dấu chấm lửng lỗi
        text = re.sub(r",{2,}", ",", text)
        text = re.sub(r"\.{2,}|…+", "...", text)

        # 9. Ép sau dấu [, ; : ! ?] chỉ có đúng 1 dấu cách duy nhất
        text = re.sub(r"([,;:])\s*", r"\1 ", text)
        text = re.sub(r" {2,}", " ", text)

        # 10. Chuẩn hóa từ cảm thán convert
        text = re.sub(r"\b(?:ah|a{2,}|a~)(?=[,.;:!?…”’)\s]|$)", "a", text, flags=re.IGNORECASE)
        text = re.sub(r"\bưm\b", "ừm", text, flags=re.IGNORECASE)
        text = re.sub(r"\blô giáo quan\b", "Lô giáo quan", text)

        return text.strip()


class BiDirectionalDialogueEmotionEngine:
    """
    CẦU NỐI CẢM XÚC 2 CHIỀU CHO LỜI THOẠI:
    1. Trích xuất cảm xúc từ Câu dẫn (`NARRATION`) đứng ngay trước hoặc ngay sau câu thoại.
    2. Phân tích trực tiếp nội dung từng vế câu thoại (`DIALOGUE`) để tìm cảm xúc nội tại.
    3. Truyền trực tiếp nhãn cảm xúc (`effort_mode`) sang `VietnameseProsodyPlanner`.
    """

    def __init__(self):
        # 1. Từ khóa cảm xúc nằm trong CÂU DẪN TRUYỆN (Narration Speech Tags)
        self.narration_tag_emotions: List[Tuple[str, re.Pattern]] = [
            ("SHOUT_ROAR", re.compile(
                r"\b(quát|quát lớn|quát lạnh|quát chói tai|hét|hét lớn|hét thảm|gầm|gầm lên|gầm thét|"
                r"gào|gào thét|rống|rống giận|mắng|mắng to|chửi|chửi ầm|nổi giận|giận dữ|"
                r"trợn mắt|đập bàn|nộ khí|điên cuồng)\b",
                re.IGNORECASE
            )),
            ("COLD_THREAT", re.compile(
                r"\b(lạnh lùng|lạnh nhạt|lạnh băng|lạnh lẽo|băng hàn|âm trầm|sát khí|sát ý|"
                r"hàn ý|nghiến răng|gằn từng chữ|hờ hững|vô tình|nhàn nhạt nói|trầm giọng cảnh cáo)\b",
                re.IGNORECASE
            )),
            ("MOCKING_GLEE", re.compile(
                r"\b(cười lạnh|cười nhạo|cười khẩy|cười đểu|cười ha hả|cười lớn|cười nhạt|"
                r"châm chọc|giễu cợt|mỉa mai|khinh thường|khinh bỉ|vẻ mặt đắc ý|cười híp mắt)\b",
                re.IGNORECASE
            )),
            ("PAIN_INJURED", re.compile(
                r"\b(thổ huyết|phun máu|phun ra một ngụm máu|trọng thương|thều thào|yếu ớt|"
                r"rên rỉ|sắc mặt trắng bệch|run rẩy|ôm ngực|đau đớn)\b",
                re.IGNORECASE
            )),
            ("URGENT_RUSH", re.compile(
                r"\b(hốt hoảng|hoảng hốt|vội vàng|vội vã|gấp gáp|sắc mặt đại biến|kinh hoàng hô)\b",
                re.IGNORECASE
            )),
            ("SURPRISE_SHOCK", re.compile(
                r"\b(kinh ngạc|kinh hãi|thất thanh|trợn tròn mắt|không dám tin|ngẩn người|"
                r"sững sờ|lắp bắp|hít một ngụm khí lạnh|biến sắc)\b",
                re.IGNORECASE
            )),
            ("SYMPATHY_SIGH", re.compile(
                r"\b(thở dài|cảm thán|lắc đầu|thương cảm|bất đắc dĩ|ngậm ngùi|chua xót|tiếc nuối)\b",
                re.IGNORECASE
            )),
            ("SOLEMN_DECREE", re.compile(
                r"\b(uy nghiêm|tuyên bố|phân phó|trầm giọng nói|giọng vang như chuông|hạ lệnh|ra lệnh)\b",
                re.IGNORECASE
            )),
            ("TENDER_RESPECT", re.compile(
                r"\b(cung kính|ôn nhu|dịu dàng|mỉm cười nói|khẽ nói|nhẹ giọng|cảm kích|hành lễ)\b",
                re.IGNORECASE
            )),
            ("CROWD_GOSSIP", re.compile(
                r"\b(nghị luận|bàn tán|xì xào|đám người|mọi người xung quanh|có người nói)\b",
                re.IGNORECASE
            )),
            ("QUESTION_RISE", re.compile(
                r"\b(nghi hoặc hỏi|tò mò hỏi|nhíu mày hỏi|truy vấn|hỏi vặn|thắc mắc)\b",
                re.IGNORECASE
            )),
        ]

        # 2. Từ khóa cảm xúc nằm NGAY BÊN TRONG NỘI DUNG LỜI THOẠI (Intrinsic Dialogue Cues)
        self.intrinsic_dialogue_emotions: List[Tuple[str, re.Pattern, float]] = [
            ("SHOUT_ROAR", re.compile(
                r"\b(cút|cút ngay|muốn chết|tìm cái chết|nộp mạng|to gan|làm càn|láo xược|"
                r"khốn kiếp|súc sinh|phế vật|câm miệng|ta giết ngươi|chết đi|chửi ầm lên|"
                r"đánh đập tàn nhẫn)\b",
                re.IGNORECASE
            ), 6.2),
            ("COLD_THREAT", re.compile(
                r"\b(thống hận|thấu xương|nhất định sẽ không tha|không tha hắn|"
                r"chết không có chỗ chôn|tự tìm đường chết|đừng trách ta|diện bích suy nghĩ|"
                r"xử phạt chấm dứt|trục xuất)\b",
                re.IGNORECASE
            ), 5.9),
            ("MOCKING_GLEE", re.compile(
                r"\b(báo ứng a|ngày hôm nay a|ha ha|hắc hắc|đáng đời|thật sự là báo ứng|"
                r"không biết tự lượng sức|chỉ bằng ngươi|thật nực cười|hung hăng càn quấy)\b",
                re.IGNORECASE
            ), 5.8),
            ("SURPRISE_SHOCK", re.compile(
                r"\b(vậy mà|thế mà|không ngờ rằng|không ngờ|chẳng ngờ|ai ngờ|"
                r"làm sao có thể|cái gì\?!|thiếu chút nữa|ngay cả|tự mình trách phạt|"
                r"chuyện trực tiếp náo đến)\b",
                re.IGNORECASE
            ), 5.5),
            ("URGENT_RUSH", re.compile(
                r"\b(mau chạy|nguy rồi|không xong rồi|mau dừng tay|cẩn thận|nhanh lên|không kịp nữa)\b",
                re.IGNORECASE
            ), 5.7),
            ("PAIN_INJURED", re.compile(
                r"\b(phốc|khụ khụ|đau quá|ta không cam lòng|ngươi\.\.\. ngươi)\b",
                re.IGNORECASE
            ), 5.6),
            ("SYMPATHY_SIGH", re.compile(
                r"\b(cũng xui xẻo|bị liên quan|đáng tiếc|haiz|biết làm sao được|đành chịu|xui xẻo)\b",
                re.IGNORECASE
            ), 5.4),
            ("CROWD_GOSSIP", re.compile(
                r"\b(nghe nói|ngươi buổi sáng không tới|cho nên không biết|lật ngược phải trái|"
                r"châm ngòi|đúng vậy a|chậc chậc)\b",
                re.IGNORECASE
            ), 5.0),
            ("SOLEMN_DECREE", re.compile(
                r"\b(truyền lệnh|nghe lệnh|bản tọa|bản tông chủ|miễn lễ|quỳ xuống)\b",
                re.IGNORECASE
            ), 5.1),
            ("TENDER_RESPECT", re.compile(
                r"\b(đa tạ|bái kiến|tuân mệnh|xin chỉ giáo|khiến mình vui|hãy cứ làm)\b",
                re.IGNORECASE
            ), 4.9),
        ]

    def extract_emotion_from_narration_tag(self, narration_text: str, look_tail: bool = True) -> Optional[str]:
        """Quét 16 từ cuối của câu dẫn trước (hoặc 16 từ đầu của câu dẫn sau) để hút cảm xúc."""
        if not narration_text:
            return None
        words = narration_text.strip().split()
        snippet = " ".join(words[-16:]) if look_tail else " ".join(words[:16])

        for mode, pattern in self.narration_tag_emotions:
            if pattern.search(snippet):
                return mode
        return None

    def resolve_dialogue_clause_emotion(
        self,
        clause_text: str,
        full_dialogue_text: str,
        inherited_emotion: Optional[str] = None
    ) -> Tuple[str, float]:
        """
        Xác định cảm xúc chính xác cho từng cụm hơi thở bên trong Lời Thoại:
        - Ưu tiên 1: Cảm xúc bùng phát trực tiếp ngay tại vế thoại hiện tại.
        - Ưu tiên 2: Cảm xúc kế thừa từ Câu dẫn (`inherited_emotion`).
        - Ưu tiên 3: Cảm xúc lan tỏa từ toàn bộ câu thoại.
        - Ưu tiên 4: Mặc định `DIALOGUE_LIVELY_NORM` (Giọng thoại nhân vật sinh động).
        """
        clean = clause_text.strip()
        is_question = clean.endswith("?") or bool(
            re.search(r"\b(không phải\s+.*\s+sao|chuyện gì xảy ra|tại sao|vì sao|thật ư|hả)\b", clean, re.IGNORECASE)
        )
        is_exclaim = clean.endswith("!")

        best_mode = None
        best_score = 0.0

        for mode, pattern, weight in self.intrinsic_dialogue_emotions:
            if pattern.search(clean):
                if weight > best_score:
                    best_score = weight
                    best_mode = mode

        if is_question and best_score < 5.6:
            return "QUESTION_RISE", 0.95

        if best_mode is not None:
            return best_mode, min(1.0, best_score / 6.0)

        if is_exclaim:
            mode_out = inherited_emotion if inherited_emotion in ("COLD_THREAT", "MOCKING_GLEE", "URGENT_RUSH") else "SHOUT_ROAR"
            return mode_out, 0.95

        if inherited_emotion:
            return inherited_emotion, 0.92

        for mode, pattern, weight in self.intrinsic_dialogue_emotions:
            if pattern.search(full_dialogue_text):
                return mode, 0.85

        return "DIALOGUE_LIVELY_NORM", 0.90


class DialogueNarrationClassifierV8:
    """
    BỘ PHÂN TÁCH LỜI THOẠI (`DIALOGUE`) VS LỜI DẪN TRUYỆN (`NARRATION`) CẤP ĐỘ ĐOẠN VĂN:
    - Khóa cứng toàn bộ đoạn bắt đầu bằng `- ` là DIALOGUE (không bao giờ đứt nửa chừng).
    - Phân giải ngoặc kép thật vs từ nhấn mạnh trong lời kể ("Thối Thể Đan", "Phế vật").
    - Bắt chính xác đoạn thoại mất dấu `-` hoặc bị cắt qua trang mới.
    """

    def __init__(self, emotion_engine: Optional[BiDirectionalDialogueEmotionEngine] = None):
        self.emotion_engine = emotion_engine or BiDirectionalDialogueEmotionEngine()

        self.speech_verbs_re = re.compile(
            r"\b(nói|mở miệng|lên tiếng|hỏi|đáp|trả lời|quát|hét|gầm|gào|rống|mắng|chửi|"
            r"cười|hừ|thở dài|thầm nghĩ|nghĩ thầm|truyền âm|phân phó|ra lệnh|hạ lệnh|"
            r"trầm giọng|lạnh nhạt|lạnh lùng|thản nhiên|tiếp lời|bổ sung|cảm thán|thốt lên|"
            r"kêu lên|hô lớn|lẩm bẩm|thì thào|nhíu mày)\b",
            re.IGNORECASE
        )

        self.non_dialogue_quote_prefix_re = re.compile(
            r"\b(hai chữ|ba chữ|bốn chữ|một chữ|chữ|cái gọi là|gọi là|danh xưng|danh hiệu|"
            r"ngoại hiệu|chiêu|một chiêu|công pháp|võ kỹ|bí tịch|đan dược|bảo vật|"
            r"cảnh giới|khái niệm|quy tắc|bảng hiệu|tấm biển)\s*$",
            re.IGNORECASE
        )

        self.direct_dialogue_markers_re = re.compile(
            r"\b(ta|ngươi|chúng ta|các ngươi|bản công tử|bản thiếu|bản cô nương|bản tọa|"
            r"bản tôn|lão tử|tại hạ|tiểu đệ|ngu huynh|sư huynh|sư tỷ|sư phụ|tiền bối|"
            r"cút|muốn chết|tìm cái chết|báo ứng a|ngày hôm nay a|đúng vậy a|ha ha|hắc hắc|"
            r"không phải\s+.*\s+sao|chuyện gì xảy ra)\b",
            re.IGNORECASE
        )

        self.strong_conversational_pronouns_re = re.compile(
            r"\b(chúng ta|các ngươi|ngươi|bản công tử|bản thiếu|bản cô nương|bản tọa|"
            r"lão tử|tại hạ|ngươi buổi sáng)\b",
            re.IGNORECASE
        )
        self.conversational_questions_re = re.compile(
            r"(không phải\s+.*\s+sao\?|chuyện gì xảy ra\?|vậy mà khiến\s+.*\s+trách phạt\?|"
            r"làm sao có thể\?|ngươi nói cái gì\?)",
            re.IGNORECASE
        )
        self.gossip_or_exclaim_openers_re = re.compile(
            r"^(nghe nói|ngươi buổi sáng|bất quá\s+[A-ZÀ-Ỹ]|lưu lực kia lúc trước|"
            r"đúng vậy|chậc chậc|haiz|hừ\s*,|khoan đã)\b",
            re.IGNORECASE
        )
        self.third_person_narration_guard_re = re.compile(
            r"\b(chỉ thấy|nhìn thấy|trong lòng hắn|trong mắt nàng|ánh mắt hắn|bước ra một bước|"
            r"hít sâu một hơi|thời gian trôi qua|không bao lâu sau|xoay người rời đi)\b",
            re.IGNORECASE
        )

    def _is_true_narrator_tag(self, segment: str) -> bool:
        clean = segment.strip()
        if not clean:
            return False
        words = clean.split()
        if len(words) > 22:
            return False
        if re.search(r"\b(chúng ta|các ngươi|bản công tử|bản tọa|lão tử)\b", clean, re.IGNORECASE):
            return False
        return bool(self.speech_verbs_re.search(clean))

    def _parse_dash_dialogue_paragraph(self, para_idx: int, para_text: str) -> List[TextRoleSpan]:
        body = re.sub(r"^-\s*", "", para_text.strip())
        if not body:
            return []

        parts = re.split(r"\s+[-–—]\s+", body)
        if len(parts) == 1:
            return [
                TextRoleSpan(
                    paragraph_index=para_idx,
                    role="DIALOGUE",
                    voice_id=VOICE_DIALOGUE_ID,
                    text=body,
                    inherited_emotion=None,
                    detection_reason="LOCKED_FULL_DASH_PARAGRAPH"
                )
            ]

        spans: List[TextRoleSpan] = []
        extracted_tag_emotion: Optional[str] = None

        for p_idx, part in enumerate(parts):
            clean_p = part.strip()
            if not clean_p:
                continue
            if p_idx > 0 and self._is_true_narrator_tag(clean_p):
                tag_emo = self.emotion_engine.extract_emotion_from_narration_tag(clean_p, look_tail=False)
                if tag_emo:
                    extracted_tag_emotion = tag_emo
                spans.append(
                    TextRoleSpan(
                        paragraph_index=para_idx,
                        role="NARRATION",
                        voice_id=VOICE_NARRATOR_ID,
                        text=clean_p,
                        detection_reason="INLINE_NARRATOR_SPEECH_TAG"
                    )
                )
            else:
                spans.append(
                    TextRoleSpan(
                        paragraph_index=para_idx,
                        role="DIALOGUE",
                        voice_id=VOICE_DIALOGUE_ID,
                        text=clean_p,
                        detection_reason="LOCKED_DASH_DIALOGUE_SEGMENT"
                    )
                )

        if extracted_tag_emotion:
            for sp in spans:
                if sp.role == "DIALOGUE":
                    sp.inherited_emotion = extracted_tag_emotion
                    sp.inherited_confidence = 0.95

        return spans

    def _is_real_spoken_quote(self, quoted_content: str, prefix_context: str) -> bool:
        clean_q = quoted_content.strip()
        if not clean_q:
            return False

        prefix_clean = prefix_context.strip()
        if self.non_dialogue_quote_prefix_re.search(prefix_clean):
            return False

        tail_prefix = " ".join(prefix_clean.split()[-8:])
        if prefix_clean.endswith(":") or self.speech_verbs_re.search(tail_prefix):
            return True

        words = re.findall(r"[A-Za-zÀ-ỹà-ỹ0-9]+", clean_q)
        word_count = len(words)

        if any(p in clean_q for p in ("?", "!", "...")) or self.direct_dialogue_markers_re.search(clean_q):
            return True

        if word_count >= 5 or "," in clean_q:
            return True

        return False

    def _parse_quoted_or_mixed_paragraph(self, para_idx: int, para_text: str) -> List[TextRoleSpan]:
        norm_text = para_text
        if '"' in norm_text:
            out_chars = []
            open_state = False
            for ch in norm_text:
                if ch == '"':
                    out_chars.append("“" if not open_state else "”")
                    open_state = not open_state
                else:
                    out_chars.append(ch)
            if open_state:
                out_chars.append("”")
            norm_text = "".join(out_chars)
        elif "“" in norm_text and "”" not in norm_text:
            norm_text = norm_text + "”"

        pattern = re.compile(r"“([^”]+)”")
        matches = list(pattern.finditer(norm_text))
        if not matches:
            return []

        spans: List[TextRoleSpan] = []
        cursor = 0

        for m in matches:
            q_start, q_end = m.span()
            quoted_str = m.group(1).strip()
            prefix_str = norm_text[cursor:q_start]

            if self._is_real_spoken_quote(quoted_str, prefix_str):
                if prefix_str.strip():
                    spans.append(
                        TextRoleSpan(
                            paragraph_index=para_idx,
                            role="NARRATION",
                            voice_id=VOICE_NARRATOR_ID,
                            text=prefix_str.strip(),
                            detection_reason="NARRATION_BEFORE_QUOTE"
                        )
                    )
                pre_emo = self.emotion_engine.extract_emotion_from_narration_tag(prefix_str, look_tail=True)
                spans.append(
                    TextRoleSpan(
                        paragraph_index=para_idx,
                        role="DIALOGUE",
                        voice_id=VOICE_DIALOGUE_ID,
                        text=quoted_str,
                        inherited_emotion=pre_emo,
                        inherited_confidence=0.95 if pre_emo else 0.0,
                        detection_reason="VERIFIED_SPOKEN_QUOTE"
                    )
                )
                cursor = q_end

        tail_str = norm_text[cursor:].strip()
        if tail_str:
            if not spans:
                return []
            spans.append(
                TextRoleSpan(
                    paragraph_index=para_idx,
                    role="NARRATION",
                    voice_id=VOICE_NARRATOR_ID,
                    text=tail_str,
                    detection_reason="NARRATION_AFTER_QUOTE"
                )
            )
            post_emo = self.emotion_engine.extract_emotion_from_narration_tag(tail_str, look_tail=False)
            if post_emo and len(spans) >= 2 and spans[-2].role == "DIALOGUE" and not spans[-2].inherited_emotion:
                spans[-2].inherited_emotion = post_emo
                spans[-2].inherited_confidence = 0.90

        return spans

    def _score_unmarked_conversational_pragmatics(
        self,
        para_text: str,
        next_para_is_dash: bool
    ) -> Tuple[bool, str]:
        clean = para_text.strip()
        if not clean:
            return False, "EMPTY"

        score = 0.0
        reasons: List[str] = []

        if re.match(r"^[a-zà-ỹ]", clean):
            score += 3.5
            reasons.append("LOWERCASE_PAGE_CONTINUATION")
            if next_para_is_dash:
                score += 2.5
                reasons.append("FOLLOWED_BY_DASH_CHAIN")

        if self.strong_conversational_pronouns_re.search(clean):
            score += 4.5
            reasons.append("DIRECT_CONVERSATIONAL_PRONOUN")

        if self.conversational_questions_re.search(clean):
            score += 3.8
            reasons.append("CONVERSATIONAL_QUESTION_PATTERN")

        if self.gossip_or_exclaim_openers_re.search(clean):
            score += 4.0
            reasons.append("GOSSIP_OR_EXCLAIM_OPENER")

        if re.search(r"\b(báo ứng a|hôm nay a|đúng vậy a|ha ha|hắc hắc)[.!?…]*$", clean, re.IGNORECASE):
            score += 3.5
            reasons.append("SPOKEN_FINAL_PARTICLE")

        if self.third_person_narration_guard_re.search(clean) and not self.strong_conversational_pronouns_re.search(clean):
            score -= 6.0
            reasons.append("THIRD_PERSON_NARRATION_SHIELD")

        is_dialogue = (score >= 4.0)
        return is_dialogue, "+".join(reasons) if reasons else "DEFAULT_NARRATION"

    def classify_chapter_into_role_spans(self, raw_chapter_text: str) -> List[TextRoleSpan]:
        clean_chapter = ChapterTextSanitizerV8.sanitize_chapter(raw_chapter_text)
        if not clean_chapter:
            return []

        raw_paragraphs = [p.strip() for p in clean_chapter.split("\n") if p.strip()]
        total_paras = len(raw_paragraphs)
        all_spans: List[TextRoleSpan] = []

        for idx, para in enumerate(raw_paragraphs):
            next_is_dash = (idx + 1 < total_paras) and raw_paragraphs[idx + 1].startswith("- ")

            if para.startswith("- "):
                dash_spans = self._parse_dash_dialogue_paragraph(idx, para)
                if all_spans and all_spans[-1].role == "NARRATION":
                    prev_narr_emo = self.emotion_engine.extract_emotion_from_narration_tag(
                        all_spans[-1].text, look_tail=True
                    )
                    if prev_narr_emo:
                        for dsp in dash_spans:
                            if dsp.role == "DIALOGUE" and not dsp.inherited_emotion:
                                dsp.inherited_emotion = prev_narr_emo
                                dsp.inherited_confidence = 0.95
                all_spans.extend(dash_spans)
                continue

            if ("“" in para and "”" in para) or ('"' in para):
                quoted_spans = self._parse_quoted_or_mixed_paragraph(idx, para)
                if quoted_spans:
                    all_spans.extend(quoted_spans)
                    continue

            is_unmarked_dlg, reason = self._score_unmarked_conversational_pragmatics(para, next_is_dash)
            if is_unmarked_dlg:
                inherited_emo = None
                if all_spans and all_spans[-1].role == "NARRATION":
                    inherited_emo = self.emotion_engine.extract_emotion_from_narration_tag(
                        all_spans[-1].text, look_tail=True
                    )
                all_spans.append(
                    TextRoleSpan(
                        paragraph_index=idx,
                        role="DIALOGUE",
                        voice_id=VOICE_DIALOGUE_ID,
                        text=para,
                        inherited_emotion=inherited_emo,
                        inherited_confidence=0.90 if inherited_emo else 0.0,
                        detection_reason=f"PRAGMATIC_DIALOGUE({reason})"
                    )
                )
            else:
                all_spans.append(
                    TextRoleSpan(
                        paragraph_index=idx,
                        role="NARRATION",
                        voice_id=VOICE_NARRATOR_ID,
                        text=para,
                        detection_reason="STANDARD_NARRATION"
                    )
                )

        return all_spans


# ==============================================================================
# PHẦN 4: HỆ THỐNG 7 TẦNG BỘ LỌC NGỮ PHÁP, ÂM VỊ HỌC & KỊCH BẢN NGỮ ĐIỆU (V7.1)
# ==============================================================================
class VietnamesePhonologyHelper:
    """
    Bộ phân tích âm vị học, nhận diện 6 thanh điệu tiếng Việt, điều hòa biến âm thanh điệu liền kề (Tone Sandhi).
    """

    STOP_CODA_RE = re.compile(r"(p|t|c|ch)[.!?…,;:\"'”’)\]]*$", re.IGNORECASE)
    NASAL_CODA_RE = re.compile(r"(m|n|ng|nh)[.!?…,;:\"'”’)\]]*$", re.IGNORECASE)
    GLIDE_CODA_RE = re.compile(
        r"(ao|au|ay|ây|eo|êu|iu|ia|ua|ưa|oi|ôi|ơi|ui|ưi|uôi|ươi|iêu|yêu|oai|oay|uây)[.!?…,;:\"'”’)\]]*$",
        re.IGNORECASE
    )

    TONE_SAC_CHARS = set("áắấéếíóốớúứýÁẮẤÉẾÍÓỐỚÚỨÝ")
    TONE_HUYEN_CHARS = set("àằầèềìòồờùừỳÀẰẦÈỀÌÒỒỜÙỪỲ")
    TONE_HOI_CHARS = set("ảẳẩẻểỉỏổởủửỷẢẲẨẺỂỈỎỔỞỦỬỶ")
    TONE_NGA_CHARS = set("ãẵẫẽễĩõỗỡũữỹÃẴẪẼỄĨÕỖỠŨỮỸ")
    TONE_NANG_CHARS = set("ạặậẹệịọộợụựỵẠẶẬẸỆỊỌỘỢỤỰỴ")

    TONE_F0_SCALE_MAP: Dict[str, float] = {
        "NGANG": 0.76,
        "HUYEN": 1.08,
        "SAC": 1.12,
        "HOI": 0.96,
        "NGA": 0.84,
        "NANG": 1.06,
    }

    ALPHABET_A_PREFIXES = {"hạng", "loại", "khu", "nhóm", "bảng", "cấp", "phòng", "vitamin", "điểm", "toà", "tòa"}

    @classmethod
    def detect_vietnamese_tone(cls, word: str) -> str:
        for ch in word:
            if ch in cls.TONE_SAC_CHARS:
                return "SAC"
            if ch in cls.TONE_HUYEN_CHARS:
                return "HUYEN"
            if ch in cls.TONE_HOI_CHARS:
                return "HOI"
            if ch in cls.TONE_NGA_CHARS:
                return "NGA"
            if ch in cls.TONE_NANG_CHARS:
                return "NANG"
        return "NGANG"

    @classmethod
    def get_tone_safe_f0_scale(cls, word: str) -> float:
        tone = cls.detect_vietnamese_tone(word)
        return cls.TONE_F0_SCALE_MAP.get(tone, 0.85)

    @classmethod
    def normalize_xianxia_particles(cls, text: str) -> str:
        return re.sub(r"\b(?:ah|a{2,}|a~)(?=[,.;:!?…”’)\s]|$)", "a", text, flags=re.IGNORECASE)

    @classmethod
    def is_exclamatory_particle_a(cls, words: List[str], index: int) -> bool:
        if index < 2 or index >= len(words):
            return False
        w = words[index]
        if w.lower() not in ("a", "nha", "à", "ạ"):
            return False
        if w == "A" and words[index - 1].lower() in cls.ALPHABET_A_PREFIXES:
            return False
        return True

    @classmethod
    def classify_syllable_coda(cls, word: str) -> str:
        clean = word.strip()
        if not clean:
            return "OPEN_VOWEL"
        if cls.STOP_CODA_RE.search(clean):
            return "STOP_CODA"
        if cls.NASAL_CODA_RE.search(clean):
            return "NASAL_SONORANT"
        if cls.GLIDE_CODA_RE.search(clean):
            return "GLIDE_DIPHTHONG"
        return "OPEN_VOWEL"

    @classmethod
    def can_elongate_word(cls, word: str) -> bool:
        return cls.classify_syllable_coda(word) != "STOP_CODA"

    @classmethod
    def max_safe_stretch_for_coda(cls, coda_type: str) -> float:
        if coda_type == "STOP_CODA":
            return 0.94
        if coda_type == "GLIDE_DIPHTHONG":
            return 1.85
        if coda_type == "NASAL_SONORANT":
            return 2.05
        return 2.15

    @classmethod
    def extract_words(cls, text: str) -> List[str]:
        return re.findall(r"[A-Za-zÀ-ỹà-ỹ0-9]+", text)

    @classmethod
    def compute_tone_sandhi_scales(cls, tones: List[str]) -> Tuple[List[float], List[float]]:
        n = len(tones)
        sandhi_scales = [cls.TONE_F0_SCALE_MAP.get(t, 0.85) for t in tones]
        declination_offsets = [0.0] * n

        ngang_streak = 0
        for i, t in enumerate(tones):
            if t in ("HOI", "NGA") and i + 1 < n and tones[i + 1] in ("HOI", "NGA"):
                sandhi_scales[i] *= 0.68
                sandhi_scales[i + 1] *= 1.06

            if t == "SAC" and i + 1 < n and tones[i + 1] in ("HUYEN", "NANG"):
                sandhi_scales[i] *= 0.88

            if t == "NGANG":
                ngang_streak += 1
                if ngang_streak >= 2:
                    declination_offsets[i] = -0.14 * min(3, ngang_streak - 1)
            else:
                ngang_streak = 0

        return sandhi_scales, declination_offsets


class ContextualSyntacticFilterBank:
    """
    HỆ THỐNG BỘ LỌC NGỮ PHÁP & NGỮ NGHĨA ĐA TẦNG (Phân giải từ đa nghĩa & 16 Khóa Cú Pháp Cấm Ngắt).
    """

    PRE_VERBAL_AUXILIARIES: Set[str] = {
        "đã", "đang", "sẽ", "vừa", "mới", "sắp", "từng", "vẫn", "còn", "cứ", "luôn",
        "không", "chẳng", "chưa", "chả", "đừng", "chớ", "hãy", "nên", "phải", "cần",
        "muốn", "dám", "định", "bị", "được", "cũng", "đều", "lại", "liền", "chỉ"
    }

    QUANTIFIERS_AND_CLASSIFIERS: Set[str] = {
        "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín", "mười", "vài",
        "những", "các", "mỗi", "mọi", "từng", "mấy", "bao", "bấy", "tấm", "bức", "miền",
        "nơi", "điều", "chuyện", "người", "kẻ", "tên", "gã", "vị", "đạo", "luồng", "tia",
        "cơn", "trận", "viên", "bình", "thanh", "chiếc", "cái", "con", "quyển", "cuốn"
    }

    PREPOSITIONS_AND_CONJUNCTIONS: Set[str] = {
        "của", "cho", "với", "tại", "ở", "vào", "trong", "giữa", "trên", "dưới", "ngoài",
        "từ", "về", "vì", "bởi", "do", "để", "mà", "như", "cùng", "và", "hay", "hoặc",
        "nhưng", "nếu", "khi", "lúc", "nơi"
    }

    VERBS_BEFORE_RESULTATIVE: Set[str] = {
        "quay", "đứng", "thu", "bé", "nhỏ", "dừng", "giữ", "nhớ", "nhìn", "ngẫm", "nghĩ",
        "khép", "đóng", "gom", "ngồi", "nằm", "lắng", "chùng", "hạ", "buông", "rơi",
        "trôi", "bay", "chạy", "bước", "kéo", "đẩy", "ném", "vứt", "xảy", "nhận", "hiện",
        "vang", "chửi", "gầm", "hét", "quát", "cười", "khóc", "thở"
    }

    INTENSIFIER_WORDS: Set[str] = {
        "rất", "quá", "lắm", "hơi", "khá", "thật", "cực", "vô", "hết", "đặc", "hoàn", "triệt"
    }

    PURE_PICKUP_WORDS: Set[str] = {
        "chúng", "sẽ", "nếu", "thì", "đừng", "khi", "rồi", "cũng", "trong", "vài",
        "giữa", "những", "để", "cho", "nên", "bởi", "vì", "của", "và", "nhưng",
        "mà", "hoặc", "là", "đã", "đang", "vừa", "vẫn", "từ", "với", "tại", "ở",
        "như", "các", "mọi", "một"
    }

    @classmethod
    def disambiguate_word_role(cls, lower_words: List[str], idx: int) -> str:
        n = len(lower_words)
        w = lower_words[idx]
        prev_w = lower_words[idx - 1] if idx > 0 else ""
        prev2_w = lower_words[idx - 2] if idx > 1 else ""
        next_w = lower_words[idx + 1] if idx + 1 < n else ""

        if w == "lại":
            if prev_w in cls.VERBS_BEFORE_RESULTATIVE or (prev2_w in cls.VERBS_BEFORE_RESULTATIVE and prev_w in ("bé", "nhỏ", "hẹp", "ngắn", "chậm")):
                if next_w not in ("dám", "muốn", "có", "là", "bị", "được", "không", "chẳng", "đi"):
                    return "RESULTATIVE_PARTICLE"
            if idx == n - 1:
                return "RESULTATIVE_PARTICLE"
            return "PICKUP_FUNCTION"

        if w == "yên":
            if prev_w in ("nằm", "đứng", "ngồi", "bình", "an", "lặng"):
                return "RESULTATIVE_PARTICLE" if idx < n - 1 else "EMOTIONAL_ANCHOR"

        if w in ("đến", "tới"):
            if next_w in ("khi", "lúc", "mức", "nỗi", "chỗ", "nơi", "tận", "cùng", "đây", "đó"):
                return "PICKUP_FUNCTION"
            if prev_w in ("muốn", "chưa", "đã", "vừa", "sắp", "không", "chẳng", "đi", "tìm") or idx == n - 1:
                return "EMOTIONAL_ANCHOR"
            return "CONTENT_NORMAL"

        if w in ("ta", "mình", "hắn", "nàng"):
            if idx >= n - 2:
                return "EMOTIONAL_ANCHOR"
            if prev_w in ("chúng", "bọn") and next_w in cls.PRE_VERBAL_AUXILIARIES:
                return "PICKUP_FUNCTION"
            return "CONTENT_NORMAL"

        if w in ("có", "còn"):
            if prev_w in ("nếu", "dù", "vẫn", "chỉ", "mà", "cũng") and idx < n - 2:
                return "PICKUP_FUNCTION"
            if prev_w in ("không", "chẳng", "chưa"):
                return "EMOTIONAL_ANCHOR"
            return "CONTENT_NORMAL"

        if w in cls.INTENSIFIER_WORDS:
            return "INTENSIFIER"

        if w in cls.PURE_PICKUP_WORDS and idx < n - 1:
            return "PICKUP_FUNCTION"

        return "CONTENT_NORMAL"

    @classmethod
    def compute_no_split_locks(cls, lower_words: List[str]) -> List[bool]:
        n = len(lower_words)
        locks = [False] * n

        for i in range(n - 1):
            w = lower_words[i]
            next_w = lower_words[i + 1]
            role = cls.disambiguate_word_role(lower_words, i)

            if role == "RESULTATIVE_PARTICLE":
                locks[i] = False
                continue

            if w in cls.PRE_VERBAL_AUXILIARIES:
                locks[i] = True
            elif w in cls.QUANTIFIERS_AND_CLASSIFIERS:
                locks[i] = True
            elif w in cls.PREPOSITIONS_AND_CONJUNCTIONS:
                locks[i] = True
            elif (w, next_w) in {
                ("chúng", "ta"), ("chúng", "tôi"), ("bọn", "hắn"), ("bọn", "họ"),
                ("hôm", "nay"), ("hôm", "qua"), ("ngày", "mai"), ("bây", "giờ"), ("bao", "giờ"),
                ("thời", "gian"), ("tuổi", "trẻ"), ("thanh", "xuân"), ("cuộc", "đời"), ("năm", "tháng"),
                ("hoàn", "hảo"), ("ký", "ức"), ("ảnh", "cũ"), ("độ", "tuổi"), ("điều", "gì"),
                ("chuyện", "gì"), ("làm", "sao"), ("tại", "sao"), ("vì", "thế"), ("bất", "quá"),
                ("thậm", "chí"), ("hiện", "giờ"), ("kết", "quả"), ("không", "ngờ"), ("vậy", "mà"),
                ("thế", "mà"), ("giáo", "quan"), ("trưởng", "lão"), ("tông", "chủ"), ("thối", "thể"),
                ("luyện", "quán"), ("diện", "bích"), ("suy", "nghĩ"), ("thống", "hận"), ("thấu", "xương"),
                ("báo", "ứng"), ("xui", "xẻo"), ("chân", "tướng"), ("trục", "xuất"), ("trách", "phạt")
            }:
                locks[i] = True
            elif w in ("chờ", "đợi", "khiến", "làm", "tha", "giúp", "nhìn", "gọi") and next_w in ("chúng", "ta", "mình", "tôi", "hắn", "nàng", "ngươi"):
                locks[i] = True

        return locks


class VietnameseProsodyPlanner:
    """
    BỘ LẬP KỊCH BẢN NGỮ ĐIỆU 7 TẦNG (ĐỒNG BỘ 100% VỚI BỘ PHÂN VAI & CẢM XÚC THOẠI):
    - Tách câu thành các Nhịp Ý Ngắn 2–6 chữ chuẩn xác theo khóa cú pháp.
    - Nhận trực tiếp `role`, `voice_id`, `inherited_emotion` và `override_clause_emotion_fn`.
    - Tự động kích hoạt `dialogue_expressive_boost = 1.35x` trên từng chữ khi `role == "DIALOGUE"`.
    """

    def __init__(self):
        self.elongate_phrases = [
            "không bao giờ", "quay lại", "độ tuổi", "khiến mình vui", "hãy cứ làm",
            "muốn đến", "muốn thử", "mãi đợi", "hoàn hảo", "thời gian", "đứng lại",
            "chờ chúng ta", "hôm nay", "hôm qua", "tuổi trẻ", "thu bé lại", "ảnh cũ",
            "nằm yên", "miền ký ức", "ký ức", "thanh xuân", "cuộc đời", "năm tháng",
            "bình yên", "hoài niệm", "cô đơn", "lặng lẽ", "mỉm cười", "nhẹ nhàng",
            "dịu dàng", "ôn nhu", "lạnh lẽo", "mênh mông", "âm u", "thê lương",
            "xui xẻo", "chầm chậm", "lững thững", "từ từ", "rầm rầm", "ầm ầm",
            "hung hăng", "ngẩn ngơ", "mờ mịt", "xa xăm", "đằng đẵng", "hiu quạnh",
            "trống trải", "thấu xương", "ngút trời", "cực kỳ", "vô cùng", "triệt để",
            "hoàn toàn", "vạn phần", "cực điểm", "vô biên", "vô tận", "xương tủy",
            "vang vọng", "ngân dài", "thở dài", "trầm ngâm", "suy nghĩ", "chân tướng",
            "hai tháng", "báo ứng"
        ]

        self.contrastive_pairs = [
            ("hôm nay", "hôm qua"),
            ("muốn đến", "muốn thử"),
            ("lúc trước", "hôm nay"),
            ("lúc trước", "hiện giờ"),
            ("buổi sáng", "hiện giờ"),
            ("bắt đầu", "kết thúc"),
            ("còn sống", "đã chết"),
            ("thiên tài", "phế vật"),
            ("nụ cười", "nước mắt"),
            ("ánh sáng", "bóng tối"),
        ]

        self.four_word_idioms = [
            "lật ngược phải trái", "hung hăng càn quấy", "diện bích suy nghĩ",
            "không ai nhường ai", "đánh đập tàn nhẫn", "chết không nhắm mắt",
            "ngàn cân treo sợi", "long trời lở đất", "sát khí ngút trời",
            "vạn kiếp bất phục", "huyết lệ tuôn rơi", "bình yên vô sự"
        ]

        self.short_poetic_openers_re = re.compile(
            r"^(Vì thế|Bởi thế|Cho nên|Thật ra|Thực ra|Bất quá|Đáng tiếc|Huống chi|"
            r"Bởi thời gian|Ngày hôm nay|Ngày mai|Tuổi trẻ|Thanh xuân|Cuộc đời|Năm tháng|"
            r"Đêm hôm đó|Giờ khắc này|Một ngày kia|Có đôi khi|Nhưng đôi khi)\b",
            re.IGNORECASE
        )

        self.pre_climax_intensifiers = {
            "thật", "rất", "quá", "cực kỳ", "vô cùng", "những miền", "vài tấm", "chẳng", "mãi"
        }

        self.final_modal_re = re.compile(
            r"\b(a|à|ạ|nha|ơi|sao|ư|nhé|nhỉ|thôi|đây|chứ|hả|vậy|nữa|làm|qua|xưa|đâu)[.!?…,;:]*$",
            re.IGNORECASE
        )

        self.trailing_laugh_re = re.compile(
            r"^(ha ha|hắc hắc|ha hả|hì hì|khặc khặc|hừ hừ|chậc chậc|haiz|ôi chao)[.!?…]*$",
            re.IGNORECASE
        )

        self.soulful_contemplation_re = re.compile(
            r"\b(không bao giờ|độ tuổi|khiến mình vui|hãy cứ làm|muốn đến|muốn thử|"
            r"đừng mãi đợi|hoàn hảo|thời gian|chẳng đứng lại|ngày hôm nay|ngày hôm qua|"
            r"tuổi trẻ|thu bé lại|tấm ảnh cũ|nằm yên|miền ký ức|ký ức|năm tháng|cuộc đời|"
            r"thanh xuân|bình yên|hoài niệm|nhớ lại|chợt nhận ra|dịu dàng|lặng lẽ)\b",
            re.IGNORECASE
        )

        self.shout_roar_re = re.compile(
            r"\b(quát|quát lạnh|quát lớn|hét|hét lớn|gầm|gầm lên|gào|chửi ầm lên|"
            r"đánh đập tàn nhẫn|điên cuồng|cút|muốn chết|tìm cái chết|nộp mạng|"
            r"phanh thây|huyết tẩy|chém giết|trục xuất|to gan|láo xược)\b",
            re.IGNORECASE
        )

        self.cold_threat_re = re.compile(
            r"\b(thống hận|thấu xương|nhất định sẽ không tha|không tha hắn|"
            r"chết không có chỗ chôn|lạnh lùng|lạnh nhạt|âm trầm|sát khí|sát ý|"
            r"diện bích|xử phạt chấm dứt|hàn ý)\b",
            re.IGNORECASE
        )

        self.solemn_decree_re = re.compile(
            r"\b(tổng giáo quan|đại trưởng lão|thái thượng trưởng lão|tông chủ|pháp chỉ|"
            r"tuyên bố|đột phá|cảnh giới|thiên địa|uy áp|đại đạo|linh khí cuồn cuộn|"
            r"chân tướng|trách phạt|huấn luyện quán)\b",
            re.IGNORECASE
        )

        self.mysterious_suspense_re = re.compile(
            r"\b(đêm khuya|tĩnh mịch|bóng đen|thần thức|quỷ dị|"
            r"không một tiếng động|rốt cuộc là ai|cẩn thận|ẩn nấp|mờ ảo|hơi thở lạ)\b",
            re.IGNORECASE
        )

        self.urgent_rush_re = re.compile(
            r"\b(đột nhiên|bỗng nhiên|tức khắc|trong nháy mắt|liền trực tiếp|"
            r"lập tức|mau chạy|không kịp nữa|vọt tới|lao ra|cấp báo|nguy cấp)\b",
            re.IGNORECASE
        )

        self.pain_injured_re = re.compile(
            r"\b(phun máu|thổ huyết|trọng thương|sắc mặt trắng bệch|khí tức yếu ớt|"
            r"thều thào|nghiến răng|gượng dậy|đau đớn|rên rỉ|vết thương)\b",
            re.IGNORECASE
        )

        self.inner_monologue_re = re.compile(
            r"\b(thầm nghĩ|trong lòng hiểu rõ|truyền âm|ánh mắt lóe lên|"
            r"tính toán trong lòng|tự nhủ|nghĩ thầm|trong đầu hiện lên)\b",
            re.IGNORECASE
        )

        self.tender_respect_re = re.compile(
            r"\b(đa tạ|bái kiến|cung kính|ôn nhu|mỉm cười|khẽ nói|"
            r"ánh mắt dịu dàng|cảm kích|nhẹ giọng|an ủi|hãy cứ)\b",
            re.IGNORECASE
        )

        self.surprise_re = re.compile(
            r"\b(vậy mà|thế mà|không ngờ rằng|không ngờ|chẳng ngờ|ai ngờ|"
            r"thiếu chút nữa|ngay cả|lại dám|tự mình|chuyện gì xảy ra)\b",
            re.IGNORECASE
        )

        self.mocking_re = re.compile(
            r"\b(báo ứng a|ngày hôm nay a|ha ha|hắc hắc|đáng đời|thật sự là báo ứng|"
            r"cười lạnh|cười nhạo|không biết tự lượng sức)\b",
            re.IGNORECASE
        )

        self.sympathy_re = re.compile(
            r"\b(cũng xui xẻo|bị liên quan|đáng tiếc|thở dài|đành chịu|xui xẻo|bi thương)\b",
            re.IGNORECASE
        )

        self.crowd_gossip_re = re.compile(
            r"^[-–—―\s]*(nghe nói|ngươi buổi sáng không tới|lưu lực kia lúc trước|"
            r"bất quá lâm tiêu|đúng vậy a|chậc chậc)\b",
            re.IGNORECASE
        )

        self.focal_keywords = [
            "không bao giờ", "đúng độ tuổi", "vui", "hãy cứ làm", "muốn đến", "muốn thử",
            "mãi đợi", "hoàn hảo", "thời gian", "chẳng đứng lại", "hôm nay", "hôm qua",
            "tuổi trẻ", "thu bé lại", "ảnh cũ", "nằm yên", "ký ức", "vậy mà", "thế mà",
            "không ngờ", "tự mình", "trách phạt", "trục xuất", "thối thể đan",
            "huấn luyện quán", "lưu lỵ", "lâm tiêu", "lưu lực", "lô giáo quan",
            "tổng giáo quan", "thống hận", "thấu xương", "không tha", "chuyện gì",
            "tại sao", "báo ứng", "diện bích", "hai tháng", "chửi ầm"
        ]

    def _is_safe_split(self, left_text: str, right_text: str) -> bool:
        left_words = VietnamesePhonologyHelper.extract_words(left_text)
        right_words = VietnamesePhonologyHelper.extract_words(right_text)

        if not left_words or not right_words:
            return False

        combined_lower = [w.lower() for w in (left_words + right_words)]
        split_idx = len(left_words) - 1
        locks = ContextualSyntacticFilterBank.compute_no_split_locks(combined_lower)

        if locks[split_idx]:
            return False

        if self.short_poetic_openers_re.match(left_text.strip()) and len(left_words) >= 2:
            return True

        if self.trailing_laugh_re.match(right_text.strip()) and len(left_words) >= 3:
            return True

        if len(left_words) >= 3 and len(right_words) >= 3:
            return True

        return False

    def split_into_safe_breath_groups(self, sentence: str) -> List[str]:
        s = VietnamesePhonologyHelper.normalize_xianxia_particles(sentence.strip())
        if not s:
            return []

        s = re.sub(
            r"^(Bởi thời gian|Ngày hôm nay|Tuổi trẻ|Thanh xuân|Cuộc đời|Năm tháng)\s+(?=[a-zà-ỹ])",
            r"\1 | ",
            s,
            flags=re.IGNORECASE
        )

        s = re.sub(
            r"\b(Chúng ta sẽ không bao giờ|rồi cũng sẽ thu bé lại|thì đừng mãi đợi)\s+(?=[a-zà-ỹ])",
            r"\1 | ",
            s,
            flags=re.IGNORECASE
        )

        s = re.sub(
            r"\b([A-ZÀ-Ỹ][a-zà-ỹ]+\s+[A-ZÀ-Ỹ][a-zà-ỹ]+\s+(?:trợ lý giáo quan|tổng giáo quan|giáo quan|trưởng lão|tông chủ))\s+"
            r"(lần này|hiện giờ|đã|đang|sẽ|liền|lại|cũng|không|bị)\b",
            r"\1 | \2",
            s
        )
        s = re.sub(
            r"\b((?:tỷ tỷ|đại tỷ|muội muội|ca ca|đệ đệ|sư huynh|sư tỷ)\s+của\s+(?:hắn|nàng|ta|ngươi)\s+[A-ZÀ-Ỹ][a-zà-ỹ]+\s+[A-ZÀ-Ỹ][a-zà-ỹ]+)\s+"
            r"(không phải|chính là|vốn là|lại là)\b",
            r"\1 | \2",
            s,
            flags=re.IGNORECASE
        )

        raw_tokens = [
            t.strip()
            for t in re.split(r"(\||[?!]+(?=\s+[A-ZÀ-Ỹ])|,|;|:)", s)
            if t and t.strip()
        ]

        candidate_clauses: List[str] = []
        buf = ""
        for tok in raw_tokens:
            if re.fullmatch(r"(\||[?!]+|,|;|:)", tok):
                buf += " |" if tok == "|" else tok
                candidate_clauses.append(buf.strip())
                buf = ""
            else:
                buf = tok if not buf else (buf + " " + tok)
        if buf:
            candidate_clauses.append(buf.strip())

        merged_clauses: List[str] = []
        idx = 0
        while idx < len(candidate_clauses):
            curr = candidate_clauses[idx]
            clean_curr = curr.rstrip("|").strip()
            words_curr = VietnamesePhonologyHelper.extract_words(clean_curr)

            if clean_curr.endswith(",") and len(words_curr) >= 2 and self.short_poetic_openers_re.match(clean_curr):
                merged_clauses.append(curr)
                idx += 1
                continue

            if len(words_curr) < 2 and idx + 1 < len(candidate_clauses):
                next_clause = candidate_clauses[idx + 1]
                combined = clean_curr.rstrip(",") + " " + next_clause
                candidate_clauses[idx + 1] = combined.strip()
            elif curr.endswith("|") and idx + 1 < len(candidate_clauses):
                next_clean = candidate_clauses[idx + 1].rstrip("|").strip()
                if self._is_safe_split(clean_curr, next_clean):
                    merged_clauses.append(curr)
                else:
                    candidate_clauses[idx + 1] = (clean_curr + " " + candidate_clauses[idx + 1]).strip()
            else:
                merged_clauses.append(curr)
            idx += 1

        if len(merged_clauses) >= 2:
            last_clause_str = merged_clauses[-1].strip()
            last_words = VietnamesePhonologyHelper.extract_words(last_clause_str)
            if len(last_words) < 3 and not self.trailing_laugh_re.match(last_clause_str):
                prev = merged_clauses[-2].rstrip("|").strip()
                merged_clauses[-2] = prev + " " + merged_clauses[-1]
                merged_clauses.pop()

        return merged_clauses

    def _build_granular_syllable_profiles(
        self,
        words: List[str],
        full_sentence_lower: str,
        seg: ProsodicSegment
    ) -> None:
        lower_words = [w.lower() for w in words]
        n = len(lower_words)
        is_dlg = (seg.role == "DIALOGUE")
        dlg_f0_mult = 1.25 if is_dlg else 1.00

        tones = [VietnamesePhonologyHelper.detect_vietnamese_tone(w) for w in words]
        codas = [VietnamesePhonologyHelper.classify_syllable_coda(w) for w in words]
        no_split_locks = ContextualSyntacticFilterBank.compute_no_split_locks(lower_words)
        sandhi_scales, declination_offsets = VietnamesePhonologyHelper.compute_tone_sandhi_scales(tones)

        pickup_fast_indices: Set[int] = set()
        elongate_indices: Set[int] = set()
        focal_indices: Set[int] = set()
        contrast_high_indices: Set[int] = set()
        contrast_low_indices: Set[int] = set()
        idiom_indices: Set[int] = set()
        intra_pauses_map: Dict[int, int] = {}

        for phrase in self.elongate_phrases:
            p_tokens = phrase.split()
            p_len = len(p_tokens)
            for i in range(n - p_len + 1):
                if lower_words[i:i + p_len] == p_tokens:
                    target_idx = i + p_len - 1
                    if codas[target_idx] != "STOP_CODA":
                        elongate_indices.add(target_idx)
                    focal_indices.update(range(i, i + p_len))
                    if target_idx < n - 2 and n >= 5 and not no_split_locks[target_idx]:
                        intra_pauses_map[target_idx] = 140 if is_dlg else 165

        for kw in self.focal_keywords:
            kw_tokens = kw.split()
            k_len = len(kw_tokens)
            for i in range(n - k_len + 1):
                if lower_words[i:i + k_len] == kw_tokens:
                    focal_indices.update(range(i, i + k_len))

        for idiom in self.four_word_idioms:
            id_tokens = idiom.split()
            if len(id_tokens) == 4:
                for i in range(n - 3):
                    if lower_words[i:i + 4] == id_tokens:
                        idiom_indices.update([i + 1, i + 3])

        for high_p, low_p in self.contrastive_pairs:
            if high_p in full_sentence_lower and low_p in full_sentence_lower:
                h_tokens = high_p.split()
                l_tokens = low_p.split()
                for i in range(n - len(h_tokens) + 1):
                    if lower_words[i:i + len(h_tokens)] == h_tokens:
                        contrast_high_indices.update(range(i, i + len(h_tokens)))
                for i in range(n - len(l_tokens) + 1):
                    if lower_words[i:i + len(l_tokens)] == l_tokens:
                        contrast_low_indices.update(range(i, i + len(l_tokens)))

        roles: List[str] = []
        for i in range(n):
            role = ContextualSyntacticFilterBank.disambiguate_word_role(lower_words, i)
            if i in elongate_indices:
                role = "EMOTIONAL_ANCHOR"
            roles.append(role)

            if role == "RESULTATIVE_PARTICLE":
                if codas[i] != "STOP_CODA":
                    elongate_indices.add(i)
                focal_indices.add(i)
                if 0 < i < n - 2 and not no_split_locks[i]:
                    intra_pauses_map[i] = 140 if is_dlg else 165
            elif role == "PICKUP_FUNCTION" and i not in focal_indices and i not in elongate_indices and i < n - 1:
                pickup_fast_indices.add(i)

        if n >= 4:
            for i in range(1, n - 1):
                two_w = " ".join(lower_words[max(0, i - 1):i + 1])
                if lower_words[i] in self.pre_climax_intensifiers or two_w in self.pre_climax_intensifiers:
                    if i >= n - 3:
                        intra_pauses_map[i] = 120 if is_dlg else 135
                        if codas[i] != "STOP_CODA":
                            elongate_indices.add(i)

        profiles: List[SyllableFilterProfile] = []
        for i in range(n):
            is_last = (i == n - 1)
            is_penultimate = (i == n - 2)
            is_antepenultimate = (i == n - 3)
            is_pickup = (i in pickup_fast_indices) and not is_last
            is_mid_elongate = (i in elongate_indices) and not is_last
            is_focal = (i in focal_indices)
            is_c_high = (i in contrast_high_indices)
            is_c_low = (i in contrast_low_indices)
            pause_ms = intra_pauses_map.get(i, 0) if not is_last else 0

            if is_last:
                stretch = seg.tail_stretch
                exp_weight = 1.38 if codas[i] != "STOP_CODA" else 0.90
            elif is_mid_elongate and codas[i] != "STOP_CODA":
                stretch = 1.50 if seg.effort_mode == "SOULFUL_CONTEMPLATION" else 1.42
                exp_weight = 1.28
            elif pause_ms > 0 and codas[i] != "STOP_CODA":
                stretch = 1.32
                exp_weight = 1.18
            elif is_pickup:
                stretch = 0.84
                exp_weight = 0.78
            elif seg.effort_mode in ("SHOUT_ROAR", "URGENT_RUSH"):
                stretch = 0.92
                exp_weight = 0.88
            else:
                stretch = 1.0
                exp_weight = 1.00 if codas[i] != "STOP_CODA" else 0.84

            s_scale = sandhi_scales[i]
            decl_st = declination_offsets[i]
            if is_c_high:
                f0_off = +0.78 * s_scale * dlg_f0_mult
            elif is_c_low:
                f0_off = -1.48 * s_scale * dlg_f0_mult
            elif seg.is_sentence_end and not seg.has_detached_particle_a:
                if n >= 3 and is_antepenultimate:
                    f0_off = -0.65 * s_scale
                elif n >= 2 and is_penultimate:
                    f0_off = -1.30 * s_scale
                elif is_last:
                    f0_off = -2.05 * s_scale
                elif is_pickup:
                    f0_off = -0.28 * s_scale + decl_st
                else:
                    f0_off = (0.45 if (i % 2 == 1) else 0.20) * s_scale * dlg_f0_mult + decl_st
            elif seg.is_comma_end and is_last:
                f0_off = +0.34 * s_scale * dlg_f0_mult
            elif is_pickup:
                f0_off = -0.28 * s_scale + decl_st
            else:
                f0_off = (0.35 if (i % 2 == 1) else -0.12) * s_scale * dlg_f0_mult + decl_st

            focal_boost_val = 2.45 if is_dlg else 1.75
            if is_pickup:
                gain_off = -1.9
            else:
                iambic_db = (1.05 if is_dlg else 0.85) if (i % 2 == 1) else -0.55
                focal_db = focal_boost_val if is_focal else 0.0
                gain_off = iambic_db + focal_db

            if is_last and seg.has_detached_particle_a:
                gain_off = 0.6 if seg.effort_mode not in ("SYMPATHY_SIGH", "PAIN_INJURED", "SOULFUL_CONTEMPLATION") else -2.2
            elif seg.is_sentence_end:
                if n >= 3 and is_antepenultimate:
                    gain_off = -1.6 if is_dlg else -1.8
                elif n >= 2 and is_penultimate:
                    gain_off = -3.2 if is_dlg else -3.8
                elif is_last:
                    gain_off = -4.8 if is_dlg else -5.6
            elif (seg.is_comma_end or pause_ms > 0) and is_last:
                gain_off = -1.0 if is_dlg else -1.2

            profiles.append(
                SyllableFilterProfile(
                    index=i,
                    word=words[i],
                    clean_lower=lower_words[i],
                    viet_tone=tones[i],
                    coda_type=codas[i],
                    syntactic_role=roles[i],
                    stretch_factor=stretch,
                    f0_offset_st=f0_off,
                    tone_sandhi_scale=s_scale,
                    gain_offset_db=gain_off,
                    pause_after_ms=pause_ms,
                    no_split_after=no_split_locks[i],
                    expected_dur_weight=exp_weight,
                )
            )

        seg.syllable_profiles = profiles
        seg.pickup_fast_syl_indices = sorted(list(pickup_fast_indices))
        seg.mid_elongate_syl_indices = sorted(list(elongate_indices - {n - 1}))
        seg.focal_stress_syl_indices = sorted(list(focal_indices))
        seg.contrast_high_syl_indices = sorted(list(contrast_high_indices))
        seg.contrast_low_syl_indices = sorted(list(contrast_low_indices))
        seg.idiom_rhythm_syl_indices = sorted(list(idiom_indices))
        seg.intra_pauses_map = intra_pauses_map

    def _classify_clause_emotion_weighted(
        self,
        clean_text: str,
        full_sentence: str,
        is_question: bool,
        is_exclaim: bool,
        is_ellipsis: bool,
        syl_count: int,
        role: str = "NARRATION",
        inherited_emotion: Optional[str] = None
    ) -> Tuple[str, float]:
        scores: Dict[str, float] = {
            "SOULFUL_CONTEMPLATION": 0.0,
            "NARRATION_NORM": 1.0 if role == "NARRATION" else 0.0,
            "DIALOGUE_LIVELY_NORM": 2.2 if role == "DIALOGUE" else 0.0,
            "SHOUT_ROAR": 0.0,
            "COLD_THREAT": 0.0,
            "SURPRISE_SHOCK": 0.0,
            "QUESTION_RISE": 0.0,
            "MOCKING_GLEE": 0.0,
            "SYMPATHY_SIGH": 0.0,
            "SOLEMN_DECREE": 0.0,
            "MYSTERIOUS_SUSPENSE": 0.0,
            "URGENT_RUSH": 0.0,
            "PAIN_INJURED": 0.0,
            "INNER_MONOLOGUE": 0.0,
            "TENDER_RESPECT": 0.0,
            "CROWD_GOSSIP": 0.0,
        }

        if inherited_emotion and inherited_emotion in scores:
            scores[inherited_emotion] += 4.2

        if self.shout_roar_re.search(clean_text) or (is_exclaim and syl_count <= 8):
            scores["SHOUT_ROAR"] += 6.0
        if self.cold_threat_re.search(clean_text):
            scores["COLD_THREAT"] += 5.8
        if self.pain_injured_re.search(clean_text):
            scores["PAIN_INJURED"] += 5.6
        if self.mocking_re.search(clean_text) or self.trailing_laugh_re.match(clean_text):
            scores["MOCKING_GLEE"] += 5.5
        if self.sympathy_re.search(clean_text):
            scores["SYMPATHY_SIGH"] += 5.2
        if self.inner_monologue_re.search(clean_text):
            scores["INNER_MONOLOGUE"] += 5.0
        if self.mysterious_suspense_re.search(clean_text) or is_ellipsis:
            scores["MYSTERIOUS_SUSPENSE"] += 4.8
        if self.urgent_rush_re.search(clean_text):
            scores["URGENT_RUSH"] += 4.9
        if self.tender_respect_re.search(clean_text):
            scores["TENDER_RESPECT"] += 4.6
        if self.solemn_decree_re.search(clean_text) and not is_question:
            scores["SOLEMN_DECREE"] += 4.5
        if self.crowd_gossip_re.search(clean_text):
            scores["CROWD_GOSSIP"] += 4.4
        if self.soulful_contemplation_re.search(clean_text):
            scores["SOULFUL_CONTEMPLATION"] += 5.4
        if self.surprise_re.search(clean_text):
            scores["SURPRISE_SHOCK"] += 5.1
        if is_question:
            scores["QUESTION_RISE"] += 5.7

        if self.soulful_contemplation_re.search(full_sentence):
            scores["SOULFUL_CONTEMPLATION"] += 2.5
        if self.crowd_gossip_re.search(full_sentence):
            scores["CROWD_GOSSIP"] += 1.8

        best_mode = max(scores.items(), key=lambda kv: kv[1])[0]
        confidence = min(1.0, scores[best_mode] / 6.0)
        return best_mode, confidence

    def plan_sentence(
        self,
        sentence: str,
        base_length_scale: float = 1.0,
        role: str = "NARRATION",
        voice_id: str = "VOICE_NARRATOR",
        inherited_emotion: Optional[str] = None,
        full_span_text: Optional[str] = None,
        override_clause_emotion_fn: Optional[Callable[[str, str, Optional[str]], Tuple[str, float]]] = None
    ) -> List[ProsodicSegment]:
        clauses = self.split_into_safe_breath_groups(sentence)
        segments: List[ProsodicSegment] = []
        total = len(clauses)
        full_sentence_lower = sentence.lower()
        is_dlg = (role == "DIALOGUE")
        dlg_context_text = full_span_text if full_span_text else sentence

        for idx, raw_c in enumerate(clauses):
            is_micro_split = raw_c.endswith("|")
            clean_text = raw_c.rstrip("|").strip()
            if not clean_text:
                continue

            words = VietnamesePhonologyHelper.extract_words(clean_text)
            syl_count = len(words)
            if syl_count == 0:
                continue

            is_last = (idx == total - 1)
            is_comma = clean_text.endswith((",", ";", ":"))
            is_ellipsis = clean_text.endswith(("...", "…"))
            is_question = clean_text.endswith("?") or bool(
                re.search(r"\b(không phải\s+.*\s+sao|chuyện gì xảy ra|tại sao|thật ư|hả)\b", clean_text, re.IGNORECASE)
            )
            is_exclaim = clean_text.endswith("!")
            is_declarative_end = is_last and not is_question and not is_exclaim and not is_ellipsis

            last_word_raw = clean_text.split()[-1]
            coda_type = VietnamesePhonologyHelper.classify_syllable_coda(last_word_raw)
            can_elongate_last = (coda_type != "STOP_CODA")
            max_stretch = VietnamesePhonologyHelper.max_safe_stretch_for_coda(coda_type)

            particle_a_idxs = [syl_count - 1] if (syl_count >= 3 and VietnamesePhonologyHelper.is_exclamatory_particle_a(words, syl_count - 1)) else []
            has_final_particle_a = len(particle_a_idxs) > 0

            if is_dlg and override_clause_emotion_fn is not None:
                effort_mode, conf = override_clause_emotion_fn(clean_text, dlg_context_text, inherited_emotion)
            else:
                effort_mode, conf = self._classify_clause_emotion_weighted(
                    clean_text, sentence, is_question, is_exclaim, is_ellipsis, syl_count,
                    role=role, inherited_emotion=inherited_emotion
                )

            seg = ProsodicSegment(
                text=clean_text,
                role=role,
                voice_id=voice_id,
                inherited_emotion=inherited_emotion,
                dialogue_expressive_boost=(1.35 if is_dlg else 1.0),
                words=words,
                syllable_count=syl_count,
                effort_mode=effort_mode,
                emotion_confidence=conf,
                length_scale=base_length_scale,
                noise_scale=(0.590 if is_dlg else 0.580),
                noise_w=0.72,
                has_detached_particle_a=has_final_particle_a,
                particle_a_syl_indices=particle_a_idxs,
                coda_type=coda_type,
                staccato_tail=not can_elongate_last,
                is_comma_end=is_comma,
                is_ellipsis_end=is_ellipsis,
                is_sentence_end=is_declarative_end,
                is_question_end=is_question,
                is_exclamation_end=is_exclaim
            )

            if effort_mode == "SHOUT_ROAR":
                seg.length_scale *= (0.86 if is_dlg else 0.88)
                seg.gain_db += (5.0 if is_dlg else 4.6)
                seg.pitch_shift_st += (2.85 if is_dlg else 2.65)
                seg.presence_boost_db += (5.0 if is_dlg else 4.8)
                seg.warmth_boost_db += 1.6
                seg.grit_drive = (0.32 if is_dlg else 0.30)
                seg.noise_scale = 0.605
                seg.soft_consonant_attack = False
                seg.enable_velvet_breath_tail = False
                seg.luyen_lay_curve = "SHOUT_PUNCH_CONTOUR"
                seg.applied_rules.append("SITUATION_01_SHOUT_ROAR")

            elif effort_mode == "COLD_THREAT":
                seg.length_scale *= (1.12 if is_dlg else 1.10)
                seg.gain_db += (1.2 if is_dlg else 0.8)
                seg.pitch_shift_st -= (2.10 if is_dlg else 1.85)
                seg.warmth_boost_db += 4.0
                seg.presence_boost_db += 1.6
                seg.grit_drive = 0.16
                seg.soft_consonant_attack = False
                seg.luyen_lay_curve = "EMOTIONAL_SIGH_LILT"
                seg.applied_rules.append("SITUATION_02_COLD_THREAT")

            elif effort_mode == "PAIN_INJURED":
                seg.length_scale *= (1.18 if is_dlg else 1.15)
                seg.gain_db -= 1.0
                seg.pitch_shift_st -= 1.65
                seg.warmth_boost_db += 2.4
                seg.presence_boost_db -= 0.8
                seg.grit_drive = 0.14
                seg.luyen_lay_curve = "EMOTIONAL_SIGH_LILT"
                seg.applied_rules.append("SITUATION_08_PAIN_INJURED")

            elif effort_mode == "MOCKING_GLEE":
                seg.length_scale *= 0.96
                seg.gain_db += (2.6 if is_dlg else 2.2)
                seg.pitch_shift_st += (1.65 if is_dlg else 1.40)
                seg.presence_boost_db += 3.0
                seg.warmth_boost_db += 0.8
                seg.soft_consonant_attack = False
                seg.luyen_lay_curve = "EMOTIONAL_SIGH_LILT"
                seg.applied_rules.append("SITUATION_03_MOCKING_GLEE")

            elif effort_mode == "SYMPATHY_SIGH":
                seg.length_scale *= 1.10
                seg.gain_db -= (0.8 if is_dlg else 1.4)
                seg.pitch_shift_st -= 1.40
                seg.warmth_boost_db += 3.2
                seg.presence_boost_db -= 1.0
                seg.soft_consonant_attack = True
                seg.luyen_lay_curve = "EMOTIONAL_SIGH_LILT"
                seg.applied_rules.append("SITUATION_07_SYMPATHY_SIGH")

            elif effort_mode == "INNER_MONOLOGUE":
                seg.length_scale *= 1.05
                seg.gain_db -= 0.6
                seg.pitch_shift_st -= 0.75
                seg.warmth_boost_db += 3.4
                seg.presence_boost_db -= 1.0
                seg.soft_consonant_attack = True
                seg.luyen_lay_curve = "CONTEMPLATIVE_OPEN_LILT"
                seg.applied_rules.append("SITUATION_13_INNER_MONOLOGUE")

            elif effort_mode == "MYSTERIOUS_SUSPENSE":
                seg.length_scale *= 1.12
                seg.gain_db -= 1.6
                seg.pitch_shift_st -= 1.00
                seg.warmth_boost_db += 2.8
                seg.presence_boost_db -= 1.2
                seg.soft_consonant_attack = True
                seg.luyen_lay_curve = "SUSPENSE_FLOATING_TAIL"
                seg.applied_rules.append("SITUATION_12_MYSTERIOUS_SUSPENSE")

            elif effort_mode == "URGENT_RUSH":
                seg.length_scale *= 0.84
                seg.gain_db += (2.8 if is_dlg else 2.2)
                seg.pitch_shift_st += (1.45 if is_dlg else 1.15)
                seg.presence_boost_db += 3.0
                seg.warmth_boost_db += 0.6
                seg.soft_consonant_attack = False
                seg.enable_velvet_breath_tail = False
                seg.applied_rules.append("SITUATION_09_URGENT_RUSH")

            elif effort_mode == "TENDER_RESPECT":
                seg.length_scale *= 1.06
                seg.gain_db += (0.2 if is_dlg else -0.3)
                seg.pitch_shift_st -= 0.45
                seg.warmth_boost_db += 2.8
                seg.presence_boost_db -= 0.5
                seg.soft_consonant_attack = True
                seg.luyen_lay_curve = "CONTEMPLATIVE_OPEN_LILT"
                seg.applied_rules.append("SITUATION_11_TENDER_RESPECT")

            elif effort_mode == "SOLEMN_DECREE":
                seg.length_scale *= 1.08
                seg.gain_db += (2.6 if is_dlg else 2.2)
                seg.pitch_shift_st -= (1.55 if is_dlg else 1.35)
                seg.warmth_boost_db += 4.2
                seg.presence_boost_db += 2.0
                seg.luyen_lay_curve = "SOLEMN_CHEST_SWELL"
                seg.applied_rules.append("SITUATION_10_SOLEMN_DECREE")

            elif effort_mode == "CROWD_GOSSIP":
                seg.length_scale *= 0.93
                seg.gain_db += 1.8
                seg.pitch_shift_st += 0.85
                seg.presence_boost_db += 2.2
                seg.warmth_boost_db += 1.0
                seg.luyen_lay_curve = "CONTEMPLATIVE_OPEN_LILT"
                seg.applied_rules.append("SITUATION_06_CROWD_GOSSIP")

            elif effort_mode == "SURPRISE_SHOCK":
                seg.length_scale *= 0.94
                seg.gain_db += (3.0 if is_dlg else 2.6)
                seg.pitch_shift_st += (1.95 if is_dlg else 1.65)
                seg.presence_boost_db += 3.5
                seg.warmth_boost_db += 0.5
                seg.luyen_lay_curve = "SURPRISE_ARCH_LILT"
                seg.applied_rules.append("SITUATION_04_SURPRISE_SHOCK")

            elif effort_mode == "QUESTION_RISE":
                seg.length_scale *= 0.96
                seg.gain_db += (2.2 if is_dlg else 2.0)
                seg.pitch_shift_st += (1.15 if is_dlg else 0.90)
                seg.presence_boost_db += 3.2
                seg.luyen_lay_curve = "QUESTION_SCOOP_RISE"
                seg.applied_rules.append("SITUATION_05_QUESTION_SCOOP_RISE")

            elif effort_mode == "DIALOGUE_LIVELY_NORM":
                seg.length_scale *= 0.96
                seg.gain_db += 1.5
                seg.pitch_shift_st += 0.65
                seg.presence_boost_db += 2.0
                seg.warmth_boost_db += 1.2
                seg.soft_consonant_attack = False
                seg.luyen_lay_curve = "CONTEMPLATIVE_OPEN_LILT"
                seg.applied_rules.append("SITUATION_15_DIALOGUE_LIVELY_NORM")

            elif effort_mode == "SOULFUL_CONTEMPLATION":
                seg.length_scale *= 1.08
                seg.pitch_shift_st -= 0.85
                seg.warmth_boost_db += 3.2
                seg.presence_boost_db -= 0.8
                seg.soft_consonant_attack = True
                seg.enable_velvet_breath_tail = True
                seg.luyen_lay_curve = "CONTEMPLATIVE_OPEN_LILT"
                seg.applied_rules.append("SITUATION_14_SOULFUL_CONTEMPLATION")

            else:
                seg.length_scale *= 1.03
                seg.pitch_shift_st -= 0.35
                seg.warmth_boost_db += 2.2
                seg.soft_consonant_attack = True
                seg.enable_velvet_breath_tail = True
                seg.luyen_lay_curve = "CONTEMPLATIVE_OPEN_LILT"
                seg.applied_rules.append("SITUATION_16_NARRATION_NORM")

            if is_dlg and effort_mode not in ("SYMPATHY_SIGH", "PAIN_INJURED"):
                seg.presence_boost_db += 1.2

            if seg.has_detached_particle_a:
                if seg.effort_mode in ("SYMPATHY_SIGH", "PAIN_INJURED", "TENDER_RESPECT", "SOULFUL_CONTEMPLATION"):
                    seg.pre_particle_pause_ms = 56
                    seg.tail_stretch = 2.08
                    seg.luyen_lay_curve = "PARTICLE_A_FALLING_SIGH"
                elif is_question:
                    seg.pre_particle_pause_ms = 38
                    seg.tail_stretch = 1.80
                    seg.luyen_lay_curve = "QUESTION_SCOOP_RISE"
                elif seg.effort_mode in ("SHOUT_ROAR", "COLD_THREAT"):
                    seg.pre_particle_pause_ms = 32
                    seg.tail_stretch = 1.50
                    seg.luyen_lay_curve = "SHOUT_PUNCH_CONTOUR"
                else:
                    seg.pre_particle_pause_ms = 48
                    seg.tail_stretch = 2.02
                    seg.luyen_lay_curve = "PARTICLE_A_FALLING_SIGH"
                seg.applied_rules.append("TRIGGER_DETACHED_PARTICLE_A")

            if not seg.has_detached_particle_a:
                if can_elongate_last:
                    if is_question:
                        seg.tail_stretch = min(max_stretch, max(seg.tail_stretch, 1.80))
                    elif self.final_modal_re.search(clean_text):
                        seg.tail_stretch = min(max_stretch, max(seg.tail_stretch, 1.76))
                        if seg.luyen_lay_curve in ("NONE", "CONTEMPLATIVE_OPEN_LILT") and is_declarative_end:
                            seg.luyen_lay_curve = "DECLARATIVE_FINAL_FALL"
                    elif is_micro_split:
                        seg.tail_stretch = min(max_stretch, max(seg.tail_stretch, 1.48))
                    elif is_comma:
                        seg.tail_stretch = min(max_stretch, max(seg.tail_stretch, 1.56))
                    elif is_declarative_end:
                        seg.tail_stretch = min(max_stretch, max(seg.tail_stretch, 1.54))
                        seg.luyen_lay_curve = "DECLARATIVE_FINAL_FALL"
                else:
                    seg.tail_stretch = 0.96 if seg.effort_mode == "SOULFUL_CONTEMPLATION" else 0.86
                    seg.staccato_tail = (seg.effort_mode != "SOULFUL_CONTEMPLATION")

            self._build_granular_syllable_profiles(words, full_sentence_lower, seg)

            if is_last:
                if seg.effort_mode == "SOULFUL_CONTEMPLATION":
                    seg.pause_after_ms = 780
                elif seg.effort_mode in ("SYMPATHY_SIGH", "MYSTERIOUS_SUSPENSE", "TENDER_RESPECT", "PAIN_INJURED"):
                    seg.pause_after_ms = 420 if is_dlg else 660
                elif seg.effort_mode == "URGENT_RUSH":
                    seg.pause_after_ms = 180 if is_dlg else 240
                elif seg.effort_mode == "SHOUT_ROAR":
                    seg.pause_after_ms = 220 if is_dlg else 320
                else:
                    seg.pause_after_ms = 240 if is_dlg else 520
            elif is_micro_split:
                seg.pause_after_ms = 120 if is_dlg else (240 if seg.effort_mode == "SOULFUL_CONTEMPLATION" else 155)
            elif is_comma:
                if syl_count <= 3 and self.short_poetic_openers_re.match(clean_text):
                    seg.pause_after_ms = 220 if is_dlg else 380
                elif seg.effort_mode == "SOULFUL_CONTEMPLATION":
                    seg.pause_after_ms = 400
                elif seg.effort_mode == "URGENT_RUSH":
                    seg.pause_after_ms = 110 if is_dlg else 140
                else:
                    seg.pause_after_ms = 135 if is_dlg else 280
            else:
                seg.pause_after_ms = 150 if is_dlg else 260

            segments.append(seg)

        return segments


# ==============================================================================
# PHẦN 5: ĐỘNG CƠ ĐIÊU KHẮC SÓNG ÂM 1-ĐỐI-1 & VELVET STUDIO MASTERING DSP (V7.1)
# ==============================================================================
class CrystalVocalMasteringDSP:
    """
    ĐỘNG CƠ PHỤC HỒI PHỔ ÂM HỌC, NỘI SUY BẬC 3 CATMULL-ROM, LÀM DỊU THÍNH GIÁC ĐỘNG
    & LÀM ẤM/TRONG GIỌNG 8 TẦNG CHUẨN PODCAST / ELEVENLABS / CAPCUT (V9.0).
    """

    _M_IDX = np.arange(-7.5, 8.0, 1.0, dtype=np.float64)
    _SINC_VAL = np.sin(np.pi * _M_IDX) / (np.pi * _M_IDX)
    _BLACKMAN_WIN = (
        0.42
        + 0.50 * np.cos(2.0 * np.pi * _M_IDX / 16.0)
        + 0.08 * np.cos(4.0 * np.pi * _M_IDX / 16.0)
    )
    POLYPHASE_HALF_BAND_KERNEL = (_SINC_VAL * _BLACKMAN_WIN / np.sum(_SINC_VAL * _BLACKMAN_WIN)).astype(np.float32)

    @staticmethod
    def cubic_catmull_rom_resample(signal: np.ndarray, sample_positions: np.ndarray) -> np.ndarray:
        n = len(signal)
        if n < 4 or len(sample_positions) == 0:
            return signal.copy()

        pos = np.clip(sample_positions, 0.0, float(n - 1) - 1e-5)
        idx0 = np.floor(pos).astype(np.int32)
        f = (pos - idx0).astype(np.float32)

        idx_m1 = np.clip(idx0 - 1, 0, n - 1)
        idx_p1 = np.clip(idx0 + 1, 0, n - 1)
        idx_p2 = np.clip(idx0 + 2, 0, n - 1)

        ym1 = signal[idx_m1]
        y0 = signal[idx0]
        y1 = signal[idx_p1]
        y2 = signal[idx_p2]

        a0 = -0.5 * ym1 + 1.5 * y0 - 1.5 * y1 + 0.5 * y2
        a1 = ym1 - 2.5 * y0 + 2.0 * y1 - 0.5 * y2
        a2 = -0.5 * ym1 + 0.5 * y1
        a3 = y0

        return (((a0 * f + a1) * f + a2) * f + a3).astype(np.float32)

    @staticmethod
    def run_biquad(
        audio: np.ndarray,
        sr: int,
        freq_hz: float,
        gain_db: float = 0.0,
        q_factor: float = 1.0,
        filter_type: str = "peaking"
    ) -> np.ndarray:
        if len(audio) < 32 or freq_hz <= 10.0 or freq_hz >= (sr * 0.485):
            return audio
        if filter_type in ("peaking", "lowshelf", "highshelf") and abs(gain_db) < 0.08:
            return audio

        A = 10.0 ** (gain_db / 40.0)
        w0 = 2.0 * np.pi * freq_hz / float(sr)
        cos_w0 = float(np.cos(w0))
        sin_w0 = float(np.sin(w0))
        alpha = sin_w0 / (2.0 * q_factor)

        if filter_type == "peaking":
            b0 = 1.0 + alpha * A
            b1 = -2.0 * cos_w0
            b2 = 1.0 - alpha * A
            a0 = 1.0 + alpha / A
            a1 = -2.0 * cos_w0
            a2 = 1.0 - alpha / A
        elif filter_type == "lowshelf":
            sqrt_A = float(np.sqrt(A))
            b0 = A * ((A + 1.0) - (A - 1.0) * cos_w0 + 2.0 * sqrt_A * alpha)
            b1 = 2.0 * A * ((A - 1.0) - (A + 1.0) * cos_w0)
            b2 = A * ((A + 1.0) - (A - 1.0) * cos_w0 - 2.0 * sqrt_A * alpha)
            a0 = (A + 1.0) + (A - 1.0) * cos_w0 + 2.0 * sqrt_A * alpha
            a1 = -2.0 * ((A - 1.0) + (A + 1.0) * cos_w0)
            a2 = (A + 1.0) + (A - 1.0) * cos_w0 - 2.0 * sqrt_A * alpha
        elif filter_type == "highshelf":
            sqrt_A = float(np.sqrt(A))
            b0 = A * ((A + 1.0) + (A - 1.0) * cos_w0 + 2.0 * sqrt_A * alpha)
            b1 = -2.0 * A * ((A - 1.0) + (A + 1.0) * cos_w0)
            b2 = A * ((A + 1.0) + (A - 1.0) * cos_w0 - 2.0 * sqrt_A * alpha)
            a0 = (A + 1.0) - (A - 1.0) * cos_w0 + 2.0 * sqrt_A * alpha
            a1 = 2.0 * ((A - 1.0) - (A + 1.0) * cos_w0)
            a2 = (A + 1.0) - (A - 1.0) * cos_w0 - 2.0 * sqrt_A * alpha
        elif filter_type == "highpass":
            b0 = (1.0 + cos_w0) / 2.0
            b1 = -(1.0 + cos_w0)
            b2 = (1.0 + cos_w0) / 2.0
            a0 = 1.0 + alpha
            a1 = -2.0 * cos_w0
            a2 = 1.0 - alpha
        elif filter_type == "lowpass":
            b0 = (1.0 - cos_w0) / 2.0
            b1 = 1.0 - cos_w0
            b2 = (1.0 - cos_w0) / 2.0
            a0 = 1.0 + alpha
            a1 = -2.0 * cos_w0
            a2 = 1.0 - alpha
        elif filter_type == "bandpass":
            b0 = alpha
            b1 = 0.0
            b2 = -alpha
            a0 = 1.0 + alpha
            a1 = -2.0 * cos_w0
            a2 = 1.0 - alpha
        else:
            return audio

        b = np.array([b0 / a0, b1 / a0, b2 / a0], dtype=np.float64)
        a = np.array([1.0, a1 / a0, a2 / a0], dtype=np.float64)

        if HAS_SCIPY:
            return _scipy_lfilter(b, a, audio).astype(np.float32)

        out = np.zeros_like(audio, dtype=np.float32)
        b0_n, b1_n, b2_n = float(b[0]), float(b[1]), float(b[2])
        a1_n, a2_n = float(a[1]), float(a[2])
        z1, z2 = 0.0, 0.0
        for i in range(len(audio)):
            x = float(audio[i])
            y = b0_n * x + z1
            z1 = b1_n * x - a1_n * y + z2
            z2 = b2_n * x - a2_n * y
            out[i] = y
        return out

    @classmethod
    def stft_harmonic_purifier_and_formant_enhancer(
        cls,
        audio: np.ndarray,
        sr: int,
        debuzz_strength: float = 0.48,
        formant_contrast: float = 0.13
    ) -> np.ndarray:
        n_samples = len(audio)
        n_fft = 512 if sr <= 24000 else 1024
        hop = n_fft // 4
        if n_samples < n_fft * 2 or debuzz_strength <= 0.02:
            return audio

        win = np.hanning(n_fft).astype(np.float32)
        pad_len = n_fft
        padded = np.pad(audio, (pad_len, pad_len), mode="reflect")
        num_frames = 1 + (len(padded) - n_fft) // hop

        shape = (num_frames, n_fft)
        strides = (padded.strides[0] * hop, padded.strides[0])
        frames = np.lib.stride_tricks.as_strided(padded, shape=shape, strides=strides) * win

        spec = np.fft.rfft(frames, axis=1)
        mag = np.abs(spec).astype(np.float32) + 1e-8

        kernel_freq = np.ones(7, dtype=np.float32) / 7.0
        local_env = np.apply_along_axis(lambda m: np.convolve(m, kernel_freq, mode="same"), axis=1, arr=mag) + 1e-8

        harmonic_ratio = mag / local_env
        gain_mask = np.power(harmonic_ratio, debuzz_strength * 0.65)
        gain_mask = np.clip(gain_mask, 1.0 - debuzz_strength, 1.0 + formant_contrast)

        freqs = np.fft.rfftfreq(n_fft, d=1.0 / float(sr))
        active_band = ((freqs >= 950.0) & (freqs <= min(8500.0, sr * 0.45))).astype(np.float32)
        final_mask = 1.0 + active_band[None, :] * (gain_mask - 1.0)

        clean_spec = spec * final_mask
        recon_frames = np.fft.irfft(clean_spec, n=n_fft, axis=1).astype(np.float32) * win

        out_padded = np.zeros(len(padded), dtype=np.float32)
        win_sq_sum = np.zeros(len(padded), dtype=np.float32)
        win_sq = (win ** 2).astype(np.float32)

        for m in range(num_frames):
            start = m * hop
            out_padded[start:start + n_fft] += recon_frames[m]
            win_sq_sum[start:start + n_fft] += win_sq

        valid = win_sq_sum > 1e-5
        out_padded[valid] /= win_sq_sum[valid]

        return out_padded[pad_len:pad_len + n_samples]

    @classmethod
    def apply_dynamic_ear_comfort_soothe(
        cls,
        audio: np.ndarray,
        sr: int,
        soothe_strength: float = 0.56
    ) -> np.ndarray:
        if len(audio) < 64 or soothe_strength <= 0.05:
            return audio

        harsh_band = cls.run_biquad(audio, sr, freq_hz=3150.0, q_factor=2.0, filter_type="bandpass")
        win_len = max(24, int(sr * 0.010))
        win_kernel = np.ones(win_len, dtype=np.float32) / float(win_len)

        harsh_env = np.sqrt(np.convolve(harsh_band ** 2, win_kernel, mode="same") + 1e-10)
        broad_env = np.sqrt(np.convolve(audio ** 2, win_kernel, mode="same") + 1e-10)

        harsh_ratio = harsh_env / (broad_env + 1e-4)
        thresh = 0.24
        active = (harsh_ratio > thresh) & (harsh_env > 0.015)

        reduction = np.zeros_like(audio, dtype=np.float32)
        if np.any(active):
            reduction[active] = np.clip((harsh_ratio[active] - thresh) * soothe_strength * 1.75, 0.0, 0.52)

        smooth_len = max(16, int(sr * 0.012))
        hann = np.hanning(smooth_len).astype(np.float32)
        smooth_red = np.convolve(reduction, hann / np.sum(hann), mode="same")

        return (audio - harsh_band * smooth_red).astype(np.float32)

    @classmethod
    def apply_relative_smart_de_esser(
        cls,
        audio: np.ndarray,
        sr: int,
        rel_threshold: float = 0.36
    ) -> np.ndarray:
        if len(audio) < 64:
            return audio

        sib_center = min(6600.0, sr * 0.36)
        sib_band = cls.run_biquad(audio, sr, freq_hz=sib_center, q_factor=1.25, filter_type="bandpass")

        win_len = max(16, int(sr * 0.006))
        win_kernel = np.ones(win_len, dtype=np.float32) / float(win_len)

        sib_env = np.sqrt(np.convolve(sib_band ** 2, win_kernel, mode="same") + 1e-10)
        broad_env = np.sqrt(np.convolve(audio ** 2, win_kernel, mode="same") + 1e-10)

        rel_ratio = sib_env / (broad_env + 1e-5)
        active_sib = (rel_ratio > rel_threshold) & (sib_env > 0.022)

        reduction = np.zeros_like(audio, dtype=np.float32)
        if np.any(active_sib):
            excess_ratio = np.clip((rel_ratio[active_sib] - rel_threshold) / 0.42, 0.0, 0.68)
            reduction[active_sib] = excess_ratio

        smooth_len = max(8, int(sr * 0.005))
        smooth_reduction = np.convolve(reduction, np.ones(smooth_len, dtype=np.float32) / smooth_len, mode="same")

        return (audio - sib_band * smooth_reduction).astype(np.float32)

    @classmethod
    def upsample_2x_sinc_polyphase_with_air_exciter(
        cls,
        audio: np.ndarray,
        orig_sr: int,
        preset: VocalClarityPreset
    ) -> Tuple[np.ndarray, int]:
        if len(audio) < 32:
            return audio, orig_sr

        src_freq = min(5400.0, orig_sr * 0.33)
        src_band = cls.run_biquad(audio, orig_sr, freq_hz=src_freq, q_factor=0.85, filter_type="bandpass")

        new_sr = orig_sr * 2
        n = len(audio)
        up_audio = np.zeros(n * 2, dtype=np.float32)
        up_audio[0::2] = audio
        up_audio[1::2] = np.convolve(audio, cls.POLYPHASE_HALF_BAND_KERNEL, mode="same")

        up_src = np.zeros(n * 2, dtype=np.float32)
        up_src[0::2] = src_band
        up_src[1::2] = np.convolve(src_band, cls.POLYPHASE_HALF_BAND_KERNEL, mode="same")

        even_harmonics = up_src * np.abs(up_src) * 3.0
        odd_harmonics = np.tanh(up_src * 2.5)

        raw_excited = (
            preset.even_tube_harmonic_weight * even_harmonics
            + preset.odd_aphex_harmonic_weight * odd_harmonics
        ).astype(np.float32)

        air_band = cls.run_biquad(raw_excited, new_sr, freq_hz=9800.0, q_factor=0.707, filter_type="highpass")
        air_band = cls.run_biquad(air_band, new_sr, freq_hz=9800.0, q_factor=0.707, filter_type="highpass")
        if new_sr >= 40000:
            air_band = cls.run_biquad(air_band, new_sr, freq_hz=17800.0, q_factor=0.707, filter_type="lowpass")

        crystal_audio = up_audio + air_band * preset.air_exciter_mix
        return crystal_audio.astype(np.float32), new_sr

    @classmethod
    def _compress_single_band(
        cls,
        band_audio: np.ndarray,
        sr: int,
        quiet_floor: float,
        quiet_ceil: float,
        upward_gain: float,
        loud_thresh: float,
        downward_exp: float
    ) -> np.ndarray:
        win_len = max(32, int(sr * 0.018))
        env = np.sqrt(np.convolve(band_audio ** 2, np.ones(win_len, dtype=np.float32) / win_len, mode="same") + 1e-10)

        gain = np.ones_like(env, dtype=np.float32)
        quiet_mask = (env > quiet_floor) & (env < quiet_ceil)
        gain[quiet_mask] = upward_gain

        loud_mask = env > loud_thresh
        if np.any(loud_mask):
            gain[loud_mask] = np.power(env[loud_mask] / loud_thresh, downward_exp)

        smooth_len = max(32, int(sr * 0.042))
        hann = np.hanning(smooth_len).astype(np.float32)
        smooth_gain = np.convolve(gain, hann / np.sum(hann), mode="same")

        return (band_audio * smooth_gain).astype(np.float32)

    @classmethod
    def apply_3band_ott_multiband_compressor(
        cls,
        audio: np.ndarray,
        sr: int,
        preset: VocalClarityPreset
    ) -> np.ndarray:
        if len(audio) < 64:
            return audio

        low_band = cls.run_biquad(audio, sr, freq_hz=230.0, q_factor=0.707, filter_type="lowpass")
        rem_mid_high = audio - low_band
        high_band = cls.run_biquad(rem_mid_high, sr, freq_hz=3800.0, q_factor=0.707, filter_type="highpass")
        mid_band = rem_mid_high - high_band

        up_lin = 10.0 ** (preset.multiband_upward_lift_db / 20.0)

        comp_low = cls._compress_single_band(
            low_band, sr, quiet_floor=0.005, quiet_ceil=0.09, upward_gain=1.10, loud_thresh=0.28, downward_exp=-0.45
        )
        comp_mid = cls._compress_single_band(
            mid_band, sr, quiet_floor=0.006, quiet_ceil=0.14, upward_gain=up_lin * 0.96, loud_thresh=0.35, downward_exp=-0.40
        )
        comp_high = cls._compress_single_band(
            high_band, sr, quiet_floor=0.002, quiet_ceil=0.07, upward_gain=up_lin * 1.02, loud_thresh=0.18, downward_exp=-0.42
        )

        return ((comp_low + comp_mid + comp_high) * 1.03).astype(np.float32)

    @classmethod
    def apply_studio_booth_micro_ambience(
        cls,
        audio: np.ndarray,
        sr: int,
        mix_level: float = 0.058
    ) -> np.ndarray:
        if len(audio) < 128 or mix_level <= 0.005:
            return audio

        booth_sig = cls.run_biquad(audio, sr, freq_hz=450.0, q_factor=0.707, filter_type="highpass")
        booth_sig = cls.run_biquad(booth_sig, sr, freq_hz=min(5600.0, sr * 0.40), q_factor=0.707, filter_type="lowpass")

        d1 = int(sr * 0.0085)
        d2 = int(sr * 0.0155)
        d3 = int(sr * 0.0235)

        er = np.zeros_like(audio, dtype=np.float32)
        if d1 < len(audio):
            er[d1:] += booth_sig[:-d1] * 0.58
        if d2 < len(audio):
            er[d2:] -= booth_sig[:-d2] * 0.30
        if d3 < len(audio):
            er[d3:] += booth_sig[:-d3] * 0.16

        return (audio + er * mix_level).astype(np.float32)


class VietnameseProsodyDSP:
    """
    ĐỘNG CƠ ĐIÊU KHẮC SÓNG ÂM KHỚP CỨNG 1-ĐỐI-1 (Exact 1:1 Aligned Soulful Rubato DSP).
    Nhận trực tiếp `ProsodicSegment` đã đồng bộ từ V8.1 + V7.1 để điêu khắc từng âm tiết.
    """

    BASELINE_HEADROOM_SCALE = 0.575

    def __init__(
        self,
        sample_rate: int = 22050,
        enable_44k_air_upsample: bool = False,
        clarity_preset_name: str = "SOULFUL_PODCAST_WARMTH"
    ):
        self.sr = sample_rate
        self.enable_44k_air_upsample = enable_44k_air_upsample
        self.preset = CLARITY_PRESETS.get(clarity_preset_name, CLARITY_PRESETS["SOULFUL_PODCAST_WARMTH"])

    @property
    def output_sample_rate(self) -> int:
        return self.sr * 2 if (self.enable_44k_air_upsample and self.sr <= 24000) else self.sr

    def locate_raw_syllables(self, audio: np.ndarray) -> Tuple[List[SyllableSpan], np.ndarray]:
        n = len(audio)
        if n < int(self.sr * 0.08):
            rms_val = float(np.sqrt(np.mean(audio ** 2) + 1e-9))
            return [SyllableSpan(0, 0, n // 2, n, rms_val)], np.abs(audio)

        win_len = max(16, int(self.sr * 0.012))
        smooth_len = max(32, int(self.sr * 0.032))

        sq = np.power(audio, 2)
        rms = np.sqrt(np.convolve(sq, np.ones(win_len) / win_len, mode="same") + 1e-10)
        hann = np.hanning(smooth_len)
        env = np.convolve(rms, hann / np.sum(hann), mode="same")

        min_syl_dist = int(self.sr * 0.085)
        noise_floor = np.max(env) * 0.055

        valleys: List[int] = [0]
        for i in range(min_syl_dist, n - min_syl_dist):
            if env[i] <= env[i - 1] and env[i] <= env[i + 1]:
                region_max = np.max(env[valleys[-1]:i])
                if (i - valleys[-1]) >= min_syl_dist and region_max > noise_floor and env[i] < region_max * 0.80:
                    valleys.append(i)
        valleys.append(n)

        spans: List[SyllableSpan] = []
        for idx in range(len(valleys) - 1):
            s_idx = valleys[idx]
            e_idx = valleys[idx + 1]
            if e_idx - s_idx < int(self.sr * 0.038) and spans:
                prev = spans[-1]
                spans[-1] = SyllableSpan(prev.index, prev.start_sample, prev.peak_sample, e_idx, prev.rms_energy)
                continue
            p_idx = s_idx + int(np.argmax(env[s_idx:e_idx]))
            syl_rms = float(np.sqrt(np.mean(sq[s_idx:e_idx]) + 1e-9))
            spans.append(SyllableSpan(len(spans), s_idx, p_idx, e_idx, syl_rms))

        if not spans:
            spans.append(SyllableSpan(0, 0, n // 2, n, float(np.sqrt(np.mean(sq) + 1e-9))))
        return spans, env

    def align_syllable_spans_exact_count(
        self,
        audio: np.ndarray,
        seg: ProsodicSegment
    ) -> List[SyllableSpan]:
        spans, env = self.locate_raw_syllables(audio)
        target_n = len(seg.words)
        if target_n <= 0:
            return spans

        while len(spans) < target_n:
            longest_idx = int(np.argmax([sp.end_sample - sp.start_sample for sp in spans]))
            sp = spans[longest_idx]
            sp_len = sp.end_sample - sp.start_sample
            if sp_len < int(self.sr * 0.090):
                break

            s_search = sp.start_sample + int(sp_len * 0.32)
            e_search = sp.start_sample + int(sp_len * 0.68)
            if e_search > s_search + 8:
                split_pt = s_search + int(np.argmin(env[s_search:e_search]))
            else:
                split_pt = sp.start_sample + sp_len // 2

            left_audio = audio[sp.start_sample:split_pt]
            right_audio = audio[split_pt:sp.end_sample]

            left_sp = SyllableSpan(
                0,
                sp.start_sample,
                sp.start_sample + (int(np.argmax(env[sp.start_sample:split_pt])) if split_pt > sp.start_sample else 0),
                split_pt,
                float(np.sqrt(np.mean(left_audio ** 2) + 1e-9))
            )
            right_sp = SyllableSpan(
                0,
                split_pt,
                split_pt + (int(np.argmax(env[split_pt:sp.end_sample])) if sp.end_sample > split_pt else 0),
                sp.end_sample,
                float(np.sqrt(np.mean(right_audio ** 2) + 1e-9))
            )
            spans = spans[:longest_idx] + [left_sp, right_sp] + spans[longest_idx + 1:]

        while len(spans) > target_n and len(spans) >= 2:
            pair_lengths = [
                (spans[i].end_sample - spans[i].start_sample) + (spans[i + 1].end_sample - spans[i + 1].start_sample)
                for i in range(len(spans) - 1)
            ]
            merge_idx = int(np.argmin(pair_lengths))
            sp1 = spans[merge_idx]
            sp2 = spans[merge_idx + 1]
            merged_audio = audio[sp1.start_sample:sp2.end_sample]
            merged_sp = SyllableSpan(
                0,
                sp1.start_sample,
                sp1.peak_sample if sp1.rms_energy >= sp2.rms_energy else sp2.peak_sample,
                sp2.end_sample,
                float(np.sqrt(np.mean(merged_audio ** 2) + 1e-9))
            )
            spans = spans[:merge_idx] + [merged_sp] + spans[merge_idx + 2:]

        for i, sp in enumerate(spans):
            sp.index = i

        return spans

    def enhance_syllable_consonant_onset(
        self,
        syl_audio: np.ndarray,
        transient_db: float,
        soft_attack: bool = True
    ) -> np.ndarray:
        n = len(syl_audio)
        onset_samples = min(int(self.sr * 0.025), n // 3)
        if onset_samples < 16:
            return syl_audio

        out = syl_audio.copy()
        if soft_attack:
            t_soft = np.linspace(0.0, np.pi / 2.0, onset_samples, dtype=np.float32)
            soft_curve = 0.55 + 0.45 * (np.sin(t_soft) ** 2)
            out[:onset_samples] *= soft_curve
            return out

        if transient_db <= 0.2:
            return out

        onset_slice = out[:onset_samples]
        hi_consonant = CrystalVocalMasteringDSP.run_biquad(
            onset_slice, self.sr, freq_hz=3200.0, q_factor=0.9, filter_type="highpass"
        )
        boost_factor = (10.0 ** (transient_db / 20.0)) - 1.0
        env_window = np.sin(np.linspace(0.0, np.pi, onset_samples, dtype=np.float32))
        out[:onset_samples] = onset_slice + hi_consonant * boost_factor * env_window
        return out

    def stretch_vowel_nucleus_wsola(
        self,
        syl_audio: np.ndarray,
        stretch_factor: float,
        coda_type: str
    ) -> np.ndarray:
        n = len(syl_audio)
        if abs(stretch_factor - 1.0) < 0.04 or n < int(self.sr * 0.065):
            return syl_audio

        if stretch_factor < 1.0 and coda_type == "STOP_CODA":
            keep_len = max(int(self.sr * 0.065), int(n * max(0.84, stretch_factor)))
            out = syl_audio[:keep_len].copy()
            fade = min(int(self.sr * 0.014), len(out) // 3)
            if fade > 0:
                out[-fade:] *= np.linspace(1.0, 0.05, fade, dtype=np.float32)
            return out

        c1_end = int(n * 0.22)
        c2_start = int(n * (0.74 if coda_type == "GLIDE_DIPHTHONG" else 0.86))

        onset = syl_audio[:c1_end]
        vowel_body = syl_audio[c1_end:c2_start]
        coda_tail = syl_audio[c2_start:]

        frame_len = int(self.sr * 0.020)
        hop_syn = frame_len // 2
        hop_ana = max(1, int(hop_syn / stretch_factor))
        tol = int(self.sr * 0.004)

        if len(vowel_body) < frame_len * 2:
            return syl_audio

        win = np.hanning(frame_len).astype(np.float32)
        num_frames = max(1, (len(vowel_body) - frame_len - tol) // hop_ana)
        out_len = frame_len + num_frames * hop_syn
        stretched = np.zeros(out_len, dtype=np.float32)
        norm_win = np.zeros(out_len, dtype=np.float32)

        stretched[:frame_len] = vowel_body[:frame_len] * win
        norm_win[:frame_len] = win ** 2
        prev_ana = 0

        for m in range(1, num_frames):
            expected_ana = m * hop_ana
            out_idx = m * hop_syn
            natural_cont = prev_ana + hop_syn
            best_delta = 0

            if natural_cont + hop_syn < len(vowel_body):
                ref = vowel_body[natural_cont:natural_cont + hop_syn]
                ref_e = np.sum(ref ** 2) + 1e-8
                best_corr = -1e9
                d_min = max(-tol, -expected_ana)
                d_max = min(tol, len(vowel_body) - frame_len - expected_ana)
                for d in range(d_min, d_max + 1, 2):
                    cand = vowel_body[expected_ana + d:expected_ana + d + hop_syn]
                    corr = np.dot(ref, cand) / np.sqrt(ref_e * (np.sum(cand ** 2) + 1e-8))
                    if corr > best_corr:
                        best_corr = corr
                        best_delta = d

            actual_ana = expected_ana + best_delta
            stretched[out_idx:out_idx + frame_len] += vowel_body[actual_ana:actual_ana + frame_len] * win
            norm_win[out_idx:out_idx + frame_len] += win ** 2
            prev_ana = actual_ana

        valid = norm_win > 1e-4
        stretched[valid] /= norm_win[valid]

        return np.concatenate([onset, stretched, coda_tail])

    def apply_luyen_lay_pitch_glide(
        self,
        syl_audio: np.ndarray,
        base_shift_st: float,
        curve_type: str,
        coda_type: str,
        tone_scale: float = 1.0,
        viet_tone: str = "NGANG"
    ) -> np.ndarray:
        n = len(syl_audio)
        if n < int(self.sr * 0.055) or (abs(base_shift_st) < 0.08 and curve_type == "NONE"):
            return syl_audio

        tau = np.linspace(0.0, 1.0, n, dtype=np.float32)
        t_sec = np.arange(n, dtype=np.float32) / float(self.sr)

        smooth_win = np.power(np.maximum(0.0, np.sin(np.pi * tau)), 0.65).astype(np.float32)
        boundary_taper = np.sin(np.pi * np.clip(tau / 0.15, 0.0, 0.5)) * np.sin(np.pi * np.clip((1.0 - tau) / 0.15, 0.0, 0.5))
        base_env = base_shift_st * (0.40 + 0.60 * boundary_taper)

        if curve_type == "QUESTION_SCOOP_RISE":
            scoop = (-0.45 * np.sin(np.pi * tau) + 3.85 * np.power(tau, 1.55) * np.sin(0.5 * np.pi * tau)) * max(0.85, tone_scale)
            glide_st = base_env + scoop
        elif curve_type == "PARTICLE_A_FALLING_SIGH":
            vibrato = 0.28 * np.sin(2.0 * np.pi * 5.2 * t_sec) * np.clip((tau - 0.25) / 0.75, 0.0, 1.0)
            sigh_curve = 1.35 * np.cos(np.pi * tau / 1.35) * smooth_win - 0.70 * tau + vibrato
            glide_st = base_env + sigh_curve
        elif curve_type == "CONTEMPLATIVE_OPEN_LILT":
            vibrato = 0.18 * np.sin(2.0 * np.pi * 5.0 * t_sec) * np.clip((tau - 0.35) / 0.65, 0.0, 1.0)
            if viet_tone in ("HOI", "NGA"):
                lilt = (-0.52 * np.sin(np.pi * np.clip(tau / 0.55, 0.0, 1.0)) + 0.72 * np.power(tau, 1.4) * smooth_win + vibrato) * tone_scale
            elif viet_tone in ("HUYEN", "NANG"):
                lilt = (-0.62 * np.power(tau, 1.15) * smooth_win + vibrato) * tone_scale
            else:
                lilt = (0.40 * np.sin(np.pi * tau) * smooth_win - 0.22 * tau + vibrato) * tone_scale
            glide_st = base_env + lilt
        elif curve_type == "EMOTIONAL_SIGH_LILT":
            vibrato = 0.24 * np.sin(2.0 * np.pi * 5.3 * t_sec) * np.clip((tau - 0.30) / 0.70, 0.0, 1.0)
            lilt = (1.00 * np.sin(2.0 * np.pi * tau) * smooth_win - 0.75 * tau + vibrato) * tone_scale
            glide_st = base_env + lilt
        elif curve_type == "SURPRISE_ARCH_LILT":
            arch = 2.10 * np.power(np.maximum(0.0, np.sin(np.pi * tau)), 1.15) * tone_scale
            glide_st = base_env + arch
        elif curve_type == "SHOUT_PUNCH_CONTOUR":
            punch = 2.05 * (1.0 - np.power(tau, 0.85)) * smooth_win * tone_scale
            glide_st = base_env + punch
        elif curve_type == "SOLEMN_CHEST_SWELL":
            swell = (0.85 * np.sin(np.pi * tau) - 0.40 * (tau ** 2)) * tone_scale
            glide_st = base_env + swell
        elif curve_type == "SUSPENSE_FLOATING_TAIL":
            suspense = (-0.35 * np.sin(np.pi * tau) + 0.65 * np.power(tau, 1.4)) * tone_scale
            glide_st = base_env + suspense
        elif curve_type == "DECLARATIVE_FINAL_FALL":
            fall = -1.15 * np.power(tau, 1.30) * tone_scale
            glide_st = base_env + fall
        else:
            glide_st = base_env

        glide_st = np.clip(glide_st, -3.5, 4.6)
        mean_shift_st = float(np.mean(glide_st))

        inst_rate = np.power(2.0, glide_st / 12.0)
        phase_grid = np.cumsum(inst_rate)
        max_phase = float(phase_grid[-1])
        if max_phase <= 4.0:
            return syl_audio

        num_resampled = max(32, int(n / np.mean(inst_rate)))
        target_phases = np.linspace(0.0, max_phase, num_resampled, dtype=np.float32)
        orig_indices = np.arange(n, dtype=np.float32)
        sample_positions = np.interp(target_phases, phase_grid, orig_indices).astype(np.float32)

        pitched_audio = CrystalVocalMasteringDSP.cubic_catmull_rom_resample(syl_audio, sample_positions)

        comp_factor = float(n) / float(len(pitched_audio))
        if abs(comp_factor - 1.0) > 0.04 and coda_type != "STOP_CODA":
            pitched_audio = self.stretch_vowel_nucleus_wsola(pitched_audio, comp_factor, coda_type)

        if abs(mean_shift_st) >= 0.25:
            chest_comp_db = np.clip(1.35 * mean_shift_st, -3.8, 4.5)
            throat_comp_db = np.clip(-0.95 * mean_shift_st, -3.5, 3.2)
            pitched_audio = CrystalVocalMasteringDSP.run_biquad(
                pitched_audio, self.sr, freq_hz=410.0, gain_db=float(chest_comp_db), q_factor=1.1, filter_type="peaking"
            )
            pitched_audio = CrystalVocalMasteringDSP.run_biquad(
                pitched_audio, self.sr, freq_hz=2850.0, gain_db=float(throat_comp_db), q_factor=1.3, filter_type="peaking"
            )

        return pitched_audio

    def apply_phrase_bell_swell_and_breath_release(
        self,
        segment_audio: np.ndarray,
        seg: ProsodicSegment
    ) -> np.ndarray:
        n = len(segment_audio)
        if n < int(self.sr * 0.12):
            return segment_audio

        tau = np.linspace(0.0, 1.0, n, dtype=np.float32)
        bell_swell = 0.92 + 0.14 * np.sin(np.pi * np.power(tau, 0.85))
        out = (segment_audio * bell_swell).astype(np.float32)

        if not seg.enable_velvet_breath_tail or self.preset.velvet_breath_tail_mix <= 0.002:
            return out

        tail_len = min(int(self.sr * 0.160), n // 3)
        if tail_len < 64:
            return out

        tail_slice = out[-tail_len:]
        tail_env = np.sqrt(np.convolve(tail_slice ** 2, np.ones(32, dtype=np.float32) / 32.0, mode="same") + 1e-9)

        raw_noise = np.random.normal(0.0, 1.0, size=tail_len).astype(np.float32)
        breath_air = CrystalVocalMasteringDSP.run_biquad(raw_noise, self.sr, freq_hz=1650.0, q_factor=0.75, filter_type="bandpass")

        t_breath = np.linspace(0.0, np.pi, tail_len, dtype=np.float32)
        breath_window = (np.maximum(0.0, np.sin(t_breath)) ** 1.4).astype(np.float32)

        aspiration_tail = breath_air * tail_env * breath_window * (self.preset.velvet_breath_tail_mix * 12.0)
        out[-tail_len:] += aspiration_tail
        return out

    def stitch_syllables_smooth_crossfade(
        self,
        syllable_list: List[Tuple[np.ndarray, bool]]
    ) -> np.ndarray:
        if not syllable_list:
            return np.array([], dtype=np.float32)

        overlap_samples = max(14, int(self.sr * 0.007))
        out = syllable_list[0][0].copy()

        for idx in range(1, len(syllable_list)):
            curr_wav, is_silence_gap = syllable_list[idx]
            prev_was_gap = syllable_list[idx - 1][1]

            if len(curr_wav) == 0:
                continue

            if is_silence_gap or prev_was_gap or len(out) < overlap_samples * 2 or len(curr_wav) < overlap_samples * 2:
                out = np.concatenate([out, curr_wav])
                continue

            t_cf = np.linspace(0.0, np.pi / 2.0, overlap_samples, dtype=np.float32)
            fade_out_win = np.cos(t_cf) ** 2
            fade_in_win = np.sin(t_cf) ** 2

            blended_boundary = out[-overlap_samples:] * fade_out_win + curr_wav[:overlap_samples] * fade_in_win
            out = np.concatenate([out[:-overlap_samples], blended_boundary, curr_wav[overlap_samples:]])

        return out

    def apply_continuous_segment_spectral_tilt(
        self,
        segment_audio: np.ndarray,
        tilt_control_curve: np.ndarray
    ) -> np.ndarray:
        n = len(segment_audio)
        if n < 64 or len(tilt_control_curve) != n:
            return segment_audio

        smooth_len = max(32, int(self.sr * 0.038))
        hann = np.hanning(smooth_len).astype(np.float32)
        smooth_tilt = np.convolve(tilt_control_curve, hann / np.sum(hann), mode="same")

        warm_chest_bus = CrystalVocalMasteringDSP.run_biquad(
            segment_audio, self.sr, freq_hz=148.0, q_factor=0.90, filter_type="bandpass"
        )
        bright_lombard_bus = CrystalVocalMasteringDSP.run_biquad(
            segment_audio, self.sr, freq_hz=2700.0, q_factor=1.05, filter_type="bandpass"
        )

        bright_weight = np.clip(smooth_tilt, -0.35, 0.60).astype(np.float32)
        warm_weight = np.clip(-smooth_tilt * 0.95, 0.0, 0.68).astype(np.float32)

        modulated = segment_audio + warm_chest_bus * warm_weight + bright_lombard_bus * bright_weight
        return modulated.astype(np.float32)

    def sculpt_detached_particle_a_envelope(self, syl_audio: np.ndarray, effort_mode: str) -> np.ndarray:
        n = len(syl_audio)
        if n < 32:
            return syl_audio

        out = syl_audio.copy()
        onset_len = min(int(self.sr * 0.015), n // 4)
        if onset_len > 4:
            onset_curve = np.power(np.linspace(0.15, 1.0, onset_len, dtype=np.float32), 0.7)
            out[:onset_len] *= onset_curve

        if effort_mode not in ("SHOUT_ROAR", "QUESTION_RISE"):
            decay_len = int(n * 0.45)
            if decay_len > 16:
                t_dec = np.linspace(0.0, np.pi, decay_len, dtype=np.float32)
                decay_curve = 0.55 + 0.45 * np.cos(t_dec)
                out[-decay_len:] *= decay_curve

        return out

    def apply_vocal_cord_grit_and_attack(self, audio: np.ndarray, grit_drive: float, sr: int) -> np.ndarray:
        if grit_drive <= 0.02 or len(audio) < 64:
            return audio

        mid_high = CrystalVocalMasteringDSP.run_biquad(
            audio, sr, freq_hz=2550.0, gain_db=4.2, q_factor=0.9, filter_type="peaking"
        ) - audio
        drive_factor = 1.0 + grit_drive * 3.8
        saturated_harmonics = np.tanh(mid_high * drive_factor + 0.05 * (mid_high ** 2)) / np.tanh(drive_factor)

        return (audio * (1.0 - grit_drive * 0.25) + saturated_harmonics * (grit_drive * 0.70)).astype(np.float32)

    def sculpt_segment_audio(self, raw_audio: np.ndarray, seg: ProsodicSegment) -> np.ndarray:
        if len(raw_audio) == 0:
            return raw_audio

        peak = float(np.max(np.abs(raw_audio)) + 1e-6)
        audio = (raw_audio.astype(np.float32) / peak) * self.BASELINE_HEADROOM_SCALE

        audio = CrystalVocalMasteringDSP.stft_harmonic_purifier_and_formant_enhancer(
            audio,
            self.sr,
            debuzz_strength=self.preset.stft_debuzz_strength,
            formant_contrast=self.preset.formant_contrast_boost
        )

        audio = CrystalVocalMasteringDSP.run_biquad(audio, self.sr, freq_hz=75.0, q_factor=0.707, filter_type="highpass")
        audio = CrystalVocalMasteringDSP.run_biquad(audio, self.sr, freq_hz=355.0, gain_db=self.preset.mud_cut_db, q_factor=1.75, filter_type="peaking")
        audio = CrystalVocalMasteringDSP.run_biquad(audio, self.sr, freq_hz=960.0, gain_db=self.preset.nasal_cut_db, q_factor=2.10, filter_type="peaking")

        spans = self.align_syllable_spans_exact_count(audio, seg)
        num_syls = len(spans)
        profiles = seg.syllable_profiles

        seg_gain_lin = 10.0 ** (seg.gain_db / 20.0)
        processed_syllables_with_flag: List[Tuple[np.ndarray, bool]] = []
        tilt_chunks: List[np.ndarray] = []

        for s_idx, span in enumerate(spans):
            syl_wav = audio[span.start_sample:span.end_sample].copy()
            is_last_syl = (s_idx == num_syls - 1)
            is_penultimate = (s_idx == num_syls - 2)
            is_sentence_tail_syl = seg.is_sentence_end and (is_last_syl or is_penultimate)

            prof = profiles[min(s_idx, len(profiles) - 1)] if profiles else SyllableFilterProfile(s_idx, "", "")
            viet_tone = prof.viet_tone
            tone_scale = prof.tone_sandhi_scale
            curr_coda = prof.coda_type
            is_pickup_fast = (prof.syntactic_role == "PICKUP_FUNCTION") and not is_last_syl
            is_focal_syl = (s_idx in seg.focal_stress_syl_indices)
            is_contrast_low = (s_idx in seg.contrast_low_syl_indices)
            is_contrast_high = (s_idx in seg.contrast_high_syl_indices)
            pause_ms = prof.pause_after_ms

            if not (is_last_syl and seg.has_detached_particle_a):
                syl_wav = self.enhance_syllable_consonant_onset(
                    syl_wav,
                    self.preset.consonant_transient_db,
                    soft_attack=(seg.soft_consonant_attack or is_pickup_fast)
                )

            if is_penultimate and seg.has_detached_particle_a and len(syl_wav) > 32:
                close_len = min(int(self.sr * 0.016), len(syl_wav) // 3)
                if close_len > 4:
                    syl_wav[-close_len:] *= np.linspace(1.0, 0.05, close_len, dtype=np.float32)

            if is_last_syl and seg.has_detached_particle_a and seg.pre_particle_pause_ms > 0:
                gap_samples = int(self.sr * (seg.pre_particle_pause_ms / 1000.0))
                pre_a_gap = np.random.normal(0.0, 0.00008, size=gap_samples).astype(np.float32)
                processed_syllables_with_flag.append((pre_a_gap, True))
                tilt_chunks.append(np.zeros(gap_samples, dtype=np.float32))

            if abs(prof.stretch_factor - 1.0) > 0.04:
                syl_wav = self.stretch_vowel_nucleus_wsola(syl_wav, prof.stretch_factor, curr_coda)

            effective_base_st = seg.pitch_shift_st + prof.f0_offset_st

            if is_last_syl and seg.has_detached_particle_a:
                syl_wav = self.apply_luyen_lay_pitch_glide(
                    syl_wav, base_shift_st=seg.pitch_shift_st, curve_type=seg.luyen_lay_curve,
                    coda_type="OPEN_VOWEL", tone_scale=1.0, viet_tone=viet_tone
                )
                syl_wav = self.sculpt_detached_particle_a_envelope(syl_wav, seg.effort_mode)
            elif is_last_syl and seg.is_question_end:
                syl_wav = self.apply_luyen_lay_pitch_glide(
                    syl_wav, base_shift_st=seg.pitch_shift_st + 0.75, curve_type="QUESTION_SCOOP_RISE",
                    coda_type=curr_coda, tone_scale=tone_scale, viet_tone=viet_tone
                )
            elif is_penultimate and seg.is_question_end and num_syls >= 2:
                syl_wav = self.apply_luyen_lay_pitch_glide(
                    syl_wav, base_shift_st=seg.pitch_shift_st + 1.10 * tone_scale, curve_type="NONE",
                    coda_type="OPEN_VOWEL", tone_scale=tone_scale, viet_tone=viet_tone
                )
            elif (is_last_syl or s_idx in seg.mid_elongate_syl_indices) and seg.luyen_lay_curve != "NONE":
                syl_wav = self.apply_luyen_lay_pitch_glide(
                    syl_wav, base_shift_st=effective_base_st, curve_type=seg.luyen_lay_curve,
                    coda_type=curr_coda, tone_scale=tone_scale, viet_tone=viet_tone
                )
            elif is_focal_syl:
                focal_curve = "CONTEMPLATIVE_OPEN_LILT" if seg.effort_mode == "SOULFUL_CONTEMPLATION" else "SURPRISE_ARCH_LILT"
                focal_lift = ((0.75 if seg.role == "DIALOGUE" else 0.60) if not is_contrast_low else -0.45) * tone_scale
                syl_wav = self.apply_luyen_lay_pitch_glide(
                    syl_wav, base_shift_st=effective_base_st + focal_lift, curve_type=focal_curve,
                    coda_type=curr_coda, tone_scale=tone_scale, viet_tone=viet_tone
                )
            elif abs(effective_base_st) >= 0.10:
                syl_wav = self.apply_luyen_lay_pitch_glide(
                    syl_wav, base_shift_st=effective_base_st, curve_type="CONTEMPLATIVE_OPEN_LILT",
                    coda_type=curr_coda, tone_scale=tone_scale, viet_tone=viet_tone
                )

            if seg.is_sentence_end and is_last_syl:
                fade_len = int(len(syl_wav) * 0.55)
                if fade_len > 16:
                    t_env = np.linspace(0, np.pi, fade_len, dtype=np.float32)
                    syl_wav[-fade_len:] *= (0.58 + 0.42 * np.cos(t_env))

            if pause_ms > 0 and len(syl_wav) > 48:
                taper_len = min(int(self.sr * 0.022), len(syl_wav) // 3)
                t_tap = np.linspace(0.0, np.pi / 2.0, taper_len, dtype=np.float32)
                syl_wav[-taper_len:] *= (0.25 + 0.75 * (np.cos(t_tap) ** 2))

            total_syl_lin = seg_gain_lin * (10.0 ** (prof.gain_offset_db / 20.0))
            syl_wav *= total_syl_lin
            processed_syllables_with_flag.append((syl_wav, False))

            if is_sentence_tail_syl or is_contrast_low or (is_last_syl and seg.has_detached_particle_a):
                syl_tilt_val = -0.52
            elif is_focal_syl and seg.effort_mode not in ("SOULFUL_CONTEMPLATION", "SYMPATHY_SIGH"):
                syl_tilt_val = 0.44 if seg.role == "DIALOGUE" else 0.38
            elif seg.effort_mode == "SOULFUL_CONTEMPLATION":
                syl_tilt_val = -0.22 if not is_contrast_high else 0.12
            else:
                syl_tilt_val = (0.14 if seg.role == "DIALOGUE" else 0.08) if (s_idx % 2 == 1) else -0.10
            tilt_chunks.append(np.full(len(syl_wav), syl_tilt_val, dtype=np.float32))

            if pause_ms > 0 and not is_last_syl:
                pause_samples = int(self.sr * (pause_ms / 1000.0))
                comfort_gap = np.random.normal(0.0, 0.00007, size=pause_samples).astype(np.float32)
                processed_syllables_with_flag.append((comfort_gap, True))
                tilt_chunks.append(np.zeros(pause_samples, dtype=np.float32))

        out = self.stitch_syllables_smooth_crossfade(processed_syllables_with_flag) if processed_syllables_with_flag else audio

        raw_tilt_curve = np.concatenate(tilt_chunks) if tilt_chunks else np.zeros(len(out), dtype=np.float32)
        if len(raw_tilt_curve) != len(out):
            raw_tilt_curve = np.interp(
                np.linspace(0.0, 1.0, len(out), dtype=np.float32),
                np.linspace(0.0, 1.0, len(raw_tilt_curve), dtype=np.float32),
                raw_tilt_curve
            ).astype(np.float32)
        out = self.apply_continuous_segment_spectral_tilt(out, raw_tilt_curve)

        out = self.apply_phrase_bell_swell_and_breath_release(out, seg)

        if abs(seg.presence_boost_db) > 0.2:
            out = CrystalVocalMasteringDSP.run_biquad(
                out, self.sr, freq_hz=2650.0, gain_db=seg.presence_boost_db, q_factor=1.05, filter_type="peaking"
            )

        total_warmth_db = self.preset.chest_warmth_db + seg.warmth_boost_db + (1.2 if seg.is_sentence_end else 0.0)
        out = CrystalVocalMasteringDSP.run_biquad(
            out, self.sr, freq_hz=148.0, gain_db=total_warmth_db, q_factor=1.05, filter_type="peaking"
        )
        out = CrystalVocalMasteringDSP.run_biquad(
            out, self.sr, freq_hz=3150.0, gain_db=self.preset.harsh_cut_db, q_factor=2.20, filter_type="peaking"
        )

        if seg.grit_drive > 0.02:
            out = self.apply_vocal_cord_grit_and_attack(out, seg.grit_drive, self.sr)

        out = CrystalVocalMasteringDSP.run_biquad(
            out, self.sr, freq_hz=4350.0, gain_db=self.preset.clarity_presence_db, q_factor=1.15, filter_type="peaking"
        )
        air_shelf_freq = min(8000.0, self.sr * 0.42)
        out = CrystalVocalMasteringDSP.run_biquad(
            out, self.sr, freq_hz=air_shelf_freq, gain_db=self.preset.brilliance_shelf_db, q_factor=0.75, filter_type="highshelf"
        )

        out = CrystalVocalMasteringDSP.apply_dynamic_ear_comfort_soothe(
            out, self.sr, soothe_strength=self.preset.ear_soothe_strength
        )
        out = CrystalVocalMasteringDSP.apply_relative_smart_de_esser(
            out, self.sr, rel_threshold=self.preset.de_esser_rel_threshold
        )

        if self.enable_44k_air_upsample and self.sr <= 24000:
            out, out_sr = CrystalVocalMasteringDSP.upsample_2x_sinc_polyphase_with_air_exciter(out, self.sr, self.preset)
        else:
            out_sr = self.sr
            hi_src = CrystalVocalMasteringDSP.run_biquad(
                out, out_sr, freq_hz=min(4600.0, out_sr * 0.31), q_factor=0.95, filter_type="bandpass"
            )
            even_h = hi_src * np.abs(hi_src) * 2.8
            odd_h = np.tanh(hi_src * 2.3)
            harm_mix = (
                self.preset.even_tube_harmonic_weight * even_h
                + self.preset.odd_aphex_harmonic_weight * odd_h
            ).astype(np.float32)
            harmonics = CrystalVocalMasteringDSP.run_biquad(
                harm_mix, out_sr, freq_hz=min(7400.0, out_sr * 0.41), q_factor=0.707, filter_type="highpass"
            )
            out = (out + harmonics * (self.preset.air_exciter_mix * 0.70)).astype(np.float32)

        out = CrystalVocalMasteringDSP.apply_3band_ott_multiband_compressor(out, out_sr, self.preset)

        ambience_mix = self.preset.studio_ambience_mix * (1.20 if seg.effort_mode in ("SOLEMN_DECREE", "SOULFUL_CONTEMPLATION") else 1.0)
        out = CrystalVocalMasteringDSP.apply_studio_booth_micro_ambience(
            out, out_sr, mix_level=ambience_mix
        )

        return np.tanh(out * 1.04).astype(np.float32) * 0.955

    def stitch_segments_zero_click(
        self,
        rendered_segments: List[Tuple[np.ndarray, ProsodicSegment]]
    ) -> np.ndarray:
        chunks: List[np.ndarray] = []
        total = len(rendered_segments)
        eff_sr = self.output_sample_rate

        for idx, (audio, seg) in enumerate(rendered_segments):
            if len(audio) == 0:
                continue

            chunk = audio.copy()
            fade_in = min(int(eff_sr * 0.014), len(chunk) // 4)
            fade_out = min(int(eff_sr * 0.022), len(chunk) // 4)

            if fade_in > 0:
                t_in = np.linspace(0.0, np.pi / 2.0, fade_in, dtype=np.float32)
                chunk[:fade_in] *= (np.sin(t_in) ** 2)
            if fade_out > 0:
                t_out = np.linspace(0.0, np.pi / 2.0, fade_out, dtype=np.float32)
                chunk[-fade_out:] *= (np.cos(t_out) ** 2)

            chunks.append(chunk)

            if idx < total - 1 and seg.pause_after_ms > 0:
                gap_samples = int(eff_sr * (seg.pause_after_ms / 1000.0))
                white = np.random.normal(0.0, 0.00007, size=gap_samples).astype(np.float32)
                comfort_room_tone = np.convolve(white, [0.5, 0.3, 0.2], mode="same").astype(np.float32)
                chunks.append(comfort_room_tone)

        if not chunks:
            return np.array([], dtype=np.float32)
        return np.concatenate(chunks)


# ==============================================================================
# PHẦN 6: BỘ ĐIỀU PHỐI HỢP NHẤT TOÀN DIỆN V9.0 (UNIFIED MASTER ORCHESTRATOR)
# ==============================================================================
class UnifiedExpressiveTTSPipelineV9:
    """
    [ĐIỂM VÀO DUY NHẤT CHO APP CỦA BẠN - ALL-IN-ONE V9.0 PIPELINE]:
    Hợp nhất hoàn toàn:
    1. Làm sạch văn bản truyện convert (`ChapterTextSanitizerV8`).
    2. Phân tách chính xác Lời Thoại (`VOICE_DIALOGUE`) vs Lời Dẫn Truyện (`VOICE_NARRATOR`)
       với khóa cứng cấp độ đoạn văn (`DialogueNarrationClassifierV8`).
    3. Hút cảm xúc 2 chiều từ câu dẫn và nội dung câu thoại (`BiDirectionalDialogueEmotionEngine`).
    4. Lập kịch bản ngữ điệu 7 tầng và khuếch đại biểu cảm thoại 1.35x (`VietnameseProsodyPlanner`).
    5. Điêu khắc sóng âm khớp cứng 1:1 và làm trong/ấm giọng chuẩn phòng thu (`VietnameseProsodyDSP`).
    """

    def __init__(
        self,
        sample_rate: int = 22050,
        enable_44k_air_upsample: bool = False,
        clarity_preset_name: str = "SOULFUL_PODCAST_WARMTH"
    ):
        self.emotion_engine = BiDirectionalDialogueEmotionEngine()
        self.classifier = DialogueNarrationClassifierV8(self.emotion_engine)
        self.prosody_planner = VietnameseProsodyPlanner()
        self.prosody_dsp = VietnameseProsodyDSP(
            sample_rate=sample_rate,
            enable_44k_air_upsample=enable_44k_air_upsample,
            clarity_preset_name=clarity_preset_name
        )

    @staticmethod
    def _split_sentences_preserving_punctuation(text: str) -> List[str]:
        """Tách Span thành các câu nhưng giữ nguyên 100% trạng thái Role và Voice ID của Span mẹ."""
        parts = re.split(r"(?<=[.!?…])\s+", text.strip())
        return [p.strip() for p in parts if p and p.strip()]

    def plan_chapter(self, raw_chapter_text: str, base_length_scale: float = 1.0) -> List[ProsodicSegment]:
        """
        Bóc tách toàn bộ chương truyện thành danh sách `List[ProsodicSegment]` đã đồng bộ 100%
        giữa Vai đọc (`VOICE_DIALOGUE` / `VOICE_NARRATOR`), Cảm xúc 2 chiều (`effort_mode`)
        và Hồ sơ 7 tầng của từng âm tiết (`syllable_profiles`).
        """
        role_spans = self.classifier.classify_chapter_into_role_spans(raw_chapter_text)
        synchronized_segments: List[ProsodicSegment] = []

        for span in role_spans:
            sentences = self._split_sentences_preserving_punctuation(span.text)
            for sent in sentences:
                sent_segments = self.prosody_planner.plan_sentence(
                    sentence=sent,
                    base_length_scale=base_length_scale,
                    role=span.role,
                    voice_id=span.voice_id,
                    inherited_emotion=span.inherited_emotion,
                    full_span_text=span.text,
                    override_clause_emotion_fn=(
                        self.emotion_engine.resolve_dialogue_clause_emotion
                        if span.role == "DIALOGUE" else None
                    ),
                )
                for seg in sent_segments:
                    seg.paragraph_index = span.paragraph_index
                    seg.detection_reason = span.detection_reason
                    synchronized_segments.append(seg)

        return synchronized_segments

    def synthesize_and_sculpt_chapter(
        self,
        raw_chapter_text: str,
        tts_synthesize_fn: Callable[[str, str, float, float], np.ndarray],
        base_length_scale: float = 1.0
    ) -> np.ndarray:
        """
        Hàm thực thi Âm thanh Đầu-Cuối (End-to-End Synchronized Audio Renderer):
        - `tts_synthesize_fn(text, voice_id, length_scale, noise_scale) -> np.ndarray`:
          Hàm gọi model TTS Offline của bạn (tự động chọn model giọng theo `voice_id`:
          `VOICE_NARRATOR` hoặc `VOICE_DIALOGUE`).
        - Trả về mảng sóng âm `np.ndarray` (Float32) của toàn chương đã qua điêu khắc DSP.
        """
        segments = self.plan_chapter(raw_chapter_text, base_length_scale=base_length_scale)
        rendered_pairs: List[Tuple[np.ndarray, ProsodicSegment]] = []

        for seg in segments:
            raw_wav = tts_synthesize_fn(
                seg.text,
                seg.voice_id,
                seg.length_scale,
                seg.noise_scale
            )
            sculpted_wav = self.prosody_dsp.sculpt_segment_audio(raw_wav, seg)
            rendered_pairs.append((sculpted_wav, seg))

        return self.prosody_dsp.stitch_segments_zero_click(rendered_pairs)

    def debug_inspect_chapter_plan(self, raw_chapter_text: str, base_length_scale: float = 1.0) -> List[Dict[str, Any]]:
        """Hàm tiện ích giúp kiểm tra nhanh kết quả phân vai & cảm xúc từng cụm trên UI/Log."""
        segments = self.plan_chapter(raw_chapter_text, base_length_scale=base_length_scale)
        report: List[Dict[str, Any]] = []
        for idx, seg in enumerate(segments):
            report.append({
                "segment_index": idx,
                "paragraph_index": seg.paragraph_index,
                "role": seg.role,
                "voice_id": seg.voice_id,
                "effort_mode": seg.effort_mode,
                "inherited_emotion": seg.inherited_emotion,
                "length_scale": round(seg.length_scale, 3),
                "gain_db": round(seg.gain_db, 2),
                "pitch_shift_st": round(seg.pitch_shift_st, 2),
                "luyen_lay_curve": seg.luyen_lay_curve,
                "pause_after_ms": seg.pause_after_ms,
                "detection_reason": seg.detection_reason,
                "text": seg.text,
            })
        return report
