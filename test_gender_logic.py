import re

def test_gender_logic(prev, curr, next_s):
    # Trích xuất thoại
    m_quote = re.search(r'[“"«「『]([^”"»」』]+)[”"»」』]', curr)
    if m_quote:
        d_content = m_quote.group(1).strip()
        outer = curr.replace(m_quote.group(0), ' ').strip()
    elif re.match(r'^[\-\–\—]', curr.strip()):
        d_content = re.sub(r'^[\-\–\—]\s*', '', curr.strip())
        # Check if dash followed by dialogue then outer
        dash_m = re.match(r'^(.+?[!?.…])[\s\-\–\—,:]+([A-ZÀ-Ỹa-zà-ỹ].*)$', d_content)
        if dash_m:
            d_content = dash_m.group(1).strip()
            outer = dash_m.group(2).strip()
        else:
            outer = ''
    else:
        return 'not_dialogue'

    lead_out = (outer or next_s or '').strip()
    lead_in = (prev or '').strip()

    female_titles = r'(?:nàng|cô|cô ấy|cô gái|ả|thị|bà|tiểu thư|cô nương|tiểu nha đầu|sư muội|sư tỷ|tỷ tỷ|muội muội|tiên tử|thánh nữ|mẫu thân|mẹ|nữ tử|công chúa|nương tử|thiếu nữ|phu nhân|nha hoàn|bà lão|mỹ phụ|nữ nhi|sư nương)'
    male_titles = r'(?:hắn|chàng|y|gã|anh|anh ấy|ông|công tử|sư huynh|sư đệ|huynh đệ|phụ thân|cha|nam tử|huynh trưởng|thiếu niên|đại ca|lão giả|đạo nhân|lão tổ|môn chủ|chưởng môn|tông chủ|tiểu tử|trượng phu|nam nhân|lão quái|lão ma|thiếu gia)'
    speech_verbs = r'(?:nói|hỏi|đáp|cười|thì thào|thốt|bảo|nghĩ|lẩm bẩm|thở dài|khẽ nói|trầm giọng|gầm|quát|lên tiếng|tiếp lời|hô|la)'

    # 1. Direct lead_out tag: "... " - hắn nói / nàng nói
    # Pattern A: [Subject] [SpeechVerb]
    f_lead_out = re.search(rf'^[,\s\-\–\—]*{female_titles}\s+(?:[a-zà-ỹ\s]*?){speech_verbs}', lead_out, re.I)
    m_lead_out = re.search(rf'^[,\s\-\–\—]*{male_titles}\s+(?:[a-zà-ỹ\s]*?){speech_verbs}', lead_out, re.I)

    # Subject-Object pattern: hắn nhìn nàng nói vs nàng nhìn hắn nói
    f_subj_obj = re.search(rf'^[,\s\-\–\—]*{female_titles}\s+(?:nhìn|hướng|quay sang|đối|với)\s+{male_titles}\s*{speech_verbs}', lead_out, re.I)
    m_subj_obj = re.search(rf'^[,\s\-\–\—]*{male_titles}\s+(?:nhìn|hướng|quay sang|đối|với)\s+{female_titles}\s*{speech_verbs}', lead_out, re.I)

    if f_subj_obj: return 'female'
    if m_subj_obj: return 'male'
    if f_lead_out and not m_lead_out: return 'female'
    if m_lead_out and not f_lead_out: return 'male'

    # 2. Direct lead_in tag: Hắn nhìn nàng nói: "..." vs Nàng mỉm cười: "..."
    f_lead_in = re.search(rf'{female_titles}\s+(?:[a-zà-ỹ\s]*?){speech_verbs}[:]\s*$', lead_in, re.I)
    m_lead_in = re.search(rf'{male_titles}\s+(?:[a-zà-ỹ\s]*?){speech_verbs}[:]\s*$', lead_in, re.I)
    f_in_subj_obj = re.search(rf'{female_titles}\s+(?:nhìn|hướng|quay sang|đối|với)\s+{male_titles}\s*{speech_verbs}[:]\s*$', lead_in, re.I)
    m_in_subj_obj = re.search(rf'{male_titles}\s+(?:nhìn|hướng|quay sang|đối|với)\s+{female_titles}\s*{speech_verbs}[:]\s*$', lead_in, re.I)

    if f_in_subj_obj: return 'female'
    if m_in_subj_obj: return 'male'
    if f_lead_in and not m_lead_in: return 'female'
    if m_lead_in and not f_lead_in: return 'male'

    # 3. Inside dialogue pronouns (first person)
    f_self = ['tiểu nữ', 'thiếp', 'thiếp thân', 'nô gia', 'nô tỳ', 'bản cung', 'tiểu muội', 'bần ni', 'lão thân', 'bản cô nương']
    m_self = ['tại hạ', 'lão phu', 'bản tọa', 'bổn tọa', 'bần đạo', 'lão nạp', 'bản công tử', 'tiểu sinh', 'mỗ', 'vi sư', 'mạt tướng', 'bản vương', 'bổn vương', 'trẫm', 'bản tôn', 'bổn tôn', 'tiểu tử', 'vi huynh', 'lão hủ']
    d_lower = d_content.lower()
    first_words = ' '.join(d_lower.split()[:8])
    for w in f_self:
        if w in first_words: return 'female'
    for w in m_self:
        if w in first_words: return 'male'

    # 4. Intimate addressing
    f_to_m = ['chàng', 'phu quân', 'tướng công', 'huynh à', 'sư huynh của muội']
    m_to_f = ['nương tử', 'tiểu thư', 'cô nương', 'tiểu nha đầu', 'ái phi', 'nàng ơi', 'sư muội của ta']
    for w in f_to_m:
        if w in first_words: return 'female'
    for w in m_to_f:
        if w in first_words: return 'male'

    return 'neutral'

samples = [
    ("", "- Đi thôi! - Hắn trầm giọng nói.", ""),
    ("", "- Muội không sao chứ? - Hắn nhìn nàng hỏi.", ""),
    ("", "- Thiếp không sao. - Nàng khẽ đáp.", ""),
    ("Hắn lạnh lùng nhìn đối phương nói:", "“Ngươi muốn chết sao?”", ""),
    ("Nàng mỉm cười nói:", "“Huynh cứ đùa.”", ""),
    ("", "- Tiểu nữ bái kiến tiền bối.", ""),
    ("", "- Lão phu há lại sợ ngươi?", ""),
    ("", "- Phu quân, chàng đã về rồi!", ""),
    ("", "- Nương tử, nàng vất vả rồi.", ""),
    ("", "- Hắn quay đầu lại nhìn đối phương.", ""), # not dialogue
]

for i, (p, c, n) in enumerate(samples):
    res = test_gender_logic(p, c, n)
    print(f"Sample {i}: -> {res}")
