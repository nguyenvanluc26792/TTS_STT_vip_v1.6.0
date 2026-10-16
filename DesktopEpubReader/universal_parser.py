import os
import re
import json
import uuid
import shutil
import hashlib
import tempfile
from pathlib import Path
from bs4 import BeautifulSoup
import charset_normalizer

# Optional / Specific format libraries
try:
    import ebooklib
    from ebooklib import epub
except ImportError:
    ebooklib = None
    epub = None

try:
    import pypdf
except ImportError:
    pypdf = None

try:
    import docx
except ImportError:
    docx = None

try:
    import openpyxl
except ImportError:
    openpyxl = None

try:
    import mobi
except ImportError:
    mobi = None

try:
    import olefile
except ImportError:
    olefile = None


CHAPTER_REGEX = re.compile(
    r'^\s*(?:hồi|chương|tiết|quyển|phần|tập|bài|mục|đoạn|chapter|part|vol|volume|book|act|scene)\s*[\d\w\.\-—:\s]+.*$',
    re.IGNORECASE | re.UNICODE
)


def clean_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    for tag in soup(["script", "style", "noscript", "iframe"]):
        tag.extract()
    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines


def split_paragraphs(lines, max_len=320):
    paragraphs = []
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
        if len(line_clean) > max_len:
            # Tách theo dấu câu . ! ? …
            parts = re.split(r'([.!?…]+[\s\n]+)', line_clean)
            buf = ""
            for i in range(0, len(parts) - 1, 2):
                sentence = (parts[i] + parts[i + 1]).strip()
                if len(buf) + len(sentence) < max_len:
                    buf += (" " if buf else "") + sentence
                else:
                    if buf:
                        paragraphs.append(buf)
                    buf = sentence
            if len(parts) % 2 != 0 and parts[-1].strip():
                buf += (" " if buf else "") + parts[-1].strip()
            if buf:
                paragraphs.append(buf)
        else:
            paragraphs.append(line_clean)
    return paragraphs


def group_paragraphs_into_chapters(all_paragraphs, default_title="Chương", chunk_size=55):
    """
    Tự động nhận diện tiêu đề chương từ danh sách đoạn văn.
    Nếu không có tiêu đề chương rõ ràng, tự chia thành từng phần hợp lý để điều hướng.
    """
    chapters = []
    curr_chapter_title = None
    curr_paras = []

    for p in all_paragraphs:
        # Kiểm tra xem đoạn văn này có phải là tiêu đề chương không
        is_heading = False
        if len(p) <= 90:
            if CHAPTER_REGEX.match(p) or re.match(r'^\s*(?:thứ|hồi|chương)\s+[\d\w]+\b', p, re.IGNORECASE):
                is_heading = True

        if is_heading:
            if curr_paras:
                c_idx = len(chapters) + 1
                c_title = curr_chapter_title or f"{default_title} {c_idx}"
                chapters.append({
                    "index": len(chapters),
                    "title": c_title,
                    "paragraphs": curr_paras
                })
                curr_paras = []
            curr_chapter_title = p
        else:
            curr_paras.append(p)

    if curr_paras:
        c_idx = len(chapters) + 1
        c_title = curr_chapter_title or f"{default_title} {c_idx}"
        chapters.append({
            "index": len(chapters),
            "title": c_title,
            "paragraphs": curr_paras
        })

    # Nếu sau khi quét mà chỉ có đúng 1 chương và số đoạn văn quá nhiều (> 75), tự phân đoạn thành từng chương
    if len(chapters) <= 1 and all_paragraphs:
        chapters = []
        for i in range(0, len(all_paragraphs), chunk_size):
            chunk = all_paragraphs[i:i + chunk_size]
            c_idx = len(chapters) + 1
            chapters.append({
                "index": len(chapters),
                "title": f"Phần {c_idx} (Đoạn {i + 1} - {i + len(chunk)})",
                "paragraphs": chunk
            })

    return chapters


# =========================================================================
# CÁC BỘ PHÂN TÍCH TỪNG ĐỊNH DẠNG TÀI LIỆU
# =========================================================================

