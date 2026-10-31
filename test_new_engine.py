import json
import re

FEMALE_NAME_KEYWORDS = ['tuyết', 'liên', 'ngọc', 'nhi', 'yến', 'nhược', 'dao', 'mộng', 'tiên', 'linh', 'vũ', 'cầm', 'nghiên', 'dung', 'thiến', 'điệp', 'mai', 'lan', 'cúc', 'trúc', 'hương', 'vy', 'my', 'thảo', 'uyên', 'diễm', 'thanh', 'hà', 'phương', 'an', 'trâm', 'quỳnh', 'châu', 'tú', 'phượng', 'thư', 'thục', 'huyên', 'thiền', 'tịnh', 'nga', 'loan', 'kiều', 'hân', 'thùy', 'trang']
MALE_NAME_KEYWORDS = ['long', 'thiên', 'phong', 'viêm', 'hàn', 'trần', 'mặc', 'chiến', 'bá', 'lôi', 'bằng', 'hạo', 'kiệt', 'phàm', 'lâm', 'động', 'đằng', 'đạt', 'huy', 'minh', 'sơn', 'bảo', 'nam', 'bắc', 'hải', 'quân', 'thành', 'trung', 'hiếu', 'nghĩa', 'trí', 'trọng', 'thần', 'nguyên', 'quang', 'hoàng', 'đại', 'tiêu', 'binh', 'hùng', 'dũng', 'cường', 'tuấn', 'vũ', 'kiếm', 'đao', 'nhạc', 'thương', 'ngạo', 'độc']

MALE_PRONOUNS = ['hắn', 'y', 'gã', 'lão', 'tên này', 'tiểu tử này', 'chàng', 'nam tử này', 'hắn ta']
FEMALE_PRONOUNS = ['nàng', 'ả', 'thị', 'cô', 'nha đầu này', 'nàng ta', 'cô ấy', 'nữ tử này', 'tiểu nương tử']

MALE_TITLES = ['sư huynh', 'sư đệ', 'sư thúc', 'sư bá', 'công tử', 'thiếu gia', 'đạo huynh', 'lão tổ', 'lão quái', 'lão ma', 'chân nhân', 'tiên sinh', 'thánh tử', 'thiếu chủ', 'tiểu tử', 'đại hán', 'lão giả', 'chưởng môn', 'tông chủ', 'vương gia', 'hoàng thượng', 'trượng phu', 'nam nhân', 'nam tử', 'tiểu sinh', 'phụ thân', 'cha', 'đại ca', 'huynh đệ', 'huynh trưởng']
FEMALE_TITLES = ['sư tỷ', 'sư muội', 'sư thái', 'tiên tử', 'cô nương', 'tiểu thư', 'nương tử', 'phu nhân', 'thánh nữ', 'yêu nữ', 'ma nữ', 'lão mẫu', 'bà bà', 'nha đầu', 'thiếu phụ', 'mỹ phụ', 'nữ nhi', 'công chúa', 'sư nương', 'mẫu thân', 'mẹ', 'tiểu nha đầu', 'tiểu nữ hài', 'bà lão', 'bà nội', 'bà ngoại']

registry = {}
lastDialogueGender = 'male'

