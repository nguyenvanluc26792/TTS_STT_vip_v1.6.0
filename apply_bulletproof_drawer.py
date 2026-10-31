import re

def apply_fixes():
    target_path = r"D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\templates\index.html"
    with open(target_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update CSS for .drawer-item, .drawer-item-btn, .drawer-item-title, .drawer-reading-badge
    old_css_drawer = """.chapter-drawer {
      position: fixed;
      top: 0;
      left: 0;
      width: 360px;
      max-width: 85vw;
      height: 100vh;
      background: var(--card-bg, #ffffff);
      color: var(--text-color, #222222);
      box-shadow: 4px 0 25px rgba(0,0,0,0.3);
      z-index: 2001 !important;
      display: flex;
      flex-direction: column;
      transform: translateX(-100%);
      transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .chapter-drawer.open {
      transform: translateX(0);
      pointer-events: auto !important;
    }

    .drawer-header {
      padding: 16px 20px;
      border-bottom: 1px solid var(--border-color);
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-weight: 600;
      font-size: 1.1rem;
    }
    .drawer-search {
      padding: 10px 16px;
      border-bottom: 1px solid var(--border-color);
    }
    .drawer-search input {
      width: 100%;
      padding: 8px 12px;
      border-radius: 8px;
      border: 1px solid var(--border-color);
      background: var(--bg-color);
      color: var(--text-color);
      font-size: 0.9rem;
    }
    .drawer-list {
      flex: 1;
      overflow-y: auto;
      list-style: none;
    }
    .drawer-item {
      padding: 14px 20px;
      font-size: 0.94rem;
      cursor: pointer;
      border-bottom: 1px solid var(--border-color);
      display: flex;
      justify-content: space-between;
      align-items: center;
      transition: background 0.15s;
      color: var(--text-color, #222222);
      -webkit-tap-highlight-color: transparent;
      user-select: none;
      -webkit-user-select: none;
    }
    .drawer-item:hover { background-color: var(--highlight); }
    .drawer-item.active {
      background-color: var(--highlight);
      color: var(--primary);
      font-weight: 700;
      border-left: 4px solid var(--primary);
    }"""

    new_css_drawer = """.chapter-drawer {
      position: fixed;
      top: 0;
      left: 0;
      width: 360px;
      max-width: 85vw;
      height: 100vh;
      background: var(--card-bg, #ffffff);
      color: var(--text-color, #222222);
      box-shadow: 4px 0 25px rgba(0,0,0,0.3);
      z-index: 2001 !important;
      display: flex;
      flex-direction: column;
      transform: translateX(-100%);
      transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
      pointer-events: none;
    }
    .chapter-drawer.open {
      transform: translateX(0);
      pointer-events: auto !important;
    }

    .drawer-header {
      padding: 16px 20px;
      border-bottom: 1px solid var(--border-color);
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-weight: 600;
      font-size: 1.1rem;
    }
    .drawer-search {
      padding: 10px 16px;
      border-bottom: 1px solid var(--border-color);
    }
    .drawer-search input {
      width: 100%;
      padding: 8px 12px;
      border-radius: 8px;
      border: 1px solid var(--border-color);
      background: var(--bg-color);
      color: var(--text-color);
      font-size: 0.9rem;
    }
    .drawer-list {
      flex: 1;
      overflow-y: auto;
      list-style: none;
      padding: 0;
      margin: 0;
      -webkit-overflow-scrolling: touch;
    }
    .drawer-item {
      list-style: none;
      padding: 0;
      margin: 0;
      border-bottom: 1px solid var(--border-color);
    }
    .drawer-item-btn {
      display: flex;
      width: 100%;
      padding: 14px 20px;
      background: transparent;
      border: none;
      outline: none;
      align-items: center;
      justify-content: space-between;
      text-align: left;
      cursor: pointer;
      color: var(--text-color, #222222);
      font-size: 0.94rem;
      -webkit-tap-highlight-color: rgba(79, 70, 229, 0.2);
      user-select: none;
      -webkit-user-select: none;
      touch-action: manipulation;
    }
    .drawer-item-title {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      pointer-events: none;
      flex: 1;
      margin-right: 8px;
    }
    .drawer-reading-badge {
      font-size: 0.75rem;
      background: rgba(16,185,129,0.15);
      color: #059669;
      padding: 2px 6px;
      border-radius: 4px;
      font-weight: 600;
      pointer-events: none;
      flex-shrink: 0;
    }
    .drawer-item-btn:hover { background-color: var(--highlight); }
    .drawer-item.active .drawer-item-btn {
      background-color: var(--highlight);
      color: var(--primary);
      font-weight: 700;
      border-left: 4px solid var(--primary);
    }"""

    if old_css_drawer in content:
        content = content.replace(old_css_drawer, new_css_drawer)
        print("Updated old_css_drawer")
    else:
        print("WARNING: old_css_drawer not found")

    # 2. Replace selectDrawerChapter & renderDrawerChapters
    start_marker = "    window.selectDrawerChapter = function(idx, e) {"
    end_marker = "    async function manualPreloadWebChapters(count = 50) {"

    if start_marker in content and end_marker in content:
        p1 = content.find(start_marker)
        p2 = content.find(end_marker)

        new_drawer_code = """    window.selectDrawerChapter = function(idx, e) {
      if (e) {
        try { e.stopPropagation(); } catch (_) {}
      }
      idx = parseInt(idx, 10);
      if (isNaN(idx)) return;
      if (!bookData || !bookData.chapters || idx < 0 || idx >= bookData.chapters.length) {
        console.warn('selectDrawerChapter: idx khong hop le hoac chua nap sach', idx);
        return;
      }
      console.log('[Drawer] Chon nhay sang chuong:', idx);

      // 1. Dong Drawer ngay lap tuc
      toggleChapterDrawer(false);

      // 2. Dong Honor overlay va backdrop neu dang mo
      if (typeof honorOverlayVisible !== 'undefined' && honorOverlayVisible) {
        if (typeof toggleHonorOverlay === 'function') toggleHonorOverlay();
      }

      // 3. Failsafe: Reset co lat trang va xoa sach clone cu
      isPageFlipping = false;
      isChapterTransitioning = false;
      try {
        const strayClone = document.getElementById('pageTurnClone');
        if (strayClone && strayClone.parentNode) {
          strayClone.parentNode.removeChild(strayClone);
        }
      } catch (_) {}

      // 4. Chuyen tab sang reader neu chua o reader
      nrCurrentTab = 'reader';
      const rv = document.getElementById('nrViewReader');
      if (rv) rv.classList.add('active');
      document.body.classList.add('in-reader-tab');

      // 5. Reset vi tri cuon ve 0 truoc khi render
      const sc = document.getElementById('readerScrollArea') || document.querySelector('main');
      if (sc) {
        sc.scrollTop = 0;
        sc.scrollLeft = 0;
      }

      // 6. Nap chuong moi (loadChapter)
      if (typeof loadChapter === 'function') {
        loadChapter(idx, 0, true);
      }

      // 7. Dam bao cuon ve dau trang sau khi render
      if (sc) {
        sc.scrollTop = 0;
        sc.scrollLeft = 0;
      }

      // 8. Cap nhat tieu de chuong va so trang
      if (typeof updateHonorTitles === 'function') updateHonorTitles();
      if (typeof updateHonorPageCounter === 'function') setTimeout(updateHonorPageCounter, 60);
      if (typeof updateNrPlayerUI === 'function') updateNrPlayerUI();

      // 9. Luu tien do doc
      if (typeof saveProgress === 'function') saveProgress();

      const targetCh = bookData.chapters[idx];
      if (targetCh && targetCh.title) {
        showToast('📖 Dang doc: ' + targetCh.title);
      }
    };

    // Render danh sach chuong trong Drawer voi the button cuc nhay
    function renderDrawerChapters(filter = '') {
      const list = document.getElementById('drawerChapterList');
      if (!list) return;
      list.innerHTML = '';
      if (!bookData || !bookData.chapters) {
        list.innerHTML = '<li style="padding:20px; text-align:center; color:var(--text-muted);">Chua nap truyen</li>';
        return;
      }

      if (bookData.is_web) {
        const webTop = document.createElement('div');
        webTop.style.cssText = 'padding: 10px 14px; margin-bottom: 8px; background: rgba(59,130,246,0.08); border: 1px solid rgba(59,130,246,0.25); border-radius: 8px; display:flex; justify-content:space-between; align-items:center;';
        webTop.innerHTML = `
          <span style="font-size:0.85rem; color:#2563eb; font-weight:600;">🌐 Truyen Web (${bookData.chapters.length} ch.)</span>
          <button class="btn btn-primary" type="button" style="font-size:0.8rem; padding:4px 10px;" id="btnDrawerFetch50" onclick="manualPreloadWebChapters(50)">
            📥 Tai truoc 50 ch. tiep
          </button>
        `;
        list.appendChild(webTop);
      }

      const fragment = document.createDocumentFragment();

      bookData.chapters.forEach((ch, idx) => {
        if (!ch) return;
        const chTitle = ch.title || `Chuong ${idx + 1}`;
        if (filter && !chTitle.toLowerCase().includes(filter)) return;

        const isCurrent = (idx === currentChapterIndex);
        const li = document.createElement('li');
        li.className = 'drawer-item' + (isCurrent ? ' active' : '');
        li.dataset.idx = idx;

        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'drawer-item-btn';
        btn.dataset.idx = idx;
        btn.innerHTML = `
          <span class="drawer-item-title">${escapeHtml(chTitle)}</span>
          ${isCurrent ? '<span class="drawer-reading-badge">Dang doc</span>' : ''}
        `;

        btn.onclick = (e) => {
          if (e) {
            e.preventDefault();
            e.stopPropagation();
          }
          window.selectDrawerChapter(idx, e);
        };

        li.appendChild(btn);
        fragment.appendChild(li);
      });

      list.appendChild(fragment);

      // Gan bat su kien delegation cho danh sach (chong ghost-touch, ho tro cuon danh sach)
      if (!list.dataset.delegationBound) {
        list.dataset.delegationBound = '1';
        let startY = 0, startX = 0, isScrolling = false;

        list.addEventListener('touchstart', (e) => {
          isScrolling = false;
          if (e.touches && e.touches[0]) {
            startY = e.touches[0].clientY;
            startX = e.touches[0].clientX;
          }
        }, { passive: true });

        list.addEventListener('touchmove', (e) => {
          if (e.touches && e.touches[0]) {
            if (Math.abs(e.touches[0].clientY - startY) > 20 || Math.abs(e.touches[0].clientX - startX) > 20) {
              isScrolling = true;
            }
          }
        }, { passive: true });

        list.addEventListener('touchend', (e) => {
          if (isScrolling) return;
          const btn = e.target.closest('.drawer-item-btn');
          if (btn && btn.dataset.idx !== undefined) {
            const idx = parseInt(btn.dataset.idx, 10);
            if (!isNaN(idx)) {
              if (e.cancelable) e.preventDefault();
              e.stopPropagation();
              window.selectDrawerChapter(idx, e);
            }
          }
        });
      }
    }

"""
        content = content[:p1] + new_drawer_code + content[p2:]
        print("Updated selectDrawerChapter and renderDrawerChapters")
    else:
        print("WARNING: start_marker or end_marker not found")

    # 3. Update document capture click listener
    old_cap_click = """    document.addEventListener('click', function(e) {
      const readerView = document.getElementById('nrViewReader');
      if (!readerView || !readerView.classList.contains('active')) return;
      if (e.target.closest('button, a, input, select, textarea, .modal, .drawer, #textSelectionToolbar, #paraContextMenu, #honorTopToolbar, #honorBottomToolbar, #honorFloatingMediaPill, #honorFabListen, #honorFontPanel, .modal-backdrop')) return;"""

    new_cap_click = """    document.addEventListener('click', function(e) {
      const readerView = document.getElementById('nrViewReader');
      if (!readerView || !readerView.classList.contains('active')) return;

      // Tuyet doi khong can thiep neu Drawer muc luc hoac bat ky modal nao dang mo
      const drawerEl = document.getElementById('chapterDrawer');
      if (drawerEl && drawerEl.classList.contains('open')) return;
      const modalOpen = document.querySelector('.modal-overlay.open, .modal.open, .library-modal.open, .chapter-drawer.open, #chapterDrawer.open, .drawer-overlay.open, #drawerOverlay.open');
      if (modalOpen) return;

      if (e.target.closest('button, a, input, select, textarea, .modal, .modal-overlay, .library-modal, .drawer, .chapter-drawer, #chapterDrawer, .drawer-item, .drawer-item-btn, .drawer-overlay, #drawerOverlay, #textSelectionToolbar, #paraContextMenu, #honorTopToolbar, #honorBottomToolbar, #honorFloatingMediaPill, #honorFabListen, #honorFontPanel, .modal-backdrop')) return;"""

    if old_cap_click in content:
        content = content.replace(old_cap_click, new_cap_click)
        print("Updated document capture click listener")
    else:
        print("WARNING: old_cap_click not found")

    # 4. Remove drawerChapterList from line 11700 stopPropagation list
    old_stop = "['chapterDrawer', 'drawerChapterList', 'drawerOverlay', 'honorFabListen'"
    new_stop = "['honorFabListen'"
    if old_stop in content:
        content = content.replace(old_stop, new_stop)
        print("Updated stopPropagation list")
    else:
        print("WARNING: old_stop not found")

    # 5. Update touchstart on window
    old_touch_start_check = """    window.addEventListener('touchstart', function(e) {"""
    new_touch_start_check = """    window.addEventListener('touchstart', function(e) {
      const drawerEl = document.getElementById('chapterDrawer');
      if (drawerEl && drawerEl.classList.contains('open')) {
        isTouchGestureHandled = true;
        return;
      }"""
    if old_touch_start_check in content and "const drawerEl = document.getElementById('chapterDrawer');\n      if (drawerEl && drawerEl.classList.contains('open'))" not in content:
        content = content.replace(old_touch_start_check, new_touch_start_check, 1)
        print("Updated window touchstart check")
    else:
        print("window touchstart check already has drawerEl or not found")

    with open(target_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("DesktopEpubReader/templates/index.html written successfully!")

    # Sync to HonorEpubReader assets
    assets_path = r"c:\Users\VANLUC\Downloads\Share tool -20261010T221918Z-1-001\Share tool\TTS_STT_vip_v1.6.0\HonorEpubReader\app\src\main\assets\index.html"
    with open(assets_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("HonorEpubReader assets synced successfully!")

    # Bump version in server.py
    server_path = r"D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\server.py"
    with open(server_path, "r", encoding="utf-8") as f:
        s_content = f.read()
    s_content = s_content.replace('"version": "v1.6.17-drawer-jump-fix"', '"version": "v1.6.18-bulletproof-drawer-jump"')
    with open(server_path, "w", encoding="utf-8") as f:
        f.write(s_content)
    print("server.py updated to v1.6.18-bulletproof-drawer-jump!")

if __name__ == "__main__":
    apply_fixes()
