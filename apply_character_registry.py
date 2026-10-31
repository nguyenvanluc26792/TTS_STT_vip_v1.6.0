import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
import re

html_path = r'D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\templates\index.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Insert Sổ tay Nhân vật Modal HTML after bilingualModalOverlay
modal_anchor = """      <div style="padding: 10px 16px; border-top: 1px solid var(--border-color); display: flex; justify-content: flex-end;">
        <button class="btn btn-primary" onclick="closeBilingualModal()" style="font-size: 0.82rem; padding: 4px 14px;">Xong</button>
      </div>
    </div>
  </div>"""

char_modal_html = """
  <!-- Modal Sổ Tay Nhân Vật (Dynamic Character Registry & AI Multi-Voice) -->
  <div id="nrCharRegistryModalOverlay" class="modal-overlay" onclick="closeCharacterRegistryModal(event)">
    <div class="library-modal" onclick="event.stopPropagation()" style="max-width: 580px; max-height: 85vh; display: flex; flex-direction: column;">
      <div class="modal-header">
        <span style="display:flex; align-items:center; gap:8px;">📖 Sổ Tay Nhân Vật (Kịch Truyền Thanh AI)</span>
        <button class="btn" style="padding: 4px 8px;" onclick="closeCharacterRegistryModal()">✕</button>
      </div>
      <div class="modal-body" style="padding: 16px; overflow-y: auto; flex: 1;">
        <p style="font-size: 0.82rem; color: var(--text-muted); margin-bottom: 12px; line-height: 1.5;">
          Hệ thống AI tự động phân tích và ghi nhớ giới tính nhân vật theo cuốn truyện. Bạn có thể bấm để chuyển đổi giới tính thủ công (Nam ↔ Nữ) bất kỳ lúc nào nếu muốn.
        </p>

        <div style="display: flex; gap: 8px; margin-bottom: 14px;">
          <input type="text" id="nrCharSearchInput" placeholder="Tìm kiếm nhân vật trong truyện..." oninput="filterCharacterRegistryList()" style="flex: 1; padding: 8px 12px; border-radius: 8px; border: 1px solid var(--border-color); background: var(--card-bg); color: var(--text-color); font-size: 0.82rem; outline: none;">
          <button class="btn" onclick="clearCurrentBookCharacterRegistry()" style="font-size: 0.76rem; color: #ef4444; border-color: rgba(239,68,68,0.3); padding: 8px 12px; white-space: nowrap;">🗑️ Xóa bộ nhớ</button>
        </div>

        <div id="nrCharListContainer" style="display: flex; flex-direction: column; gap: 8px; min-height: 120px;">
          <span style="font-size:0.78rem; color:var(--text-muted); font-style:italic; padding:12px; text-align:center;">Đang tải danh sách nhân vật...</span>
        </div>
      </div>
      <div style="padding: 10px 16px; border-top: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center;">
        <span id="nrCharTotalCount" style="font-size: 0.78rem; color: var(--text-muted);">0 nhân vật</span>
        <button class="btn btn-primary" onclick="closeCharacterRegistryModal()" style="padding: 6px 16px; font-size: 0.82rem;">Xong</button>
      </div>
    </div>
  </div>"""

if modal_anchor in html:
    html = html.replace(modal_anchor, modal_anchor + "\n" + char_modal_html, 1)
    print("1. Added nrCharRegistryModalOverlay successfully!")
else:
    print("ERROR: modal_anchor not found!")
    exit(1)

# 2. Add Sổ tay Nhân vật button in Settings Drawer
drawer_anchor = """          <div class="nr-link-row" style="cursor:pointer;" onclick="toggleMultiVoiceSetting()">
            <div style="display:flex; flex-direction:column; gap:2px; flex:1;">
              <span style="font-weight:600;">🎭 Kịch truyền thanh AI (3 Phương án)</span>
              <span style="font-size:0.75rem; color:#888;">Tự động phân vai Nam - Nữ, ngắt nghỉ &amp; biểu cảm theo ngữ cảnh</span>
            </div>
            <span id="nrMultiVoiceStatus" class="nr-badge" style="background:#10b981; color:#fff; font-size:0.72rem; padding:3px 8px; border-radius:12px; font-weight:600;">ĐANG BẬT</span>
          </div>"""

