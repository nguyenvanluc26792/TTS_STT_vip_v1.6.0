import re
import zlib
import base64
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'vi,en-US;q=0.9,en;q=0.8',
}

def clean_web_paragraphs(raw_text):
    if not raw_text:
        return []
    if '<p' in raw_text or '<br' in raw_text or '<div' in raw_text:
        soup = BeautifulSoup(raw_text, 'html.parser')
        for sc in soup(["script", "style"]):
            sc.extract()
        paras = []
        for p in soup.find_all(['p', 'div']):
            t = p.get_text(strip=True)
            if t and t not in paras:
                paras.append(t)
        if paras:
            lines = paras
        else:
            text = soup.get_text(separator="\n")
            lines = [l.strip() for l in text.splitlines() if l.strip()]
    else:
        lines = [l.strip() for l in raw_text.splitlines() if l.strip()]

    cleaned = []
    for l in lines:
        if any(bad in l.lower() for bad in ['tải xuống x-truyện', 'tải app x-truyện', 'download app']):
            continue
        # Bỏ qua dòng nếu phát hiện chữ tiếng Hán
        if re.search(r'[\u4e00-\u9fff]', l):
            continue
        cleaned.append(l)
    return cleaned

# -------------------------------------------------------------
# XTRUYEN.VN DECODER & PARSER
# -------------------------------------------------------------
XTRUYEN_ALPHABET_SRC = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_'
XTRUYEN_ALPHABET_DST = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'

def decode_xtruyen_content(html):
    """Giải mã nội dung chương mã hóa bằng zlib + custom alphabet trên XTruyện"""
    m_data = None
    soup = BeautifulSoup(html, 'html.parser')
    for sc in soup.find_all('script'):
        txt = sc.string or ''
        if 'pako' in txt and 'translated' in txt:
            m_found = re.findall(r'"([A-Za-z0-9_\-]{500,})"', txt)
            if m_found:
                m_data = m_found[0]
                break

    if not m_data:
        m_x = re.search(r'data_x\s*=\s*"([^"]+)"', html)
        if m_x:
            m_data = m_x.group(1)
    if not m_data:
        m_enc = re.search(r'encodedData:\s*"([^"]+)"', html)
        if m_enc:
            m_data = m_enc.group(1)

    if not m_data:
        return ""

    data_x = m_data
    tr = ''.join(XTRUYEN_ALPHABET_DST[XTRUYEN_ALPHABET_SRC.find(ch)] if XTRUYEN_ALPHABET_SRC.find(ch) >= 0 else ch for ch in data_x)
    pad = (4 - len(tr) % 4) % 4
    try:
        raw = base64.b64decode(tr + '=' * pad)
        for wbits in [15, -15, 15 | 16]:
            try:
                decomp = zlib.decompress(raw, wbits).decode('utf-8')
                return decomp
            except Exception:
                pass
    except Exception:
        pass
    return ""

