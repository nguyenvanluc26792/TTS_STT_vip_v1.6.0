import sys

path = r'D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\templates\index.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update CSS
old_css_anchor = '/* Ẩn Bottom Dock của trang chủ khi đang ở màn hình Reader */'
new_css = '''/* Ẩn Bottom Dock và Floating Edge Widget khi đang ở Reader */
    body.in-reader-tab #nrBottomDock,
    body:has(#nrViewReader.active) #nrBottomDock,
    .nr-view-reader.active ~ #nrBottomDock,
    #nrViewReader.active + #nrBottomDock,
    body.in-reader-tab #floatingEdgeMediaWidget,
    body:has(#nrViewReader.active) #floatingEdgeMediaWidget,
    .nr-view-reader.active ~ #floatingEdgeMediaWidget {
      display: none !important;
    }

    /* Chế độ Sáng (Light Mode) khi bấm nút Sáng/Tối */
    body.honor-light-mode .nr-view-reader.honor-reader-mode,
    body.honor-light-mode .honor-scroll-area,
    body.honor-light-mode .honor-container,
    body.honor-light-mode .honor-content {
      background: #f6f3eb !important;
      color: #2c2c2c !important;
    }
    body.honor-light-mode .honor-content .paragraph-item {
      color: #2c2c2c !important;
    }
    body.honor-light-mode .honor-content .sentence-item.sentence-active {
      color: #000000 !important;
      background-color: rgba(0, 0, 0, 0.08) !important;
    }
    body.honor-light-mode .honor-status-title,
    body.honor-light-mode .honor-status-subtitle,
    body.honor-light-mode .honor-status-page,
    body.honor-light-mode .honor-status-right {
      color: #777777 !important;
    }'''

if old_css_anchor in content:
    idx1 = content.find(old_css_anchor)
    idx2 = content.find('/* Header & Footer trạng thái cố định trên trang sách */', idx1)
    if idx1 != -1 and idx2 != -1:
        content = content[:idx1] + new_css + '\n\n    ' + content[idx2:]
        print('CSS updated successfully!')
    else:
        print('CSS anchor range not matched!')
else:
    print('old_css_anchor not found!')

# 2. Update FAB listen initial class to hidden
old_fab = '<button id="honorFabListen" class="honor-fab-listen"'
new_fab = '<button id="honorFabListen" class="honor-fab-listen hidden"'
if old_fab in content:
    content = content.replace(old_fab, new_fab)
    print('FAB class set to hidden!')

# 3. Update switchNrTab('reader')
old_tab_reader = '''      if (tabName === 'reader') {
        if (readerView) readerView.classList.add('active');
      } else {
        if (readerView) readerView.classList.remove('active');
      }'''

new_tab_reader = '''      if (tabName === 'reader') {
        if (readerView) readerView.classList.add('active');
        document.body.classList.add('in-reader-tab');
        if (typeof updateHonorTitles === 'function') updateHonorTitles();
        if (typeof updateHonorPageCounter === 'function') setTimeout(updateHonorPageCounter, 60);
        if (typeof updateHonorClockAndBattery === 'function') updateHonorClockAndBattery();
      } else {
        if (readerView) readerView.classList.remove('active');
        document.body.classList.remove('in-reader-tab');
      }'''

if old_tab_reader in content:
    content = content.replace(old_tab_reader, new_tab_reader)
    print('switchNrTab updated successfully!')
else:
    print('old_tab_reader not found!')

# 4. Update loadChapter title & page sync
old_load_ch = '''      if (window.isHonorApp && !document.body.classList.contains('zen-mode')) {
        setTimeout(() => {
          window.enterZenMode();
        }, 300);
      }

      if (isPlaying) {
        playParagraph(currentParagraphIndex);
      }'''

new_load_ch = '''      if (window.isHonorApp && !document.body.classList.contains('zen-mode')) {
        setTimeout(() => {
          window.enterZenMode();
        }, 300);
      }

      if (typeof updateHonorTitles === 'function') updateHonorTitles();
      if (typeof updateHonorPageCounter === 'function') setTimeout(updateHonorPageCounter, 60);

      if (isPlaying) {
        playParagraph(currentParagraphIndex);
      }'''