def parse_epub_file(filepath, filename=""):
    if not epub:
        raise ImportError("Thư viện EbookLib chưa được cài đặt")

    book = epub.read_epub(filepath)
    title_meta = book.get_metadata('DC', 'title')
    title_str = title_meta[0][0] if title_meta else Path(filename or filepath).stem

    creator_meta = book.get_metadata('DC', 'creator')
    author_str = creator_meta[0][0] if creator_meta else "Tác giả chưa rõ"

    chapters = []
    c_idx = 1
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            content = item.get_content().decode('utf-8', errors='ignore')
            lines = clean_html(content)
            if lines:
                paras = split_paragraphs(lines)
                if paras:
                    c_title = paras[0] if len(paras[0]) < 80 else f"Chương {c_idx}"
                    chapters.append({
                        "index": c_idx - 1,
                        "title": c_title,
                        "paragraphs": paras
                    })
                    c_idx += 1

    return title_str, author_str, chapters


def parse_txt_file(filepath, filename=""):
    with open(filepath, "rb") as f:
        raw_bytes = f.read()

    detection = charset_normalizer.from_bytes(raw_bytes).best()
    encoding = detection.encoding if detection else "utf-8"

    try:
        text = raw_bytes.decode(encoding, errors="replace")
    except Exception:
        text = raw_bytes.decode("utf-8", errors="ignore")

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    paras = split_paragraphs(lines)

    title_str = Path(filename or filepath).stem
    author_str = "Tác giả chưa rõ"

    chapters = group_paragraphs_into_chapters(paras, default_title="Chương")
    return title_str, author_str, chapters


def parse_html_file(filepath, filename=""):
    with open(filepath, "rb") as f:
        raw_bytes = f.read()

    detection = charset_normalizer.from_bytes(raw_bytes).best()
    encoding = detection.encoding if detection else "utf-8"

    try:
        html_content = raw_bytes.decode(encoding, errors="replace")
    except Exception:
        html_content = raw_bytes.decode("utf-8", errors="ignore")

    soup = BeautifulSoup(html_content, 'html.parser')

    # Lấy tiêu đề từ thẻ title hoặc h1
    title_el = soup.find('title')
    title_str = title_el.get_text().strip() if title_el else Path(filename or filepath).stem
    author_str = "Tác giả chưa rõ"

    meta_author = soup.find('meta', attrs={'name': 'author'})
    if meta_author and meta_author.get('content'):
        author_str = meta_author['content'].strip()

    lines = clean_html(html_content)
    paras = split_paragraphs(lines)
    chapters = group_paragraphs_into_chapters(paras, default_title="Chương")
    return title_str, author_str, chapters


def parse_docx_file(filepath, filename=""):
    if not docx:
        raise ImportError("Thư viện python-docx chưa được cài đặt")

    doc = docx.Document(filepath)
    title_str = doc.core_properties.title or Path(filename or filepath).stem
    author_str = doc.core_properties.author or "Tác giả chưa rõ"

    chapters = []
    curr_chapter_title = None
    curr_paras = []

    for p in doc.paragraphs:
        txt = p.text.strip()
        if not txt:
            continue

        is_heading = False
        style_name = p.style.name.lower() if p.style and p.style.name else ""
        if 'heading' in style_name or 'title' in style_name:
            is_heading = True
        elif len(txt) <= 85 and CHAPTER_REGEX.match(txt):
            is_heading = True

        if is_heading:
            if curr_paras:
                c_idx = len(chapters) + 1
                chapters.append({
                    "index": len(chapters),
                    "title": curr_chapter_title or f"Chương {c_idx}",
                    "paragraphs": curr_paras
                })
                curr_paras = []
            curr_chapter_title = txt
        else:
            sub_paras = split_paragraphs([txt])
            curr_paras.extend(sub_paras)

    if curr_paras:
        c_idx = len(chapters) + 1
        chapters.append({
            "index": len(chapters),
            "title": curr_chapter_title or f"Chương {c_idx}",
            "paragraphs": curr_paras
        })

    if not chapters:
        chapters.append({
            "index": 0,
            "title": "Chương 1",
            "paragraphs": ["Tài liệu không có nội dung chữ."]
        })

    return title_str, author_str, chapters


