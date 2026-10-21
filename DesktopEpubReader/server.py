import os
import sys
import io
import json
import hashlib
import asyncio
import tempfile
import subprocess
import marshal
import threading
import time
from pathlib import Path
import re
import unicodedata

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import requests
from flask import Flask, request, jsonify, send_file, render_template, render_template_string
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import edge_tts
import offline_tts
import bilingual_engine as bilingual
from universal_parser import parse_any_book_file, SUPPORTED_EXTENSIONS

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True
BASE_DIR = Path(__file__).parent
CACHE_DIR = BASE_DIR / "cache"
CACHE_DIR.mkdir(exist_ok=True)

# Tải module tts_service gốc để gọi CapCut
CAPCUT_MODULE_PATH = BASE_DIR / "decomp_tts_service.bin"
_capcut_ns = {'__file__': 'tts_service.py'}
if CAPCUT_MODULE_PATH.exists():
    _code = marshal.loads(CAPCUT_MODULE_PATH.read_bytes())
    exec(_code, _capcut_ns)
    print("[OK] Đã nạp thành công bộ sinh giọng CapCut TTS chính gốc!")
else:
    print("[WARN] Chưa tìm thấy decomp_tts_service.bin!")

# Tải module ElevenLabs TTS chính gốc (chạy qua cổng bảo mật không cần API Key)
ELEVENLABS_MODULE_PATH = BASE_DIR / "decomp_module.bin"
_elevenlabs_ns = {}
_elevenlabs_tts = None
if ELEVENLABS_MODULE_PATH.exists():
    try:
        _code_11 = marshal.loads(ELEVENLABS_MODULE_PATH.read_bytes())
        exec(_code_11, _elevenlabs_ns)
        if 'ElevenLabsCapCutTTS' in _elevenlabs_ns:
            _elevenlabs_tts = _elevenlabs_ns['ElevenLabsCapCutTTS']()
            print("[OK] Đã nạp thành công bộ sinh giọng ElevenLabs TTS!")
    except Exception as e:
        print(f"[WARN] Lỗi nạp decomp_module.bin cho ElevenLabs: {e}")
else:
    print("[WARN] Chưa tìm thấy decomp_module.bin!")

# Danh sách toàn bộ giọng đọc (CapCut + Edge + ElevenLabs)
VOICE_CATALOG = [
    # CapCut TTS
    {
        "id": "BV421_vivn_streaming",
        "name": "Nhỏ Ngọt Ngào (Truyền Cảm • Audiobook)",
        "provider": "capcut",
        "lang": "vi",
        "desc": "CapCut AI - Nữ ấm dịu, truyền cảm, ngắt nhịp văn học cực tốt"
    },
    {
        "id": "BV075_streaming",
        "name": "Nam Trầm Ấm (Kể Chuyện • Tiên Hiệp)",
        "provider": "capcut",
        "lang": "vi",
        "desc": "CapCut AI - Nam dõng dạc, trầm hùng, hoàn hảo cho truyện tiên hiệp/hành động"
    },
    {
        "id": "multi_female_richgirl_uranus_bigtts",
        "name": "Review Phim (Siêu Truyền Cảm)",
        "provider": "capcut",
        "lang": "vi",
        "desc": "CapCut AI - Trầm ấm, siêu truyền cảm, chuyên đọc truyện và review"
    },
    {
        "id": "BV074_streaming",
        "name": "Cô Gái Hoạt Ngôn (Tươi Vui)",
        "provider": "capcut",
        "lang": "vi",
        "desc": "CapCut AI - Tự nhiên, hoạt bát, biểu cảm hội thoại"
    },
    {
        "id": "vi_female_huong",
        "name": "Nữ Phổ Thông",
        "provider": "capcut",
        "lang": "vi",
        "desc": "CapCut - Nữ chuẩn phát âm miền Bắc"
    },
    {
        "id": "BV074_streaming_dsp",
        "name": "Giọng Bé",
        "provider": "capcut",
        "lang": "vi",
        "desc": "CapCut - Trẻ con đáng yêu"
    },
    # Edge TTS
    {
        "id": "vi-VN-HoaiMyNeural",
        "name": "Hoài My (Edge)",
        "provider": "edge",
        "lang": "vi",
        "desc": "Microsoft - Nữ phát thanh viên êm đềm, đọc truyện đêm"
    },
    {
        "id": "vi-VN-NamMinhNeural",
        "name": "Nam Minh (Edge)",
        "provider": "edge",
        "lang": "vi",
        "desc": "Microsoft - Nam đọc truyện điềm đạm, ấm áp"
    },
    {
        "id": "en-US-JennyNeural",
        "name": "Jenny (Edge EN)",
        "provider": "edge",
        "lang": "en",
        "desc": "Microsoft - Nữ tiếng Anh bản xứ Mỹ"
    },
    {
        "id": "en-US-GuyNeural",
        "name": "Guy (Edge EN)",
        "provider": "edge",
        "lang": "en",
        "desc": "Microsoft - Nam tiếng Anh bản xứ Mỹ"
    },
    # ElevenLabs TTS (Ngôn ngữ tiếng Anh - Chuẩn Studio đỉnh cao)
    {
        "id": "eleven_zA6D7RyKdc2EClouEMkP",
        "name": "Almee-Anh (ElevenLabs)",
        "provider": "elevenlabs",
        "lang": "en",
        "desc": "ElevenLabs - Nữ Anh Quốc (British) thanh lịch, truyền cảm"
    },
    {
        "id": "eleven_Gsndh0O5AnuI2Hj3YUlA",
        "name": "Adam-Anh (ElevenLabs)",
        "provider": "elevenlabs",
        "lang": "en",
        "desc": "ElevenLabs - Nam Anh Quốc (British) điềm tĩnh, ấm áp"
    },
    {
        "id": "eleven_IRHApOXLvnW57QJPQH2P",
        "name": "Adam-Mỹ (ElevenLabs)",
        "provider": "elevenlabs",
        "lang": "en",
        "desc": "ElevenLabs - Nam Mỹ kinh điển, kể chuyện & thuyết minh"
    }
]

def clean_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    for script in soup(["script", "style"]):
        script.extract()
    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines

def split_paragraphs(lines):
    paragraphs = []
    for line in lines:
        if len(line) > 350:
            import re
            parts = re.split(r'([.!?]+)', line)
            buf = ""
            for i in range(0, len(parts)-1, 2):
                sentence = (parts[i] + parts[i+1]).strip()
                if len(buf) + len(sentence) < 300:
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
            paragraphs.append(line)
    return paragraphs

@app.route("/")
def index():
    resp = app.make_response(render_template("index.html"))
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp

@app.route("/download-app")
@app.route("/LReader.apk")
@app.route("/HonorReader_VIP_v1.0.apk")
def download_app():
    apk_path = BASE_DIR / "LReader.apk"
    if not apk_path.exists():
        apk_path = BASE_DIR / "HonorReader_VIP_v1.0.apk"
    if apk_path.exists():
        return send_file(apk_path, as_attachment=True, download_name="LReader.apk", mimetype="application/vnd.android.package-archive")
    return "Tệp APK chưa sẵn sàng. Vui lòng kiểm tra lại!", 404

@app.before_request
def handle_ota_interception():
    qs = request.query_string.decode("utf-8", errors="ignore")
    full = request.full_path
    if "api/ota/version" in qs or "api/ota/version" in full:
        return get_ota_version()
    if "api/ota/bundle" in qs or "api/ota/bundle" in full or "api/ota/index.html" in qs:
        return get_ota_bundle()

@app.route("/api/ota/bundle")
@app.route("/api/ota/index.html")
def get_ota_bundle():
    bundle_path = BASE_DIR / "templates" / "index.html"
    if bundle_path.exists():
        return send_file(bundle_path, mimetype="text/html; charset=utf-8")
    return "Bundle not found", 404

@app.route("/api/ota/version")
def get_ota_version():
    bundle_path = BASE_DIR / "templates" / "index.html"
    if bundle_path.exists():
        stat = bundle_path.stat()
        return jsonify({
            "success": True,
            "version": "v1.6.62",
            "version_code": 222,
            "size": stat.st_size,
            "updated_at": int(stat.st_mtime),
            "changelog": [
                "🎯 Tách biệt hoàn toàn Giọng Online vs Offline: Chọn giọng Offline đọc 100% bằng máy (không bao giờ nhảy sang Online); chọn giọng Online đọc đúng các giọng CapCut chuẩn",
                "⚡ Tối ưu tốc độ mở app tức thì (<0.5s): Không còn bị treo chờ 10s lúc khởi động",
                "📖 Bổ sung nút 'Quét chương này' trong Sổ tay Nhân vật AI: Tự động phân vai Nam/Nữ và khóa cứng nhân vật",
                "🔇 Khởi động app ở trạng thái Dừng (Pause), bấm Play mới đọc"
            ]
        })
    return jsonify({"success": False}), 404

@app.route("/api/ota/status")
def get_ota_status():
    return jsonify({"success": True, "active": True})

@app.route("/api/debug/crash-log")
def get_debug_crash_log():
    return jsonify({"success": True, "crashes": []})