def parse_xtruyen_chapter(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code != 200:
            return None
        html = r.text
        soup = BeautifulSoup(html, 'html.parser')

        # Tên truyện
        story_title = ""
        st_meta = soup.select_one('meta[property="og:title"]')
        if st_meta and '-' in st_meta.get('content', ''):
            story_title = st_meta['content'].split('-')[0].strip()
        if not story_title and soup.title:
            story_title = soup.title.string.split('-')[0].strip()

        # Tên chương
        chap_title = ""
        if soup.title and '-' in soup.title.string:
            parts = soup.title.string.split('-')
            if len(parts) >= 2:
                chap_title = parts[1].strip()
        if not chap_title:
            h1 = soup.find('h1')
            if h1:
                chap_title = h1.get_text(strip=True)

        # Giải mã các đoạn văn
        content_html = decode_xtruyen_content(html)
        paragraphs = []
        if content_html:
            s_content = BeautifulSoup(content_html, 'html.parser')
            for el in s_content.find_all(['p', 'div']):
                t = el.get_text(strip=True)
                if t and t not in paragraphs:
                    paragraphs.append(t)

        if not paragraphs:
            for sel in ['#chapter-content', '.chapter-c', '.entry-content', '.reading-content']:
                el = soup.select_one(sel)
                if el:
                    for p in el.find_all('p'):
                        t = p.get_text(strip=True)
                        if t and t not in paragraphs:
                            paragraphs.append(t)
                    break

        # Tìm link chương tiếp theo
        next_url = None
        for a in soup.find_all('a', href=True):
            txt = a.get_text().strip().lower()
            if 'chương tiếp' in txt or 'tiếp theo' in txt or a.get('rel') == ['next']:
                next_url = a['href']
                if not next_url.startswith('http'):
                    next_url = urljoin(url, next_url)
                break

        return {
            "story_title": story_title or "Truyện XTruyện",
            "chapter_title": chap_title or "Chương",
            "paragraphs": paragraphs,
            "next_url": next_url
        }
    except Exception as e:
        print(f"Lỗi parse_xtruyen_chapter ({url}):", e)
        return None

# -------------------------------------------------------------
# SOTTRUYEN.COM DECODER & PARSER
# -------------------------------------------------------------
def decode_sottruyen_html(html, salt="MjAyNi0x"):
    """Giải mã nội dung chương được mã hóa bằng XOR + salt trên Sọt Truyện"""
    try:
        key = salt.encode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')
        for sc in soup.find_all('script'):
            t_sc = sc.string or ''
            if len(t_sc) > 3000 and 'self.__next_f.push' in t_sc:
                for m in re.finditer(r'self\.__next_f\.push\(\[1,"(.*)"\]\)', t_sc, re.DOTALL):
                    chk = m.group(1)
                    if chk.startswith('21:'):
                        chk = chk[3:]
                    try:
                        raw = base64.b64decode(chk)
                        dec = bytes([b ^ key[i % len(key)] for i, b in enumerate(raw)]).decode('utf-8')
                        if len(dec) > 100:
                            return [line.strip() for line in dec.splitlines() if line.strip()]
                    except Exception:
                        pass
    except Exception:
        pass
    return []

def parse_sottruyen_story(url, max_chapters=50):
    try:
        # Chuẩn hóa slug
        parsed = urlparse(url)
        parts = [p for p in parsed.path.split('/') if p]
        if 'truyen' in parts:
            idx = parts.index('truyen')
            slug = parts[idx + 1] if len(parts) > idx + 1 else parts[-1]
        else:
            slug = parts[0]

        # 1. Lấy thông tin truyện
        r_story = requests.get(f'https://sottruyen.com/truyen/{slug}', headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r_story.text, 'html.parser')
        h1 = soup.find('h1')
        title = h1.get_text(strip=True) if h1 else slug.replace('-', ' ').title()

        author = "Sọt Truyện"
        for el in soup.select('a[href*="/tac-gia/"], .author, meta[name="author"]'):
            t = el.get_text(strip=True) if el.name != 'meta' else el.get('content', '')
            if t:
                author = t
                break

        # 2. Lấy danh sách chương từ range API (bắt đầu đúng từ chương người dùng nhập nếu có)
        m_ch = re.search(r'(?:chuong|chapter)[-_](\d+)', url.lower())
        start_ch = int(m_ch.group(1)) if m_ch else 1
        end_ch = start_ch + max_chapters - 1

        session = requests.Session()
        session.headers.update(HEADERS)

        api_url = f'https://sottruyen.com/api/v1/stories/{slug}/chapters/range?from={start_ch}&to={end_ch}'
        r_api = session.get(api_url, timeout=10)
        ch_list = []
        if r_api.status_code == 200:
            ch_list = r_api.json().get('chapters', [])

        def fetch_single_sot_chapter(item_tuple):
            idx, ch = item_tuple
            ch_slug = ch.get('slug')
            ch_num = ch.get('chapter_number', start_ch + idx)
            ch_title = ch.get('title', f"Chương {ch_num}")
            paras = []
            try:
                r_c = session.get(f'https://sottruyen.com/api/v1/chapters/{ch_slug}', timeout=6)
                if r_c.status_code == 200:
                    c_data = r_c.json().get('data', {})
                    raw_b64 = c_data.get('content')
                    if raw_b64:
                        txt = base64.b64decode(raw_b64).decode('utf-8')
                        paras = clean_web_paragraphs(txt)
            except Exception:
                pass

            if not paras:
                try:
                    r_h = session.get(f'https://sottruyen.com/truyen/{slug}/chuong-{ch_num}', timeout=6)
                    m_salt = re.search(r'\\?["\']salt\\?["\']\s*:\s*\\?["\']([^"\'\\]+)', r_h.text)
                    salt = m_salt.group(1) if m_salt else 'MjAyNi0x'
                    paras = decode_sottruyen_html(r_h.text, salt)
                except Exception:
                    pass

            if paras:
                return {
                    "index": idx,
                    "title": ch_title,
                    "paragraphs": paras,
                    "chapter_number": ch_num
                }
            return None

        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=8) as executor:
            fetched_results = list(executor.map(fetch_single_sot_chapter, enumerate(ch_list)))

        chapters = [ch for ch in fetched_results if ch is not None]
        # Sắp xếp lại theo thứ tự index đúng
        chapters.sort(key=lambda x: x["index"])
        for i, ch in enumerate(chapters):
            ch["index"] = i

        return {
            "title": title,
            "author": author,
            "slug": slug,
            "chapters": chapters,
            "totalChapters": len(chapters),
            "next_chapter_index": start_ch + len(chapters),
            "is_web": True
        }
    except Exception as e:
        print(f"Lỗi parse_sottruyen_story ({url}):", e)
        return None

