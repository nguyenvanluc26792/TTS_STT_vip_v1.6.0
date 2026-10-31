path = r'D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\templates\index.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix isUIOverlayActive override at line 6062
old_overlay_override = '''        window.isUIOverlayActive = function() {
          const baseActive = origIsOverlay();
          const finalActive = (nrCurrentTab !== 'reader') ? true : baseActive;
          if (window.HonorBridge && typeof window.HonorBridge.setUiOverlayActive === 'function') {
            try { window.HonorBridge.setUiOverlayActive(finalActive); } catch (e) {}
          }
          return finalActive;
        };'''

new_overlay_override = '''        window.isUIOverlayActive = function() {
          const readerView = document.getElementById('nrViewReader');
          if (readerView && readerView.classList.contains('active')) {
            nrCurrentTab = 'reader';
          }
          const baseActive = origIsOverlay();
          const finalActive = (nrCurrentTab !== 'reader') ? true : baseActive;
          if (window.HonorBridge && typeof window.HonorBridge.setUiOverlayActive === 'function') {
            try { window.HonorBridge.setUiOverlayActive(finalActive); } catch (e) {}
          }
          return finalActive;
        };'''

if old_overlay_override in content:
    content = content.replace(old_overlay_override, new_overlay_override, 1)
    print('1. isUIOverlayActive override updated!')
else:
    print('1. Warning: old_overlay_override not found!')

# 2. Fix desktop click listener (lines 10228-10256)
old_desktop_click_pattern = '''    // Hỗ trợ Click chuột: Chỉ ấn ở PHÍA DƯỚI CÙNG của màn hình mới hiện thanh công cụ
    document.addEventListener('click', function(e) {
      const sc = document.getElementById('readerScrollArea');
      if (!sc || !sc.contains(e.target)) return;
      if (isPlaying || (typeof isUIOverlayActive === 'function' && isUIOverlayActive())) return;
      if (e.target.closest('button, a, input, select, textarea, .modal, .drawer, #textSelectionToolbar, #paraContextMenu, #honorTopToolbar, #honorBottomToolbar, #honorFloatingMediaPill, #honorFabListen, #honorFontPanel, .modal-backdrop')) return;
      const curSel = window.getSelection();
      if (curSel && !curSel.isCollapsed && curSel.toString().trim()) return;

      const rect = sc.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const clickY = e.clientY - rect.top;
      const w = rect.width;
      const h = rect.height;

      // Nếu đang mở thanh công cụ, bấm vào màn hình đọc sẽ đóng lại
      if (typeof honorOverlayVisible !== 'undefined' && honorOverlayVisible) {
        toggleHonorOverlay();
        return;
      }

      // Đổi thành: Chỉ khi ấn ở PHÍA DƯỚI CÙNG của màn hình (khoảng 22% cạnh đáy) thì mới hiện thanh công cụ!
      if (clickY >= h * 0.78 && clickX >= w * 0.15 && clickX <= w * 0.85) {
        if (typeof toggleHonorOverlay === 'function') {
          toggleHonorOverlay();
        }
      }
    }, true);'''

new_desktop_click = '''    // Hỗ trợ Click chuột: Ấn ở PHÍA DƯỚI CÙNG của màn hình mới hiện thanh công cụ
    document.addEventListener('click', function(e) {
      const readerView = document.getElementById('nrViewReader');
      if (!readerView || !readerView.classList.contains('active')) return;
      if (e.target.closest('button, a, input, select, textarea, .modal, .drawer, #textSelectionToolbar, #paraContextMenu, #honorTopToolbar, #honorBottomToolbar, #honorFloatingMediaPill, #honorFabListen, #honorFontPanel, .modal-backdrop')) return;
      
      const curSel = window.getSelection();
      if (curSel && !curSel.isCollapsed && curSel.toString().trim()) return;

      const h = window.innerHeight;
      const clickY = e.clientY;

      // Nếu đang mở thanh công cụ, bấm vào khoảng trống bất kỳ sẽ đóng lại
      if (typeof honorOverlayVisible !== 'undefined' && honorOverlayVisible) {
        if (typeof toggleHonorOverlay === 'function') {
          toggleHonorOverlay();
        }
        return;
      }

      // Bấm ở PHÍA DƯỚI CÙNG (khoảng 30% cạnh đáy, chỗ pop up media / footer) thì hiện thanh công cụ và nút nghe!
      if (clickY >= h * 0.70) {
        if (typeof toggleHonorOverlay === 'function') {
          toggleHonorOverlay();
        }
      }
    }, true);'''

