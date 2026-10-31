# -*- coding: utf-8 -*-
import json, re, sys, os
sys.stdout.reconfigure(encoding="utf-8")

books_dir = r"D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\saved_books"
ch_pattern = re.compile(r"^\s*(?:chương|hồi|tiết|quyển|phần|tập|bài|chapter|part)\s*[\d\w]+[:\s\.\-—].*", re.IGNORECASE)

for fname in os.listdir(books_dir):
    if not fname.endswith(".json") or fname == "library_index.json":
        continue
    fpath = os.path.join(books_dir, fname)
    try:
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            data = json.load(f)
        
        chs = data.get("chapters", [])
        if not chs:
            continue
        
        fixed_count = 0
        for i, ch in enumerate(chs):
            paras = ch.get("paragraphs", [])
            real_title = None
            for p in paras[:5]:
                p_strip = p.strip()
                if ch_pattern.match(p_strip) and len(p_strip) < 95:
                    real_title = p_strip
                    break
            
            if real_title:
                if ch.get("title") != real_title:
                    ch["title"] = real_title
                    fixed_count += 1
            elif i == 0 and paras and "Table of Contents" in paras[0]:
                ch["title"] = "Mục lục"
                fixed_count += 1
            elif i == 1 and paras and "Thông tin" in paras[0]:
                ch["title"] = "Thông tin Ebook"
                fixed_count += 1
            elif i == 2 and paras and "Trang 1# 1" in paras[0]:
                ch["title"] = "Giới thiệu truyện"
                fixed_count += 1

        if fixed_count > 0:
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            print(f"Fixed {fixed_count} chapter titles in {fname} ({data.get('title')})")
    except Exception as e:
        print(f"Error fixing {fname}: {e}")

print("Saved books titles updated successfully!")
