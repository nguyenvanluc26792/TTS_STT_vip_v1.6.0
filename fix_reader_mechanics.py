import re

path = r'D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\templates\index.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove sentence click listener that automatically plays audio
old_sentence_click = '''          span.addEventListener('click', (e) => {
            if (isLongPress || (Date.now() - lastContextMenuOpenTime < 500) || (Date.now() - lastDismissTime < 300)) return;
            const curSel = window.getSelection();
            if (curSel && !curSel.isCollapsed && curSel.toString().trim()) return;
            e.stopPropagation();

            currentSentenceIndex = sIdx;
            currentParagraphIndex = sIdx;
            highlightActiveSentence(sIdx, true);
            saveProgress();

            currentPlaybackSessionId++;
            if (audio) {
              audio.pause();
              audio.onended = null;
            }
            if (typeof paragraphAudioCache !== 'undefined') {
              paragraphAudioCache.clear();
            }
            if (typeof paragraphPrefetchInFlight !== 'undefined') {
              paragraphPrefetchInFlight.clear();
            }
            isPlaying = true;
            updatePlayBtn();
            playParagraph(sIdx);
          });'''

if old_sentence_click in content:
    content = content.replace(old_sentence_click, '// Bấm vào câu trong sách không tự ý phát giọng (chuẩn app gốc)')
    print('1. Sentence click auto-play removed successfully!')
else:
    print('1. Warning: old_sentence_click not found exactly, attempting regex search...')
    pattern = r"span\.addEventListener\('click',\s*\(e\)\s*=>\s*\{[\s\S]*?playParagraph\(sIdx\);\s*\}\);"
    if re.search(pattern, content):
        content = re.sub(pattern, '// Bấm vào câu trong sách không tự ý phát giọng (chuẩn app gốc)', content, count=1)
        print('1. Sentence click auto-play removed via regex!')
    else:
        print('1. Error: sentence click listener not found!')

# 2. Update HTML of honorFloatingMediaPill & honorFabListen
old_pill_html = '''      <!-- NÚT TRÒN NỔI "NGHE" MÀU XANH DƯƠNG GÓC PHẢI DƯỚI (CHUẨN SCREENSHOT 3) -->
      <button id="honorFabListen" class="honor-fab-listen hidden" onclick="openHonorMediaPill()" title="Bật điều khiển đọc giọng (TTS)">
        <span>Nghe</span>
      </button>

      <!-- POP-UP MEDIA DẠNG VIÊN THUỐC BÊN TRÁI DƯỚI (CHUẨN SCREENSHOT 2) -->
      <div id="honorFloatingMediaPill" class="honor-media-pill">
        <div class="honor-pill-cover-disc" id="honorPillDisc" onclick="togglePlay()" title="Phát / Tạm dừng">
          <img id="honorPillCoverImg" src="" alt="" style="display:none; width:100%; height:100%; border-radius:50%; object-fit:cover;">
          <div id="honorPillCoverPlaceholder" class="honor-pill-cover-placeholder">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/></svg>
          </div>
        </div>
        <button id="honorPillPlayBtn" class="honor-pill-play-btn" onclick="togglePlay()" title="Phát / Tạm dừng">
          <svg id="honorPillPlayIcon" width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><polygon points="6 3 20 12 6 21 6 3"/></svg>
          <svg id="honorPillPauseIcon" width="22" height="22" viewBox="0 0 24 24" fill="currentColor" style="display:none;"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
        </button>
        <button class="honor-pill-close-btn" onclick="dismissHonorMediaPill()" title="Thu gọn điều khiển">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>'''