# -------------------------------------------------------------
# GENERIC & UNIVERSAL NOVEL SCRAPER (metruyenhotvn, truyenfullmoi, truyenfull, v.v.)
# -------------------------------------------------------------
def resolve_first_chapter_url(url):
    """Tự động phân giải URL truyện chính (chưa vào chương) sang link Chương 1 chuẩn xác"""
    if any(k in url.lower() for k in ['chuong-', 'chapter-', 'chuong_']):
        return url

    parsed = urlparse(url)
    slug = [p for p in parsed.path.split('/') if p][-1]
    base_slug = slug.split('.')[0]

    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')

            # 1. Tìm trực tiếp link có chứa base_slug và chuong-1
            for a in soup.find_all('a', href=True):
                href = a['href']
                if base_slug in href and any(p in href.lower() for p in ['chuong-1.', 'chuong-1/', 'chuong-01.', 'chuong-01/', 'chapter-1']):
                    return urljoin(url, href)

            # 2. Tìm link văn bản "chương 1", "đọc từ đầu", "đọc truyện"
            for a in soup.find_all('a', href=True):
                href = a['href']
                txt = a.get_text().strip().lower()
                if any(k in txt for k in ['đọc từ đầu', 'đọc ngay', 'đọc truyện', 'chương 1', 'chuong 1', 'chương 01']):
                    if href and href != '#' and not href.startswith('javascript'):
                        return urljoin(url, href)

            # 3. Đặc thù truyenfullmoi, truyenhoan: trang truyện chính có dạng .1147/
            for a in soup.find_all('a', href=True):
                if base_slug in a['href'] and a['href'] != url and any(c.isdigit() for c in a['href']):
                    target = urljoin(url, a['href'])
                    if 'chuong-' not in target:
                        try:
                            r2 = requests.get(target, headers=HEADERS, timeout=8)
                            if r2.status_code == 200:
                                soup2 = BeautifulSoup(r2.text, 'html.parser')
                                for a2 in soup2.find_all('a', href=True):
                                    if base_slug in a2['href'] and any(p in a2['href'].lower() for p in ['chuong-1.', 'chuong-1/', 'chuong-1-']):
                                        return urljoin(target, a2['href'])
                        except Exception:
                            pass

            # 4. Fallback: tìm link bất kỳ có chứa chuong-1, chuong-01 hoặc chapter-1
            for a in soup.find_all('a', href=True):
                href = a['href']
                if any(p in href.lower() for p in ['/chuong-1.', '/chuong-1/', '/chuong-1-', '/chuong-01.', '/chuong-01/', '/chapter-1']):
                    return urljoin(url, href)

            # 5. Fallback 2: Lấy link chương đầu tiên xuất hiện trong danh sách chương
            for a in soup.find_all('a', href=True):
                href = a['href']
                if 'chuong' in href.lower() and ('-1' in href.lower() or '1' in a.get_text().strip()):
                    return urljoin(url, href)
    except Exception as e:
        print(f"Lỗi resolve_first_chapter_url ({url}):", e)

    return url

