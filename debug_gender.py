cleanSp = "Lữ Tuyết lạnh lùng"
manner = ""
leadOut = "Lữ Tuyết lạnh lùng lên tiếng."

FEMALE_NAME_KEYWORDS = ['tuyết', 'nhi', 'nguyệt', 'băng', 'dao', 'mai', 'lan', 'cúc', 'trúc', 'linh', 'hương', 'vy', 'my', 'thảo', 'dung', 'uyên', 'diễm', 'thanh', 'hà', 'phương', 'an', 'trâm', 'quỳnh', 'ngọc', 'châu', 'tú', 'yến', 'phượng', 'liên', 'thư', 'thục', 'huyên', 'mộng', 'thiền']
MALE_NAME_KEYWORDS = ['tiêu', 'phong', 'hạo', 'binh', 'hùng', 'dũng', 'long', 'cường', 'tuấn', 'kiệt', 'vũ', 'đạt', 'huy', 'minh', 'sơn', 'bảo', 'nam', 'bắc', 'hải', 'quân', 'thành', 'trung', 'hiếu', 'nghĩa', 'trí', 'trọng', 'thần', 'viêm', 'nguyên', 'quang', 'hoàng', 'bá', 'đại']
FEMALE_TITLES = ['nàng', 'cô ấy', 'tiểu thư', 'sư muội', 'tỷ tỷ', 'mẫu thân', 'mẹ', 'nữ tử', 'công chúa', 'nương tử', 'thiếu nữ', 'phu nhân', 'muội muội', 'tiên tử', 'thánh nữ', 'nha hoàn', 'bà lão', 'mỹ phụ', 'nữ nhi', 'sư tôn', 'sư nương', 'tiểu nha đầu', 'tiểu nữ hài', 'cô nương', 'bà nội', 'bà ngoại']
MALE_TITLES = ['chàng', 'hắn', 'công tử', 'sư huynh', 'huynh đệ', 'phụ thân', 'cha', 'nam tử', 'huynh trưởng', 'thiếu niên', 'đại ca', 'lão giả', 'đạo nhân', 'lão tổ', 'môn chủ', 'chưởng môn', 'tông chủ', 'tiểu tử', 'gã', 'y', 'trượng phu', 'nam nhân', 'hoàng thượng', 'vương gia', 'tiểu sinh']

lowerSp = cleanSp.lower()
spWords = lowerSp.split()
fullContext = f"{lowerSp} {manner.lower()} {leadOut[:120].lower()}"

fScore = 0
mScore = 0

for w in spWords:
    if w in FEMALE_NAME_KEYWORDS:
        fScore += 3
        print(f"FEMALE keyword hit: {w}")
    if w in MALE_NAME_KEYWORDS:
        mScore += 3
        print(f"MALE keyword hit: {w}")

for t in FEMALE_TITLES:
    if t in fullContext:
        fScore += 3
        print(f"FEMALE title hit: {t}")

for t in MALE_TITLES:
    if t in fullContext:
        mScore += 3
        print(f"MALE title hit: {t}")

print(f"fScore={fScore}, mScore={mScore}")