new_pill_html = '''      <!-- NÚT TRÒN NỔI "NGHE" MÀU XANH DƯƠNG GÓC PHẢI DƯỚI (CHUẨN SCREENSHOT 3) -->
      <button id="honorFabListen" class="honor-fab-listen hidden" onclick="openHonorMediaPill(event)" title="Bật điều khiển đọc giọng (TTS)">
        <span>Nghe</span>
      </button>

      <!-- POP-UP MEDIA DẠNG VIÊN THUỐC BÊN TRÁI DƯỚI (CHUẨN SCREENSHOT 2) -->
      <div id="honorFloatingMediaPill" class="honor-media-pill" onclick="event.stopPropagation()">
        <div class="honor-pill-cover-disc" id="honorPillDisc" onclick="handleHonorPillPlayToggle(event)" title="Phát / Tạm dừng">
          <img id="honorPillCoverImg" src="" alt="" style="display:none; width:100%; height:100%; border-radius:50%; object-fit:cover;">
          <div id="honorPillCoverPlaceholder" class="honor-pill-cover-placeholder">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/></svg>
          </div>
        </div>
        <button id="honorPillPlayBtn" class="honor-pill-play-btn" onclick="handleHonorPillPlayToggle(event)" title="Phát / Tạm dừng">
          <svg id="honorPillPlayIcon" width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><polygon points="6 3 20 12 6 21 6 3"/></svg>
          <svg id="honorPillPauseIcon" width="22" height="22" viewBox="0 0 24 24" fill="currentColor" style="display:none;"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
        </button>
        <button class="honor-pill-close-btn" onclick="dismissHonorMediaPill(event)" title="Thu gọn điều khiển">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>'''

if old_pill_html in content:
    content = content.replace(old_pill_html, new_pill_html)
    print('2. Media pill HTML updated with stopPropagation & event handlers!')
else:
    print('2. Warning: old_pill_html not found!')

# 3. Update desktop click handler: edge clicks have NO effect, middle clicks toggle overlay
old_desktop_click = '''      const rect = sc.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const w = rect.width;
      if (clickX < w * 0.25) {
        window.safeTurnPrevPage();
      } else if (clickX > w * 0.75) {
        window.safeTurnNextPage();
      } else {
        if (typeof toggleHonorOverlay === 'function') {
          toggleHonorOverlay();
        } else if (document.body.classList.contains('zen-mode')) {
          window.exitZenMode();
        } else {
          window.enterZenMode();
        }
      }'''

new_desktop_click = '''      const rect = sc.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const w = rect.width;
      // Chuẩn app Honor gốc: Bấm vào rìa (trái/phải) KHÔNG có tác dụng!
      // Bấm vào giữa (25% - 75%) chỉ hiện thanh công cụ và nút nghe!
      if (clickX >= w * 0.25 && clickX <= w * 0.75) {
        if (typeof toggleHonorOverlay === 'function') {
          toggleHonorOverlay();
        } else if (document.body.classList.contains('zen-mode')) {
          window.exitZenMode();
        } else {
          window.enterZenMode();
        }
      }'''

if old_desktop_click in content:
    content = content.replace(old_desktop_click, new_desktop_click)
    print('3. Desktop click listener updated!')
else:
    print('3. Warning: old_desktop_click not found!')

# 4. Update touchend handler: edge tap has NO effect, middle tap toggles overlay
old_touchend_tap = '''        // 2. Chạm (Tap) 3 vùng chuẩn Honor Reader gốc (25% Trái = lùi, 25% Phải = tới, 50% Giữa = Menu/Toolbar)
        if (absX < 14 && absY < 14 && duration < 350) {
          if (e.target && e.target.closest && e.target.closest('#honorTopToolbar, #honorBottomToolbar, #honorFabListen, #honorFloatingMediaPill, #honorFontPanel, .modal-backdrop, .modal, button, input, select, a, #chapterDrawer')) {
            return;
          }
          const w = window.innerWidth;
          const clickX = touch.clientX;
          if (clickX < w * 0.25) {
            if (!isPlaying) window.safeTurnPrevPage();
          } else if (clickX > w * 0.75) {
            if (!isPlaying) window.safeTurnNextPage();
          } else {
            // Vùng 50% trung tâm: Chuyển đổi thanh công cụ Honor Reader
            if (typeof toggleHonorOverlay === 'function') {
              toggleHonorOverlay();
            } else if (document.body.classList.contains('zen-mode')) {
              window.exitZenMode();
            } else {
              window.enterZenMode();
            }
          }
        }'''