def parse_generic_chapter(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, 'html.parser')

        # 1. Tiêu đề truyện
        story_title = ""
        st_el = soup.select_one('a.truyen-title, .story-title, .truyen-title, .rv-full-story-title, .rv-heading-story, .truyen-name, .book-info h1, .book-title, .novel-title, h1.title')
        if st_el and st_el.get_text(strip=True):
            story_title = st_el.get_text(strip=True)
        if not story_title:
            st_meta = soup.select_one('meta[property="og:title"], meta[name="title"]')
            if st_meta and st_meta.get('content'):
                story_title = st_meta['content'].split('-')[0].strip()
        if not story_title and soup.title:
            story_title = soup.title.string.split('-')[0].strip()

        # 2. Tiêu đề chương
        chap_title = ""
        ch_el = soup.select_one('a.chapter-title, .chapter-title, .chapter-name, .rv-chapt-title, .rv-heading-chapter, .chapter-text, h2.chapter-title, .chr-title')
        if ch_el and ch_el.get_text(strip=True):
            chap_title = ch_el.get_text(strip=True)
        if not chap_title:
            h1 = soup.find(['h1', 'h2'])
            if h1:
                chap_title = h1.get_text(strip=True)

        # 3. Tác giả
        author = ""
        auth_el = soup.select_one('a[href*="/tac-gia/"], .author, meta[property="og:novel:author"], meta[name="author"], .author-name')
        if auth_el:
            author = auth_el.get_text(strip=True) if auth_el.name != 'meta' else auth_el.get('content', '')

        # 4. Nội dung đoạn văn
        paragraphs = []
        for sel in [
            '#vungdoc', '.vung-doc', '.vungdoc', '#chapter-content', '.chapter-c', 
            '.entry-content', '.reading-content', 'div.content-inner', 'div.content', 
            '#content', '.content-body', '#chapter-c', '.reading-detail', '.box-chap', 
            '#bookContentBody', '.chap-content', '.txt-content', '.chapter-text', 
            '#chr-content', '.chr-c', '.doc-content'
        ]:
            el = soup.select_one(sel)
            if el:
                for script in el(["script", "style", "ins", "iframe", "noscript", ".ads", ".ads-holder"]):
                    script.extract()

                # Thay thẻ br, hr bằng newline để giữ nguyên dòng trên các trang dùng ngắt dòng <br> (như truyenfullmoi)
                for br in el.find_all(['br', 'hr']):
                    br.replace_with('\n')

                # Ưu tiên các thẻ p và div
                for p in el.find_all(['p', 'div']):
                    t = p.get_text(strip=True)
                    if t and t not in paragraphs:
                        if re.search(r'[\u4e00-\u9fff]', t):
                            continue
                        if any(bad in t.lower() for bad in ['quảng cáo', 'tải app', 'download app', 'truyenfullmoi.net', 'metruyenhotvn.com', 'truyenhoan.com', 'vivutruyen.com']):
                            continue
                        paragraphs.append(t)

                if not paragraphs:
                    text = el.get_text()
                    for line in text.splitlines():
                        l = line.strip()
                        if l and l not in paragraphs:
                            if re.search(r'[\u4e00-\u9fff]', l):
                                continue
                            if any(bad in l.lower() for bad in ['quảng cáo', 'tải app', 'download app', 'truyenfullmoi.net', 'metruyenhotvn.com', 'truyenhoan.com', 'vivutruyen.com']):
                                continue
                            paragraphs.append(l)
                if paragraphs:
                    break

        # Nếu đoạn đầu tiên là tiêu đề chương
        if paragraphs and len(paragraphs[0]) < 90:
            first_l = paragraphs[0].lower()
            if first_l.startswith("chương ") or first_l.startswith("chuong ") or first_l.startswith("chapter "):
                if not chap_title or "chương" not in chap_title.lower() or len(chap_title) < len(paragraphs[0]):
                    chap_title = paragraphs[0]
                paragraphs = paragraphs[1:]

        # 5. Link chương sau (Next Chapter)
        next_url = None
        for sel in [
            '#next_chap', 'a#next_chap', 'a[rel="next"]', '.btn-next', '.chapter-next', 
            '.next-chap', '#btn-next', '#next-chapter', '.nav-next a', 'a.next-page',
            'a[title*="Chương sau"]', 'a[title*="Chương tiếp"]'
        ]:
            btn = soup.select_one(sel)
            if btn and btn.get('href'):
                href = btn['href'].strip()
                if href and href != '#' and not href.startswith('javascript'):
                    next_url = urljoin(url, href)
                    break

        if not next_url:
            for a in soup.find_all('a', href=True):
                href = a['href'].strip()
                if not href or href == '#' or href.startswith('javascript') or href == url:
                    continue
                txt = a.get_text().strip().lower().replace(' ', '').replace('\xa0', '')
                if any(k in txt for k in ['chuongtiep', 'chươngtiếp', 'doctiep', 'đọctiếp', 'tieptheo', 'tiếptheo', 'chuongsau', 'chươngsau', 'tiep', 'tiếp', 'next']):
                    next_url = urljoin(url, href)
                    break
                # Hoặc li.detail-chapter-btn > a với chữ "tiếp" (metruyenhotvn)
                if a.parent and 'detail-chapter-btn' in a.parent.get('class', []) and any(k in a.get_text().lower() for k in ['tiếp', 'sau', 'next']):
                    next_url = urljoin(url, href)
                    break

        return {
            "story_title": story_title or "Truyện Web",
            "chapter_title": chap_title or "Chương",
            "author": author or "Tác giả Online",
            "paragraphs": paragraphs,
            "next_url": next_url
        }
    except Exception as e:
        print(f"Lỗi parse_generic_chapter ({url}):", e)
        return None

