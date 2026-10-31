import re

FEMALE_NAMES = set([
    'tuyết', 'liên', 'như', 'oanh', 'uyển', 'quỳnh', 'nga', 'loan', 'kiều', 'hân',
    'thùy', 'trang', 'diễm', 'trâm', 'châu', 'thục', 'huyên', 'bích', 'thúy', 'mai',
    'lan', 'cúc', 'trúc', 'hương', 'vy', 'mỹ', 'thảo', 'uyên', 'điệp', 'yến', 'phượng'
])
MALE_NAMES = set([
    'phong', 'viêm', 'hàn', 'phàm', 'hạo', 'kiệt', 'dũng', 'cường', 'tuấn', 'khang',
    'thắng', 'vĩnh', 'đức', 'tráng', 'mãnh', 'thạch', 'trần', 'bá', 'lâm', 'quang',
    'hoàng', 'bảo', 'huy', 'minh', 'sơn', 'long', 'thiên', 'trung', 'hiếu', 'nghĩa'
])

def test_character_names(text):
    female_titles = r'(?:nàng|cô|cô ấy|cô gái|ả|thị|bà|tiểu thư|cô nương|tiểu nha đầu|sư muội|sư tỷ|tỷ tỷ|muội muội|tiên tử|thánh nữ|mẫu thân|mẹ|nữ tử|công chúa|nương tử|thiếu nữ|phu nhân|nha hoàn|bà lão|mỹ phụ|nữ nhi|sư nương)'
    male_titles = r'(?:hắn|chàng|y|gã|anh|anh ấy|ông|công tử|sư huynh|sư đệ|huynh đệ|phụ thân|cha|nam tử|huynh trưởng|thiếu niên|đại ca|lão giả|đạo nhân|lão tổ|môn chủ|chưởng môn|tông chủ|tiểu tử|trượng phu|nam nhân|lão quái|lão ma|thiếu gia)'
    speech_verbs = r'(?:nói|hỏi|đáp|cười|thì thào|thốt|bảo|nghĩ|lẩm bẩm|thở dài|khẽ nói|trầm giọng|gầm|quát|lên tiếng|tiếp lời|hô|la)'

    # Name match after quote: case-sensitive for Capitalized Names!
    name_m = re.search(rf'^[,\s\-\–\—]*([A-ZÀ-Ỹ][a-zà-ỹ]+(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]+)*)(?:\s+(.*?))?\s*{speech_verbs}', text)
    if name_m:
        cand = name_m.group(1).strip()
        last_word = cand.lower().split()[-1]
        if last_word in FEMALE_NAMES: return f"female ({cand})"
        if last_word in MALE_NAMES: return f"male ({cand})"
        return f"neutral ({cand})"
    return "no_name"

tests = [
    "- Đi thôi! - Diệp Phong nói.",
    "- Ngươi là ai? - Tiêu Viêm trầm giọng hỏi.",
    "- Ta không biết. - Liễu Như Yên thở dài.",
    "- Đa tạ công tử. - Bạch Tuyết khẽ cười đáp.",
]

for i, t in enumerate(tests):
    d_content = re.sub(r'^[\-\–\—]\s*', '', t)
    dash_m = re.match(r'^(.+?[!?.…])[\s\-\–\—,:]+([A-ZÀ-Ỹa-zà-ỹ].*)$', d_content)
    outer = dash_m.group(2).strip() if dash_m else ''
    res = test_character_names(outer)
    print(f"Test {i}: -> {res.encode('ascii', 'ignore').decode()}")