@app.route("/ota")
@app.route("/ota-3g")
def ota_helper_page():
    return render_template_string("""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
  <title>Cập nhật Honor Reader OTA qua 3G</title>
  <style>
    * { box-sizing: border-box; margin:0; padding:0; }
    body {
      background: #0b0f19;
      color: #f1f5f9;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      padding: 20px 16px;
    }
    .card {
      background: #1e293b;
      border: 1.5px solid rgba(56, 189, 248, 0.4);
      border-radius: 20px;
      padding: 24px 20px;
      max-width: 440px;
      width: 100%;
      text-align: center;
      box-shadow: 0 12px 35px rgba(0,0,0,0.55);
    }
    .badge {
      display: inline-block;
      padding: 5px 14px;
      background: rgba(56, 189, 248, 0.18);
      color: #38bdf8;
      border-radius: 99px;
      font-size: 0.82rem;
      font-weight: 700;
      margin-bottom: 12px;
      letter-spacing: 0.5px;
    }
    h2 { font-size: 1.35rem; margin-bottom: 6px; color: #fff; }
    .ver-tag { font-size: 0.88rem; color: #4ade80; font-weight: 700; margin-bottom: 16px; }
    
    .guide-box {
      background: rgba(15, 23, 42, 0.9);
      border: 1.5px solid rgba(251, 191, 36, 0.35);
      border-radius: 14px;
      padding: 16px 14px;
      margin-bottom: 18px;
      text-align: left;
    }
    .guide-title {
      font-size: 0.86rem;
      font-weight: 700;
      color: #fbbf24;
      margin-bottom: 10px;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .guide-step {
      font-size: 0.80rem;
      color: #cbd5e1;
      line-height: 1.6;
      margin-bottom: 8px;
    }
    .guide-step b { color: #f1f5f9; }
    .url-box {
      display: flex;
      gap: 6px;
      margin-top: 10px;
      margin-bottom: 4px;
    }
    .url-input {
      flex: 1;
      padding: 9px 10px;
      border-radius: 8px;
      border: 1px solid rgba(56, 189, 248, 0.4);
      background: rgba(0, 0, 0, 0.5);
      color: #38bdf8;
      font-size: 0.74rem;
      font-family: monospace;
      outline: none;
    }
    .copy-btn {
      padding: 9px 14px;
      border-radius: 8px;
      background: #0284c7;
      color: #fff;
      font-size: 0.80rem;
      font-weight: 700;
      border: none;
      cursor: pointer;
      white-space: nowrap;
      transition: all 0.2s;
    }
    .copy-btn:active { background: #0369a1; transform: scale(0.96); }
    
    .btn {
      display: block;
      width: 100%;
      padding: 13px 16px;
      border-radius: 14px;
      font-size: 0.90rem;
      font-weight: 700;
      cursor: pointer;
      text-decoration: none;
      border: none;
      margin-bottom: 10px;
      transition: all 0.2s;
    }
    .btn-app {
      background: linear-gradient(135deg, #0284c7, #2563eb);
      color: #fff;
      box-shadow: 0 4px 16px rgba(37, 99, 235, 0.4);
    }
    .btn-web {
      background: rgba(34, 197, 94, 0.15);
      color: #4ade80;
      border: 1px solid rgba(34, 197, 94, 0.35);
    }
    .btn-apk {
      background: #334155;
      color: #cbd5e1;
      border: 1px solid rgba(255,255,255,0.1);
    }
    .note-sec {
      margin-top: 10px;
      font-size: 0.75rem;
      color: #94a3b8;
      line-height: 1.5;
      border-top: 1px solid rgba(255,255,255,0.08);
      padding-top: 12px;
      text-align: left;
    }
  </style>
</head>
<body>
  <div class="card">
    <div class="badge">⚡ MÁY CHỦ OTA 3G ONLINE</div>
    <h2>Cập Nhật Honor Reader</h2>
    <div class="ver-tag">Bản cập nhật mới nhất: v1.6.62 (Build 222)</div>

    <!-- Hướng dẫn 2 bước -->
    <div class="guide-box">
      <div class="guide-title">📲 HƯỚNG DẪN CẬP NHẬT TRONG APP (30 GIÂY):</div>
      
      <div class="guide-step">
        <b>Bước 1:</b> Bấm <b>Sao Chép</b> link máy chủ 3G dưới đây:
      </div>
      <div class="url-box">
        <input type="text" id="srvUrl" class="url-input" value="https://opinion-personality-activities-mailto.trycloudflare.com/?rehab-survey-clusters-joins" readonly>
        <button type="button" class="copy-btn" id="btnCopy" onclick="copyUrl()">📋 Sao Chép</button>
      </div>

      <div class="guide-step" style="margin-top:12px;">
        <b>Bước 2:</b> Mở app <b>Honor Reader</b> trên máy:<br>
        &bull; Bấm vào biểu tượng ⚙️ <b>Cài đặt</b>.<br>
        &bull; Kéo xuống mục <b>Máy chủ cập nhật</b> &rarr; Xóa link cũ, <b>Dán link vừa sao chép vào</b>.<br>
        &bull; Bấm nút <b>Kiểm tra cập nhật</b> &rarr; Bấm nút đỏ <b>CẬP NHẬT OTA</b> (Chờ 1-2 giây là xong)!
      </div>
    </div>

    <!-- Nút mở nhanh ứng dụng -->
    <a href="intent://#Intent;action=android.intent.action.MAIN;category=android.intent.category.LAUNCHER;package=com.dragon.read;end" class="btn btn-app">
      🚀 MỞ APP HONOR READER ĐỂ DÁN LINK
    </a>

    <!-- Hoặc đọc truyện trên Web -->
    <a href="/" class="btn btn-web">
      📖 Hoặc Đọc Trực Tiếp Trên Web 3G
    </a>

    <!-- Hoặc tải Full APK -->
    <a href="/download-app" class="btn btn-apk">
      📥 Tải Bộ Cài APK Đầy Đủ (62MB)
    </a>

    <div class="note-sec">
      💡 <b>Vì sao cần dán link trong App?</b><br>
      Do chính sách bảo mật của Android, trình duyệt Chrome bên ngoài không được phép tự ý can thiệp vào tệp tin của ứng dụng khác. Vì vậy bạn chỉ cần copy link trên và dán vào phần Cài đặt trong App là cập nhật cực kỳ nhanh chóng và an toàn.
    </div>
  </div>

  <script>
    function copyUrl() {
      const input = document.getElementById('srvUrl');
      input.select();
      input.setSelectionRange(0, 99999);
      const btn = document.getElementById('btnCopy');
      
      function onCopied() {
        if (btn) {
          btn.innerText = '✅ Đã Chép!';
          btn.style.background = '#16a34a';
          setTimeout(() => {
            btn.innerText = '📋 Sao Chép';
            btn.style.background = '#0284c7';
          }, 2500);
        }
        alert('✅ ĐÃ SAO CHÉP LINK MÁY CHỦ 3G!\n\nBây giờ bạn hãy:\n1. Mở app Honor Reader\n2. Vào Cài đặt\n3. Dán vào ô Máy chủ cập nhật\n4. Bấm Kiểm tra cập nhật -> Cập nhật OTA.');
      }

      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(input.value).then(onCopied).catch(() => {
          document.execCommand('copy');
          onCopied();
        });
      } else {
        document.execCommand('copy');
        onCopied();
      }
    }
  </script>
</body>
</html>""")

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, PUT, DELETE, HEAD'
    response.headers['Access-Control-Allow-Headers'] = '*'
    return response

BOOKS_DIR = BASE_DIR / "saved_books"
BOOKS_DIR.mkdir(exist_ok=True)
INDEX_FILE = BOOKS_DIR / "library_index.json"