# -------------------------------------------------------------
# UNIVERSAL WEB NOVEL ENTRY POINT
# -------------------------------------------------------------
def fetch_web_novel(url, max_chapters=50, progress_callback=None):
    """
    Hàm phân tích tổng hợp: Tự động phát hiện nguồn truyện (XTruyện, Sọt Truyện, Metruyenhotvn, Truyenfullmoi, v.v.),
    tải trước danh sách 50 chương đầu tiên (hoặc tất cả chương có thể).
    """
    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    # 1. Trường hợp Sọt Truyện
    if 'sottruyen.com' in domain:
        story_data = parse_sottruyen_story(url, max_chapters=max_chapters)
        if story_data and story_data.get('chapters'):
            return story_data

    # 2. Trường hợp XTruyện hoặc Web Generic (metruyenhotvn, truyenfullmoi, v.v.)
    current_url = resolve_first_chapter_url(url)

    chapters = []
    visited_urls = set()
    story_title = "Truyện Online"
    author = "Tác giả Online"

    for c_idx in range(max_chapters):
        if not current_url or current_url in visited_urls:
            break
        visited_urls.add(current_url)

        if progress_callback:
            progress_callback(c_idx + 1, max_chapters, current_url)

        if 'xtruyen.vn' in domain:
            chap = parse_xtruyen_chapter(current_url)
        else:
            chap = parse_generic_chapter(current_url)

        if not chap or not chap.get('paragraphs'):
            break

        if c_idx == 0:
            story_title = chap.get('story_title') or story_title
            if chap.get('author') and chap.get('author') != "Tác giả Online":
                author = chap.get('author')
            
        c_title = chap.get('chapter_title') or f"Chương {c_idx + 1}"
        chapters.append({
            "index": c_idx,
            "title": c_title,
            "paragraphs": chap.get('paragraphs', []),
            "source_url": current_url
        })

        next_url = chap.get('next_url')
        if not next_url or next_url == current_url:
            break
        current_url = next_url

    return {
        "title": story_title,
        "author": author,
        "source_url": url,
        "last_crawl_url": current_url,
        "chapters": chapters,
        "totalChapters": len(chapters),
        "is_web": True
    }

