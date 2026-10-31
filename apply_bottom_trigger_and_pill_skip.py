path = r'D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\templates\index.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update HTML of honorFloatingMediaPill & honorReaderBottomStatus
old_bottom_status = '<div id="honorReaderBottomStatus" class="honor-status-bottom">'
new_bottom_status = '<div id="honorReaderBottomStatus" class="honor-status-bottom" onclick="toggleHonorOverlay()" style="pointer-events: auto; cursor: pointer;" title="Chạm để mở thanh công cụ">'

if old_bottom_status in content:
    content = content.replace(old_bottom_status, new_bottom_status, 1)
    print('1. honorReaderBottomStatus updated with direct click handler!')
else:
    print('1. Warning: old_bottom_status not found!')

# Replace old pill HTML
old_pill_pattern_start = '<!-- POP-UP MEDIA DẠNG VIÊN THUỐC BÊN TRÁI DƯỚI'
old_pill_pattern_end = '<!-- THANH CÔNG CỤ DƯỚI'

new_pill_html = '''<!-- POP-UP MEDIA DẠNG VIÊN THUỐC BÊN TRÁI DƯỚI (VỚI 3 NÚT: LÙI CÂU - PHÁT/DỪNG - TIẾP CÂU) -->
      <div id="honorFloatingMediaPill" class="honor-media-pill" onclick="event.stopPropagation()">
        <!-- 1. NÚT LÙI CÂU TRƯỚC ĐÓ (Tua lùi) -->
        <button id="honorPillPrevBtn" class="honor-pill-skip-btn" onclick="handleHonorPillPrev(event)" title="Quay lại câu trước">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <polygon points="19 20 9 12 19 4 19 20"/>
            <line x1="5" y1="19" x2="5" y2="5" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"/>
          </svg>
        </button>

        <!-- 2. NÚT PHÁT / TẠM DỪNG Ở GIỮA -->
        <button id="honorPillPlayBtn" class="honor-pill-play-btn" onclick="handleHonorPillPlayToggle(event)" title="Phát / Tạm dừng">
          <svg id="honorPillPlayIcon" width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><polygon points="6 3 20 12 6 21 6 3"/></svg>
          <svg id="honorPillPauseIcon" width="22" height="22" viewBox="0 0 24 24" fill="currentColor" style="display:none;"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
        </button>

        <!-- 3. NÚT NHẢY ĐẾN CÂU SAU (Tua nhanh qua đoạn không muốn nghe) -->
        <button id="honorPillNextBtn" class="honor-pill-skip-btn" onclick="handleHonorPillNext(event)" title="Nhảy đến câu sau">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <polygon points="5 4 15 12 5 20 5 4"/>
            <line x1="19" y1="5" x2="19" y2="19" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"/>
          </svg>
        </button>

        <!-- 4. VẠCH NGĂN NHẸ & NÚT THU GỌN ✕ -->
        <div class="honor-pill-divider"></div>
        <button class="honor-pill-close-btn" onclick="dismissHonorMediaPill(event)" title="Thu gọn điều khiển">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>

      '''

idx_p1 = content.find(old_pill_pattern_start)
idx_p2 = content.find(old_pill_pattern_end, idx_p1)
if idx_p1 != -1 and idx_p2 != -1:
    content = content[:idx_p1] + new_pill_html + content[idx_p2:]
    print('2. Pop-up media HTML replaced with 3 skip/play buttons!')
else:
    print('2. Error: old pill pattern not found!')

# 2. Update CSS for honor-media-pill & skip buttons
old_css_start = '/* POP-UP MEDIA DẠNG VIÊN THUỐC BÊN TRÁI DƯỚI'
old_css_end = '/* POPUP CHỈNH CỠ CHỮ & GIÃN DÒNG */'