drawer_link = """          <div class="nr-link-row" style="cursor:pointer;" onclick="openCharacterRegistryModal()">
            <div style="display:flex; flex-direction:column; gap:2px; flex:1;">
              <span style="font-weight:600;">📖 Sổ tay Nhân vật (AI Phân vai)</span>
              <span id="nrCharRegistrySub" style="font-size:0.75rem; color:#888;">Quản lý danh sách nhân vật, giới tính &amp; độ tin cậy của truyện</span>
            </div>
            <span id="nrCharCountBadge" class="nr-badge" style="background:rgba(56,189,248,0.18); color:#38bdf8; font-size:0.72rem; padding:3px 8px; border-radius:12px; font-weight:600;">0 nhân vật</span>
          </div>"""

if drawer_anchor in html:
    html = html.replace(drawer_anchor, drawer_anchor + "\n" + drawer_link, 1)
    print("2. Added So tay Nhan vat to Settings Drawer successfully!")
else:
    print("ERROR: drawer_anchor not found!")
    exit(1)

# 3. Replace the Dialogue Attribution & Add Registry Engine
code_anchor_start = """    // =====================================================================
    // HỆ THỐNG PHÂN VAI KỊCH TRUYỀN THANH TIÊN HIỆP & BỘ NHỚ LUÂN PHIÊN (TURN-TAKING)
    // TÍCH HỢP LOOK-AHEAD CONTEXT ATTRIBUTION & EMOTIONAL TONE MODULATION
    // ====================================================================="""

code_anchor_end = """    function analyzeDialogueGender(text, nextText = '', prevText = '') {
      const res = analyzeDialogueAttribution(text, nextText, prevText);
      return res.gender;
    }"""