def fetch_more_chapters(book_data, count=1):
    """
    Tải thêm số chương tiếp theo (mặc định 1 chương) khi người đọc tiến gần cuối bộ đệm 50 chương.
    Cập nhật trực tiếp vào đối tượng book_data.
    """
    if not book_data or not book_data.get("is_web"):
        return False, 0

    source_url = book_data.get("source_url", "")
    parsed = urlparse(source_url)
    domain = parsed.netloc.lower()
    existing_chapters = book_data.get("chapters", [])
    added_count = 0

    # 1. Trường hợp Sọt Truyện
    if 'sottruyen.com' in domain:
        slug = book_data.get("slug")
        if not slug and 'truyen/' in source_url:
            slug = source_url.split('truyen/')[1].split('/')[0]
        if not slug:
            return False, 0

        start_num = book_data.get("next_chapter_index", len(existing_chapters) + 1)
        end_num = start_num + count - 1

        session = requests.Session()
        session.headers.update(HEADERS)
        api_url = f'https://sottruyen.com/api/v1/stories/{slug}/chapters/range?from={start_num}&to={end_num}'
        try:
            r_api = session.get(api_url, timeout=10)
            if r_api.status_code == 200:
                ch_list = r_api.json().get('chapters', [])
                
                def _fetch_single_chapter(item_tuple):
                    i, ch = item_tuple
                    ch_slug = ch.get('slug')
                    ch_num = ch.get('chapter_number', start_num + i)
                    ch_title = ch.get('title', f"Chương {ch_num}")
                    paras = []

                    try:
                        r_c = session.get(f'https://sottruyen.com/api/v1/chapters/{ch_slug}', timeout=8)
                        if r_c.status_code == 200:
                            c_data = r_c.json().get('data', {})
                            raw_b64 = c_data.get('content')
                            if raw_b64:
                                txt = base64.b64decode(raw_b64).decode('utf-8')
                                paras = clean_web_paragraphs(txt)
                    except Exception:
                        pass

                    if not paras:
                        try:
                            r_h = session.get(f'https://sottruyen.com/truyen/{slug}/chuong-{ch_num}', timeout=8)
                            m_salt = re.search(r'\\?["\']salt\\?["\']\s*:\s*\\?["\']([^"\'\\]+)', r_h.text)
                            salt = m_salt.group(1) if m_salt else 'MjAyNi0x'
                            paras = decode_sottruyen_html(r_h.text, salt)
                        except Exception:
                            pass

                    if paras:
                        return {
                            "order": i,
                            "title": ch_title,
                            "paragraphs": paras,
                            "chapter_number": ch_num
                        }
                    return None

                from concurrent.futures import ThreadPoolExecutor
                with ThreadPoolExecutor(max_workers=8) as executor:
                    fetched = list(executor.map(_fetch_single_chapter, enumerate(ch_list)))

                valid_new = [x for x in fetched if x is not None]
                valid_new.sort(key=lambda x: x["order"])

                for item in valid_new:
                    new_ch = {
                        "index": len(existing_chapters),
                        "title": item["title"],
                        "paragraphs": item["paragraphs"],
                        "chapter_number": item["chapter_number"]
                    }
                    existing_chapters.append(new_ch)
                    added_count += 1

                book_data["next_chapter_index"] = start_num + len(ch_list)
                book_data["totalChapters"] = len(existing_chapters)
                return True, added_count
        except Exception as e:
            print("Lỗi fetch_more_chapters Sọt Truyện:", e)
            return False, 0

    # 2. Trường hợp XTruyện hoặc Web Generic
    current_url = book_data.get("last_crawl_url")
    if not current_url:
        return False, 0

    for _ in range(count):
        if not current_url:
            break
        if 'xtruyen.vn' in domain:
            chap = parse_xtruyen_chapter(current_url)
        else:
            chap = parse_generic_chapter(current_url)

        if not chap or not chap.get('paragraphs'):
            break

        c_title = chap.get('chapter_title') or f"Chương {len(existing_chapters) + 1}"
        new_ch = {
            "index": len(existing_chapters),
            "title": c_title,
            "paragraphs": chap.get('paragraphs', []),
            "source_url": current_url
        }
        existing_chapters.append(new_ch)
        added_count += 1

        next_url = chap.get('next_url')
        if not next_url or next_url == current_url:
            current_url = None
            break
        current_url = next_url

    book_data["last_crawl_url"] = current_url
    book_data["totalChapters"] = len(existing_chapters)
    return True, added_count