if old_desktop_click_pattern in content:
    content = content.replace(old_desktop_click_pattern, new_desktop_click, 1)
    print('2. Desktop click listener replaced with robust reader check!')
else:
    print('2. Warning: old_desktop_click_pattern not found, attempting loose match...')
    idx_m = content.find('// Hỗ trợ Click chuột: Chỉ ấn ở PHÍA DƯỚI CÙNG')
    if idx_m != -1:
        idx_m_end = content.find('}, true);', idx_m) + 9
        content = content[:idx_m] + new_desktop_click + content[idx_m_end:]
        print('2. Desktop click listener replaced via loose match!')

# 3. Fix touchend listener: don't let false isUIOverlayActive block reader bottom tap
old_touchend_start = "window.addEventListener('touchend', function(e) {"
idx_te = content.find(old_touchend_start)
if idx_te != -1:
    idx_te_end = content.find("window.addEventListener('touchcancel'", idx_te)
    new_touchend = '''window.addEventListener('touchend', function(e) {
      const readerView = document.getElementById('nrViewReader');
      const inReader = readerView && readerView.classList.contains('active');

      if (isTouchGestureHandled || !bookData || isChapterTransitioning) {
        isTouchGestureHandled = false;
        isTouchStartedInTopSafeZone = false;
        return;
      }

      // Kiểm tra modal đang mở thực tế
      const modalOpen = document.querySelector('.modal-overlay.open, .modal.open, .library-modal.open, .drawer.open');
      if (modalOpen) {
        isTouchGestureHandled = false;
        return;
      }

      if (e.changedTouches && e.changedTouches.length === 1) {
        const touch = e.changedTouches[0];

        const target = touch.target || e.target;
        if (target && target.closest && target.closest('button, a, input, select, textarea, .modal, .modal-overlay, .library-modal, .drawer, #mobileMenuDropdown, #mobileMenuBackdrop, #floatingEdgeMediaWidget, .audio-player-bar, .popover, .text-selection-toolbar, #textSelectionToolbar, .para-context-menu, #paraContextMenu, #honorTopToolbar, #honorBottomToolbar, #honorFloatingMediaPill, #honorFabListen, #honorFontPanel')) {
          isTouchGestureHandled = false;
          isTouchStartedInTopSafeZone = false;
          return;
        }

        const diffX = touch.clientX - touchGestureStartX;
        const diffY = touch.clientY - touchGestureStartY;
        const absX = Math.abs(diffX);
        const absY = Math.abs(diffY);
        const duration = Date.now() - touchGestureStartTime;

        // 1. Vuốt nhanh nhả tay (Fling gesture ngang dứt khoát để lật trang 3D)
        if (duration < 750 && absX > 30 && absX > absY * 1.5) {
          if (isPlaying) return;
          const curSel = window.getSelection();
          if (curSel && !curSel.isCollapsed && curSel.toString().trim()) {
            try { curSel.removeAllRanges(); } catch(e){}
          }
          isTouchGestureHandled = true;
          if (diffX < 0) {
            window.safeTurnNextPage();
          } else {
            window.safeTurnPrevPage();
          }
          return;
        }

        // 2. Chạm (Tap): Hiện thanh công cụ khi ấn ở PHÍA DƯỚI CÙNG màn hình
        if (absX < 20 && absY < 20 && duration < 450) {
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
          if (clickY >= h * 0.70) {
            if (typeof toggleHonorOverlay === 'function') {
              toggleHonorOverlay();
            }
          }
        }
      }
      isTouchGestureHandled = false;
      isTouchStartedInTopSafeZone = false;
    }, { passive: true });\n\n    '''
    content = content[:idx_te] + new_touchend + content[idx_te_end:]
    print('3. Touchend listener replaced cleanly!')

# 4. In loadChapter, ensure nrCurrentTab = 'reader'
old_load_ch_entry = '''      currentChapterIndex = idx;
      currentParagraphIndex = targetParagraph;
      currentSentenceIndex = targetParagraph;'''

new_load_ch_entry = '''      nrCurrentTab = 'reader';
      const rv = document.getElementById('nrViewReader');
      if (rv) rv.classList.add('active');
      document.body.classList.add('in-reader-tab');
      currentChapterIndex = idx;
      currentParagraphIndex = targetParagraph;
      currentSentenceIndex = targetParagraph;'''

if old_load_ch_entry in content:
    content = content.replace(old_load_ch_entry, new_load_ch_entry, 1)
    print('4. loadChapter updated to ensure reader tab active!')
else:
    print('4. Warning: old_load_ch_entry not found!')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Finished updating index.html!')
