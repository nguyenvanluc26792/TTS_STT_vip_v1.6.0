import sys, re
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

def clean_comma(text):
    text = re.sub(r'[\u200B-\u200D\uFEFF\u00AD]', '', text)
    text = re.sub(r'[\t\xa0\u1680\u2000-\u200a\u202f\u205f\u3000]+', ' ', text)
    # Xóa sạch khoảng trắng trước dấu câu
    text = re.sub(r'\s+([,.;:!?\)\]”’»])', r'\1', text)
    # Quy tắc vàng: Ép sau dấu phẩy CHỈ CÓ ĐÚNG 1 DẤU CÁCH DUY NHẤT
    text = re.sub(r'\s*,\s*', ', ', text)
    # Xóa mọi chuỗi 2 dấu cách trở lên
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()

t1 = 'được, chuyện trực tiếp náo đến chỗ tổng giáo quan.'
t2 = 'được,  chuyện trực tiếp náo đến chỗ tổng giáo quan.'
t3 = 'được,   chuyện trực tiếp náo đến chỗ tổng giáo quan.'
t4 = 'được ,\u3000chuyện trực tiếp náo đến chỗ tổng giáo quan.'

print(repr(clean_comma(t1)))
print(repr(clean_comma(t2)))
print(repr(clean_comma(t3)))
print(repr(clean_comma(t4)))
assert clean_comma(t1) == clean_comma(t2) == clean_comma(t3) == clean_comma(t4)
print('ALL EQUAL 100%!')