def search_web_novels(query, limit=25):
    """Tìm kiếm truyện online đồng thời trên các kho truyện hỗ trợ"""
    if not query or not query.strip():
        return []

    q = query.strip()
    encoded_q = requests.utils.quote(q)
    results = []

    from concurrent.futures import ThreadPoolExecutor

    def search_truyenfullmoi():
        sub_res = []
        try:
            url = f"https://truyenfullmoi.net/tim-kiem?tukhoa={encoded_q}"
            r = requests.get(url, headers=HEADERS, timeout=7)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                for row in soup.select('.list-truyen .row')[:10]:
                    t_el = row.select_one('h3.truyen-title a')
                    a_el = row.select_one('.author')
                    ch_el = row.select_one('.text-info a')
                    if t_el and t_el.get('href'):
                        b_url = t_el.get('href').strip()
                        if b_url.startswith('/'):
                            b_url = 'https://truyenfullmoi.net' + b_url
                        sub_res.append({
                            "title": t_el.get_text(strip=True),
                            "url": b_url,
                            "author": a_el.get_text(strip=True) if a_el else "Nhiều tác giả",
                            "latest_chapter": ch_el.get_text(strip=True) if ch_el else "",
                            "source": "Truyện Full Mới",
                            "domain": "truyenfullmoi.net"
                        })
        except Exception as e:
            print("[Search] Lỗi truyenfullmoi:", e)
        return sub_res

    def search_truyenhoan():
        sub_res = []
        try:
            url = f"https://truyenhoan.com/tim-kiem/?tukhoa={encoded_q}"
            r = requests.get(url, headers=HEADERS, timeout=7)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                for row in soup.select('.list-truyen .row')[:10]:
                    t_el = row.select_one('h3.truyen-title a')
                    a_el = row.select_one('.author')
                    ch_el = row.select_one('.text-info a')
                    if t_el and t_el.get('href'):
                        b_url = t_el.get('href').strip()
                        if b_url.startswith('/'):
                            b_url = 'https://truyenhoan.com' + b_url
                        sub_res.append({
                            "title": t_el.get_text(strip=True),
                            "url": b_url,
                            "author": a_el.get_text(strip=True) if a_el else "Nhiều tác giả",
                            "latest_chapter": ch_el.get_text(strip=True) if ch_el else "",
                            "source": "Truyện Hoàn",
                            "domain": "truyenhoan.com"
                        })
        except Exception as e:
            print("[Search] Lỗi truyenhoan:", e)
        return sub_res

    def search_vivutruyen():
        sub_res = []
        try:
            url = f"https://vivutruyen.com/search?k={encoded_q}"
            r = requests.get(url, headers=HEADERS, timeout=7)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                for h in soup.find_all(['h2', 'h3', 'h4'])[:10]:
                    a_el = h.find('a')
                    if a_el and a_el.get('href') and '/truyen/' in a_el['href']:
                        b_url = a_el['href'].strip()
                        if b_url.startswith('/'):
                            b_url = 'https://vivutruyen.com' + b_url
                        title_str = a_el.get_text(strip=True)
                        if title_str and not any(r['url'] == b_url for r in sub_res):
                            sub_res.append({
                                "title": title_str,
                                "url": b_url,
                                "author": "ViVuTruyen",
                                "latest_chapter": "",
                                "source": "ViVu Truyện",
                                "domain": "vivutruyen.com"
                            })
        except Exception as e:
            print("[Search] Lỗi vivutruyen:", e)
        return sub_res

    def search_tamhoan():
        sub_res = []
        try:
            url = f"https://tamhoan.com/tim-kiem?tr={encoded_q}"
            r = requests.get(url, headers=HEADERS, timeout=7)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                for h in soup.find_all(['h2', 'h3', 'h4'])[:10]:
                    a_el = h.find('a')
                    if a_el and a_el.get('href') and '/truyen/' in a_el['href']:
                        b_url = a_el['href'].strip()
                        if b_url.startswith('/'):
                            b_url = 'https://tamhoan.com' + b_url
                        title_str = a_el.get_text(strip=True)
                        if title_str and not any(r['url'] == b_url for r in sub_res):
                            sub_res.append({
                                "title": title_str,
                                "url": b_url,
                                "author": "Tầm Hoàn",
                                "latest_chapter": "",
                                "source": "Tầm Hoàn",
                                "domain": "tamhoan.com"
                            })
        except Exception as e:
            print("[Search] Lỗi tamhoan:", e)
        return sub_res

    with ThreadPoolExecutor(max_workers=4) as executor:
        f1 = executor.submit(search_truyenfullmoi)
        f2 = executor.submit(search_truyenhoan)
        f3 = executor.submit(search_vivutruyen)
        f4 = executor.submit(search_tamhoan)

        for f in [f1, f2, f3, f4]:
            try:
                results.extend(f.result() or [])
            except Exception:
                pass

    return results[:limit]