def analyze(text, nextText='', prevText=''):
    global lastDialogueGender, registry
    trimmed = text.strip()
    isQuote = bool(re.match(r'^[“"«「『]', trimmed) or re.match(r'^[-–—]\s*', trimmed) or re.search(r'[“"«「『][^”"»」』]+[”"»」』]', trimmed))
    if not isQuote:
        return {'isDialogue': False, 'gender': 'narration'}

    dialogueContent = trimmed
    sameSentenceOuter = ''
    quoteMatch = re.search(r'[“"«「『]([^”"»」』]+)[”"»」』]', trimmed)
    if quoteMatch:
        dialogueContent = quoteMatch.group(1)
        sameSentenceOuter = trimmed.replace(quoteMatch.group(0), ' ').strip()
    elif re.match(r'^[-–—]', trimmed):
        dashMatch = re.match(r'^(.+?[!?.…])\s+([A-ZÀ-Ỹa-zà-ỹ].*)$', re.sub(r'^[-–—]\s*', '', trimmed))
        if dashMatch:
            dialogueContent = dashMatch.group(1).strip()
            sameSentenceOuter = dashMatch.group(2).strip()
        else:
            dialogueContent = re.sub(r'^[-–—]\s*', '', trimmed)

    leadOut = (sameSentenceOuter or nextText or '').strip()
    leadIn = (prevText or '').strip()

    speaker = ''
    manner = ''
    verb = ''

    if leadOut:
        nameMatch = re.match(r'^([A-ZÀ-Ỹ][a-zà-ỹ]+(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]+)*)(?:\s+(.*?))?\s*(lên tiếng|nói|hỏi|đáp|hừ(?:\s+một\s+tiếng)?|quát(?:\s+lớn)?|thét|gầm(?:\s+lên)?|rống|la|cười(?:\s+lạnh|\s+khẽ|\s+nhạt|\s+gượng|\s+lớn|\s+một\s+tiếng)?|thầm|bảo|thì thào|thỏ thẻ|than|lẩm bẩm|thốt lên|nhủ|nghĩ|truyền âm|tiếp lời|khẽ nói|hô)(?:[,.;:!?…\s]|$)', leadOut)
        if nameMatch:
            speaker = nameMatch.group(1).strip()
            manner = (nameMatch.group(2) or '').strip()
            verb = (nameMatch.group(3) or '').strip()
        else:
            pronounMatch = re.match(r'^([A-ZÀ-Ỹa-zà-ỹ0-9\s]+?)\s+([a-zà-ỹ\s]*?)(lên tiếng|nói|hỏi|đáp|hừ(?:\s+một\s+tiếng)?|quát(?:\s+lớn)?|thét|gầm(?:\s+lên)?|rống|la|cười(?:\s+lạnh|\s+khẽ|\s+nhạt|\s+gượng|\s+lớn|\s+một\s+tiếng)?|thầm|bảo|thì thào|thỏ thẻ|than|lẩm bẩm|thốt lên|nhủ|nghĩ|truyền âm|tiếp lời|khẽ nói|hô)(?:[,.;:!?…\s]|$)', leadOut, re.IGNORECASE)
            if pronounMatch:
                speaker = pronounMatch.group(1).strip()
                manner = (pronounMatch.group(2) or '').strip()
                verb = (pronounMatch.group(3) or '').strip()

    if not speaker and leadIn:
        leadInMatch = re.search(r'([A-ZÀ-Ỹ][a-zà-ỹ]+(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]+)*|[a-zà-ỹ0-9\s]+?)\s+(.*?)\s*(?:nói|hỏi|đáp|lên tiếng|bảo|quát|nhủ|nghĩ)[:]\s*$', leadIn, re.IGNORECASE)
        if leadInMatch:
            speaker = leadInMatch.group(1).strip()
            manner = (leadInMatch.group(2) or '').strip()

    cleanSp = speaker.strip()
    cached = registry.get(cleanSp)

    fullContextWindow = f"{leadIn} {cleanSp} {manner} {verb} {leadOut}".lower()
    windowTokens = [t for t in re.split(r'[\s,.;:!?…–—"“«»”]+', fullContextWindow) if t]

    mPronounHit = any(p in fullContextWindow if ' ' in p else p in windowTokens for p in MALE_PRONOUNS)
    fPronounHit = any(p in fullContextWindow if ' ' in p else p in windowTokens for p in FEMALE_PRONOUNS)

    gender = 'neutral'
    confidence = 0.5
    bestSource = ''

    if cached and cached['confidence'] >= 0.85 and not (mPronounHit and cached['gender'] == 'female') and not (fPronounHit and cached['gender'] == 'male'):
        gender = cached['gender']
        confidence = cached['confidence']
        bestSource = cached['source'] + ' (từ Sổ tay)'
    else:
        mScore = 0.0
        fScore = 0.0

        if mPronounHit and not fPronounHit:
            mScore += 10.0
            bestSource = 'Đại từ (hắn/y...)'
        elif fPronounHit and not mPronounHit:
            fScore += 10.0
            bestSource = 'Đại từ (nàng/ả...)'

        mTitleHit = any(t in fullContextWindow if ' ' in t else t in windowTokens for t in MALE_TITLES)
        fTitleHit = any(t in fullContextWindow if ' ' in t else t in windowTokens for t in FEMALE_TITLES)

        if mTitleHit and not fTitleHit:
            mScore += 6.0
            if not bestSource: bestSource = 'Danh xưng (sư huynh/công tử...)'
        elif fTitleHit and not mTitleHit:
            fScore += 6.0
            if not bestSource: bestSource = 'Danh xưng (sư tỷ/tiên tử...)'

        if cleanSp:
            spTokens = cleanSp.lower().split()
            givenName = spTokens[-1]
            middleName = spTokens[-2] if len(spTokens) > 1 else ''

            if givenName in FEMALE_NAME_KEYWORDS:
                fScore += 4.0
                if not bestSource: bestSource = f'Tên Hán Việt ({givenName})'
            if middleName in FEMALE_NAME_KEYWORDS:
                fScore += 2.0
                if not bestSource: bestSource = f'Tên đệm ({middleName})'

            if givenName in MALE_NAME_KEYWORDS:
                mScore += 4.0
                if not bestSource: bestSource = f'Tên Hán Việt ({givenName})'
            if middleName in MALE_NAME_KEYWORDS:
                mScore += 2.0
                if not bestSource: bestSource = f'Tên đệm ({middleName})'

        if fScore > mScore:
            gender = 'female'
            confidence = 1.0 if fScore >= 10.0 else (0.95 if fScore >= 6.0 else (0.85 if fScore >= 4.0 else 0.70))
        elif mScore > fScore:
            gender = 'male'
            confidence = 1.0 if mScore >= 10.0 else (0.95 if mScore >= 6.0 else (0.85 if mScore >= 4.0 else 0.70))
        else:
            gender = 'female' if lastDialogueGender == 'male' else 'male'
            confidence = 0.50
            bestSource = 'Luân phiên (Turn-taking)'

        if cleanSp and confidence >= 0.70:
            registry[cleanSp] = {'gender': gender, 'confidence': confidence, 'source': bestSource}

    lastDialogueGender = gender
    return {
        'speaker': cleanSp,
        'gender': gender,
        'confidence': confidence,
        'source': bestSource,
        'dialogue': dialogueContent
    }

test_cases = [
    "Bạch Tiểu Thuần vỗ ngực, hắn cười lớn nói: \"Ta chính là thiên tài!\"",
    "\"Sư đệ đừng làm càn!\" - Nam Cung Uyển khẽ nói.",
    "- không có hứng thú! Lữ Tuyết lạnh lùng lên tiếng.",
    "\"Diệp Phàm, ngươi dám!\" - Vương Đằng giận dữ hét lên.",
    "Bạch Tiểu Thuần lại tiếp lời: \"Mau giao linh thạch ra!\"",
]

for tc in test_cases:
    res = analyze(tc)
    print(f"INPUT: {tc[:55]}...")
    print(f" -> Speaker: '{res['speaker']}', Gender: {res['gender']}, Conf: {res['confidence']}, Source: {res['source']}\n")

print("FINAL REGISTRY:")
print(json.dumps(registry, ensure_ascii=False, indent=2))