new_engine_code = r"""    // =====================================================================
    // HỆ THỐNG XÁC ĐỊNH GIỚI TÍNH NHÂN VẬT ĐA TẦNG & SỔ TAY NHÂN VẬT (DYNAMIC STATE REGISTRY)
    // CÔNG THỨC TRỌNG SỐ: S_gender = w1·Pronoun + w2·Title + w3·LexicalName + w4·DialogueContext
    // =====================================================================
    let lastDialogueGender = 'male';

    const FEMALE_NAME_KEYWORDS = [
      'tuyết', 'liên', 'ngọc', 'nhi', 'yến', 'nhược', 'dao', 'mộng', 'tiên', 'linh', 'vũ', 'cầm',
      'nghiên', 'dung', 'thiến', 'điệp', 'mai', 'lan', 'cúc', 'trúc', 'hương', 'vy', 'my', 'thảo',
      'uyên', 'uyển', 'diễm', 'thanh', 'hà', 'phương', 'an', 'trâm', 'quỳnh', 'châu', 'tú', 'phượng',
      'thư', 'thục', 'huyên', 'thiền', 'tịnh', 'nga', 'loan', 'kiều', 'hân', 'thùy', 'trang', 'kỳ',
      'kính', 'nguyệt', 'hằng', 'tâm', 'huyền', 'nhạn', 'khuê', 'oanh', 'bích', 'thúy', 'thuần', 'nhã', 'tường'
    ];

    const MALE_NAME_KEYWORDS = [
      'long', 'thiên', 'phong', 'viêm', 'hàn', 'trần', 'mặc', 'chiến', 'bá', 'lôi', 'bằng', 'hạo',
      'kiệt', 'phàm', 'lâm', 'động', 'đằng', 'đạt', 'huy', 'minh', 'sơn', 'bảo', 'nam', 'bắc', 'hải',
      'quân', 'thành', 'trung', 'hiếu', 'nghĩa', 'trí', 'trọng', 'thần', 'nguyên', 'quang', 'hoàng',
      'đại', 'tiêu', 'binh', 'hùng', 'dũng', 'cường', 'tuấn', 'vũ', 'kiếm', 'đao', 'nhạc', 'thương',
      'ngạo', 'độc', 'cương', 'khang', 'thắng', 'bình', 'tiến', 'vĩnh', 'đức'
    ];

    const MALE_PRONOUNS = ['hắn', 'y', 'gã', 'lão', 'tên này', 'tiểu tử này', 'chàng', 'nam tử này', 'hắn ta'];
    const FEMALE_PRONOUNS = ['nàng', 'ả', 'thị', 'cô', 'nha đầu này', 'nàng ta', 'cô ấy', 'nữ tử này', 'tiểu nương tử'];

    const MALE_TITLES = [
      'sư huynh', 'sư đệ', 'sư thúc', 'sư bá', 'công tử', 'thiếu gia', 'đạo huynh', 'lão tổ',
      'lão quái', 'lão ma', 'chân nhân', 'tiên sinh', 'thánh tử', 'thiếu chủ', 'tiểu tử', 'đại hán',
      'lão giả', 'chưởng môn', 'tông chủ', 'vương gia', 'hoàng thượng', 'trượng phu', 'nam nhân',
      'nam tử', 'tiểu sinh', 'phụ thân', 'cha', 'đại ca', 'huynh đệ', 'huynh trưởng'
    ];

    const FEMALE_TITLES = [
      'sư tỷ', 'sư muội', 'sư thái', 'tiên tử', 'cô nương', 'tiểu thư', 'nương tử', 'phu nhân',
      'thánh nữ', 'yêu nữ', 'ma nữ', 'lão mẫu', 'bà bà', 'nha đầu', 'thiếu phụ', 'mỹ phụ',
      'nữ nhi', 'công chúa', 'sư nương', 'mẫu thân', 'mẹ', 'tiểu nha đầu', 'tiểu nữ hài',
      'bà lão', 'bà nội', 'bà ngoại'
    ];

    const COLD_KEYWORDS = ['lạnh lùng', 'hờ hững', 'lạnh nhạt', 'băng lãnh', 'khô khốc', 'thản nhiên', 'dứt khoát', 'nghiêm nghị', 'vô cảm', 'cười lạnh', 'hừ lạnh', 'băng hàn', 'lãnh khốc', 'nguội lạnh'];
    const ANGRY_KEYWORDS = ['tức giận', 'phẫn nộ', 'quát', 'thét', 'gầm', 'rống', 'oán hận', 'nghiến răng', 'hung dữ', 'nổi giận', 'thịnh nộ', 'quát mắng'];
    const TENDER_KEYWORDS = ['dịu dàng', 'ngọt ngào', 'thỏ thẻ', 'nhẹ nhàng', 'e thẹn', 'khẽ nói', 'mỉm cười', 'ngượng ngùng', 'ôn nhu'];
    const WHISPER_KEYWORDS = ['thì thầm', 'thì thào', 'nhỏ giọng', 'trầm giọng', 'lẩm bẩm', 'lặng lẽ', 'khẽ bảo'];

    // SỔ TAY NHÂN VẬT (REGISTRY PERSISTENCE)
    function getBookRegistryKey() {
      const bTitle = (typeof bookData !== 'undefined' && bookData && (bookData.title || bookData.id)) ? (bookData.title || bookData.id) : 'default_novel';
      return 'nr_char_registry_' + encodeURIComponent(String(bTitle).trim().slice(0, 50));
    }

    function loadCharacterRegistry() {
      try {
        const key = getBookRegistryKey();
        const raw = localStorage.getItem(key);
        return raw ? JSON.parse(raw) : {};
      } catch (e) {
        return {};
      }
    }

    function saveCharacterToRegistry(name, gender, confidence, source) {
      if (!name || typeof name !== 'string') return;
      const clean = name.trim();
      if (!clean || clean.length < 2) return;
      try {
        const key = getBookRegistryKey();
        const reg = loadCharacterRegistry();
        const existing = reg[clean];
        // Confidence upgrade: nâng cấp nếu chưa có hoặc độ tin cậy mới >= độ tin cậy cũ
        if (!existing || confidence >= (existing.confidence || 0)) {
          reg[clean] = {
            gender: gender,
            confidence: confidence,
            source: source,
            updatedAt: Date.now(),
            count: (existing?.count || 0) + 1
          };
        } else {
          existing.count = (existing.count || 0) + 1;
        }
        localStorage.setItem(key, JSON.stringify(reg));
        updateCharacterRegistryUIBadge();
      } catch (e) {
        console.warn('[CharacterRegistry] save error:', e);
      }
    }

    function updateCharacterGenderManual(name, newGender) {
      if (!name) return;
      try {
        const key = getBookRegistryKey();
        const reg = loadCharacterRegistry();
        if (reg[name]) {
          reg[name].gender = newGender;
          reg[name].confidence = 1.0;
          reg[name].source = 'Chỉ định thủ công';
          reg[name].updatedAt = Date.now();
          localStorage.setItem(key, JSON.stringify(reg));
          renderCharacterRegistryModal();
        }
      } catch (e) {}
    }

    function deleteCharacterFromRegistry(name) {
      if (!name) return;
      try {
        const key = getBookRegistryKey();
        const reg = loadCharacterRegistry();
        delete reg[name];
        localStorage.setItem(key, JSON.stringify(reg));
        renderCharacterRegistryModal();
        updateCharacterRegistryUIBadge();
      } catch (e) {}
    }

    function clearCurrentBookCharacterRegistry() {
      if (confirm('Bạn có chắc chắn muốn xóa toàn bộ bộ nhớ nhân vật đã ghi nhận của cuốn sách này? AI sẽ nhận diện lại từ đầu.')) {
        try {
          const key = getBookRegistryKey();
          localStorage.removeItem(key);
          renderCharacterRegistryModal();
          updateCharacterRegistryUIBadge();
        } catch (e) {}
      }
    }

    function updateCharacterRegistryUIBadge() {
      try {
        const reg = loadCharacterRegistry();
        const count = Object.keys(reg).length;
        const badge = document.getElementById('nrCharCountBadge');
        if (badge) badge.textContent = `${count} nhân vật`;
        const sub = document.getElementById('nrCharRegistrySub');
        if (sub) {
          if (count === 0) {
            sub.textContent = 'Chưa có nhân vật nào được lưu trong bộ nhớ cuốn này';
          } else {
            sub.textContent = `Đã ghi nhận ${count} nhân vật (Bấm để xem & đổi giọng)`;
          }
        }
      } catch (e) {}
    }

    function openCharacterRegistryModal() {
      const overlay = document.getElementById('nrCharRegistryModalOverlay');
      if (overlay) {
        overlay.classList.add('show');
        renderCharacterRegistryModal();
      }
    }

    function closeCharacterRegistryModal(e) {
      if (e && e.target && e.target !== e.currentTarget && !e.target.classList.contains('modal-overlay')) {
        return;
      }
      const overlay = document.getElementById('nrCharRegistryModalOverlay');
      if (overlay) overlay.classList.remove('show');
    }

    function filterCharacterRegistryList() {
      renderCharacterRegistryModal();
    }

    function renderCharacterRegistryModal() {
      const container = document.getElementById('nrCharListContainer');
      const totalCountEl = document.getElementById('nrCharTotalCount');
      const searchInput = document.getElementById('nrCharSearchInput');
      if (!container) return;

      const reg = loadCharacterRegistry();
      const query = (searchInput?.value || '').trim().toLowerCase();
      let entries = Object.entries(reg);

      if (query) {
        entries = entries.filter(([name]) => name.toLowerCase().includes(query));
      }

      entries.sort((a, b) => (b[1].count || 0) - (a[1].count || 0));

      if (totalCountEl) totalCountEl.textContent = `${entries.length} / ${Object.keys(reg).length} nhân vật`;

      if (entries.length === 0) {
        container.innerHTML = `<div style="text-align:center; padding:24px; color:var(--text-muted); font-size:0.84rem;">${query ? 'Không tìm thấy nhân vật phù hợp' : 'Chưa có nhân vật nào được phân vai trong cuốn sách này. Khi bạn nghe truyện có thoại, AI sẽ tự động điền danh sách vào đây.'}</div>`;
        return;
      }

      container.innerHTML = entries.map(([name, data]) => {
        const isMale = (data.gender === 'male');
        const badgeColor = isMale ? '#38bdf8' : '#f472b6';
        const badgeBg = isMale ? 'rgba(56,189,248,0.18)' : 'rgba(244,114,182,0.18)';
        const icon = isMale ? '👨' : '👩';
        const targetGender = isMale ? 'female' : 'male';
        const targetLabel = isMale ? 'Đổi sang Nữ 👩' : 'Đổi sang Nam 👨';
        const targetBtnColor = isMale ? '#f472b6' : '#38bdf8';
        const targetBtnBorder = isMale ? 'rgba(244,114,182,0.4)' : 'rgba(56,189,248,0.4)';
        const confPct = Math.round((data.confidence || 0.7) * 100);

        return `
          <div style="display:flex; align-items:center; justify-content:space-between; padding:10px 12px; background:rgba(255,255,255,0.03); border:1px solid var(--border-color); border-radius:10px; gap:8px;">
            <div style="display:flex; align-items:center; gap:10px; flex:1; min-width:0;">
              <div style="font-size:1.45rem; flex-shrink:0;">${icon}</div>
              <div style="min-width:0; flex:1;">
                <div style="display:flex; align-items:center; gap:6px; flex-wrap:wrap;">
                  <span style="font-weight:700; font-size:0.88rem; color:var(--text-color);">${name}</span>
                  <span style="font-size:0.70rem; font-weight:700; padding:1px 6px; border-radius:6px; background:${badgeBg}; color:${badgeColor};">${isMale ? 'Nam' : 'Nữ'} (${confPct}%)</span>
                </div>
                <div style="font-size:0.73rem; color:var(--text-muted); margin-top:2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                  Nguồn: ${data.source || 'Nhận diện tự động'} • ${data.count || 1} lượt thoại
                </div>
              </div>
            </div>
            <div style="display:flex; align-items:center; gap:6px; flex-shrink:0;">
              <button class="btn" onclick="updateCharacterGenderManual('${name.replace(/'/g, "\\\\'")}', '${targetGender}')" style="padding:5px 9px; font-size:0.74rem; font-weight:600; color:${targetBtnColor}; border-color:${targetBtnBorder};">
                ${targetLabel}
              </button>
              <button class="btn" onclick="deleteCharacterFromRegistry('${name.replace(/'/g, "\\\\'")}')" style="padding:5px 8px; font-size:0.74rem; color:#ef4444; border-color:transparent;" title="Xóa nhân vật này khỏi bộ nhớ">✕</button>
            </div>
          </div>
        `;
      }).join('');
    }

    // =====================================================================
    // HỆ THỐNG PHÂN VAI KỊCH TRUYỀN THANH ĐA TẦNG (LOOK-AHEAD CONTEXT ATTRIBUTION)
    // =====================================================================
    function analyzeDialogueAttribution(text, nextText = '', prevText = '') {
      try {
        if (!text) return { isDialogue: false, gender: 'narration', emotion: 'normal', speedFactor: 1.0, pitchFactor: 1.0, speaker: '' };

        const trimmed = text.trim();
        const isQuote = /^[“"«「『]/.test(trimmed) || /^[-–—]\s*/.test(trimmed) || /[“"«「『][^”"»」』]+[”"»」』]/.test(trimmed);
        if (!isQuote) {
          return { isDialogue: false, gender: 'narration', emotion: 'normal', speedFactor: 1.0, pitchFactor: 1.0, speaker: '' };
        }

        let dialogueContent = trimmed;
        const quoteMatch = trimmed.match(/[“"«「『]([^”"»」』]+)[”"»」』]/);
        let sameSentenceOuter = '';
        if (quoteMatch) {
          dialogueContent = quoteMatch[1];
          sameSentenceOuter = trimmed.replace(quoteMatch[0], ' ').trim();
        } else if (/^[-–—]/.test(trimmed)) {
          const dashMatch = trimmed.replace(/^[-–—]\s*/, '').match(/^(.+?[!?.…])\s+([A-ZÀ-Ỹa-zà-ỹ].*)$/);
          if (dashMatch) {
            dialogueContent = dashMatch[1].trim();
            sameSentenceOuter = dashMatch[2].trim();
          } else {
            dialogueContent = trimmed.replace(/^[-–—]\s*/, '');
          }
        } else {
          dialogueContent = trimmed;
        }

        // Vùng văn bản dẫn xuất (Lead-out & Lead-in), chuẩn hóa bỏ ký tự gạch đầu dòng
        const rawLeadOut = (sameSentenceOuter || nextText || '').trim();
        const leadOut = rawLeadOut.replace(/^[-–—\s:,]+/, '').trim();
        const rawLeadIn = (prevText || '').trim();
        const leadIn = rawLeadIn.replace(/[-–—\s:,]+$/, '').trim();

        let speaker = '';
        let manner = '';
        let verb = '';

        // TẦNG 1: TRÍCH XUẤT TÊN RIÊNG & NGƯỜI NÓI (LOOK-AHEAD & LOOK-BEHIND)
        if (leadOut) {
          // 1.1 Khớp Tên Riêng Viết Hoa (Bạch Tiểu Thuần, Nam Cung Uyển, Vương Đằng, Lữ Tuyết...)
          const nameMatch = leadOut.match(/^([A-ZÀ-Ỹ][a-zà-ỹ]+(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]+)*)(?:\s+(.*?))?\s*(lên tiếng|nói|hỏi|đáp|hừ(?:\s+một\s+tiếng)?|quát(?:\s+lớn)?|thét|hét(?:\s+lên)?|gầm(?:\s+lên)?|rống|la|cười(?:\s+lạnh|\s+khẽ|\s+nhạt|\s+gượng|\s+lớn|\s+một\s+tiếng)?|thầm|bảo|thì thào|thỏ thẻ|than|lẩm bẩm|thốt lên|nhủ|nghĩ|truyền âm|tiếp lời|khẽ nói|hô)(?:[,.;:!?…\s]|$)/);
          if (nameMatch) {
            speaker = nameMatch[1].trim();
            manner = (nameMatch[2] || '').trim();
            verb = (nameMatch[3] || '').trim();
          } else {
            // 1.2 Khớp Đại từ / Chức vị (Nàng, Hắn, Sư tỷ, Thiếu niên, Tiểu nha đầu...)
            const pronounMatch = leadOut.match(/^([A-ZÀ-Ỹa-zà-ỹ0-9\s]+?)\s+([a-zà-ỹ\s]*?)(lên tiếng|nói|hỏi|đáp|hừ(?:\s+một\s+tiếng)?|quát(?:\s+lớn)?|thét|hét(?:\s+lên)?|gầm(?:\s+lên)?|rống|la|cười(?:\s+lạnh|\s+khẽ|\s+nhạt|\s+gượng|\s+lớn|\s+một\s+tiếng)?|thầm|bảo|thì thào|thỏ thẻ|than|lẩm bẩm|thốt lên|nhủ|nghĩ|truyền âm|tiếp lời|khẽ nói|hô)(?:[,.;:!?…\s]|$)/i);
            if (pronounMatch) {
              speaker = pronounMatch[1].trim();
              manner = (pronounMatch[2] || '').trim();
              verb = (pronounMatch[3] || '').trim();
            }
          }
        }

        if (!speaker && leadIn) {
          const leadInMatch = leadIn.match(/([A-ZÀ-Ỹ][a-zà-ỹ]+(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]+)*|[a-zà-ỹ0-9\s]+?)\s+(.*?)\s*(?:nói|hỏi|đáp|lên tiếng|bảo|quát|nhủ|nghĩ)[:]\s*$/i);
          if (leadInMatch) {
            speaker = leadInMatch[1].trim();
            manner = (leadInMatch[2] || '').trim();
          }
        }

        const cleanSp = speaker ? speaker.trim() : '';
        const registry = loadCharacterRegistry();
        const cached = cleanSp ? registry[cleanSp] : null;

        // Khung ngữ cảnh xung quanh câu dẫn
        const fullContextWindow = `${leadIn} ${cleanSp} ${manner} ${verb} ${leadOut}`.toLowerCase();
        const windowTokens = fullContextWindow.split(/[\s,.;:!?…–—"“«»”]+/).filter(Boolean);

        let mPronounHit = false;
        let fPronounHit = false;
        for (const p of MALE_PRONOUNS) {
          if (p.includes(' ') ? fullContextWindow.includes(p) : windowTokens.includes(p)) {
            mPronounHit = true; break;
          }
        }
        for (const p of FEMALE_PRONOUNS) {
          if (p.includes(' ') ? fullContextWindow.includes(p) : windowTokens.includes(p)) {
            fPronounHit = true; break;
          }
        }

        let gender = 'neutral';
        let confidence = 0.5;
        let bestSource = '';

        // KIỂM TRA SỔ TAY NHÂN VẬT NẾU ĐÃ CÓ (Confidence >= 0.85)
        // Nếu câu hiện tại có đại từ chắc chắn 100% (hắn vs nàng), sẽ tự động nâng cấp nếu trước đó bị đoán lệch
        if (cached && cached.confidence >= 0.85 && !(mPronounHit && cached.gender === 'female') && !(fPronounHit && cached.gender === 'male')) {
          gender = cached.gender;
          confidence = cached.confidence;
          bestSource = cached.source ? `${cached.source} (Sổ tay)` : 'Sổ tay Nhân vật';
        } else {
          // HỆ THỐNG TÍNH ĐIỂM TRỌNG SỐ ĐA TẦNG: S = w1·P(Đại từ) + w2·P(Danh xưng) + w3·P(Tên)
          let mScore = 0;
          let fScore = 0;

          // TẦNG 1: ĐẠI TỪ NHÂN XƯNG (w1 = 1.0, Trọng số tối cao) - Hắn/Chàng vs Nàng/Ả/Thị
          if (mPronounHit && !fPronounHit) {
            mScore += 10.0;
            bestSource = 'Đại từ (hắn/y...)';
          } else if (fPronounHit && !mPronounHit) {
            fScore += 10.0;
            bestSource = 'Đại từ (nàng/ả...)';
          }

          // TẦNG 2: DANH XƯNG & HẬU TỐ (w2 = 0.85) - Sư huynh/Lão ma vs Sư tỷ/Tiên tử
          let mTitleHit = false;
          let fTitleHit = false;
          for (const t of MALE_TITLES) {
            if (t.includes(' ') ? fullContextWindow.includes(t) : windowTokens.includes(t)) {
              mTitleHit = true; break;
            }
          }
          for (const t of FEMALE_TITLES) {
            if (t.includes(' ') ? fullContextWindow.includes(t) : windowTokens.includes(t)) {
              fTitleHit = true; break;
            }
          }
          if (mTitleHit && !fTitleHit) {
            mScore += 6.0;
            if (!bestSource) bestSource = 'Danh xưng (sư huynh/công tử...)';
          } else if (fTitleHit && !mTitleHit) {
            fScore += 6.0;
            if (!bestSource) bestSource = 'Danh xưng (sư tỷ/tiên tử...)';
          }

          // TẦNG 3: TỪ ĐIỂN ÂM HÁN VIỆT TRONG TÊN (w3 = 0.65)
          if (cleanSp) {
            const spTokens = cleanSp.toLowerCase().split(/\s+/);
            // Quy tắc vàng: Bỏ qua Họ (spTokens[0]), chỉ xét Tên chính (spTokens[-1]) và Tên đệm (spTokens[-2])
            const givenName = spTokens[spTokens.length - 1];
            const middleName = spTokens.length > 2 ? spTokens[spTokens.length - 2] : '';

            if (FEMALE_NAME_KEYWORDS.includes(givenName)) {
              fScore += 5.0;
              if (!bestSource) bestSource = `Tên Hán Việt (${givenName})`;
            }
            if (middleName && FEMALE_NAME_KEYWORDS.includes(middleName)) {
              fScore += 2.0;
              if (!bestSource) bestSource = `Tên đệm (${middleName})`;
            }

            if (MALE_NAME_KEYWORDS.includes(givenName)) {
              mScore += 5.0;
              if (!bestSource) bestSource = `Tên Hán Việt (${givenName})`;
            }
            if (middleName && MALE_NAME_KEYWORDS.includes(middleName)) {
              mScore += 2.0;
              if (!bestSource) bestSource = `Tên đệm (${middleName})`;
            }
          }

          // TẦNG 4: NỘI DUNG THOẠI (XƯNG HÔ)
          const lowerDia = dialogueContent.toLowerCase();
          const firstWords = lowerDia.split(/\s+/).slice(0, 10).join(' ');
          const femaleSelf = ['tiểu nữ', 'thiếp', 'thiếp thân', 'nô gia', 'nô tỳ', 'bản cung', 'tiểu muội', 'bần ni', 'lão thân', 'muội muội', 'muội', 'nhi thần', 'bản cô nương'];
          const maleSelf = ['tại hạ', 'lão phu', 'bản tọa', 'bổn tọa', 'bần đạo', 'lão nạp', 'bản công tử', 'tiểu sinh', 'mỗ', 'vi sư', 'mạt tướng', 'huynh đệ', 'bản vương', 'bổn vương', 'trẫm', 'bản tôn', 'bổn tôn', 'tiểu tử', 'vi huynh', 'lão hủ'];
          const femaleToMale = ['sư huynh', 'công tử', 'chàng', 'đại ca', 'phu quân', 'tướng công', 'huynh', 'phụ thân', 'lão gia', 'vương gia', 'hoàng thượng', 'biểu ca'];
          const maleToFemale = ['nương tử', 'tiểu thư', 'cô nương', 'tiểu nha đầu', 'sư muội', 'nàng', 'ái phi', 'tiên tử', 'thánh nữ', 'muội muội', 'mẫu thân', 'nương'];

          if (femaleSelf.some(w => firstWords.includes(w)) || femaleToMale.some(w => firstWords.includes(w))) {
            fScore += 3.0;
            if (!bestSource) bestSource = 'Xưng hô trong thoại';
          } else if (maleSelf.some(w => firstWords.includes(w)) || maleToFemale.some(w => firstWords.includes(w))) {
            mScore += 3.0;
            if (!bestSource) bestSource = 'Xưng hô trong thoại';
          }

          // QUYẾT ĐỊNH GIỚI TÍNH & ĐỘ TIN CẬY
          if (fScore > mScore) {
            gender = 'female';
            confidence = fScore >= 10.0 ? 1.0 : (fScore >= 6.0 ? 0.95 : (fScore >= 4.0 ? 0.85 : 0.70));
          } else if (mScore > fScore) {
            gender = 'male';
            confidence = mScore >= 10.0 ? 1.0 : (mScore >= 6.0 ? 0.95 : (mScore >= 4.0 ? 0.85 : 0.70));
          } else {
            // TẦNG 5: FALLBACK LUÂN PHIÊN (TURN-TAKING)
            gender = (lastDialogueGender === 'male') ? 'female' : 'male';
            confidence = 0.50;
            bestSource = 'Luân phiên (Turn-taking)';
          }

          // LƯU VÀO SỔ TAY NHÂN VẬT VỚI CONFIDENCE UPGRADE
          if (cleanSp && confidence >= 0.70) {
            saveCharacterToRegistry(cleanSp, gender, confidence, bestSource);
          }
        }

        lastDialogueGender = gender;

        // XÁC ĐỊNH BIỂU CẢM & NGỮ ĐIỆU (EMOTIONAL TONE MODULATION)
        let emotion = 'normal';
        let speedFactor = 1.0;
        let pitchFactor = 1.0;

        const combinedManner = `${manner} ${verb} ${leadOut.slice(0, 80)}`.toLowerCase();
        if (COLD_KEYWORDS.some(k => combinedManner.includes(k)) || /lạnh lùng|hờ hững|hừ/i.test(combinedManner)) {
          emotion = 'cold';
          speedFactor = 1.05;
          pitchFactor = 0.94;
        } else if (ANGRY_KEYWORDS.some(k => combinedManner.includes(k)) || /quát|gầm|thét|tức giận/i.test(combinedManner)) {
          emotion = 'angry';
          speedFactor = 1.08;
          pitchFactor = 1.06;
        } else if (TENDER_KEYWORDS.some(k => combinedManner.includes(k)) || /dịu dàng|ngọt ngào|khẽ/i.test(combinedManner)) {
          emotion = 'tender';
          speedFactor = 0.96;
          pitchFactor = 1.04;
        } else if (WHISPER_KEYWORDS.some(k => combinedManner.includes(k)) || /thì thầm|nhỏ giọng/i.test(combinedManner)) {
          emotion = 'whisper';
          speedFactor = 0.92;
          pitchFactor = 0.92;
        }

        return {
          isDialogue: true,
          speaker: cleanSp,
          gender: gender,
          confidence: confidence,
          source: bestSource,
          emotion: emotion,
          manner: manner,
          speedFactor: speedFactor,
          pitchFactor: pitchFactor
        };
      } catch (err) {
        console.warn('[Dialogue Attribution Exception]', err);
        return { isDialogue: false, gender: 'narration', emotion: 'normal', speedFactor: 1.0, pitchFactor: 1.0, speaker: '' };
      }
    }"""