def parse_doc_file(filepath, filename=""):
    """Phân tích file Word cổ điển định dạng .doc (Microsoft Word 97-2003 OLE Binary)"""
    title_str = Path(filename or filepath).stem
    author_str = "Tác giả chưa rõ"

    lines = []
    if olefile and olefile.isOleFile(filepath):
        try:
            ole = olefile.OleFileIO(filepath)
            # Lấy thông tin metadata nếu có
            if ole.exists('\x05SummaryInformation'):
                try:
                    summary = ole.getproperties('\x05SummaryInformation')
                    if summary.get(2):  # Title
                        title_str = str(summary[2]).strip()
                    if summary.get(4):  # Author
                        author_str = str(summary[4]).strip()
                except Exception:
                    pass

            if ole.exists('WordDocument'):
                stream = ole.openstream('WordDocument').read()
                # Trích xuất các chuỗi ký tự unicode tiếng Việt / ASCII có thể đọc được
                raw_text = stream.decode('latin-1', errors='ignore')
                extracted_lines = re.findall(r'[\w\s,.\'\"!?\-—:;()]{8,}', raw_text)
                for l in extracted_lines:
                    cleaned = l.strip()
                    if len(cleaned) >= 12 and not cleaned.startswith('\x00'):
                        lines.append(cleaned)
        except Exception as e:
            print("Lỗi đọc OLE doc:", e)

    if not lines:
        # Fallback đọc binary regex
        with open(filepath, "rb") as f:
            content = f.read().decode('latin-1', errors='ignore')
            lines = [l.strip() for l in re.findall(r'[\w\s,.\'\"!?\-—:;()]{12,}', content) if len(l.strip()) > 15]

    paras = split_paragraphs(lines)
    chapters = group_paragraphs_into_chapters(paras, default_title="Chương")
    return title_str, author_str, chapters


def parse_pdf_file(filepath, filename=""):
    if not pypdf:
        raise ImportError("Thư viện pypdf chưa được cài đặt")

    reader = pypdf.PdfReader(filepath)
    title_str = Path(filename or filepath).stem
    author_str = "Tác giả chưa rõ"

    if reader.metadata:
        if reader.metadata.title:
            title_str = str(reader.metadata.title).strip()
        if reader.metadata.author:
            author_str = str(reader.metadata.author).strip()

    total_pages = len(reader.pages)
    chapters = []
    pages_per_chapter = 4  # Gom mỗi 4 trang PDF thành 1 chương để đọc mượt mà

    for i in range(0, total_pages, pages_per_chapter):
        end_p = min(i + pages_per_chapter, total_pages)
        c_title = f"Trang {i + 1} - {end_p}"
        paras = []

        for p_idx in range(i, end_p):
            try:
                page_text = reader.pages[p_idx].extract_text() or ""
                lines = [l.strip() for l in page_text.splitlines() if l.strip()]
                paras.extend(split_paragraphs(lines))
            except Exception as e:
                print(f"Lỗi đọc trang PDF {p_idx}:", e)

        if not paras:
            paras = [f"[Trang {i + 1} - {end_p}: Trang ảnh scan hoặc không có chữ trích xuất được]"]

        chapters.append({
            "index": len(chapters),
            "title": c_title,
            "paragraphs": paras
        })

    return title_str, author_str, chapters