if old_load_ch in content:
    content = content.replace(old_load_ch, new_load_ch)
    print('loadChapter updated successfully!')
else:
    print('old_load_ch not found!')

# 5. Update updatePlayBtn to sync honor media pill
old_play_btn = 'syncMediaSensorState(isPlaying);'
new_play_btn = '''syncMediaSensorState(isPlaying);
      if (typeof updateHonorMediaPillState === 'function') updateHonorMediaPillState();'''
if old_play_btn in content:
    content = content.replace(old_play_btn, new_play_btn, 1)
    print('updatePlayBtn updated successfully!')
else:
    print('old_play_btn not found!')

# 6. Update touchend tap zone
old_touch = '''        // 2. Chạm (Tap) 3 vùng chuẩn Honor Reader gốc (33% Trái = lùi, 33% Phải = tới, 34% Giữa = Menu/Zen mode)
        if (absX < 14 && absY < 14 && duration < 350) {
          if (isPlaying) return; // Khi media bật thì không nhận tap lật trang vô tình
          const w = window.innerWidth;
          const clickX = touch.clientX;
          if (clickX < w * 0.33) {
            window.safeTurnPrevPage();
          } else if (clickX > w * 0.67) {
            window.safeTurnNextPage();
          } else {
            // Vùng 34% trung tâm: Chuyển đổi Menu / Chế độ đọc tràn viền Zen Mode như Honor Reader onMenuAreaClick
            if (document.body.classList.contains('zen-mode')) {
              window.exitZenMode();
            } else {
              window.enterZenMode();
            }
          }
        }'''

new_touch = '''        // 2. Chạm (Tap) 3 vùng chuẩn Honor Reader gốc (25% Trái = lùi, 25% Phải = tới, 50% Giữa = Menu/Toolbar)
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

if old_touch in content:
    content = content.replace(old_touch, new_touch)
    print('touchend handler updated successfully!')
else:
    print('old_touch not found!')

# 7. Add Honor Reader controller functions before </script>
honor_controller_js = '''
    // =====================================================================
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

      if (fabListen) {
        if (honorOverlayVisible) {
          if (!honorMediaPillVisible) {
            fabListen.classList.remove('hidden');
          }
          fabListen.classList.add('with-toolbar');
        } else {
          if (!window.isPlaying && !honorMediaPillVisible) {
            fabListen.classList.add('hidden');
          }
          fabListen.classList.remove('with-toolbar');
        }
      }

      if (mediaPill) {
        mediaPill.classList.toggle('with-toolbar', honorOverlayVisible);
      }
    }

    function openHonorMediaPill() {
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
      updateHonorMediaPillState();
    }

    function dismissHonorMediaPill() {
      const mediaPill = document.getElementById('honorFloatingMediaPill');
      const fabListen = document.getElementById('honorFabListen');
      honorMediaPillVisible = false;
      if (mediaPill) {
        mediaPill.classList.remove('open');
      }
      if (fabListen) {
        if (honorOverlayVisible || window.isPlaying) {
          fabListen.classList.remove('hidden');
        }
      }
    }

    function updateHonorMediaPillState() {
      const mediaPill = document.getElementById('honorFloatingMediaPill');
      const playIcon = document.getElementById('honorPillPlayIcon');
      const pauseIcon = document.getElementById('honorPillPauseIcon');
      const coverImg = document.getElementById('honorPillCoverImg');
      const coverPlaceholder = document.getElementById('honorPillCoverPlaceholder');

      if (mediaPill) {
        mediaPill.classList.toggle('playing', !!window.isPlaying);
      }
      if (playIcon) playIcon.style.display = window.isPlaying ? 'none' : 'block';
      if (pauseIcon) pauseIcon.style.display = window.isPlaying ? 'block' : 'none';

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
    updateHonorClockAndBattery();
'''

script_end_tag = '  </script>'
if script_end_tag in content:
    content = content.replace(script_end_tag, honor_controller_js + '\n' + script_end_tag, 1)
    print('Honor Reader Controller JS added successfully!')
else:
    print('script_end_tag not found!')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Finished updating index.html!')
