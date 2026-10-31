import re

def update_file():
    target_path = r"D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\templates\index.html"
    with open(target_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Fix CSS for .chapter-drawer and .drawer-overlay
    old_css_drawer = """.drawer-overlay {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.45);
      z-index: 100;
      opacity: 0;
      visibility: hidden;
      transition: all 0.25s ease;
    }
    .drawer-overlay.open {
      opacity: 1;
      visibility: visible;
    }

    .chapter-drawer {
      position: fixed;
      top: 0;
      left: 0;
      width: 360px;
      max-width: 85vw;
      height: 100vh;
      background: var(--card-bg);
      box-shadow: 4px 0 25px rgba(0,0,0,0.2);
      z-index: 101;
      display: flex;
      flex-direction: column;
      transform: translateX(-100%);
      transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .chapter-drawer.open {
      transform: translateX(0);
    }"""

    new_css_drawer = """.drawer-overlay {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.55);
      z-index: 2000 !important;
      opacity: 0;
      visibility: hidden;
      transition: all 0.25s ease;
    }
    .drawer-overlay.open {
      opacity: 1;
      visibility: visible;
      pointer-events: auto !important;
    }

    .chapter-drawer {
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
    }"""

    if old_css_drawer in content:
        content = content.replace(old_css_drawer, new_css_drawer)
        print("Updated old_css_drawer successfully")
    else:
        print("WARNING: old_css_drawer not found")

    # 1b. Fix .drawer-item style for touch responsiveness and clear font
    old_css_item = """.drawer-item {
      padding: 13px 20px;
      font-size: 0.92rem;
      cursor: pointer;
      border-bottom: 1px solid var(--border-color);
      display: flex;
      justify-content: space-between;
      align-items: center;
      transition: background 0.15s;
    }
    .drawer-item:hover { background-color: var(--highlight); }
    .drawer-item.active {
      background-color: var(--highlight);
      color: var(--primary);
      font-weight: 700;
      border-left: 4px solid var(--primary);
    }"""

    new_css_item = """.drawer-item {
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

    if old_css_item in content:
        content = content.replace(old_css_item, new_css_item)
        print("Updated old_css_item successfully")
    else:
        print("WARNING: old_css_item not found")

    # 1c. Fix general z-index overrides in line 1956
    old_zi = """/* Đảm bảo toàn bộ Modal, Drawer, Popup luôn nổi TRÊN màn hình chính và thanh điều hướng */
.drawer-overlay {
  z-index: 1000 !important;
}
.drawer {
  z-index: 1001 !important;
}
.modal-overlay {
  z-index: 1100 !important;
}
.modal {
  z-index: 1101 !important;
}"""

    new_zi = """/* Đảm bảo toàn bộ Modal, Drawer, Popup luôn nổi TRÊN màn hình chính và thanh điều hướng */
.drawer-overlay, #drawerOverlay {
  z-index: 2000 !important;
}
.chapter-drawer, #chapterDrawer, .drawer {
  z-index: 2001 !important;
}
.modal-overlay, #libraryModalOverlay {
  z-index: 2100 !important;
}
.modal, .library-modal {
  z-index: 2101 !important;
}"""

    if old_zi in content:
        content = content.replace(old_zi, new_zi)
        print("Updated old_zi successfully")
    else:
        print("WARNING: old_zi not found")

    # 2. Fix drawer HTML close button
    old_drawer_html = """  <div id="drawerOverlay" class="drawer-overlay" onclick="toggleChapterDrawer()"></div>
  <div id="chapterDrawer" class="chapter-drawer">
    <div class="drawer-header">
      <span>Mục Lục Chương</span>
      <button class="btn" style="padding: 4px 8px;" onclick="toggleChapterDrawer()">✕</button>
    </div>"""

    new_drawer_html = """  <div id="drawerOverlay" class="drawer-overlay" onclick="toggleChapterDrawer(false)"></div>
  <div id="chapterDrawer" class="chapter-drawer">
    <div class="drawer-header">
      <span>Mục Lục Chương</span>
      <button class="btn" style="padding: 4px 8px;" onclick="toggleChapterDrawer(false)">✕</button>
    </div>"""

    if old_drawer_html in content:
        content = content.replace(old_drawer_html, new_drawer_html)
        print("Updated old_drawer_html successfully")
    else:
        print("WARNING: old_drawer_html not found")

    # 3. Replace toggleChapterDrawer and renderDrawerChapters with robust selectDrawerChapter
    old_drawer_js = """    function toggleChapterDrawer() {
      const drawer = document.getElementById('chapterDrawer');
      const overlay = document.getElementById('drawerOverlay');
      const isOpen = drawer.classList.contains('open');
      if (isOpen) {
        drawer.classList.remove('open');
        overlay.classList.remove('open');
      } else {
        renderDrawerChapters();
        drawer.classList.add('open');
        overlay.classList.add('open');
      }
    }

    function filterChapters(query) {
      renderDrawerChapters(query.toLowerCase().trim());
    }

    // Render danh sách chương trong Drawer
    function renderDrawerChapters(filter = '') {
      const list = document.getElementById('drawerChapterList');
      list.innerHTML = '';
      if (!bookData || !bookData.chapters) {
        list.innerHTML = '<li style="padding:20px; text-align:center; color:var(--text-muted);">Chưa nạp truyện</li>';
        return;
      }

      if (bookData.is_web) {
        const webTop = document.createElement('div');
        webTop.style.cssText = 'padding: 10px 14px; margin-bottom: 8px; background: rgba(59,130,246,0.08); border: 1px solid rgba(59,130,246,0.25); border-radius: 8px; display:flex; justify-content:space-between; align-items:center;';
        webTop.innerHTML = `
          <span style="font-size:0.85rem; color:#2563eb; font-weight:600;">🌐 Truyện Web (${bookData.chapters.length} ch.)</span>
          <button class="btn btn-primary" style="font-size:0.8rem; padding:4px 10px;" id="btnDrawerFetch50" onclick="manualPreloadWebChapters(50)">
            📥 Tải trước 50 ch. tiếp
          </button>
        `;
        list.appendChild(webTop);
      }

      bookData.chapters.forEach((ch, idx) => {
        if (!ch) return;
        const chTitle = ch.title || `Chương ${idx + 1}`;
        if (filter && !chTitle.toLowerCase().includes(filter)) return;
        const li = document.createElement('li');
        li.className = 'drawer-item' + (idx === currentChapterIndex ? ' active' : '');
        li.innerHTML = `
          <span style="overflow:hidden; text-overflow:ellipsis;">${chTitle}</span>
          ${idx === currentChapterIndex ? '<span style="font-size:0.75rem; background:rgba(16,185,129,0.15); color:#059669; padding:2px 6px; border-radius:4px; font-weight:600;">Đang đọc</span>' : ''}
        `;
        li.onclick = () => {
          toggleChapterDrawer();
          loadChapter(idx, 0);
        };
        list.appendChild(li);
      });
    }"""

    new_drawer_js = """    function toggleChapterDrawer(forceOpen = null) {
      const drawer = document.getElementById('chapterDrawer');
      const overlay = document.getElementById('drawerOverlay');
      if (!drawer || !overlay) return;
      const isOpen = drawer.classList.contains('open');
      const shouldOpen = forceOpen !== null ? forceOpen : !isOpen;
      if (!shouldOpen) {
        drawer.classList.remove('open');
        overlay.classList.remove('open');
      } else {
        renderDrawerChapters();
        drawer.classList.add('open');
        overlay.classList.add('open');
        setTimeout(() => {
          const activeItem = drawer.querySelector('.drawer-item.active');
          if (activeItem) {
            try { activeItem.scrollIntoView({ block: 'center', behavior: 'smooth' }); } catch (_) {}
          }
        }, 150);
      }
    }

    function filterChapters(query) {
      renderDrawerChapters(query.toLowerCase().trim());
    }

    window.selectDrawerChapter = function(idx, e) {
      if (e) {
        try { e.stopPropagation(); } catch (_) {}
      }
      console.log('[Drawer] Chọn nhảy sang chương:', idx);
      toggleChapterDrawer(false);

      if (typeof honorOverlayVisible !== 'undefined' && honorOverlayVisible) {
        if (typeof toggleHonorOverlay === 'function') toggleHonorOverlay();
      }

      isPageFlipping = false;
      isChapterTransitioning = false;
      try {
        const strayClone = document.getElementById('pageTurnClone');
        if (strayClone && strayClone.parentNode) {
          strayClone.parentNode.removeChild(strayClone);
        }
      } catch (_) {}

      if (typeof switchNrTab === 'function') {
        switchNrTab('reader');
      }

      if (typeof loadChapter === 'function') {
        loadChapter(idx, 0, true);
      }

      const sc = document.getElementById('readerScrollArea') || document.querySelector('main');
      if (sc) {
        sc.scrollTop = 0;
        sc.scrollLeft = 0;
      }

      if (typeof updateHonorTitles === 'function') updateHonorTitles();
      if (typeof updateHonorPageCounter === 'function') setTimeout(updateHonorPageCounter, 60);
      if (typeof updateNrPlayerUI === 'function') updateNrPlayerUI();

      const targetCh = (bookData && bookData.chapters) ? bookData.chapters[idx] : null;
      if (targetCh && targetCh.title) {
        showToast('📖 Đang đọc: ' + targetCh.title);
      }
    };

    // Render danh sách chương trong Drawer với cảm ứng siêu nhạy
    function renderDrawerChapters(filter = '') {
      const list = document.getElementById('drawerChapterList');
      if (!list) return;
      list.innerHTML = '';
      if (!bookData || !bookData.chapters) {
        list.innerHTML = '<li style="padding:20px; text-align:center; color:var(--text-muted);">Chưa nạp truyện</li>';
        return;
      }

      if (bookData.is_web) {
        const webTop = document.createElement('div');
        webTop.style.cssText = 'padding: 10px 14px; margin-bottom: 8px; background: rgba(59,130,246,0.08); border: 1px solid rgba(59,130,246,0.25); border-radius: 8px; display:flex; justify-content:space-between; align-items:center;';
        webTop.innerHTML = `
          <span style="font-size:0.85rem; color:#2563eb; font-weight:600;">🌐 Truyện Web (${bookData.chapters.length} ch.)</span>
          <button class="btn btn-primary" style="font-size:0.8rem; padding:4px 10px;" id="btnDrawerFetch50" onclick="manualPreloadWebChapters(50)">
            📥 Tải trước 50 ch. tiếp
          </button>
        `;
        list.appendChild(webTop);
      }

      bookData.chapters.forEach((ch, idx) => {
        if (!ch) return;
        const chTitle = ch.title || `Chương ${idx + 1}`;
        if (filter && !chTitle.toLowerCase().includes(filter)) return;
        const li = document.createElement('li');
        li.className = 'drawer-item' + (idx === currentChapterIndex ? ' active' : '');
        li.innerHTML = `
          <span style="overflow:hidden; text-overflow:ellipsis; pointer-events:none;">${chTitle}</span>
          ${idx === currentChapterIndex ? '<span style="font-size:0.75rem; background:rgba(16,185,129,0.15); color:#059669; padding:2px 6px; border-radius:4px; font-weight:600; pointer-events:none;">Đang đọc</span>' : ''}
        `;

        let touchStartY = 0;
        let isTouchMoved = false;

        li.addEventListener('touchstart', (e) => {
          isTouchMoved = false;
          if (e.touches && e.touches.length > 0) {
            touchStartY = e.touches[0].clientY;
          }
        }, { passive: true });

        li.addEventListener('touchmove', (e) => {
          if (e.touches && e.touches.length > 0) {
            if (Math.abs(e.touches[0].clientY - touchStartY) > 8) {
              isTouchMoved = true;
            }
          }
        }, { passive: true });

        li.addEventListener('touchend', (e) => {
          if (!isTouchMoved) {
            e.stopPropagation();
            window.selectDrawerChapter(idx, e);
          }
        });

        li.addEventListener('click', (e) => {
          e.stopPropagation();
          window.selectDrawerChapter(idx, e);
        });

        list.appendChild(li);
      });
    }"""

    if old_drawer_js in content:
        content = content.replace(old_drawer_js, new_drawer_js)
        print("Updated old_drawer_js successfully")
    else:
        print("WARNING: old_drawer_js not found")

    # 4. Update onHonorChapterSliderCommit to use window.selectDrawerChapter
    old_slider_commit = """    function onHonorChapterSliderCommit(val) {
      const idx = parseInt(val, 10);
      if (typeof loadChapter === 'function') {
        loadChapter(idx, 0);
      }
    }"""

    new_slider_commit = """    function onHonorChapterSliderCommit(val) {
      const idx = parseInt(val, 10);
      if (typeof window.selectDrawerChapter === 'function') {
        window.selectDrawerChapter(idx);
      } else if (typeof loadChapter === 'function') {
        loadChapter(idx, 0, true);
      }
    }"""

    if old_slider_commit in content:
        content = content.replace(old_slider_commit, new_slider_commit)
        print("Updated old_slider_commit successfully")
    else:
        print("WARNING: old_slider_commit not found")

    # 5. Update nextChapter & prevChapter hooks
    old_nav_hooks = """      // 2. Hook vào nextChapter, prevChapter để cập nhật số chương
      const origNextCh = window.nextChapter;
      window.nextChapter = function() {
        if (typeof origNextCh === 'function') {
          origNextCh();
        } else if (typeof triggerNextChapterByScroll === 'function') {
          triggerNextChapterByScroll();
        } else if (bookData && currentChapterIndex + 1 < bookData.chapters.length) {
          loadChapter(currentChapterIndex + 1, 0);
        }
        updateNrPlayerUI();
      };

      const origPrevCh = window.prevChapter;
      window.prevChapter = function() {
        if (typeof origPrevCh === 'function') {
          origPrevCh();
        } else if (bookData && currentChapterIndex > 0) {
          loadChapter(currentChapterIndex - 1, 0);
        }
        updateNrPlayerUI();
      };"""

    new_nav_hooks = """      // 2. Hook vào nextChapter, prevChapter để cập nhật số chương
      window.nextChapter = function() {
        if (!bookData || !bookData.chapters) return;
        if (currentChapterIndex + 1 < bookData.chapters.length) {
          if (typeof window.selectDrawerChapter === 'function') {
            window.selectDrawerChapter(currentChapterIndex + 1);
          } else {
            loadChapter(currentChapterIndex + 1, 0, true);
          }
        } else if (bookData.is_web && typeof fetchMoreWebChapters === 'function') {
          showToast('⏳ Đang tải thêm chương tiếp theo từ web...');
          fetchMoreWebChapters(5).then(added => {
            if (added > 0 && currentChapterIndex + 1 < bookData.chapters.length) {
              if (typeof window.selectDrawerChapter === 'function') {
                window.selectDrawerChapter(currentChapterIndex + 1);
              } else {
                loadChapter(currentChapterIndex + 1, 0, true);
              }
            } else {
              showToast('✅ Đã là chương mới nhất của truyện!');
            }
          });
        } else {
          showToast('✅ Đã là chương cuối cùng của quyển truyện!');
        }
        updateNrPlayerUI();
      };

      window.prevChapter = function() {
        if (!bookData || !bookData.chapters) return;
        if (currentChapterIndex > 0) {
          if (typeof window.selectDrawerChapter === 'function') {
            window.selectDrawerChapter(currentChapterIndex - 1);
          } else {
            loadChapter(currentChapterIndex - 1, 0, true);
          }
        } else {
          showToast('✅ Đã là chương đầu tiên của quyển truyện!');
        }
        updateNrPlayerUI();
      };"""

    if old_nav_hooks in content:
        content = content.replace(old_nav_hooks, new_nav_hooks)
        print("Updated old_nav_hooks successfully")
    else:
        print("WARNING: old_nav_hooks not found")

    # 6. Update isUIOverlayActive to include drawer and overlay
    old_overlay_active = """    function isUIOverlayActive() {
      // 1. Kiểm tra các modal overlay, drawer, dropdown
      const overlays = document.querySelectorAll('.modal-overlay.open, .modal.open, .library-modal.open, .drawer.open, #mobileMenuDropdown.open, .mobile-menu-dropdown.open');"""

    new_overlay_active = """    function isUIOverlayActive() {
      // 1. Kiểm tra các modal overlay, drawer, dropdown
      const overlays = document.querySelectorAll('.modal-overlay.open, .modal.open, .library-modal.open, .drawer.open, .chapter-drawer.open, #chapterDrawer.open, .drawer-overlay.open, #drawerOverlay.open, #mobileMenuDropdown.open, .mobile-menu-dropdown.open');"""

    if old_overlay_active in content:
        content = content.replace(old_overlay_active, new_overlay_active)
        print("Updated old_overlay_active successfully")
    else:
        print("WARNING: old_overlay_active not found")

    # 7. Update touch listeners closest selectors
    old_touch_closest = """.modal, .modal-overlay, .library-modal, .drawer, #mobileMenuDropdown"""
    new_touch_closest = """.modal, .modal-overlay, .library-modal, .drawer, .chapter-drawer, #chapterDrawer, .drawer-item, .drawer-overlay, #drawerOverlay, #mobileMenuDropdown"""

    if old_touch_closest in content:
        content = content.replace(old_touch_closest, new_touch_closest)
        print("Updated old_touch_closest successfully")
    else:
        print("WARNING: old_touch_closest not found")

    # 7b. Update modalOpen check in touchend
    old_modal_open = """      // Kiểm tra modal đang mở thực tế
      const modalOpen = document.querySelector('.modal-overlay.open, .modal.open, .library-modal.open, .drawer.open');"""

    new_modal_open = """      // Kiểm tra modal đang mở thực tế
      const modalOpen = document.querySelector('.modal-overlay.open, .modal.open, .library-modal.open, .drawer.open, .chapter-drawer.open, #chapterDrawer.open, .drawer-overlay.open, #drawerOverlay.open');"""

    if old_modal_open in content:
        content = content.replace(old_modal_open, new_modal_open)
        print("Updated old_modal_open successfully")
    else:
        print("WARNING: old_modal_open not found")

    # 8. Add chapterDrawer and drawerChapterList to stopPropagation
    old_stop_prop = """    ['honorFabListen', 'honorFloatingMediaPill', 'honorTopToolbar', 'honorBottomToolbar', 'honorFontPanel'].forEach(id => {"""
    new_stop_prop = """    ['chapterDrawer', 'drawerChapterList', 'drawerOverlay', 'honorFabListen', 'honorFloatingMediaPill', 'honorTopToolbar', 'honorBottomToolbar', 'honorFontPanel'].forEach(id => {"""

    if old_stop_prop in content:
        content = content.replace(old_stop_prop, new_stop_prop)
        print("Updated old_stop_prop successfully")
    else:
        print("WARNING: old_stop_prop not found")

    with open(target_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("DesktopEpubReader/templates/index.html updated successfully!")

    # Also sync to HonorEpubReader/app/src/main/assets/index.html
    assets_path = r"c:\Users\VANLUC\Downloads\Share tool -20261010T221918Z-1-001\Share tool\TTS_STT_vip_v1.6.0\HonorEpubReader\app\src\main\assets\index.html"
    with open(assets_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("HonorEpubReader assets/index.html synced successfully!")

    # Update version in server.py
    server_path = r"D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\server.py"
    with open(server_path, "r", encoding="utf-8") as f:
        s_content = f.read()
    s_content = s_content.replace('"version": "v1.6.16-honor-top-touch-pill-bottom"', '"version": "v1.6.17-drawer-jump-fix"')
    with open(server_path, "w", encoding="utf-8") as f:
        f.write(s_content)
    print("server.py updated to v1.6.17-drawer-jump-fix!")

if __name__ == "__main__":
    update_file()