def parse_mobi_file(filepath, filename=""):
    """Phân tích các tệp Kindle .mobi, .azw, .azw3"""
    if not mobi:
        raise ImportError("Thư viện mobi chưa được cài đặt")

    title_str = Path(filename or filepath).stem
    author_str = "Tác giả chưa rõ"

    temp_dir = tempfile.mkdtemp(prefix="mobi_unpack_")
    try:
        out_dir, filepath_extracted = mobi.extract(filepath)
        # Kiểm tra xem mobi giải nén ra file epub hay html
        extracted_path = Path(filepath_extracted)
        if extracted_path.suffix.lower() == '.epub':
            t, a, chs = parse_epub_file(str(extracted_path), filename)
            return t or title_str, a or author_str, chs
        elif extracted_path.suffix.lower() in ['.html', '.htm', '.xhtml']:
            t, a, chs = parse_html_file(str(extracted_path), filename)
            return t or title_str, a or author_str, chs
        else:
            # Tìm file html hoặc epub trong thư mục giải nén
            epubs = list(Path(out_dir).glob('**/*.epub'))
            if epubs:
                t, a, chs = parse_epub_file(str(epubs[0]), filename)
                return t or title_str, a or author_str, chs
            htmls = list(Path(out_dir).glob('**/*.html')) + list(Path(out_dir).glob('**/*.htm'))
            if htmls:
                t, a, chs = parse_html_file(str(htmls[0]), filename)
                return t or title_str, a or author_str, chs

            # Fallback đọc text
            with open(extracted_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = [l.strip() for l in f.readlines() if l.strip()]
            paras = split_paragraphs(lines)
            chs = group_paragraphs_into_chapters(paras)
            return title_str, author_str, chs
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def parse_xlsx_file(filepath, filename=""):
    if not openpyxl:
        raise ImportError("Thư viện openpyxl chưa được cài đặt")

    wb = openpyxl.load_workbook(filepath, data_only=True, read_only=True)
    title_str = Path(filename or filepath).stem
    author_str = "Bảng tính Excel"

    chapters = []
    for sheet_idx, sheet_name in enumerate(wb.sheetnames):
        ws = wb[sheet_name]
        paras = []
        for row in ws.iter_rows(values_only=True):
            cells = [str(c).strip() for c in row if c is not None and str(c).strip()]
            if cells:
                line_text = " • ".join(cells)
                paras.extend(split_paragraphs([line_text]))

        if not paras:
            paras = ["[Trang tính trống]"]

        chapters.append({
            "index": sheet_idx,
            "title": f"Sheet: {sheet_name}",
            "paragraphs": paras
        })

    wb.close()
    return title_str, author_str, chapters


# =========================================================================
# HÀM ĐIỀU PHỐI ĐA ĐỊNH DẠNG TOÀN CỤC (UNIVERSAL BOOK PARSER)
# =========================================================================

SUPPORTED_EXTENSIONS = {
    '.epub', '.mobi', '.azw', '.azw3',
    '.pdf', '.txt', '.doc', '.docx',
    '.xlsx', '.html', '.htm'
}


def parse_any_book_file(filepath, filename=""):
    """
    Tự động nhận diện phần mở rộng tệp và phân tích thành dữ liệu sách thống nhất.
    Trả về: { id, title, author, chapters, totalChapters }
    """
    ext = Path(filename or filepath).suffix.lower()

    if ext == '.epub':
        title, author, chapters = parse_epub_file(filepath, filename)
    elif ext in ('.mobi', '.azw', '.azw3'):
        title, author, chapters = parse_mobi_file(filepath, filename)
    elif ext == '.pdf':
        title, author, chapters = parse_pdf_file(filepath, filename)
    elif ext == '.docx':
        title, author, chapters = parse_docx_file(filepath, filename)
    elif ext == '.doc':
        title, author, chapters = parse_doc_file(filepath, filename)
    elif ext == '.txt':
        title, author, chapters = parse_txt_file(filepath, filename)
    elif ext in ('.html', '.htm'):
        title, author, chapters = parse_html_file(filepath, filename)
    elif ext == '.xlsx':
        title, author, chapters = parse_xlsx_file(filepath, filename)
    else:
        # Nếu phần mở rộng chưa biết, thử đoán theo định dạng EPUB rồi TXT
        try:
            title, author, chapters = parse_epub_file(filepath, filename)
        except Exception:
            title, author, chapters = parse_txt_file(filepath, filename)

    if not title:
        title = Path(filename or filepath).stem
    if not author:
        author = "Tác giả chưa rõ"

    # Tạo mã ID định danh sách
    book_id = hashlib.md5(f"{title}:{author}".encode('utf-8')).hexdigest()[:12]

    return {
        "id": book_id,
        "title": title,
        "author": author,
        "chapters": chapters,
        "totalChapters": len(chapters)
    }