def get_library_index():
    entries = []
    if INDEX_FILE.exists():
        try:
            with open(INDEX_FILE, "r", encoding="utf-8") as f:
                entries = json.load(f)
        except Exception:
            entries = []
    if not entries:
        for p in sorted(BOOKS_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
            if p.name == "library_index.json": continue
            try:
                with open(p, "r", encoding="utf-8") as bf:
                    d = json.load(bf)
                    entries.append({
                        "id": d.get("id", p.stem),
                        "title": d.get("title", p.stem),
                        "author": d.get("author", "Không rõ"),
                        "totalChapters": len(d.get("chapters", [])),
                        "lastChapter": d.get("lastChapter", 0),
                        "lastParagraph": d.get("lastParagraph", 0),
                        "is_web": d.get("is_web", False)
                    })
            except Exception:
                pass
        if entries:
            save_library_index(entries)
    return entries

def save_library_index(index_data):
    try:
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Lỗi lưu index:", e)

# Quản lý danh sách câu bỏ qua (Skip Rules) - theo từng sách riêng biệt
SKIP_RULES_DIR = BASE_DIR / "skip_rules"
SKIP_RULES_DIR.mkdir(exist_ok=True)
DEFAULT_SKIP_RULES_FILE = BASE_DIR / "skip_rules.json"

def get_skip_rules_path(book_id=None):
    if book_id:
        safe_id = "".join(c for c in str(book_id) if c.isalnum() or c in ("-", "_"))
        if safe_id:
            return SKIP_RULES_DIR / f"{safe_id}.json"
    return DEFAULT_SKIP_RULES_FILE

def get_skip_rules(book_id=None):
    p = get_skip_rules_path(book_id)
    if p.exists():
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # Nếu chưa có file riêng cho sách này, kiểm tra file mặc định
    if book_id and DEFAULT_SKIP_RULES_FILE.exists():
        try:
            with open(DEFAULT_SKIP_RULES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # Mẫu mặc định ban đầu
    initial = [
        "Tác giả: Lừa Con Lon Ton",
        "—★—",
        "DTV-EBOOK"
    ]
    try:
        with open(p, "w", encoding="utf-8") as f:
            json.dump(initial, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    return initial

def save_skip_rules(rules, book_id=None):
    try:
        import re
        cleaned = []
        seen = set()
        for r in rules:
            if not r: continue
            r_str = str(r).strip()
            norm = re.sub(r'\s+', ' ', r_str.lower())
            if norm and norm not in seen:
                seen.add(norm)
                cleaned.append(r_str)
        p = get_skip_rules_path(book_id)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(cleaned, f, ensure_ascii=False, indent=2)
        return cleaned
    except Exception as e:
        print(f"Lỗi lưu skip rules (book_id={book_id}):", e)
        return rules

def normalize_for_skip(text):
    if not text:
        return ""
    import re
    return re.sub(r'\s+', ' ', text.strip().lower())

def filter_skipped_phrases(text, rules=None, book_id=None):
    if not text:
        return ""
    if rules is None:
        rules = get_skip_rules(book_id)
    if not rules:
        return text
    import re
    result = text
    sorted_rules = sorted([str(r).strip() for r in rules if r and str(r).strip()], key=len, reverse=True)
    for r in sorted_rules:
        try:
            esc = re.escape(r)
            result = re.sub(rf'(?i){esc}', ' ', result)
        except Exception:
            pass
    result = re.sub(r',\s*,+', ',', result)
    result = re.sub(r'\s+', ' ', result).strip()
    return result

def is_text_skipped(text, rules=None, book_id=None):
    if not text:
        return True
    # Tự động bỏ qua câu nếu phát hiện chữ tiếng Hán
    if re.search(r'[\u4e00-\u9fff]', text):
        return True
    if rules is None:
        rules = get_skip_rules(book_id)
    if not rules:
        return False
    norm_text = normalize_for_skip(text)
    for r in rules:
        if not r: continue
        if norm_text == normalize_for_skip(r):
            return True
    filtered = filter_skipped_phrases(text, rules)
    if not re.search(r'\w', filtered, re.UNICODE):
        return True
    return False
    norm_text = normalize_for_skip(text)
    for r in rules:
        if not r: continue
        if norm_text == normalize_for_skip(r):
            return True
    return False

@app.route("/api/skip-rules", methods=["GET"])
def api_get_skip_rules():
    book_id = request.args.get("bookId") or request.args.get("book_id")
    return jsonify(get_skip_rules(book_id))

@app.route("/api/skip-rules", methods=["POST"])
def api_save_skip_rules():
    data = request.get_json(force=True, silent=True) or {}
    book_id = data.get("bookId") or data.get("book_id") or request.args.get("bookId")
    rules = data.get("rules", [])
    saved = save_skip_rules(rules, book_id)
    return jsonify({"success": True, "rules": saved, "bookId": book_id})

# =====================================================================
# TỪ ĐIỂN PHÁT ÂM (PRONUNCIATION REPLACEMENT RULES)
# Sửa từ bị AI đọc sai trước khi phát âm
# =====================================================================
PRONUNCIATION_RULES_FILE = BASE_DIR / "pronunciation_rules.json"

def get_pronunciation_rules():
    if PRONUNCIATION_RULES_FILE.exists():
        try:
            with open(PRONUNCIATION_RULES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    initial = [
        {"find": "boss", "replace": "trùm", "match_word": True},
        {"find": "level", "replace": "cấp độ", "match_word": True},
        {"find": "lv", "replace": "cấp", "match_word": True},
        {"find": "PK", "replace": "pê ca", "match_word": True},
        {"find": "NPC", "replace": "en pi xi", "match_word": True}
    ]
    try:
        with open(PRONUNCIATION_RULES_FILE, "w", encoding="utf-8") as f:
            json.dump(initial, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    return initial

def save_pronunciation_rules(rules):
    try:
        cleaned = []
        for r in rules:
            f_str = str(r.get("find", "")).strip()
            rep_str = str(r.get("replace", "")).strip()
            match_word = bool(r.get("match_word", True))
            if f_str and rep_str:
                cleaned.append({
                    "find": f_str,
                    "replace": rep_str,
                    "match_word": match_word
                })
        with open(PRONUNCIATION_RULES_FILE, "w", encoding="utf-8") as f:
            json.dump(cleaned, f, ensure_ascii=False, indent=2)
        return cleaned
    except Exception as e:
        print("Lỗi lưu pronunciation rules:", e)
        return rules

def apply_pronunciation_rules(text, rules=None):
    if not text:
        return ""
    if rules is None:
        rules = get_pronunciation_rules()

    import re
    # 0. Chuẩn hóa Unicode NFC & Xóa sạch ký tự ẩn, khoảng trắng toàn phần của truyện convert
    result = unicodedata.normalize("NFC", text)
    result = re.sub(r"[\u200B-\u200D\uFEFF\u00AD]", "", result)
    result = re.sub(r"[\t\xa0\u1680\u2000-\u200a\u202f\u205f\u3000]+", " ", result)
    result = re.sub(r"\s+([,.;:!?\)\]”’»])", r"\1", result)
    result = re.sub(r",{2,}", ",", result)
    result = re.sub(r"\.{2,}|…+", "...", result)
    # Micro-Clause Smoothing: Xóa dấu phẩy sau các từ nối ngắn 2 âm tiết đầu câu để AI lướt mượt vào chủ ngữ
    result = re.sub(r"(?i)(^|[-–—\n]\s*|[.!?…]\s+)(Vậy mà|Bất quá|Thậm chí|Hiện giờ|Quả nhiên|Không ngờ),\s*", r"\1\2 ", result)
    # Ép sau dấu câu [, . ; : ! ?] chỉ có đúng 1 dấu cách duy nhất (loại bỏ triệt để 1 vs 2 khoảng trắng sau dấu phẩy)
    result = re.sub(r"([,.;:!?])\s*", r"\1 ", result)
    result = re.sub(r" {2,}", " ", result)
    # Chuẩn hóa từ cảm thán & tên riêng convert hay gặp
    result = re.sub(r"(?i)\bah\b", "a", result)
    result = re.sub(r"(?i)\bưm\b", "ừm", result)
    result = re.sub(r"\blô giáo quan\b", "Lô giáo quan", result)

    # 1. Áp dụng quy tắc từ bảng phát âm (pronunciation_rules.json)
    if rules:
        for r in rules:
            find_w = r.get("find", "").strip()
            rep_w = r.get("replace", "").strip()
            match_word = r.get("match_word", True)
            if not find_w:
                continue
            try:
                escaped = re.escape(find_w)
                if match_word:
                    prefix = r'\b' if re.match(r'^\w', find_w) else r'(?:^|[\s,.\-!?:;\'"()\[\]])'
                    suffix = r'\b' if re.search(r'\w$', find_w) else r'(?:$|[\s,.\-!?:;\'"()\[\]])'
                    pattern = rf'(?i){prefix}{escaped}{suffix}'
                else:
                    pattern = rf'(?i){escaped}'
                result = re.sub(pattern, rep_w, result)
            except Exception as e:
                print(f"[apply_pronunciation_rules error] '{find_w}':", e)

    # 2. Áp dụng phiên âm từ danh sách từ tiếng Anh tùy chỉnh (custom_english_words.json)
    try:
        custom_words = bilingual.get_custom_english_words()
        for item in custom_words:
            if isinstance(item, dict):
                w = item.get("word", "").strip()
                ph = item.get("phonetic", "").strip()
                if w and ph:
                    escaped = re.escape(w)
                    prefix = r'\b' if re.match(r'^\w', w) else r'(?:^|[\s,.\-!?:;\'"()\[\]])'
                    suffix = r'\b' if re.search(r'\w$', w) else r'(?:$|[\s,.\-!?:;\'"()\[\]])'
                    pattern = rf'(?i){prefix}{escaped}{suffix}'
                    result = re.sub(pattern, ph, result)
    except Exception as e:
        print("[apply_pronunciation_rules custom words error]:", e)

    # Chuẩn hóa nhịp điệu và làm giàu ngữ điệu văn học (Prosody & Rhythm Enhancer):
    # 1. Chuẩn hóa dấu gạch đầu dòng đối thoại trong tiểu thuyết:
    result = re.sub(r'^[—–\-]+\s*(?=[\w\u00C0-\u1EF9\u201C\u201D"\'`])', '“', result)

    # 2. Chuẩn hóa dấu biểu cảm convert mạng (~~~ -> …, ?? -> ?, !? -> !?)
    result = re.sub(r'([\w\u00C0-\u1EF9])~+', r'\1… ', result)
    result = re.sub(r'\?{2,}', '?', result)
    result = re.sub(r'!{2,}', '!', result)
    result = re.sub(r'\?![\?!]+', '?!', result)
    result = re.sub(r'!\?[\?!]+', '!?', result)
    result = re.sub(r'\.{2,}', '…', result)

    # 3. Chuẩn hóa thán từ (Interjections): thêm dấu phẩy để AI ngắt hơi và nhấn âm tự nhiên (bỏ A, Ô, Á để không làm hỏng tên riêng như Ô Hạo, A Bảo)
    result = re.sub(r'(?i)(^|[\s.!?…\u201C\u201D"\'—–\-])(Ồ|Hừ|Ôi|Hơ|Chao ôi|Trời ơi|Ha ha|Hì hì|Hừm|Ô kìa|Ô hay)(?=\s+[\w\u00C0-\u1EF9])', r'\1\2,', result)

    # 4. Chuẩn hóa phát âm tiếng Việt cho CapCut / ByteDance TTS:
    # Tránh bị nhận nhầm thành số La Mã VI (6 -> sáu/sáo) và XI (11 -> mười mốt)
    result = re.sub(r'(?i)(chương|hồi|tập|phần|mục)\s+VI\b', r'\1 6', result)
    result = re.sub(r'(?i)(chương|hồi|tập|phần|mục)\s+XI\b', r'\1 11', result)
    result = re.sub(r'(?<![\w\u00C0-\u1EF9])vi(?![\w\u00C0-\u1EF9])', 'vy', result)
    result = re.sub(r'(?<![\w\u00C0-\u1EF9])Vi(?![\w\u00C0-\u1EF9])', 'Vy', result)
    result = re.sub(r'(?<![\w\u00C0-\u1EF9])VI(?![\w\u00C0-\u1EF9])', 'Vy', result)
    result = re.sub(r'(?<![\w\u00C0-\u1EF9])xi(?![\w\u00C0-\u1EF9])', 'xy', result)
    result = re.sub(r'(?<![\w\u00C0-\u1EF9])Xi(?![\w\u00C0-\u1EF9])', 'Xy', result)
    result = re.sub(r'(?<![\w\u00C0-\u1EF9])[Ôô](?![\w\u00C0-\u1EF9])', 'Ôh', result)
    result = re.sub(r'(?<![\w\u00C0-\u1EF9])A(?![\w\u00C0-\u1EF9])', 'Ah', result)
    result = re.sub(r'(?<![\w\u00C0-\u1EF9])a(?![\w\u00C0-\u1EF9])', 'ah', result)

    # 5. Tinh chỉnh nhịp ngắt nghỉ dấu câu tự nhiên và đều đặn:
    # Ép sau dấu phẩy CHỈ CÓ ĐÚNG 1 DẤU CÁCH DUY NHẤT (bằng nhau 100% giữa 1 vs 2 khoảng trắng)
    result = re.sub(r'[\s\u00A0\u1680\u2000-\u200A\u2028\u2029\u202F\u205F\u3000\uFEFF—–-]*[,，、﹐][\s\u00A0\u1680\u2000-\u200A\u2028\u2029\u202F\u205F\u3000\uFEFF—–-]*(?:…|\.{3})?', ', ', result)
    result = re.sub(r'\s*([;:.!?…])\s*', r'\1 ', result)
    result = re.sub(r' {2,}', ' ', result)
    result = re.sub(r'[.…~–—\s]+$', '.', result) # Đuôi câu đồng nhất dấu chấm
    result = re.sub(r' {2,}', ' ', result).strip()

    return result

@app.route("/api/pronunciation-rules", methods=["GET"])
def api_get_pronunciation_rules():
    return jsonify(get_pronunciation_rules())

@app.route("/api/pronunciation-rules", methods=["POST"])
def api_save_pronunciation_rules():
    data = request.get_json(force=True, silent=True) or {}
    rules = data.get("rules", [])
    saved = save_pronunciation_rules(rules)
    return jsonify({"success": True, "rules": saved})

@app.route("/api/voices", methods=["GET"])
def get_voices():
    return jsonify(VOICE_CATALOG)

@app.route("/api/books", methods=["GET"])
def get_books():
    return jsonify(get_library_index())

@app.route("/api/books/<book_id>", methods=["GET"])
def get_single_book(book_id):
    book_file = BOOKS_DIR / f"{book_id}.json"
    if not book_file.exists():
        return jsonify({"error": "Không tìm thấy truyện"}), 404
    try:
        with open(book_file, "r", encoding="utf-8") as f:
            book_data = json.load(f)
            try:
                from universal_parser import sort_chapters_if_scrambled
                book_data["chapters"] = sort_chapters_if_scrambled(book_data.get("chapters", []))
            except Exception:
                pass
            return jsonify(book_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/books/<book_id>", methods=["DELETE"])
def delete_book(book_id):
    book_file = BOOKS_DIR / f"{book_id}.json"
    if book_file.exists():
        try:
            book_file.unlink()
        except Exception:
            pass
    index_data = get_library_index()
    index_data = [b for b in index_data if b.get("id") != book_id]
    save_library_index(index_data)
    return jsonify({"success": True})

@app.route("/api/parse-epub", methods=["POST"])
@app.route("/api/parse-book", methods=["POST"])
@app.route("/api/upload", methods=["POST"])
def parse_epub():
    if "file" not in request.files:
        return jsonify({"error": "Chưa chọn file sách hoặc tài liệu"}), 400
    
    f = request.files["file"]
    orig_name = f.filename or "unknown.epub"
    orig_ext = Path(orig_name).suffix.lower() or ".epub"

    with tempfile.NamedTemporaryFile(delete=False, suffix=orig_ext) as tmp:
        f.save(tmp.name)
        tmp_path = tmp.name

    try:
        book_data = parse_any_book_file(tmp_path, orig_name)
        book_id = book_data["id"]
        title_str = book_data["title"]
        author_str = book_data["author"]
        chapters = book_data["chapters"]

        # Lưu truyện vào kho (Tối đa 10 cuốn)
        index_data = get_library_index()
        # Nếu sách đã có trong kho, cập nhật
        existing_idx = next((i for i, b in enumerate(index_data) if b.get("id") == book_id), None)
        
        if existing_idx is not None:
            last_ch = index_data[existing_idx].get("lastChapter", 0)
            last_para = index_data[existing_idx].get("lastParagraph", 0)
            index_data[existing_idx]["totalChapters"] = len(chapters)
            index_data[existing_idx]["title"] = title_str
            index_data[existing_idx]["author"] = author_str
        else:
            last_ch = 0
            last_para = 0
            # Nếu đã đủ 10 truyện, xoá truyện cũ nhất
            if len(index_data) >= 10:
                oldest_book = index_data.pop(-1)
                old_file = BOOKS_DIR / f"{oldest_book.get('id')}.json"
                if old_file.exists():
                    try:
                        old_file.unlink()
                    except Exception:
                        pass

            index_data.insert(0, {
                "id": book_id,
                "title": title_str,
                "author": author_str,
                "totalChapters": len(chapters),
                "lastChapter": 0,
                "lastParagraph": 0
            })

        save_library_index(index_data)

        # Lưu file nội dung truyện
        with open(BOOKS_DIR / f"{book_id}.json", "w", encoding="utf-8") as f_save:
            json.dump(book_data, f_save, ensure_ascii=False)

        # Lưu làm sách mở gần nhất
        with open(CACHE_DIR / "last_book_id.txt", "w", encoding="utf-8") as f_last:
            f_last.write(book_id)

        book_data["lastChapter"] = last_ch
        book_data["lastParagraph"] = last_para
        return jsonify(book_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@app.route("/api/web-novel/parse", methods=["POST"])
def api_parse_web_novel():
    req = request.get_json(force=True, silent=True) or {}
    url = req.get("url", "").strip()
    if not url:
        return jsonify({"error": "Vui lòng nhập link truyện hoặc link chương web"}), 400

    try:
        from web_crawler import fetch_web_novel
        story_data = fetch_web_novel(url, max_chapters=5)
        if not story_data or not story_data.get("chapters"):
            return jsonify({"error": "Không thể tải nội dung truyện từ đường link này. Vui lòng kiểm tra lại URL hoặc đảm bảo trang truyện mở công khai."}), 400

        title_str = story_data.get("title", "Truyện Online")
        author_str = story_data.get("author", "Tác giả Online")
        chapters = story_data.get("chapters", [])

        book_id = "web_" + hashlib.md5(url.encode('utf-8')).hexdigest()[:10]
        book_data = {
            "id": book_id,
            "title": title_str,
            "author": author_str,
            "source_url": url,
            "is_web": True,
            "slug": story_data.get("slug"),
            "last_crawl_url": story_data.get("last_crawl_url"),
            "next_chapter_index": story_data.get("next_chapter_index", len(chapters) + 1),
            "chapters": chapters,
            "totalChapters": len(chapters)
        }

        # Lưu truyện vào kho (Tối đa 10 cuốn)
        index_data = get_library_index()
        existing_idx = next((i for i, b in enumerate(index_data) if b.get("id") == book_id), None)
        if existing_idx is not None:
            last_ch = index_data[existing_idx].get("lastChapter", 0)
            last_para = index_data[existing_idx].get("lastParagraph", 0)
            index_data[existing_idx]["totalChapters"] = len(chapters)
            index_data[existing_idx]["title"] = title_str
            index_data[existing_idx]["author"] = author_str
            index_data[existing_idx]["is_web"] = True
        else:
            last_ch = 0
            last_para = 0
            if len(index_data) >= 10:
                oldest_book = index_data.pop(-1)
                old_file = BOOKS_DIR / f"{oldest_book.get('id')}.json"
                if old_file.exists():
                    try:
                        old_file.unlink()
                    except Exception:
                        pass
            index_data.insert(0, {
                "id": book_id,
                "title": title_str,
                "author": author_str,
                "totalChapters": len(chapters),
                "lastChapter": 0,
                "lastParagraph": 0,
                "is_web": True
            })

        save_library_index(index_data)

        with open(BOOKS_DIR / f"{book_id}.json", "w", encoding="utf-8") as f_save:
            json.dump(book_data, f_save, ensure_ascii=False)

        with open(CACHE_DIR / "last_book_id.txt", "w", encoding="utf-8") as f_last:
            f_last.write(book_id)

        # Đảm bảo last_ch không vượt quá số lượng chương hiện có trong book_data
        safe_last_ch = min(max(0, last_ch), max(0, len(chapters) - 1))
        book_data["lastChapter"] = safe_last_ch
        book_data["lastParagraph"] = last_para if safe_last_ch == last_ch else 0
        return jsonify(book_data)
    except Exception as e:
        print("Lỗi parse_web_novel:", e)
        return jsonify({"error": f"Lỗi nạp truyện: {str(e)}"}), 500

@app.route("/api/web-novel/search", methods=["POST", "GET"])
def api_search_web_novels():
    if request.method == "POST":
        req = request.get_json(force=True, silent=True) or {}
        q = req.get("query", req.get("keyword", "")).strip()
    else:
        q = request.args.get("query", request.args.get("keyword", "")).strip()

    if not q:
        return jsonify({"success": True, "results": [], "count": 0})

    try:
        from web_crawler import search_web_novels
        results = search_web_novels(q, limit=20)
        for it in results:
            if "site" not in it:
                it["site"] = it.get("source") or it.get("domain") or "Truyện Web"
        return jsonify({"success": True, "results": results, "count": len(results)})
    except Exception as e:
        print("Lỗi search_web_novels:", e)
        return jsonify({"error": str(e), "results": []}), 500


@app.route("/api/web-novel/fetch-more", methods=["POST"])
def api_fetch_more_chapters():
    req = request.get_json(force=True, silent=True) or {}
    book_id = req.get("bookId")
    count = int(req.get("count", 5))
    last_url = req.get("lastUrl")
    if not book_id:
        return jsonify({"error": "Thiếu bookId"}), 400

    book_file = BOOKS_DIR / f"{book_id}.json"
    if not book_file.exists():
        if last_url:
            from web_crawler import parse_generic_chapter, parse_xtruyen_chapter
            new_chapters = []
            cur_url = last_url
            for _ in range(count):
                if not cur_url:
                    break
                if 'xtruyen.vn' in cur_url:
                    chap = parse_xtruyen_chapter(cur_url)
                else:
                    chap = parse_generic_chapter(cur_url)

                if not chap or not chap.get('paragraphs'):
                    break
                c_title = chap.get('chapter_title') or f"Chương {len(new_chapters) + 1}"
                new_ch = {
                    "index": len(new_chapters),
                    "title": c_title,
                    "paragraphs": chap.get('paragraphs', []),
                    "source_url": cur_url,
                    "next_url": chap.get('next_url')
                }
                new_chapters.append(new_ch)
                nxt = chap.get('next_url')
                if not nxt or nxt == cur_url:
                    break
                cur_url = nxt
            if new_chapters:
                return jsonify({
                    "success": True,
                    "added": len(new_chapters),
                    "newChapters": new_chapters
                })
        return jsonify({"error": "Không tìm thấy truyện"}), 404

    try:
        with open(book_file, "r", encoding="utf-8") as f:
            book_data = json.load(f)

        if last_url:
            book_data["last_crawl_url"] = last_url

        from web_crawler import fetch_more_chapters
        success, added = fetch_more_chapters(book_data, count=count)
        if success and added > 0:
            with open(book_file, "w", encoding="utf-8") as f:
                json.dump(book_data, f, ensure_ascii=False)

            index_data = get_library_index()
            for b in index_data:
                if b.get("id") == book_id:
                    b["totalChapters"] = len(book_data.get("chapters", []))
                    break
            save_library_index(index_data)

            return jsonify({
                "success": True,
                "added": added,
                "totalChapters": len(book_data.get("chapters", [])),
                "newChapters": book_data.get("chapters", [])[-added:]
            })
        return jsonify({"success": False, "message": "Không có thêm chương mới hoặc đã đến chương cuối cùng"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/last-book", methods=["GET"])
def get_last_book():
    last_file = CACHE_DIR / "last_book_id.txt"
    book_id = None
    if last_file.exists():
        try:
            book_id = last_file.read_text(encoding="utf-8").strip()
        except Exception:
            pass

    index_data = get_library_index()
    if not book_id and index_data:
        book_id = index_data[0].get("id")

    if book_id:
        target_file = BOOKS_DIR / f"{book_id}.json"
        if target_file.exists():
            try:
                with open(target_file, "r", encoding="utf-8") as f_read:
                    data = json.load(f_read)
                entry = next((b for b in index_data if b.get("id") == book_id), {})
                data["lastChapter"] = entry.get("lastChapter", 0)
                data["lastParagraph"] = entry.get("lastParagraph", 0)
                return jsonify(data)
            except Exception as e:
                return jsonify({"error": str(e)}), 500
    return jsonify(None)

@app.route("/api/progress", methods=["POST"])
def manage_progress():
    data = request.get_json(force=True, silent=True) or {}
    book_id = data.get("bookId")
    chapter_idx = data.get("chapterIndex", 0)
    paragraph_idx = data.get("paragraphIndex", 0)

    if book_id:
        index_data = get_library_index()
        for b in index_data:
            if b.get("id") == book_id:
                b["lastChapter"] = chapter_idx
                b["lastParagraph"] = paragraph_idx
                break
        save_library_index(index_data)

        # Cập nhật last_book_id
        try:
            with open(CACHE_DIR / "last_book_id.txt", "w", encoding="utf-8") as f_last:
                f_last.write(book_id)
        except Exception:
            pass

        # Cập nhật tiến độ vào preloader
        if 'preloader' in globals():
            preloader.update(book_id, chapter_idx)

    return jsonify({"success": True})



capcut_tts_lock = threading.Lock()
eleven_tts_lock = threading.Lock()
_interactive_req_active = 0
_interactive_lock = threading.Lock()

def notify_interactive_start():
    global _interactive_req_active
    with _interactive_lock:
        _interactive_req_active += 1

def notify_interactive_done():
    global _interactive_req_active
    with _interactive_lock:
        _interactive_req_active = max(0, _interactive_req_active - 1)

def is_interactive_active():
    return _interactive_req_active > 0

def generate_capcut_audio(text, voice_id):
    if 'doc_lo' not in _capcut_ns:
        raise Exception("Chưa khởi tạo được module CapCut")
    clean_text = re.sub(r'[\s\u00A0\u1680\u2000-\u200A\u2028\u2029\u202F\u205F\u3000\uFEFF—–-]*[,，、﹐][\s\u00A0\u1680\u2000-\u200A\u2028\u2029\u202F\u205F\u3000\uFEFF—–-]*(?:…|\.{3})?', ', ', text)
    clean_text = re.sub(r' {2,}', ' ', clean_text).strip()
    last_err = None
    for attempt in range(3):
        try:
            with capcut_tts_lock:
                res = _capcut_ns['doc_lo']([clean_text], voice_id)
            if not res or not res[0]:
                raise Exception("CapCut không trả về đường dẫn âm thanh")
            audio_url = res[0]
            resp = requests.get(audio_url, timeout=12)
            resp.raise_for_status()
            if len(resp.content) > 300:
                return resp.content
        except Exception as e:
            last_err = e
            time.sleep(0.3 * (attempt + 1))
    raise last_err or Exception("Không thể tạo giọng đọc CapCut sau 3 lần thử")

ELEVEN_VOICE_MAP = {
    "almee-anh": "zA6D7RyKdc2EClouEMkP",
    "aimee-anh": "zA6D7RyKdc2EClouEMkP",
    "almee": "zA6D7RyKdc2EClouEMkP",
    "aimee": "zA6D7RyKdc2EClouEMkP",
    "adam-anh": "Gsndh0O5AnuI2Hj3YUlA",
    "adam": "Gsndh0O5AnuI2Hj3YUlA",
    "adam-my": "IRHApOXLvnW57QJPQH2P",
    "adam-us": "IRHApOXLvnW57QJPQH2P",
}

def generate_elevenlabs_audio(text, voice_id):
    if not _elevenlabs_tts:
        raise Exception("Chưa khởi tạo được module ElevenLabs TTS")

    clean_vid = str(voice_id).replace("eleven_", "").strip()
    clean_vid = ELEVEN_VOICE_MAP.get(clean_vid.lower(), clean_vid)

    last_err = None
    for attempt in range(2):
        try:
            with eleven_tts_lock:
                audio_url = _elevenlabs_tts.get_audio_url(text, clean_vid)
            if not audio_url:
                raise Exception("ElevenLabs không trả về URL âm thanh")
            resp = requests.get(audio_url, timeout=10)
            resp.raise_for_status()
            if len(resp.content) > 300:
                return resp.content
        except Exception as e:
            last_err = e
            time.sleep(0.2 * (attempt + 1))
    raise last_err or Exception(f"Không thể tạo giọng đọc ElevenLabs: {last_err}")

async def generate_edge_audio(text, voice_id, speed=1.0, emotion="normal"):
    rate_percent = int((speed - 1.0) * 100)
    pitch_str = "+0Hz"
    if emotion == "cold":
        rate_percent -= 8
        pitch_str = "-12Hz"
    elif emotion == "cold_shout":
        rate_percent += 15
        pitch_str = "-10Hz"
    elif emotion in ("angry_shout", "angry"):
        rate_percent += 18
        pitch_str = "+15Hz"
    elif emotion == "mocking":
        rate_percent -= 6
        pitch_str = "+6Hz"
    elif emotion == "solemn":
        rate_percent -= 14
        pitch_str = "-18Hz"
    elif emotion == "weak_pain":
        rate_percent -= 18
        pitch_str = "-8Hz"
    elif emotion == "laugh_joy":
        rate_percent += 12
        pitch_str = "+12Hz"
    elif emotion == "telepathy":
        rate_percent -= 5
        pitch_str = "+0Hz"
    elif emotion == "tender":
        rate_percent -= 6
        pitch_str = "+4Hz"
    elif emotion == "whisper":
        rate_percent -= 10
        pitch_str = "-4Hz"

    rate_str = f"+{rate_percent}%" if rate_percent >= 0 else f"{rate_percent}%"
    communicate = edge_tts.Communicate(text, voice_id, rate=rate_str, pitch=pitch_str)
    audio_bytes = bytearray()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_bytes.extend(chunk["data"])
    return bytes(audio_bytes)

def get_silent_audio():
    silent_file = CACHE_DIR / "silent.mp3"
    if silent_file.exists() and silent_file.stat().st_size > 300:
        try:
            with open(silent_file, "rb") as sf:
                return sf.read()
        except Exception:
            pass
    return b'\xff\xfb\x90d\x00\x00\x00\x00' * 50

def merge_audio_chunks(chunks_bytes):
    """Ghép nhiều đoạn audio (WAV, MP3) thành 1 luồng MP3 thống nhất mượt mà"""
    valid_chunks = [c for c in chunks_bytes if c and len(c) > 0]
    if not valid_chunks:
        return None
    if len(valid_chunks) == 1:
        return valid_chunks[0]

    ffmpeg_bin = BASE_DIR / "ffmpeg.exe"
    ffmpeg_cmd = str(ffmpeg_bin) if ffmpeg_bin.exists() else "ffmpeg"

    temp_files = []
    try:
        inputs = []
        filter_parts = []
        for i, c in enumerate(valid_chunks):
            ext = ".wav" if c.startswith(b"RIFF") else ".mp3"
            t = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
            t.write(c)
            t.close()
            temp_files.append(t.name)
            inputs.extend(["-i", t.name])
            filter_parts.append(f"[{i}:a]aformat=sample_rates=24000:channel_layouts=mono[a{i}];")

        concat_in = "".join(f"[a{i}]" for i in range(len(valid_chunks)))
        filter_str = "".join(filter_parts) + f"{concat_in}concat=n={len(valid_chunks)}:v=0:a=1[out]"

        cmd = [ffmpeg_cmd, "-y"] + inputs + ["-filter_complex", filter_str, "-map", "[out]", "-b:a", "64k", "-f", "mp3", "pipe:1"]
        res = subprocess.run(cmd, capture_output=True)
        if res.returncode == 0 and res.stdout:
            return res.stdout
        else:
            print("[merge_audio_chunks Error]", res.stderr.decode('utf-8', errors='ignore'))
            if all(not c.startswith(b"RIFF") for c in valid_chunks):
                return b"".join(valid_chunks)
            return valid_chunks[0]
    except Exception as e:
        print("[merge_audio_chunks Exception]", e)
        return valid_chunks[0]
    finally:
        for f in temp_files:
            try:
                os.remove(f)
            except Exception:
                pass

def synthesize_audio_smart(spoken_text, voice_id, provider, speed=1.0, bilingual_mode="off", emotion="normal"):
    # 1. Tự động chuyển ký hiệu toán học & so sánh (> ➔ lớn hơn, < ➔ nhỏ hơn, >= ➔ lớn hơn hoặc bằng...)
    spoken_text = bilingual.convert_symbols_to_spoken_text(spoken_text)

    # 2. Tự động loại bỏ chữ tiếng Hán khỏi câu để không gây lỗi cho AI tiếng Việt
    clean_text = re.sub(r'[\u4e00-\u9fff]+', '', spoken_text).strip()
    # Chuẩn hóa tuyệt đối nhịp nghỉ dấu phẩy: Mọi dấu phẩy đều chỉ có đúng 1 dấu cách duy nhất
    clean_text = re.sub(r'[\s\u00A0\u1680\u2000-\u200a\u202f\u205f\u3000—–-]*[,，、﹐][\s\u00A0\u1680\u2000-\u200a\u202f\u205f\u3000—–-]*(?:…|\.{3})?', ', ', clean_text)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    if not clean_text:
        return None

    if emotion in ("cold", "cold_shout", "angry_shout") and not clean_text.endswith(('!', '?')):
        clean_text = clean_text.rstrip(' ,;…-–—') + '!'

    if not bilingual_mode:
        bilingual_mode = bilingual.get_bilingual_mode()

    # Smart Provider Routing: Tự động điều phối provider theo định dạng voice_id
    effective_provider = provider
    str_v = str(voice_id).lower()
    if str_v.startswith("offline_"):
        effective_provider = "offline"
    elif str_v.startswith("vi-vn-") or str_v.startswith("en-us-"):
        effective_provider = "edge"
    elif str_v.startswith("bv") or "bigtts" in str_v or "vi_female" in str_v:
        effective_provider = "capcut"

    # 2. Xử lý theo chế độ song ngữ đã chọn
    is_11labs = (effective_provider == "elevenlabs" or str(voice_id).startswith("eleven_") or "almee" in str_v or "adam" in str_v)

    if is_11labs:
        # Nếu đang chọn giọng ElevenLabs (Almee-Anh, Adam-Anh, Adam-Mỹ) -> Sinh âm thanh tiếng Anh chuẩn Studio
        try:
            return generate_elevenlabs_audio(clean_text, voice_id)
        except Exception as e:
            print(f"[ElevenLabs Fallback] {e}. Đang chuyển ngay sang CapCut English (en_us_006).")
            try:
                return generate_capcut_audio(clean_text, "en_us_006")
            except Exception as e2:
                print(f"[CapCut Fallback Error] {e2}")
                if offline_dict_engine:
                    try:
                        b, _ = offline_dict_engine.OfflineTtsEngine.get_online_tts_bytes(clean_text, "en")
                        if b: return b
                    except Exception:
                        pass
                return None

    if bilingual_mode == "phonetic":
        # Chế độ 2: Phiên âm thuần Việt - chuyển toàn bộ từ tiếng Anh sang cách đọc ngữ âm tiếng Việt
        clean_text = bilingual.transliterate_english_to_vietnamese(clean_text)
        if effective_provider == "offline" or voice_id.startswith("offline_"):
            return offline_tts.synthesize_offline(clean_text, voice_id, speed)
        elif effective_provider == "capcut":
            return generate_capcut_audio(clean_text, voice_id)
        else:
            return asyncio.run(generate_edge_audio(clean_text, voice_id, speed, emotion=emotion))

    elif bilingual_mode == "native":
        # Chế độ 1: Song ngữ bản xứ (Giọng lai Việt + Mỹ chuẩn bản xứ)
        segments = bilingual.split_into_language_segments(clean_text)
        has_en = any(lang == 'en' for lang, _ in segments)

        # Nếu không có từ tiếng Anh -> đọc bình thường với giọng đã chọn
        if not has_en:
            if effective_provider == "offline" or voice_id.startswith("offline_"):
                return offline_tts.synthesize_offline(clean_text, voice_id, speed)
            elif effective_provider == "capcut":
                return generate_capcut_audio(clean_text, voice_id)
            else:
                return asyncio.run(generate_edge_audio(clean_text, voice_id, speed, emotion=emotion))

        # Nếu có từ tiếng Anh:
        if provider == "capcut":
            en_voice = bilingual.get_paired_english_voice(voice_id, "capcut")
            chunks = []
            for lang, seg in segments:
                s = seg.strip()
                if not s:
                    continue
                v = voice_id if lang == 'vi' else en_voice
                try:
                    c = generate_capcut_audio(s, v)
                    if c:
                        chunks.append(c)
                except Exception as err:
                    print(f"[Bilingual Native CapCut Error] '{s}' với giọng {v}: {err}")
                    c = generate_capcut_audio(s, voice_id)
                    if c:
                        chunks.append(c)
            return b"".join(chunks) if chunks else None

        elif provider == "edge":
            en_voice = bilingual.get_paired_english_voice(voice_id, "edge")
            chunks = []
            for lang, seg in segments:
                s = seg.strip()
                if not s:
                    continue
                v = voice_id if lang == 'vi' else en_voice
                try:
                    c = asyncio.run(generate_edge_audio(s, v, speed, emotion=emotion))
                    if c:
                        chunks.append(c)
                except Exception as err:
                    print(f"[Bilingual Native Edge Error] '{s}' với giọng {v}: {err}")
                    c = asyncio.run(generate_edge_audio(s, voice_id, speed, emotion=emotion))
                    if c:
                        chunks.append(c)
            return b"".join(chunks) if chunks else None

        else: # offline TTS
            en_voice = bilingual.get_paired_english_voice(voice_id, "offline")
            chunks = []
            for lang, seg in segments:
                s = seg.strip()
                if not s:
                    continue
                if lang == 'vi':
                    try:
                        c = offline_tts.synthesize_offline(s, voice_id, speed)
                        if c:
                            chunks.append(c)
                    except Exception as err:
                        print(f"[Bilingual Native Offline VI Error] '{s}': {err}")
                else: # lang == 'en'
                    c = None
                    try:
                        c = generate_capcut_audio(s, en_voice)
                    except Exception as err:
                        print(f"[Bilingual Native Offline -> CapCut Error] '{s}' với giọng {en_voice}: {err}")

                    if not c:
                        try:
                            edge_en = "en-US-JennyNeural" if "001" in en_voice else "en-US-GuyNeural"
                            c = asyncio.run(generate_edge_audio(s, edge_en, speed))
                        except Exception as err:
                            print(f"[Bilingual Native Offline -> Edge Error] '{s}': {err}")

                    if not c:
                        try:
                            phonetic_s = bilingual.transliterate_english_to_vietnamese(s)
                            c = offline_tts.synthesize_offline(phonetic_s, voice_id, speed)
                        except Exception as err:
                            print(f"[Bilingual Native Offline -> Phonetic Error] '{s}': {err}")

                    if c:
                        chunks.append(c)

            if not chunks:
                return None
            return merge_audio_chunks(chunks)

    else:
        # Chế độ 0: Tắt (Mặc định) - giữ nguyên câu gốc
        if effective_provider == "offline" or voice_id.startswith("offline_"):
            return offline_tts.synthesize_offline(clean_text, voice_id, speed)
        elif effective_provider == "capcut":
            return generate_capcut_audio(clean_text, voice_id)
        else:
            return asyncio.run(generate_edge_audio(clean_text, voice_id, speed, emotion=emotion))

@app.route("/api/bilingual-mode", methods=["GET", "POST"])
def api_bilingual_mode():
    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or {}
        mode = data.get("mode", "off")
        saved = bilingual.set_bilingual_mode(mode)
        return jsonify({"success": True, "mode": saved})
    return jsonify({"mode": bilingual.get_bilingual_mode()})

@app.route("/api/custom-english-words", methods=["GET", "POST"])
def api_custom_english_words():
    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or {}
        if "words" in data and isinstance(data["words"], list):
            saved = bilingual.save_custom_english_words(data["words"])
            return jsonify({"success": True, "words": saved})
        word = data.get("word", "").strip()
        phonetic = data.get("phonetic", "").strip()
        desc = data.get("desc", "").strip()
        res = bilingual.add_custom_english_word(word, phonetic, desc)
        res["words"] = bilingual.get_custom_english_words()
        return jsonify(res)
    return jsonify(bilingual.get_custom_english_words())

@app.route("/api/custom-english-words/delete", methods=["POST"])
def api_delete_custom_english_word():
    data = request.get_json(force=True, silent=True) or {}
    word = data.get("word", "").strip()
    ok = bilingual.delete_custom_english_word(word)
    return jsonify({"success": ok, "words": bilingual.get_custom_english_words()})

@app.route("/api/offline_voices", methods=["GET"])
def get_offline_voices():
    return jsonify(offline_tts.get_all_voices_status())

@app.route("/api/offline_voices/demo/<voice_id>", methods=["GET"])
def get_offline_voice_demo(voice_id):
    try:
        audio_data = offline_tts.get_demo_audio_bytes(voice_id)
        if audio_data:
            return send_file(io.BytesIO(audio_data), mimetype="audio/wav")
        return jsonify({"error": "Không tìm thấy file demo"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/offline_voices/download", methods=["POST"])
def download_offline_voice():
    data = request.get_json(force=True, silent=True) or {}
    voice_id = data.get("voice_id", "")
    if not voice_id:
        return jsonify({"error": "Thiếu voice_id"}), 400
    res = offline_tts.start_download_voice(voice_id)
    return jsonify(res)

@app.route("/api/offline_voices/delete", methods=["POST"])
def delete_offline_voice():
    data = request.get_json(force=True, silent=True) or {}
    voice_id = data.get("voice_id", "")
    if not voice_id:
        return jsonify({"error": "Thiếu voice_id"}), 400
    ok = offline_tts.delete_voice(voice_id)
    return jsonify({"success": ok})

@app.route("/api/tts", methods=["POST"])
def get_tts():
    notify_interactive_start()
    spoken_text = ""
    try:
        req = request.get_json(force=True, silent=True) or {}
        text = req.get("text", "").strip()
        voice_id = req.get("voice_id") or req.get("voice") or "BV074_streaming"
        provider = req.get("provider", "capcut")
        if provider == "elevenlabs" or str(voice_id).startswith("eleven_") or "almee" in str(voice_id).lower() or "adam" in str(voice_id).lower():
            provider = "elevenlabs"
        speed = float(req.get("speed", 1.0))
        bilingual_mode = req.get("bilingual_mode") or bilingual.get_bilingual_mode()
        emotion = req.get("emotion") or "normal"
        dialogue_role = req.get("dialogue_role") or "narration"
        speaker = req.get("speaker") or ""

        is_offline = (provider == "offline" or voice_id.startswith("offline_"))
        default_mime = "audio/wav" if is_offline else "audio/mpeg"

        if not text:
            return send_file(io.BytesIO(get_silent_audio()), mimetype=default_mime)

        book_id = req.get("book_id") or req.get("bookId")
        filtered_text = filter_skipped_phrases(text, book_id=book_id)
        if not filtered_text or not re.search(r'\w', filtered_text, re.UNICODE):
            return send_file(io.BytesIO(get_silent_audio()), mimetype=default_mime)

        # Kiểm tra và xử lý từ tượng thanh (Foley SFX Engine)
        sfx_type, pruned_sfx, sfx_count = offline_tts.detect_and_prune_sfx(filtered_text)
        if sfx_type:
            if not pruned_sfx or not re.search(r'\w', pruned_sfx, re.UNICODE):
                # Câu thuần túy là từ tượng thanh (ví dụ: "Oanh long!", "Ầm!", "Keng!", "Vút!", "Vèo, vèo, vèo!")
                sfx_wav = offline_tts.generate_sfx_wav_bytes(sfx_type, count=sfx_count)
                if sfx_wav:
                    return send_file(io.BytesIO(sfx_wav), mimetype="audio/wav")
            else:
                filtered_text = pruned_sfx

        spoken_text = apply_pronunciation_rules(filtered_text)
        spoken_text = bilingual.convert_symbols_to_spoken_text(spoken_text)
        # Đồng nhất tuyệt đối dấu phẩy và khoảng trắng trước khi tính cache hash
        spoken_text = re.sub(r'[\s\u00A0\u1680\u2000-\u200a\u202f\u205f\u3000—–-]*[,，、﹐][\s\u00A0\u1680\u2000-\u200a\u202f\u205f\u3000—–-]*(?:…|\.{3})?', ', ', spoken_text)
        spoken_text = re.sub(r'\s+', ' ', spoken_text).strip()
        words_ver = bilingual.get_custom_words_version()
        cache_key = hashlib.md5(f"v2_breath:{provider}:{voice_id}:{speed}:{emotion}:{bilingual_mode}:{words_ver}:{spoken_text}".encode('utf-8')).hexdigest()

        # Kiểm tra cache trước (hỗ trợ cả .mp3 và .wav)
        for ext, m in [("mp3", "audio/mpeg"), ("wav", "audio/wav")]:
            cache_file = CACHE_DIR / f"{cache_key}.{ext}"
            if cache_file.exists() and cache_file.stat().st_size > 1000:
                return send_file(cache_file, mimetype=m)

        audio_bytes = synthesize_audio_smart(spoken_text, voice_id, provider, speed, bilingual_mode, emotion=emotion)
        if not audio_bytes or len(audio_bytes) < 1000:
            # Câu chỉ có chữ Hán -> trả về im lặng ngắn nhưng không lưu vào cache
            return send_file(io.BytesIO(get_silent_audio()), mimetype=default_mime)

        # Tự động nhận diện định dạng audio thực tế từ header byte
        if audio_bytes.startswith(b"RIFF"):
            actual_mime = "audio/wav"
            actual_ext = "wav"
        else:
            actual_mime = "audio/mpeg"
            actual_ext = "mp3"

        cache_file = CACHE_DIR / f"{cache_key}.{actual_ext}"
        with open(cache_file, "wb") as f:
            f.write(audio_bytes)
        return send_file(cache_file, mimetype=actual_mime)
    except Exception as e:
        print(f"[TTS Error] Lỗi tạo âm thanh câu '{spoken_text[:40]}...': {e}")
        # Trả về HTTP 500 để trình đọc ở client biết và thử lại sau 1.2s, TUYỆT ĐỐI không nhảy cóc qua câu kế tiếp
        return jsonify({"error": str(e)}), 500
    finally:
        notify_interactive_done()


# =====================================================================
# BỘ ĐỆM TỰ ĐỘNG TẢI TRƯỚC 30 CHƯƠNG (SLIDING WINDOW PRELOADER SIÊU TỐC)
# Luôn giữ trước tối đa 30 chương trong bộ nhớ đệm, đa luồng tải nhanh gấp 3 lần
# =====================================================================
def split_into_sentences(text):
    if not text:
        return []
    text = re.sub(r'\.{3,}', '…', text.strip())
    if not text:
        return []
    text = re.sub(r'\.\s*([a-zA-Z]{2,6})\b', r'\uE000\1', text)
    def mask_quotes(m):
        q = m.group(0)
        return q.replace('.', '\uE001').replace('!', '\uE002').replace('?', '\uE003').replace('…', '\uE004')
    text = re.sub(r'([“"«「『][^”"»」』]+[”"»」』])', mask_quotes, text)
    matches = re.findall(r'([^.!?…\n]+(?:[.!?…]+["\'”’»)]*|[\n]+|$))', text)
    raw_sentences = []
    buf = ""
    for m in matches:
        part = m.replace('\uE000', '.').replace('\uE001', '.').replace('\uE002', '!').replace('\uE003', '?').replace('\uE004', '…').strip()
        if not part:
            continue
        if re.match(r'^\d+\.$', part) or re.match(r'^\$\d+\.$', part):
            buf = f"{buf} {part}" if buf else part
            continue
        if buf:
            part = f"{buf} {part}"
            buf = ""
        if len(part) > 220:
            sub_parts = re.split(r'([,;:—]\s+)', part)
            sub_buf = ""
            for s in sub_parts:
                if len(sub_buf) + len(s) > 160 and len(sub_buf) > 30:
                    raw_sentences.append(sub_buf.strip())
                    sub_buf = s
                else:
                    sub_buf += s
            if sub_buf.strip():
                raw_sentences.append(sub_buf.strip())
        else:
            raw_sentences.append(part)
    if buf.strip():
        raw_sentences.append(buf.strip())
    return raw_sentences

class ChapterPreloader:
    def __init__(self):
        self.lock = threading.Lock()
        self.enabled = True
        self.book_id = None
        self.current_chapter = 0
        self.window_size = 30
        self.voice_id = "BV074_streaming"
        self.provider = "capcut"
        self.speed = 1.0
        
        self.is_running = False
        self.current_working_chapter = None
        self.current_working_para = 0
        self.total_working_paras = 0
        self.cached_count = 0
        self.window_total = 0
        self.total_book_chapters = 0
        
        self._thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._thread.start()

    def update(self, book_id, chapter_idx, voice_id=None, provider=None, speed=None, window_size=30, enabled=None):
        with self.lock:
            self.book_id = book_id
            self.current_chapter = chapter_idx
            if voice_id: self.voice_id = voice_id
            if provider: self.provider = provider
            if speed: self.speed = speed
            self.window_size = min(int(window_size or 30), 30)
            if enabled is not None:
                self.enabled = enabled

    def toggle(self):
        with self.lock:
            self.enabled = not self.enabled
            return self.enabled

    def get_status(self):
        with self.lock:
            return {
                "enabled": self.enabled,
                "bookId": self.book_id,
                "currentChapter": self.current_chapter,
                "windowSize": self.window_size,
                "cachedCount": self.cached_count,
                "windowTotal": self.window_total,
                "isWorking": self.is_running,
                "workingChapter": self.current_working_chapter,
                "workingPara": self.current_working_para,
                "totalWorkingParas": self.total_working_paras,
                "totalBookChapters": self.total_book_chapters
            }

    def _get_cache_key(self, text, voice_id, provider, speed, emotion="normal"):
        spoken_text = apply_pronunciation_rules(text)
        spoken_text = bilingual.convert_symbols_to_spoken_text(spoken_text)
        b_mode = bilingual.get_bilingual_mode()
        words_ver = bilingual.get_custom_words_version()
        return hashlib.md5(f"v2_breath:{provider}:{voice_id}:{speed}:{emotion}:{b_mode}:{words_ver}:{spoken_text}".encode('utf-8')).hexdigest()

    def _is_para_cached(self, text, voice_id, provider, speed):
        key = self._get_cache_key(text, voice_id, provider, speed)
        for ext in ["mp3", "wav"]:
            p = CACHE_DIR / f"{key}.{ext}"
            if p.exists() and p.stat().st_size > 500:
                return True
        return False

    def _cache_para(self, text, voice_id, provider, speed):
        spoken_text = apply_pronunciation_rules(text)
        spoken_text = bilingual.convert_symbols_to_spoken_text(spoken_text)
        b_mode = bilingual.get_bilingual_mode()
        key = self._get_cache_key(text, voice_id, provider, speed)
        for ext in ["mp3", "wav"]:
            p = CACHE_DIR / f"{key}.{ext}"
            if p.exists() and p.stat().st_size > 500:
                return True
        try:
            audio_bytes = synthesize_audio_smart(spoken_text, voice_id, provider, speed, b_mode, emotion="normal")
            if audio_bytes and len(audio_bytes) > 500:
                ext = "wav" if audio_bytes.startswith(b"RIFF") else "mp3"
                p = CACHE_DIR / f"{key}.{ext}"
                with open(p, "wb") as f:
                    f.write(audio_bytes)
                return True
            else:
                # Nếu câu không có âm thanh (chữ Hán hoặc ký hiệu rỗng), lưu file im lặng nhỏ để tránh kẹt
                p = CACHE_DIR / f"{key}.mp3"
                with open(p, "wb") as f:
                    f.write(get_silent_audio())
                return True
        except Exception as e:
            print(f"[Preload] Bỏ qua câu do lỗi ('{spoken_text[:30]}...'): {e}")
            return False

    def _worker_loop(self):
        from concurrent.futures import ThreadPoolExecutor, as_completed
        while True:
            time.sleep(0.3)
            try:
                with self.lock:
                    if not self.enabled or not self.book_id:
                        continue
                    book_id = self.book_id
                    start_ch = self.current_chapter
                    win_size = min(self.window_size, 30)
                    voice_id = self.voice_id
                    provider = self.provider
                    speed = self.speed

                book_file = BOOKS_DIR / f"{book_id}.json"
                if not book_file.exists():
                    continue

                try:
                    with open(book_file, "r", encoding="utf-8") as f:
                        book_data = json.load(f)
                except Exception:
                    continue

                chapters = book_data.get("chapters", [])
                total_chapters = len(chapters)
                if not chapters or start_ch >= total_chapters:
                    continue

                # Tự động nạp thêm chương từ web nếu còn dưới 30 chương phía trước
                if book_data.get("is_web"):
                    remaining_ahead = total_chapters - 1 - start_ch
                    if remaining_ahead < win_size:
                        needed = win_size - remaining_ahead
                        to_fetch = min(needed, 5)
                        try:
                            from web_crawler import fetch_more_chapters
                            succ, added = fetch_more_chapters(book_data, count=to_fetch)
                            if succ and added > 0:
                                with open(book_file, "w", encoding="utf-8") as f_save:
                                    json.dump(book_data, f_save, ensure_ascii=False)
                                idx_data = get_library_index()
                                for b in idx_data:
                                    if b.get("id") == book_id:
                                        b["totalChapters"] = len(book_data.get("chapters", []))
                                        break
                                save_library_index(idx_data)
                                chapters = book_data.get("chapters", [])
                                total_chapters = len(chapters)
                                print(f"[Preloader] Đã tự động nạp thêm {added} chương web mới. Tổng: {total_chapters}")
                        except Exception as ex_fetch:
                            print(f"[Preloader] Lỗi tự nạp thêm chương web: {ex_fetch}")

                with self.lock:
                    self.total_book_chapters = total_chapters

                end_ch = min(start_ch + win_size, total_chapters)
                window_slice = list(range(start_ch, end_ch))

                skip_rules = get_skip_rules(book_id)
                cached_in_win = 0
                needed_chapters = []

                for c_idx in window_slice:
                    ch = chapters[c_idx]
                    paras = ch.get("paragraphs", [])
                    missing_sentences = []
                    all_sentences = []
                    for p in paras:
                        p_txt = p.strip()
                        if not p_txt or is_text_skipped(p_txt, skip_rules, book_id):
                            continue
                        sents = split_into_sentences(p_txt)
                        for s in sents:
                            s_txt = filter_skipped_phrases(s, skip_rules, book_id).strip()
                            clean_text = re.sub(r'[\u4e00-\u9fff]+', '', s_txt).strip()
                            if clean_text and re.search(r'\w', clean_text, re.UNICODE):
                                all_sentences.append(s_txt)
                                if not self._is_para_cached(s_txt, voice_id, provider, speed):
                                    missing_sentences.append(s_txt)
                    
                    if len(missing_sentences) == 0 and len(all_sentences) > 0:
                        cached_in_win += 1
                    elif len(missing_sentences) > 0:
                        needed_chapters.append((c_idx, missing_sentences, len(all_sentences)))

                with self.lock:
                    self.cached_count = cached_in_win
                    self.window_total = len(window_slice)

                if not needed_chapters:
                    with self.lock:
                        self.is_running = False
                    time.sleep(1.0)
                    continue

                for c_idx, missing_sentences, total_s in needed_chapters:
                    with self.lock:
                        if (not self.enabled or self.book_id != book_id or 
                            self.current_chapter != start_ch or self.voice_id != voice_id):
                            break
                        self.is_running = True
                        self.current_working_chapter = c_idx
                        self.total_working_paras = total_s
                        self.current_working_para = 0

                    num_workers = 1 if (provider == "offline" or str(voice_id).startswith("offline_")) else 3

                    def task_fn(txt_to_cache):
                        while is_interactive_active():
                            time.sleep(0.5)
                        res = self._cache_para(txt_to_cache, voice_id, provider, speed)
                        with self.lock:
                            self.current_working_para = min(self.current_working_para + 1, total_s)
                        return res

                    with ThreadPoolExecutor(max_workers=num_workers) as executor:
                        futures = []
                        for txt in missing_sentences:
                            with self.lock:
                                if (not self.enabled or self.book_id != book_id or 
                                    self.current_chapter != start_ch or self.voice_id != voice_id):
                                    break
                            futures.append(executor.submit(task_fn, txt))

                        for fut in as_completed(futures):
                            try:
                                fut.result()
                            except Exception:
                                pass

                    # Cập nhật số chương đã đệm xong ngay khi chương c_idx hoàn thành
                    with self.lock:
                        if (self.book_id == book_id and self.current_chapter == start_ch and self.voice_id == voice_id):
                            self.cached_count = min(self.cached_count + 1, self.window_total)

                with self.lock:
                    self.is_running = False

            except Exception as loop_err:
                print(f"[Preloader Loop Error]: {loop_err}")
                time.sleep(1.0)

preloader = ChapterPreloader()

@app.route("/api/preload/update", methods=["POST"])
def update_preload():
    req = request.get_json(force=True, silent=True) or {}
    book_id = req.get("bookId")
    chapter_idx = int(req.get("chapterIndex", 0))
    voice_id = req.get("voiceId")
    provider = req.get("provider")
    speed = float(req.get("speed", 1.0))
    window_size = int(req.get("windowSize", 30))
    enabled = req.get("enabled")
    if book_id:
        preloader.update(book_id, chapter_idx, voice_id, provider, speed, window_size, enabled)
    return jsonify(preloader.get_status())

@app.route("/api/preload/status", methods=["GET"])
def get_preload_status():
    book_id = request.args.get("bookId")
    if book_id and not preloader.book_id:
        preloader.update(book_id, 0)
    return jsonify(preloader.get_status())

@app.route("/api/preload/toggle", methods=["POST"])
def toggle_preload():
    req = request.get_json(force=True, silent=True) or {}
    desired = req.get("enabled")
    if desired is not None:
        with preloader.lock:
            preloader.enabled = bool(desired)
            new_state = preloader.enabled
    else:
        new_state = preloader.toggle()
    return jsonify({"enabled": new_state})

@app.route("/api/web-novel/preload-batch", methods=["POST"])
def api_preload_batch():
    req = request.get_json(force=True, silent=True) or {}
    book_id = req.get("bookId")
    count = int(req.get("count", 30))
    if not book_id:
        return jsonify({"error": "Thiếu bookId"}), 400

    book_file = BOOKS_DIR / f"{book_id}.json"
    if not book_file.exists():
        return jsonify({"error": "Không tìm thấy truyện"}), 404

    try:
        with open(book_file, "r", encoding="utf-8") as f:
            book_data = json.load(f)

        from web_crawler import fetch_more_chapters
        success, added = fetch_more_chapters(book_data, count=count)
        if success and added > 0:
            with open(book_file, "w", encoding="utf-8") as f:
                json.dump(book_data, f, ensure_ascii=False)

            index_data = get_library_index()
            for b in index_data:
                if b.get("id") == book_id:
                    b["totalChapters"] = len(book_data.get("chapters", []))
                    break
            save_library_index(index_data)

            return jsonify({
                "success": True,
                "added": added,
                "totalChapters": len(book_data.get("chapters", []))
            })
        return jsonify({"success": False, "message": "Không có thêm chương mới hoặc đã đến chương mới nhất"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/debug_methods', methods=['POST'])
def receive_debug_methods():
    try:
        data = request.get_json(force=True)
        print("\n" + "="*50)
        print("[HONOR DEBUG] Received methods from device:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print("="*50 + "\n")
        debug_log = BASE_DIR / "honor_device_methods.json"
        with open(debug_log, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =====================================================================
# TÍCH HỢP TỪ ĐIỂN & DỊCH THUẬT NGOẠI TUYẾN (OFFLINE DICTIONARY)
# =====================================================================
OFFLINE_DICT_PATH = Path(r"D:\3. DOCUMENT\Antigravity\Offline Dictionary")
offline_dict_engine = None

if OFFLINE_DICT_PATH.exists() and str(OFFLINE_DICT_PATH) not in sys.path:
    sys.path.append(str(OFFLINE_DICT_PATH))

try:
    import translator as offline_dict_engine
    print("[OK] Đã kết nối thành công với bộ Từ điển & Dịch thuật Ngoại tuyến (132K từ & AI NMT)!")
except Exception as _e_dict:
    print(f"[WARN] Không thể nạp module từ điển Offline Dictionary: {_e_dict}")

@app.route("/api/dictionary/translate", methods=["POST"])
def api_dictionary_translate():
    req = request.get_json(force=True, silent=True) or {}
    text = req.get("text", "").strip()
    source_lang = req.get("source_lang", "auto")
    target_lang = req.get("target_lang", "vi")
    mode = req.get("mode", "auto")  # 'auto', 'offline', 'online'

    if not text:
        return jsonify({"success": False, "error": "Chưa có nội dung cần dịch"}), 400

    if not offline_dict_engine:
        return jsonify({
            "success": False,
            "error": "Bộ từ điển ngoại tuyến chưa được cấu hình trên máy chủ"
        }), 500

    try:
        # 1. Dịch từ / câu bằng PolyTranslator
        trans_res = offline_dict_engine.PolyTranslator.translate(text, source_lang, target_lang, mode)
        translated_text = trans_res.get("text", "")
        detected_lang = trans_res.get("detected_lang") or ("en" if source_lang == "auto" else source_lang)
        engine = trans_res.get("engine", "offline_dict")
        source_label = trans_res.get("source", "")

        # 2. Tra cứu chi tiết từ điển SQLite (132K từ) nếu là 1-3 từ
        dict_details = None
        ipa = ""
        is_short_phrase = len(text.split()) <= 3
        if is_short_phrase:
            try:
                w_info = offline_dict_engine.OfflineTranslator.lookup_word(text, detected_lang, target_lang)
                if not w_info and '-' in text:
                    w_info = offline_dict_engine.OfflineTranslator.lookup_word(text.split('-')[0], detected_lang, target_lang)
                if w_info:
                    dict_details = w_info
                    # Trích xuất phiên âm IPA từ thẻ <i>/.../</i> hoặc /.../
                    html_content = w_info.get("html", "")
                    import re
                    m_ipa = re.search(r"<i>/([^/<]+)/</i>", html_content)
                    if not m_ipa:
                        m_ipa = re.search(r"/([^/<]{2,30})/", html_content)
                    if m_ipa:
                        ipa = m_ipa.group(1).strip()
                    # Nếu chưa có bản dịch hoặc bản dịch là rỗng, lấy simple_meaning từ từ điển
                    if not translated_text and w_info.get("simple_meaning"):
                        translated_text = w_info.get("simple_meaning")
                        engine = "offline_dict"
            except Exception as _ex_lookup:
                print(f"[DICT LOOKUP EXCEPTION] {_ex_lookup}")

        return jsonify({
            "success": True,
            "original_text": text,
            "translated_text": translated_text,
            "detected_lang": detected_lang,
            "target_lang": target_lang,
            "engine": engine,
            "source_label": source_label,
            "ipa": ipa,
            "dict_details": dict_details,
            "raw": trans_res
        })
    except Exception as e:
        print(f"[TRANSLATE EXCEPTION] {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/dictionary/tts", methods=["POST", "GET"])
def api_dictionary_tts():
    if request.method == "POST":
        req = request.get_json(force=True, silent=True) or {}
        text = req.get("text", "").strip()
        lang = req.get("lang", "en")
    else:
        text = request.args.get("text", "").strip()
        lang = request.args.get("lang", "en")

    if not text:
        return jsonify({"error": "Thiếu nội dung phát âm"}), 400

    if not offline_dict_engine:
        return jsonify({"error": "Bộ từ điển ngoại tuyến chưa sẵn sàng"}), 500

    try:
        # 1. Thử phát âm bằng Offline VITS Piper trước
        if offline_dict_engine.OfflineTtsEngine.is_available(lang):
            wav_bytes = offline_dict_engine.OfflineTtsEngine.synthesize_wav_bytes(text, lang)
            if wav_bytes:
                return send_file(
                    io.BytesIO(wav_bytes),
                    mimetype="audio/wav",
                    as_attachment=False,
                    download_name="dict_pronounce.wav"
                )
        # 2. Nếu chưa có offline, dùng online TTS fallback
        if offline_dict_engine.check_internet():
            audio_bytes, mime = offline_dict_engine.OfflineTtsEngine.get_online_tts_bytes(text, lang)
            if audio_bytes:
                return send_file(
                    io.BytesIO(audio_bytes),
                    mimetype=mime or "audio/mpeg",
                    as_attachment=False,
                    download_name="dict_pronounce.mp3"
                )
        return jsonify({"error": "Không thể phát âm từ này"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/dictionary/packages", methods=["GET"])
def api_dictionary_packages():
    if not offline_dict_engine:
        return jsonify({"success": False, "error": "Bộ từ điển chưa sẵn sàng"}), 500
    try:
        data = offline_dict_engine.DownloadManager.get_packages_status()
        return jsonify({"success": True, **data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/dictionary/download/start", methods=["POST"])
def api_dictionary_download_start():
    if not offline_dict_engine:
        return jsonify({"success": False, "message": "Bộ từ điển chưa sẵn sàng"}), 500
    try:
        req = request.get_json(force=True, silent=True) or {}
        pkg_id = req.get("package_id", "dict_full_109k")
        res = offline_dict_engine.DownloadManager.start_download(pkg_id)
        return jsonify(res)
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/dictionary/download/progress", methods=["GET"])
def api_dictionary_download_progress():
    if not offline_dict_engine:
        return jsonify({"active": False, "error": "Bộ từ điển chưa sẵn sàng"}), 500
    try:
        data = offline_dict_engine.DownloadManager.get_progress()
        return jsonify(data)
    except Exception as e:
        return jsonify({"active": False, "error": str(e)}), 500

@app.route("/api/dictionary/packages/delete", methods=["POST"])
def api_dictionary_packages_delete():
    if not offline_dict_engine:
        return jsonify({"success": False, "message": "Bộ từ điển chưa sẵn sàng"}), 500
    try:
        req = request.get_json(force=True, silent=True) or {}
        pkg_id = req.get("package_id")
        res = offline_dict_engine.DownloadManager.delete_package(pkg_id)
        return jsonify(res)
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == "__main__":
    print("Khởi động Trình Đọc Truyện EPUB tại http://localhost:5000 hoặc http://0.0.0.0:5000 ...")
    app.run(host="0.0.0.0", port=5000, debug=False)