new_css_pill = '''/* POP-UP MEDIA DẠNG VIÊN THUỐC BÊN TRÁI DƯỚI (VỚI 3 NÚT TUA CÂU) */
    .honor-media-pill {
      position: absolute;
      left: 18px;
      bottom: 26px;
      height: 48px;
      border-radius: 9999px;
      background: rgba(30, 30, 34, 0.96);
      backdrop-filter: blur(25px);
      -webkit-backdrop-filter: blur(25px);
      border: 1px solid rgba(255, 255, 255, 0.15);
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.7);
      display: flex;
      align-items: center;
      padding: 0 8px 0 10px;
      gap: 8px;
      z-index: 1050;
      transform: translateY(20px) scale(0.9);
      opacity: 0;
      pointer-events: none;
      transition: transform 0.28s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.22s ease, bottom 0.28s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .honor-media-pill.open {
      transform: translateY(0) scale(1);
      opacity: 1;
      pointer-events: auto;
    }
    .honor-bottom-toolbar.open ~ .honor-media-pill,
    .honor-media-pill.with-toolbar {
      bottom: 120px;
    }
    .honor-pill-skip-btn {
      background: transparent;
      border: none;
      color: #a1a1aa;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      padding: 8px 6px;
      border-radius: 50%;
      transition: color 0.15s, transform 0.15s, background 0.15s;
    }
    .honor-pill-skip-btn:active {
      color: #ffffff;
      transform: scale(0.88);
      background: rgba(255, 255, 255, 0.1);
    }
    .honor-pill-play-btn {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      background: #38bdf8;
      border: none;
      color: #0f172a;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      box-shadow: 0 2px 10px rgba(56, 189, 248, 0.4);
      transition: transform 0.15s, background 0.15s;
    }
    .honor-pill-play-btn:active {
      transform: scale(0.9);
      background: #0284c7;
    }
    .honor-pill-divider {
      width: 1px;
      height: 18px;
      background: rgba(255, 255, 255, 0.15);
      margin: 0 2px;
    }
    .honor-pill-close-btn {
      background: transparent;
      border: none;
      color: #71717a;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      padding: 6px;
      border-radius: 50%;
    }
    .honor-pill-close-btn:active {
      color: #ffffff;
    }

    '''

idx_c1 = content.find(old_css_start)
idx_c2 = content.find(old_css_end, idx_c1)
if idx_c1 != -1 and idx_c2 != -1:
    content = content[:idx_c1] + new_css_pill + content[idx_c2:]
    print('3. CSS updated for new media pill with skip buttons!')
else:
    print('3. Error: old CSS range not found!')

# 4. Update desktop click listener: only bottom zone (clickY >= h * 0.72) triggers overlay
old_desktop_click_anchor = 'window.addEventListener(\'click\', (e) => {'
idx_dc = content.find(old_desktop_click_anchor)
if idx_dc != -1:
    idx_dc_end = content.find('}, true);', idx_dc)
    new_desktop_click = '''window.addEventListener('click', (e) => {
      const sc = document.getElementById('readerScrollArea');
      if (!sc || !sc.contains(e.target)) return;
      if (isPlaying || (typeof isUIOverlayActive === 'function' && isUIOverlayActive())) return;
      if (e.target.closest('button, a, input, select, textarea, .modal, .drawer, #textSelectionToolbar, #paraContextMenu, #honorTopToolbar, #honorBottomToolbar, #honorFloatingMediaPill, #honorFabListen, #honorFontPanel')) return;
      const curSel = window.getSelection();
      if (curSel && !curSel.isCollapsed && curSel.toString().trim()) return;

      const h = window.innerHeight;
      const clickY = e.clientY;

      // Nếu thanh công cụ đang mở: bấm vào khoảng trống bất kỳ để đóng lại
      if (typeof honorOverlayVisible !== 'undefined' && honorOverlayVisible) {
        if (typeof toggleHonorOverlay === 'function') {
          toggleHonorOverlay();
        }
        return;
      }

      // Theo yêu cầu: Ấn ở PHÍA DƯỚI CÙNG (khoảng 28% cạnh đáy) thì mới hiện thanh công cụ và nút nghe!
      if (clickY >= h * 0.72) {
        if (typeof toggleHonorOverlay === 'function') {
          toggleHonorOverlay();
        }
      }
    '''
    content = content[:idx_dc] + new_desktop_click + content[idx_dc_end:]
    print('4. Desktop click listener updated for bottom zone trigger!')

