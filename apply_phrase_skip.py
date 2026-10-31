import re
import os
import sys

# Paths to update
files_to_update = [
    r"c:\Users\VANLUC\Downloads\Share tool -20261010T221918Z-1-001\Share tool\TTS_STT_vip_v1.6.0\HonorEpubReader\app\src\main\assets\index.html",
    r"D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\templates\index.html",
    r"c:\Users\VANLUC\Downloads\Share tool -20261010T221918Z-1-001\Share tool\DesktopEpubReader\templates\index.html"
]

server_files = [
    r"D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\server.py",
    r"c:\Users\VANLUC\Downloads\Share tool -20261010T221918Z-1-001\Share tool\DesktopEpubReader\server.py"
]

def update_html_file(filepath):
    if not os.path.exists(filepath):
        print(f"[SKIP] File not found: {filepath}")
        return False
    print(f"[UPDATING] {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add .skipped-phrase CSS
    if '.skipped-phrase' not in content:
        css_replacement = """.paragraph-item.skipped {
      opacity: 0.38;
      text-decoration: line-through;
      font-style: italic;
    }
    .skipped-phrase {
      text-decoration: line-through !important;
      opacity: 0.45;
      color: #888888 !important;
      background-color: rgba(239, 68, 68, 0.12);
      border-radius: 3px;
      padding: 0 2px;
      cursor: pointer;
    }
    body.theme-dark .skipped-phrase,
    body.honor-dark-mode .skipped-phrase {
      color: #999999 !important;
      background-color: rgba(239, 68, 68, 0.18);
    }"""
        content = re.sub(
            r'\.paragraph-item\.skipped\s*\{[^}]*\}',
            lambda m: css_replacement,
            content,
            count=1
        )
        print("  -> Injected .skipped-phrase CSS")

    # 2. Add menuOptionSkipPhrase to #paraContextMenu
    if 'id="menuOptionSkipPhrase"' not in content:
        old_menu_skip = r'''<div id="menuOptionSkip" class="context-menu-item danger" onclick="onContextMenuAction('toggle_skip')">
      <span id="menuOptionSkipText">🚫 Bỏ qua câu này</span>
    </div>'''
        new_menu_skip = '''<div id="menuOptionSkipPhrase" class="context-menu-item danger" style="display:none;" onclick="onContextMenuAction('toggle_skip_phrase')">
      <span id="menuOptionSkipPhraseText">🚫 Bỏ qua chữ đã chọn</span>
    </div>
    <div id="menuOptionSkip" class="context-menu-item danger" onclick="onContextMenuAction('toggle_skip')">
      <span id="menuOptionSkipText">🚫 Bỏ qua câu này</span>
    </div>'''
        if old_menu_skip in content:
            content = content.replace(old_menu_skip, new_menu_skip)
            print("  -> Added menuOptionSkipPhrase to context menu")
        else:
            content = re.sub(
                r'(<div id="menuOptionSkip"[^>]*>[\s\S]*?</div>)',
                lambda m: f'''<div id="menuOptionSkipPhrase" class="context-menu-item danger" style="display:none;" onclick="onContextMenuAction('toggle_skip_phrase')">
      <span id="menuOptionSkipPhraseText">🚫 Bỏ qua chữ đã chọn</span>
    </div>\n    {m.group(1)}''',
                content,
                count=1
            )
            print("  -> Added menuOptionSkipPhrase via regex")

    # 3. Add toggleSkipSelectedText to textSelectionToolbar
    if 'toggleSkipSelectedText()' not in content:
        old_toolbar_btn = r'''<button class="sel-btn" onclick="copySelectedText()" title="Sao chép phần chữ đã chọn">
        <span>📋 Sao chép</span>
      </button>'''
        new_toolbar_btn = '''<button class="sel-btn" onclick="copySelectedText()" title="Sao chép phần chữ đã chọn">
        <span>📋 Sao chép</span>
      </button>
      <button class="sel-btn" onclick="toggleSkipSelectedText()" title="Bỏ qua không đọc các chữ đã chọn này">
        <span>🚫 Bỏ qua chữ chọn</span>
      </button>'''
        if old_toolbar_btn in content:
            content = content.replace(old_toolbar_btn, new_toolbar_btn)
            print("  -> Added toggleSkipSelectedText to selection toolbar")
        else:
            content = re.sub(
                r'(<button class="sel-btn"[^>]*onclick="copySelectedText\(\)"[^>]*>[\s\S]*?</button>)',
                lambda m: f'''{m.group(1)}\n      <button class="sel-btn" onclick="toggleSkipSelectedText()" title="Bỏ qua không đọc các chữ đã chọn này">\n        <span>🚫 Bỏ qua chữ chọn</span>\n      </button>''',
                content,
                count=1
            )
            print("  -> Added toggleSkipSelectedText to selection toolbar via regex")

    # 4. Replace isParagraphSkipped and add filterSkippedPhrases, renderSentenceHtml
    skip_rules_old_pattern = r'// QUẢN LÝ DANH SÁCH CÂU BỎ QUA \(SKIP RULES\)[\s\S]*?async function loadSkipRules\(bookId = null\)'
    skip_rules_new_code = '''// QUẢN LÝ DANH SÁCH CÂU & CỤM TỪ BỎ QUA (SKIP RULES)
    // =====================================================================
    let skipRules = [];

    function normalizeForCompare(str) {
      return (str || '').replace(/\\s+/g, ' ').trim().toLowerCase();
    }

    function filterSkippedPhrases(str) {
      if (!str) return '';
      if (!skipRules || skipRules.length === 0) return str;
      let res = str;
      const sorted = [...skipRules].filter(r => r && r.trim()).sort((a, b) => b.length - a.length);
      for (const r of sorted) {
        const cleanR = r.trim();
        if (!cleanR) continue;
        try {
          const esc = cleanR.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&');
          res = res.replace(new RegExp(esc, 'gi'), ' ');
        } catch (_) {}
      }
      res = res.replace(/,\\s*,+/g, ',').replace(/\\s+/g, ' ').trim();
      return res;
    }

    function isParagraphSkipped(text) {
      if (!text) return true;
      // Tự động bỏ qua câu nếu phát hiện chữ tiếng Hán
      if (/[\\u4e00-\\u9fff]/.test(text)) return true;
      if (!skipRules || skipRules.length === 0) return false;
      const norm = normalizeForCompare(text);
      if (skipRules.some(r => norm === normalizeForCompare(r))) return true;
      // Nếu sau khi lược bỏ các cụm từ bị bỏ qua, câu không còn chữ cái/số nào để đọc
      const filtered = filterSkippedPhrases(text);
      if (!filtered || !/[^\\p{P}\\s]/u.test(filtered)) return true;
      return false;
    }

    function renderSentenceHtml(sentText) {
      if (!sentText) return '';
      if (!skipRules || skipRules.length === 0) {
        return escapeHtml(sentText);
      }
      const normSent = normalizeForCompare(sentText);
      const activePhraseRules = skipRules.filter(r => {
        if (!r || !r.trim()) return false;
        const normR = normalizeForCompare(r);
        return normR && normR !== normSent && normSent.includes(normR);
      }).sort((a, b) => b.length - a.length);

      if (activePhraseRules.length === 0) {
        return escapeHtml(sentText);
      }

      const escapedPatterns = activePhraseRules.map(r => escapeHtml(r.trim()).replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&')).join('|');
      try {
        const regex = new RegExp(`(${escapedPatterns})`, 'gi');
        return escapeHtml(sentText).replace(regex, '<span class="skipped-phrase" title="Cụm từ đã bỏ qua không đọc">$1</span>');
      } catch (_) {
        return escapeHtml(sentText);
      }
    }

    async function loadSkipRules(bookId = null)'''

    if 'function filterSkippedPhrases(' not in content:
        content = re.sub(skip_rules_old_pattern, lambda m: skip_rules_new_code, content, count=1)
        print("  -> Injected filterSkippedPhrases & renderSentenceHtml into skip rules section")

    # 5. Update updateSkippedParagraphsInDOM to refresh sentence-item spans
    old_update_dom = r'''function updateSkippedParagraphsInDOM() {
      const reader = document.getElementById('readerContent');
      if (!reader) return;
      const items = reader.querySelectorAll('.paragraph-item');
      items.forEach(el => {
        const text = el.textContent;
        if (isParagraphSkipped(text)) {
          el.classList.add('skipped');
        } else {
          el.classList.remove('skipped');
        }
      });
    }'''

    new_update_dom = '''function updateSkippedParagraphsInDOM() {
      const reader = document.getElementById('readerContent');
      if (!reader) return;
      const items = reader.querySelectorAll('.paragraph-item');
      items.forEach(el => {
        const text = el.textContent;
        if (isParagraphSkipped(text)) {
          el.classList.add('skipped');
        } else {
          el.classList.remove('skipped');
        }
      });
      const sItems = reader.querySelectorAll('.sentence-item');
      sItems.forEach(sEl => {
        const sIdx = parseInt(sEl.dataset.index);
        if (!isNaN(sIdx) && typeof allSentences !== 'undefined' && allSentences[sIdx]) {
          sEl.innerHTML = renderSentenceHtml(allSentences[sIdx]) + ' ';
        }
      });
    }'''
    if old_update_dom in content:
        content = content.replace(old_update_dom, new_update_dom)
        print("  -> Updated updateSkippedParagraphsInDOM")

    # 6. Add toggleSkipSelectedText function
    if 'function toggleSkipSelectedText(' not in content:
        target_pos = "function removeSkipRule(ruleText) {"
        toggle_func = '''function toggleSkipSelectedText() {
      const w = (currentSelectedText || (window.getSelection() ? window.getSelection().toString() : '')).trim();
      dismissSelectionToolbar();
      if (!w) return;
      const normW = normalizeForCompare(w);
      if (skipRules.some(r => normalizeForCompare(r) === normW)) {
        removeSkipRule(w);
      } else {
        addSkipRule(w);
      }
    }

    '''
        content = content.replace(target_pos, toggle_func + target_pos)
        print("  -> Added toggleSkipSelectedText function")

    # 7. Update showContextMenu skip item handling
    old_show_ctx_skip = r'''      if (skipItem && skipText) {
        if (isParagraphSkipped(text)) {
          skipItem.className = 'context-menu-item success';
          skipText.textContent = '✅ Khôi phục câu này (không bỏ qua nữa)';
        } else {
          skipItem.className = 'context-menu-item danger';
          skipText.textContent = '🚫 Bỏ qua câu này (không đọc ở mọi chương)';
        }
      }'''

    new_show_ctx_skip = '''      const skipPhraseItem = document.getElementById('menuOptionSkipPhrase');
      const skipPhraseText = document.getElementById('menuOptionSkipPhraseText');
      const normTarget = normalizeForCompare(targetWord);
      const normText = normalizeForCompare(text);
      const hasSpecificSelection = targetWord && targetWord.length > 0 && normTarget !== normText;

      if (skipPhraseItem && skipPhraseText) {
        if (hasSpecificSelection) {
          skipPhraseItem.style.display = 'flex';
          const displayW = targetWord.length > 20 ? targetWord.substring(0, 20) + '...' : targetWord;
          const isWordSkipped = skipRules.some(r => normalizeForCompare(r) === normTarget);
          if (isWordSkipped) {
            skipPhraseItem.className = 'context-menu-item success';
            skipPhraseText.textContent = `✅ Khôi phục chữ đã chọn ("${displayW}")`;
          } else {
            skipPhraseItem.className = 'context-menu-item danger';
            skipPhraseText.textContent = `🚫 Bỏ qua chữ đã chọn ("${displayW}")`;
          }
        } else {
          skipPhraseItem.style.display = 'none';
        }
      }

      if (skipItem && skipText) {
        if (isParagraphSkipped(text)) {
          skipItem.className = 'context-menu-item success';
          skipText.textContent = '✅ Khôi phục câu này (không bỏ qua nữa)';
        } else {
          skipItem.className = 'context-menu-item danger';
          skipText.textContent = hasSpecificSelection ? '🚫 Bỏ qua toàn bộ câu này' : '🚫 Bỏ qua câu này (không đọc ở mọi chương)';
        }
      }'''

    if old_show_ctx_skip in content:
        content = content.replace(old_show_ctx_skip, new_show_ctx_skip)
        print("  -> Updated showContextMenu skip item display")

    # 8. Update onContextMenuAction
    old_action_skip = r'''      if (action === 'toggle_skip') {
        if (isParagraphSkipped(text)) {
          removeSkipRule(text);
        } else {
          addSkipRule(text);
        }
      }'''

    new_action_skip = '''      if (action === 'toggle_skip_phrase') {
        const w = targetW || contextMenuSelectedWord;
        if (w) {
          const normW = normalizeForCompare(w);
          if (skipRules.some(r => normalizeForCompare(r) === normW)) {
            removeSkipRule(w);
          } else {
            addSkipRule(w);
          }
        }
      } else if (action === 'toggle_skip') {
        const normW = normalizeForCompare(targetW);
        const normT = normalizeForCompare(text);
        if (targetW && normW !== normT) {
          // Người dùng đang chọn cụm từ cụ thể -> chỉ bỏ qua cụm từ đó!
          if (skipRules.some(r => normalizeForCompare(r) === normW)) {
            removeSkipRule(targetW);
          } else {
            addSkipRule(targetW);
          }
        } else {
          // Không chọn chữ nào -> thao tác trên toàn bộ câu/đoạn
          if (isParagraphSkipped(text)) {
            removeSkipRule(text);
          } else {
            addSkipRule(text);
          }
        }
      } else if (action === 'toggle_skip_whole') {
        if (isParagraphSkipped(text)) {
          removeSkipRule(text);
        } else {
          addSkipRule(text);
        }
      }'''

    if old_action_skip in content:
        content = content.replace(old_action_skip, new_action_skip)
        print("  -> Updated onContextMenuAction skip logic")

    # 9. Update loadChapter to render sentence spans with renderSentenceHtml
    old_span_text = "span.textContent = sentText + ' ';"
    new_span_text = "span.innerHTML = renderSentenceHtml(sentText) + ' ';"
    if old_span_text in content:
        content = content.replace(old_span_text, new_span_text)
        print("  -> Updated loadChapter to use renderSentenceHtml for sentence spans")

    # 10. Update prefetchSentenceAudio to filter skipped phrases
    old_prefetch_filter = r'''      const text = allSentences[sIdx].trim();
      if (!text || isParagraphSkipped(text)) return;'''

    new_prefetch_filter = '''      const text = allSentences[sIdx].trim();
      if (!text || isParagraphSkipped(text)) return;
      const spokenText = filterSkippedPhrases(text);
      if (!spokenText || !/[^\\p{P}\\s]/u.test(spokenText)) return;'''

    if old_prefetch_filter in content:
        content = content.replace(old_prefetch_filter, new_prefetch_filter)
        content = content.replace(
            "text: text,\n            voice_id: voiceId,\n            provider: provider,",
            "text: spokenText,\n            book_id: bookData ? bookData.id : null,\n            voice_id: voiceId,\n            provider: provider,"
        )
        print("  -> Updated prefetchSentenceAudio to filter skipped phrases")

    # 11. Update playParagraph to filter skipped phrases
    old_play_text = r'''      let text = allSentences[idx].trim();
      if (!text) {
        nextParagraph();
        return;
      }'''

    new_play_text = '''      let text = allSentences[idx].trim();
      if (!text) {
        nextParagraph();
        return;
      }
      const spokenText = filterSkippedPhrases(text);
      if (!spokenText || !/[^\\p{P}\\s]/u.test(spokenText)) {
        console.log(`[Skip] Bỏ qua câu do không còn từ đọc sau khi lọc cụm từ: "${text}"`);
        nextParagraph();
        return;
      }'''

    if old_play_text in content:
        content = content.replace(old_play_text, new_play_text)
        # Replace occurrences in playParagraph for native TTS & synthesis
        content = content.replace(
            "updateMediaSession(ch.title, text);\n          const ok = window.HonorBridge.speakNative(text, currentSpeed);",
            "updateMediaSession(ch.title, spokenText);\n          const ok = window.HonorBridge.speakNative(spokenText, currentSpeed);"
        )
        content = content.replace(
            "const utt = new SpeechSynthesisUtterance(text);",
            "const utt = new SpeechSynthesisUtterance(spokenText);"
        )
        content = content.replace(
            "updateMediaSession(ch.title, text);\n          window.speechSynthesis.speak(utt);",
            "updateMediaSession(ch.title, spokenText);\n          window.speechSynthesis.speak(utt);"
        )
        content = content.replace(
            "text: text,\n              voice_id: voiceId,\n              provider: provider,",
            "text: spokenText,\n              book_id: bookData ? bookData.id : null,\n              voice_id: voiceId,\n              provider: provider,"
        )
        print("  -> Updated playParagraph to speak filtered text")

    # 12. Modal header text & description update
    content = content.replace(
        "<span>🚫 Danh Sách Bỏ Qua Câu <span id=\"skipRulesBookScope\"",
        "<span>🚫 Danh Sách Bỏ Qua Câu &amp; Cụm Từ <span id=\"skipRulesBookScope\""
    )
    content = content.replace(
        "Tự động bỏ qua không đọc các câu trùng khớp chính xác (như tên tác giả, dịch giả, nguồn đầu chương).",
        "Tự động bỏ qua không đọc các câu hoặc cụm từ được chọn (như tên dịch giả, watermark, cụm từ quảng cáo...)."
    )

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  [OK] Successfully updated {filepath}")
    return True

def update_server_file(filepath):
    if not os.path.exists(filepath):
        print(f"[SKIP] Server file not found: {filepath}")
        return False
    print(f"[UPDATING SERVER] {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Add filter_skipped_phrases and update is_text_skipped
    if 'def filter_skipped_phrases(' not in content:
        new_skip_func = '''def normalize_for_skip(text):
    if not text:
        return ""
    import re
    return re.sub(r'\\s+', ' ', text.strip().lower())

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
    result = re.sub(r',\\s*,+', ',', result)
    result = re.sub(r'\\s+', ' ', result).strip()
    return result

def is_text_skipped(text, rules=None, book_id=None):
    if not text:
        return True
    # Tự động bỏ qua câu nếu phát hiện chữ tiếng Hán
    if re.search(r'[\\u4e00-\\u9fff]', text):
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
    if not re.search(r'\\w', filtered, re.UNICODE):
        return True
    return False'''

        if 'def is_text_skipped(' in content:
            content = re.sub(
                r'def normalize_for_skip\(text\):[\s\S]*?def is_text_skipped\(text, rules=None, book_id=None\):[\s\S]*?return False',
                lambda m: new_skip_func,
                content,
                count=1
            )
            print("  -> Injected filter_skipped_phrases and updated is_text_skipped in server.py")

    # In ChapterPreloader, filter skipped phrases
    old_preloader_p = r'''            if not txt or is_text_skipped(txt, skip_rules, book_id):
                continue
            clean_text = re.sub(r'[\u4e00-\u9fff]+', '', txt).strip()'''

    new_preloader_p = '''            if not txt or is_text_skipped(txt, skip_rules, book_id):
                continue
            txt = filter_skipped_phrases(txt, skip_rules, book_id)
            clean_text = re.sub(r'[\u4e00-\u9fff]+', '', txt).strip()'''

    if old_preloader_p in content:
        content = content.replace(old_preloader_p, new_preloader_p)
        print("  -> Updated ChapterPreloader to filter skipped phrases")

    # In get_tts, filter skipped phrases
    old_get_tts = r'''        if not text:
            return send_file(io.BytesIO(get_silent_audio()), mimetype=default_mime)

        spoken_text = apply_pronunciation_rules(text)'''

    new_get_tts = '''        if not text:
            return send_file(io.BytesIO(get_silent_audio()), mimetype=default_mime)

        book_id = req.get("book_id") or req.get("bookId")
        filtered_text = filter_skipped_phrases(text, book_id=book_id)
        if not filtered_text or not re.search(r'\\w', filtered_text, re.UNICODE):
            return send_file(io.BytesIO(get_silent_audio()), mimetype=default_mime)

        spoken_text = apply_pronunciation_rules(filtered_text)'''

    if old_get_tts in content:
        content = content.replace(old_get_tts, new_get_tts)
        print("  -> Updated get_tts to filter skipped phrases before synthesis")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  [OK] Successfully updated server file {filepath}")
    return True

print("=== STARTING UPDATE ===")
for hf in files_to_update:
    update_html_file(hf)
for sf in server_files:
    update_server_file(sf)
print("=== ALL UPDATES COMPLETED ===")