start_idx = html.find(code_anchor_start)
end_idx = html.find(code_anchor_end)
if start_idx != -1 and end_idx != -1:
    end_pos = end_idx + len(code_anchor_end)
    html = html[:start_idx] + new_engine_code + "\n\n" + code_anchor_end + html[end_pos:]
    print("3. Replaced Character Attribution & Registry Engine successfully!")
else:
    print("ERROR: code_anchors not found! start_idx:", start_idx, "end_idx:", end_idx)
    exit(1)

# 4. Bump version to v1.6.38 / build 198
html = html.replace('v1.6.37</span>', 'v1.6.38</span>')
html = html.replace('v1.6.37</b>', 'v1.6.38</b>')
html = html.replace("const CURRENT_APP_VERSION = 'v1.6.37';", "const CURRENT_APP_VERSION = 'v1.6.38';")
html = html.replace("const CURRENT_APP_BUILD = 197;", "const CURRENT_APP_BUILD = 198;")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)

print("HTML updated and saved successfully!")

# 5. Update server.py
server_path = r'D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\server.py'
with open(server_path, 'r', encoding='utf-8') as f:
    s_content = f.read()

s_content = s_content.replace('"version": "v1.6.37"', '"version": "v1.6.38"')
s_content = s_content.replace('"version_code": 197', '"version_code": 198')
s_content = s_content.replace(
    '"changelog": [',
    '"changelog": [\n                "🎭 Nâng cấp Kịch truyền thanh AI Đa tầng & Sổ tay Nhân vật: Tự động phân vai theo trọng số (Đại từ w1=1.0, Danh xưng w2=0.85, Âm Hán Việt w3=0.65; Tránh bẫy tên Bạch Tiểu Thuần; Bảng quản lý & đổi giọng thủ công)",'
)

with open(server_path, 'r', encoding='utf-8') as f:
    f.write(s_content)

print("server.py updated and saved successfully!")