# 5. Update touchend: only bottom zone (clickY >= h * 0.72) triggers overlay
old_touch_tap_start = '// 2. Chạm (Tap)'
idx_tt = content.find(old_touch_tap_start)
if idx_tt != -1:
    idx_tt_end = content.find('}\n      }\n      isTouchGestureHandled = false;', idx_tt)
    new_touch_tap = '''// 2. Chạm (Tap): Hiện thanh công cụ khi ấn ở PHÍA DƯỚI CÙNG màn hình
        if (absX < 18 && absY < 18 && duration < 400) {
          if (e.target && e.target.closest && e.target.closest('#honorTopToolbar, #honorBottomToolbar, #honorFabListen, #honorFloatingMediaPill, #honorFontPanel, .modal-backdrop, .modal, button, input, select, a, #chapterDrawer')) {
            return;
          }
          const h = window.innerHeight;
          const clickY = touch.clientY;

          // Nếu thanh công cụ đang mở: chạm ở đâu cũng đóng thanh công cụ
          if (typeof honorOverlayVisible !== 'undefined' && honorOverlayVisible) {
            if (typeof toggleHonorOverlay === 'function') {
              toggleHonorOverlay();
            }
            return;
          }

          // Theo yêu cầu người dùng: Ấn ở PHÍA DƯỚI CÙNG (chỗ pop up media / footer) thì hiện thanh công cụ và nút nghe!
          if (clickY >= h * 0.72) {
            if (typeof toggleHonorOverlay === 'function') {
              toggleHonorOverlay();
            }
          }
        }
      '''
    content = content[:idx_tt] + new_touch_tap + content[idx_tt_end:]
    print('5. Touchend handler updated for bottom zone trigger!')

# 6. Update Honor Controller JS: add handleHonorPillPrev and handleHonorPillNext, clean up updateHonorMediaPillState
old_ctrl_start = '// =====================================================================\n    // BỘ ĐIỀU KHIỂN GIAO DIỆN VÀ TÍNH NĂNG CHUẨN HONOR READER GỐC'