new_touchend_tap = '''        // 2. Chạm (Tap) chuẩn Honor Reader gốc: Bấm vào rìa không có tác dụng, bấm vào giữa chỉ hiện thanh công cụ và nút nghe
        if (absX < 14 && absY < 14 && duration < 350) {
          if (e.target && e.target.closest && e.target.closest('#honorTopToolbar, #honorBottomToolbar, #honorFabListen, #honorFloatingMediaPill, #honorFontPanel, .modal-backdrop, .modal, button, input, select, a, #chapterDrawer')) {
            return;
          }
          const w = window.innerWidth;
          const clickX = touch.clientX;
          // Bấm vào giữa: Hiện thanh công cụ & nút nghe. Bấm rìa không có tác dụng!
          if (clickX >= w * 0.25 && clickX <= w * 0.75) {
            if (typeof toggleHonorOverlay === 'function') {
              toggleHonorOverlay();
            } else if (document.body.classList.contains('zen-mode')) {
              window.exitZenMode();
            } else {
              window.enterZenMode();
            }
          }
        }'''

if old_touchend_tap in content:
    content = content.replace(old_touchend_tap, new_touchend_tap)
    print('4. Touchend handler updated!')
else:
    print('4. Warning: old_touchend_tap not found!')

# 5. Replace Honor Controller JS with full synchronization & pause/play fixes
old_controller_anchor = '// =====================================================================\n    // BỘ ĐIỀU KHIỂN GIAO DIỆN VÀ TÍNH NĂNG CHUẨN HONOR READER GỐC'

new_controller_code = '''// =====================================================================
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

      // "Bấm vào giữa chỉ hiện thanh công cụ và nút nghe"
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

      // Khi bấm nút "Nghe", nếu chưa phát thì bắt đầu đọc ngay lập tức!
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

    function updateHonorMediaPillState() {
      const mediaPill = document.getElementById('honorFloatingMediaPill');
      const playIcon = document.getElementById('honorPillPlayIcon');
      const pauseIcon = document.getElementById('honorPillPauseIcon');
      const coverImg = document.getElementById('honorPillCoverImg');
      const coverPlaceholder = document.getElementById('honorPillCoverPlaceholder');

      // Đồng bộ chuẩn biến isPlaying thực tế
      const isCurrentPlaying = (typeof isPlaying !== 'undefined') ? !!isPlaying : !!window.isPlaying;
      window.isPlaying = isCurrentPlaying;

      if (mediaPill) {
        mediaPill.classList.toggle('playing', isCurrentPlaying);
      }
      if (playIcon) playIcon.style.display = isCurrentPlaying ? 'none' : 'block';
      if (pauseIcon) pauseIcon.style.display = isCurrentPlaying ? 'block' : 'none';

      if (bookData && bookData.cover && coverImg) {
        coverImg.src = bookData.cover;
        coverImg.style.display = 'block';
        if (coverPlaceholder) coverPlaceholder.style.display = 'none';
      } else if (coverPlaceholder) {
        coverPlaceholder.style.display = 'flex';
        if (coverImg) coverImg.style.display = 'none';
      }
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

if old_controller_anchor in content:
    idx_start = content.find(old_controller_anchor)
    idx_end = content.find('  </script>', idx_start)
    if idx_start != -1 and idx_end != -1:
        content = content[:idx_start] + new_controller_code + '\n' + content[idx_end:]
        print('5. Honor Controller JS updated!')
    else:
        print('5. Error finding end of controller JS!')
else:
    print('5. Error finding old_controller_anchor!')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Finished writing modified index.html!')