new_ctrl_code = '''// =====================================================================
    // BỘ ĐIỀU KHIỂN GIAO DIỆN VÀ TÍNH NĂNG CHUẨN HONOR READER GỐC
    // =====================================================================
    let honorOverlayVisible = false;
    let honorMediaPillVisible = false;

    function toggleHonorOverlay() {
      const topToolbar = document.getElementById('honorTopToolbar');
      const bottomToolbar = document.getElementById('honorBottomToolbar');
      const fabListen = document.getElementById('honorFabListen');
      const fontPanel = document.getElementById('honorFontPanel');
      const mediaPill = document.getElementById('honorFloatingMediaPill');

      honorOverlayVisible = !honorOverlayVisible;

      if (topToolbar) topToolbar.classList.toggle('open', honorOverlayVisible);
      if (bottomToolbar) bottomToolbar.classList.toggle('open', honorOverlayVisible);

      if (fontPanel && !honorOverlayVisible) {
        fontPanel.classList.remove('open');
      }

      // Ấn ở phía dưới cùng: Hiện/ẩn thanh công cụ và nút nghe
      if (fabListen) {
        if (honorOverlayVisible) {
          if (!honorMediaPillVisible) {
            fabListen.classList.remove('hidden');
          }
          fabListen.classList.add('with-toolbar');
        } else {
          if (!honorMediaPillVisible) {
            fabListen.classList.add('hidden');
          }
          fabListen.classList.remove('with-toolbar');
        }
      }

      if (mediaPill) {
        mediaPill.classList.toggle('with-toolbar', honorOverlayVisible);
      }
    }

    function openHonorMediaPill(e) {
      if (e) {
        e.stopPropagation();
        e.preventDefault();
      }
      const mediaPill = document.getElementById('honorFloatingMediaPill');
      const fabListen = document.getElementById('honorFabListen');
      honorMediaPillVisible = true;
      if (mediaPill) {
        mediaPill.classList.add('open');
        mediaPill.classList.toggle('with-toolbar', honorOverlayVisible);
      }
      if (fabListen) {
        fabListen.classList.add('hidden');
      }

      // Bấm vào nút "Nghe": Nếu chưa phát thì bắt đầu đọc ngay lập tức!
      if (!isPlaying) {
        togglePlay();
      } else {
        updateHonorMediaPillState();
      }
    }

    function dismissHonorMediaPill(e) {
      if (e) {
        e.stopPropagation();
        e.preventDefault();
      }
      const mediaPill = document.getElementById('honorFloatingMediaPill');
      const fabListen = document.getElementById('honorFabListen');
      honorMediaPillVisible = false;
      if (mediaPill) {
        mediaPill.classList.remove('open');
      }
      if (fabListen && honorOverlayVisible) {
        fabListen.classList.remove('hidden');
      }
    }

    function handleHonorPillPlayToggle(e) {
      if (e) {
        e.stopPropagation();
        e.preventDefault();
      }
      togglePlay();
    }

    // Nút lùi lại câu trước đó để đọc (Tua lùi)
    function handleHonorPillPrev(e) {
      if (e) {
        e.stopPropagation();
        e.preventDefault();
      }
      currentPlaybackSessionId++;
      if (audio) {
        audio.pause();
        audio.onended = null;
      }
      if (window.HonorBridge && window.HonorBridge.stopNativeSpeak) {
        try { window.HonorBridge.stopNativeSpeak(); } catch(_) {}
      }
      if ('speechSynthesis' in window) {
        try { window.speechSynthesis.cancel(); } catch(_) {}
      }

      if (currentSentenceIndex > 0) {
        currentSentenceIndex--;
        currentParagraphIndex = currentSentenceIndex;
      }
      isPlaying = true;
      window.isPlaying = true;
      updatePlayBtn();
      updateHonorMediaPillState();
      playParagraph(currentSentenceIndex);
    }

    // Nút nhảy đến câu sau để đọc (Tua nhanh qua đoạn không muốn nghe)
    function handleHonorPillNext(e) {
      if (e) {
        e.stopPropagation();
        e.preventDefault();
      }
      currentPlaybackSessionId++;
      if (audio) {
        audio.pause();
        audio.onended = null;
      }
      if (window.HonorBridge && window.HonorBridge.stopNativeSpeak) {
        try { window.HonorBridge.stopNativeSpeak(); } catch(_) {}
      }
      if ('speechSynthesis' in window) {
        try { window.speechSynthesis.cancel(); } catch(_) {}
      }

      if (allSentences && currentSentenceIndex + 1 < allSentences.length) {
        currentSentenceIndex++;
        currentParagraphIndex = currentSentenceIndex;
      }
      isPlaying = true;
      window.isPlaying = true;
      updatePlayBtn();
      updateHonorMediaPillState();
      playParagraph(currentSentenceIndex);
    }

    function updateHonorMediaPillState() {
      const mediaPill = document.getElementById('honorFloatingMediaPill');
      const playIcon = document.getElementById('honorPillPlayIcon');
      const pauseIcon = document.getElementById('honorPillPauseIcon');

      const isCurrentPlaying = (typeof isPlaying !== 'undefined') ? !!isPlaying : !!window.isPlaying;
      window.isPlaying = isCurrentPlaying;

      if (mediaPill) {
        mediaPill.classList.toggle('playing', isCurrentPlaying);
      }
      if (playIcon) playIcon.style.display = isCurrentPlaying ? 'none' : 'block';
      if (pauseIcon) pauseIcon.style.display = isCurrentPlaying ? 'block' : 'none';
    }

    function toggleHonorFontPanel(e) {
      if (e) e.stopPropagation();
      const fontPanel = document.getElementById('honorFontPanel');
      if (fontPanel) {
        fontPanel.classList.toggle('open');
      }
    }

    function adjustHonorFontSize(delta) {
      let cur = parseInt(localStorage.getItem('honor_font_size') || '19', 10);
      cur = Math.min(32, Math.max(14, cur + delta));
      localStorage.setItem('honor_font_size', cur);
      document.documentElement.style.setProperty('--honor-font-size', cur + 'px');
      const disp = document.getElementById('honorFontSizeDisplay');
      if (disp) disp.textContent = cur;
      if (typeof updateHonorPageCounter === 'function') {
        setTimeout(updateHonorPageCounter, 60);
      }
    }

    function setHonorLineHeight(val) {
      localStorage.setItem('honor_line_height', val);
      document.documentElement.style.setProperty('--honor-line-height', val);
      ['honorLineTight', 'honorLineNormal', 'honorLineLoose'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.classList.remove('active');
      });
      if (val <= 1.6) {
        const el = document.getElementById('honorLineTight');
        if (el) el.classList.add('active');
      } else if (val <= 1.95) {
        const el = document.getElementById('honorLineNormal');
        if (el) el.classList.add('active');
      } else {
        const el = document.getElementById('honorLineLoose');
        if (el) el.classList.add('active');
      }
      if (typeof updateHonorPageCounter === 'function') {
        setTimeout(updateHonorPageCounter, 60);
      }
    }

    function toggleHonorDayNight() {
      const isNight = document.body.classList.toggle('honor-light-mode');
      const lbl = document.getElementById('honorDayNightLabel');
      if (lbl) {
        lbl.textContent = isNight ? 'Tối' : 'Sáng';
      }
      localStorage.setItem('honor_light_mode', isNight ? '1' : '0');
    }

    function toggleHonorMoreMenu(e) {
      if (e) e.stopPropagation();
      if (typeof openSettingsModal === 'function') {
        openSettingsModal();
      }
    }

    function updateHonorTitles() {
      const topBook = document.getElementById('honorTopBookTitle');
      const topChap = document.getElementById('honorTopChapterTitle');
      const activeChap = document.getElementById('honorTopActiveChap');
      const slider = document.getElementById('honorChapterSlider');

      const bTitle = (bookData && (bookData.title || (bookData.meta && bookData.meta.title))) || 'Truyện';
      if (topBook) topBook.textContent = bTitle;

      let cTitle = '';
      if (bookData && bookData.chapters && bookData.chapters[currentChapterIndex]) {
        const ch = bookData.chapters[currentChapterIndex];
        cTitle = ch.title || `Chương ${currentChapterIndex + 1}`;
      } else {
        cTitle = `Chương ${(currentChapterIndex || 0) + 1}`;
      }

      if (topChap) topChap.textContent = cTitle;
      if (activeChap) activeChap.textContent = cTitle;

      if (slider && bookData && bookData.chapters && bookData.chapters.length > 0) {
        slider.max = Math.max(0, bookData.chapters.length - 1);
        slider.value = currentChapterIndex;
      }
    }

    function onHonorChapterSliderChange(val) {
      const activeChap = document.getElementById('honorTopActiveChap');
      const idx = parseInt(val, 10);
      if (bookData && bookData.chapters && bookData.chapters[idx]) {
        const ch = bookData.chapters[idx];
        if (activeChap) activeChap.textContent = ch.title || `Chương ${idx + 1}`;
      } else if (activeChap) {
        activeChap.textContent = `Chương ${idx + 1}`;
      }
    }

    function onHonorChapterSliderCommit(val) {
      const idx = parseInt(val, 10);
      if (typeof loadChapter === 'function') {
        loadChapter(idx, 0);
      }
    }

    function updateHonorPageCounter() {
      const sc = document.getElementById('readerScrollArea');
      const pageDisp = document.getElementById('honorBottomPageNumber');
      if (!sc || !pageDisp) return;
      const turnDistance = Math.max(260, (sc.clientHeight || window.innerHeight) - 20);
      const totalPages = Math.max(1, Math.ceil((sc.scrollHeight - 20) / turnDistance));
      const currentPage = Math.min(totalPages, Math.max(1, Math.round(sc.scrollTop / turnDistance) + 1));
      pageDisp.textContent = `${currentPage} / ${totalPages}`;
    }

    function updateHonorClockAndBattery() {
      const clockEl = document.getElementById('honorClockTime');
      if (clockEl) {
        const now = new Date();
        const hh = String(now.getHours()).padStart(2, '0');
        const mm = String(now.getMinutes()).padStart(2, '0');
        clockEl.textContent = `${hh}:${mm}`;
      }
      const battLevelEl = document.getElementById('honorBatteryLevel');
      if (battLevelEl && navigator.getBattery) {
        navigator.getBattery().then(battery => {
          battLevelEl.style.width = Math.round(battery.level * 100) + '%';
        }).catch(() => {});
      }
    }

    // Chặn touch/click xuyên thấu cho các thanh điều khiển Honor Reader
    ['honorFabListen', 'honorFloatingMediaPill', 'honorTopToolbar', 'honorBottomToolbar', 'honorFontPanel'].forEach(id => {
      const el = document.getElementById(id);
      if (el) {
        ['touchstart', 'touchmove', 'touchend'].forEach(evt => {
          el.addEventListener(evt, (e) => e.stopPropagation(), { passive: true });
        });
      }
    });

    // Khởi tạo các thông số đã lưu của Honor Reader
    try {
      const savedHonorSize = localStorage.getItem('honor_font_size');
      if (savedHonorSize) {
        document.documentElement.style.setProperty('--honor-font-size', savedHonorSize + 'px');
        const disp = document.getElementById('honorFontSizeDisplay');
        if (disp) disp.textContent = savedHonorSize;
      }
      const savedHonorLine = localStorage.getItem('honor_line_height');
      if (savedHonorLine) {
        setHonorLineHeight(parseFloat(savedHonorLine));
      }
      if (localStorage.getItem('honor_light_mode') === '1') {
        toggleHonorDayNight();
      }
    } catch(e){}

    setInterval(updateHonorClockAndBattery, 20000);
    updateHonorClockAndBattery();'''

idx_ctrl1 = content.find(old_ctrl_start)
idx_ctrl2 = content.find('  </script>', idx_ctrl1)
if idx_ctrl1 != -1 and idx_ctrl2 != -1:
    content = content[:idx_ctrl1] + new_ctrl_code + '\n' + content[idx_ctrl2:]
    print('6. Honor Controller JS updated!')
else:
    print('6. Error: old_ctrl_start not found!')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Finished writing modified index.html!')
