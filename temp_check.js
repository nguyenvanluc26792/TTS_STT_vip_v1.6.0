
    let bookData = null;
    let currentChapterIndex = 0;
    let currentParagraphIndex = 0;
    let isPlaying = false;
    let isLoading = false;
    let voices = [];
    let currentFontSize = 18;
    let currentSpeed = 1.0;
    const audio = document.getElementById('audioPlayer');

    
    // =====================================================================
    // NOVELREADER UI CONTROLLER V3 (NATIVE VIEWPAGER & SPRING PILL NAVIGATION)
    // =====================================================================
    let nrCurrentTab = 'home';
    let nrShelfFilter = 'all';

    function getCurrentChapterParagraphs() {
      try {
        if (typeof allParagraphs !== 'undefined' && Array.isArray(allParagraphs) && allParagraphs.length > 0) {
          return allParagraphs;
        }
        if (typeof bookData !== 'undefined' && bookData && bookData.chapters) {
          const ch = bookData.chapters[currentChapterIndex || 0];
          if (ch && Array.isArray(ch.paragraphs)) return ch.paragraphs;
        }
      } catch (e) {}
      return [];
    }

    function updateNrPlayerUI() {
      try {
        const titleEl = document.getElementById('nrPlayerTitle');
        const bufferEl = document.getElementById('nrPlayerBuffer');
        const dotEl = document.getElementById('nrPlayerDot');
        const subEl = document.getElementById('nrPlayerSub');
        const fillEl = document.getElementById('nrPlayerFill');
        const thumbEl = document.getElementById('nrPlayerThumb');
        const pctEl = document.getElementById('nrPlayerPct');
        const playIcon = document.getElementById('nrPlayIcon');
        const pauseIcon = document.getElementById('nrPauseIcon');
        const quickVoiceEl = document.getElementById('nrQuickVoiceName');
        const quickChEl = document.getElementById('nrQuickChapterText');

        const isPlayingNow = (typeof isPlaying !== "undefined") ? isPlaying : false;
        if (playIcon) playIcon.style.display = isPlayingNow ? "none" : "block";
        if (pauseIcon) pauseIcon.style.display = isPlayingNow ? "block" : "none";
        const playBtnEl = document.getElementById("nrPlayBtn");
        if (playBtnEl) {
          if (isPlayingNow) playBtnEl.classList.add("is-playing");
          else playBtnEl.classList.remove("is-playing");
        }

        if (quickVoiceEl) {
          const vText = document.getElementById('nrSelectedVoiceText')?.textContent || 'Ngọc Huyền';
          quickVoiceEl.textContent = vText;
        }

        if (typeof bookData !== 'undefined' && bookData) {
          const bTitle = bookData.title || 'Truyện không tên';
          const totalCh = (bookData.chapters || []).length;
          const currentChNum = (currentChapterIndex || 0) + 1;

          if (titleEl) titleEl.textContent = bTitle;
          if (quickChEl) quickChEl.textContent = `Chương ${currentChNum}/${totalCh || 1}`;

          // Hiển thị số trang đệm
          let bufferStr = 'Đệm: 0/30';
          if (window.latestPreloadStatus && window.latestPreloadStatus.cachedCount !== undefined) {
            const st = window.latestPreloadStatus;
            bufferStr = `Đệm: ${st.cachedCount}/${st.windowTotal || 30}`;
          } else {
            const cachedCount = (bookData.chapters || []).length;
            bufferStr = `Đệm: ${Math.min(cachedCount, 30)}/30`;
          }
          if (bufferEl) bufferEl.textContent = bufferStr;
          if (dotEl) dotEl.style.display = 'inline';
          if (subEl) subEl.textContent = bufferStr;

          const paras = getCurrentChapterParagraphs();
          const totalParas = paras.length || 1;
          const curP = (typeof currentParagraphIndex !== 'undefined') ? currentParagraphIndex : 0;
          const pct = Math.min(100, Math.max(0, Math.round(((curP + 1) / totalParas) * 100)));

          if (fillEl) fillEl.style.width = pct + '%';
          if (thumbEl) thumbEl.style.left = pct + '%';
          if (pctEl) pctEl.textContent = pct + '%';
        } else {
          if (titleEl) titleEl.textContent = 'Chưa mở truyện';
          if (bufferEl) bufferEl.textContent = 'Sẵn sàng';
          if (dotEl) dotEl.style.display = 'inline';
          if (subEl) subEl.textContent = 'Sẵn sàng đọc truyện';
          if (fillEl) fillEl.style.width = '0%';
          if (thumbEl) thumbEl.style.left = '0%';
          if (pctEl) pctEl.textContent = '0%';
          if (quickChEl) quickChEl.textContent = 'Danh sách chương';
        }
      } catch (err) {
        console.warn('Lỗi cập nhật Mini Player UI:', err);
      }
    }

    function seekNrPlayerFromTrack(e) {
      try {
        const track = document.getElementById('nrPlayerTrack');
        if (!track) return;
        const rect = track.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const pct = Math.max(0, Math.min(1, clickX / rect.width));

        const paras = getCurrentChapterParagraphs();
        if (paras.length > 0) {
          const targetIndex = Math.floor(pct * paras.length);
          if (typeof playParagraph === 'function') {
            playParagraph(targetIndex);
          } else if (typeof currentParagraphIndex !== 'undefined') {
            currentParagraphIndex = targetIndex;
            updateNrPlayerUI();
          }
        }
      } catch (e) {
        console.error('Lỗi tua mini player:', e);
      }
    }

    function triggerAddNewBook() {
      if (window.HonorBridge && typeof window.HonorBridge.openFilePicker === 'function') {
        try {
          window.HonorBridge.openFilePicker();
          return;
        } catch (e) {}
      }
      document.getElementById('epubFileInput')?.click();
    }

    function toggleEyeTracking() {
      if (typeof window.triggerEyeSettings === 'function') {
        window.triggerEyeSettings();
      } else if (window.HonorBridge && typeof window.HonorBridge.toggleEyeTracking === 'function') {
        window.HonorBridge.toggleEyeTracking();
      }
      setTimeout(updateNrSettingsUI, 200);
    }

    function setHonorEyeMode(modeCode) {
      window.eyeTrackingEnabled = (modeCode !== 0);
      localStorage.setItem('honor_eye_enabled', window.eyeTrackingEnabled ? 'true' : 'false');
      const modeMap = { 1: 'slide', 2: 'scroll', 3: 'curl' };
      if (modeMap[modeCode] && typeof window.setReaderPageMode === 'function') {
        window.setReaderPageMode(modeMap[modeCode]);
      }
      if (window.HonorBridge && typeof window.HonorBridge.setAnimMode === 'function') {
        try { window.HonorBridge.setAnimMode(modeCode); } catch (e) {}
      }
      const modeNames = { 0: 'Đã TẮT theo dõi mắt', 1: 'Trượt Ngang (SLIDE)', 2: 'Cuộn Dọc (SCROLL)', 3: 'Lật Trang 3D (CURL)' };
      showToast('👁️ MagicOS: ' + (modeNames[modeCode] || 'Đã cập nhật'));
      updateNrSettingsUI();
    }

    function openHonorEyeDiagnostics() {
      if (window.HonorBridge && typeof window.HonorBridge.openDiagnostics === 'function') {
        try {
          window.HonorBridge.openDiagnostics();
          return;
        } catch (e) {}
      }
      toggleEyeTracking();
    }

    function syncNrReaderLayout() {
      try {
        const dock = document.getElementById('nrBottomDock');
        if (dock && !document.body.classList.contains('zen-mode')) {
          const h = dock.offsetHeight;
          if (h > 40) {
            document.documentElement.style.setProperty('--nr-dock-h', h + 'px');
          }
        }
      } catch (e) {}
    }

    /* CHUYỂN TAB CHUẨN NOVELREADER VỚI VIEWPAGER TRACK VÀ SPRING INDICATOR */
    function switchNrTab(tabName) {
      nrCurrentTab = tabName;
      const track = document.getElementById('nrViewPagerTrack');
      const readerView = document.getElementById('nrViewReader');
      const indicator = document.getElementById('nrNavActiveIndicator');

      // 1. Quản lý Màn hình Đọc Truyện (Reader Overlay)
      if (tabName === 'reader') {
        if (readerView) readerView.classList.add('active');
        document.body.classList.add('in-reader-tab');
        if (typeof updateHonorTitles === 'function') updateHonorTitles();
        if (typeof updateHonorPageCounter === 'function') setTimeout(updateHonorPageCounter, 60);
        if (typeof updateHonorClockAndBattery === 'function') updateHonorClockAndBattery();
      } else {
        if (readerView) readerView.classList.remove('active');
        document.body.classList.remove('in-reader-tab');
      }

      // 2. Chuyển động Horizontal ViewPager Track mượt mà
      if (track) {
        if (tabName === 'home') {
          track.style.transform = 'translateX(0%)';
        } else if (tabName === 'shelf' || tabName === 'reader') {
          track.style.transform = 'translateX(-33.333333%)';
        } else if (tabName === 'settings') {
          track.style.transform = 'translateX(-66.666667%)';
        }
      }

      // 3. Chuyển động Floating Active Pill Indicator trên thanh Bottom Nav
      if (indicator) {
        let tabIndex = 0;
        if (tabName === 'home') tabIndex = 0;
        else if (tabName === 'shelf' || tabName === 'reader') tabIndex = 1;
        else if (tabName === 'settings') tabIndex = 2;
        indicator.style.transform = `translateX(${tabIndex * 100}%)`;
      }

      // 4. Nếu chuyển sang màn hình ngoài Đọc truyện thì thoát chế độ Zen để hiện lại thanh điều hướng
      if (tabName !== 'reader' && document.body.classList.contains('zen-mode')) {
        if (typeof window.exitZenMode === 'function') {
          window.exitZenMode();
        } else {
          document.body.classList.remove('zen-mode');
        }
      }

      // 5. Cập nhật trạng thái Bottom Dock (Ẩn player ở Cài đặt, ẩn quick pills ở Reader)
      const dock = document.getElementById('nrBottomDock');
      if (dock) {
        dock.classList.toggle('settings-mode', tabName === 'settings');
        dock.classList.toggle('reader-mode', tabName === 'reader');
      }

      // 6. Cập nhật Tab Active Indicators & Icons
      ['nrNavTabHome', 'nrNavTabShelf', 'nrNavTabSettings'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.classList.remove('active');
      });
      if (tabName === 'home') document.getElementById('nrNavTabHome')?.classList.add('active');
      if (tabName === 'shelf' || tabName === 'reader') {
        document.getElementById('nrNavTabShelf')?.classList.add('active');
        if (tabName === 'shelf') loadNrBookshelf();
      }
      if (tabName === 'settings') {
        document.getElementById('nrNavTabSettings')?.classList.add('active');
        updateNrSettingsUI();
      }

      // 7. FAB chỉ hiện khi ở tab Tủ Sách
      const fab = document.getElementById('nrFabAdd');
      if (fab) fab.style.display = (tabName === 'shelf') ? 'flex' : 'none';

      // 8. Cập nhật số chương rút gọn C1, C2, C3... và đồng bộ chiều cao vùng đọc khi ở màn hình đọc sách
      if (tabName === 'reader') {
        const chPill = document.getElementById('nrReaderChapterPill');
        if (chPill) chPill.textContent = 'C' + ((currentChapterIndex || 0) + 1);
        requestAnimationFrame(syncNrReaderLayout);
        setTimeout(syncNrReaderLayout, 80);
      }

      // 9. Báo cho tầng Native Android biết có đang ở màn hình ngoài Reader hay không để không chặn vuốt ngang
      if (typeof isUIOverlayActive === 'function') {
        try { isUIOverlayActive(); } catch (e) {}
      }
    }

    function openReaderView() {
      if (!bookData) {
        showToast('📖 Hãy chọn một cuốn truyện trong Tủ Sách hoặc dán link online để bắt đầu đọc!');
        switchNrTab('shelf');
        return;
      }
      switchNrTab('reader');
    }

    let shelfLongPressTimer = null;
    let shelfIsLongPress = false;
    let shelfTouchStartX = 0, shelfTouchStartY = 0;
    let currentActionBook = null;

    function onShelfBookTouchStart(e, bookId, title, author, isWeb, sourceUrl) {
      shelfIsLongPress = false;
      if (!e.touches || !e.touches.length) return;
      const t = e.touches[0];
      shelfTouchStartX = t.clientX;
      shelfTouchStartY = t.clientY;
      clearTimeout(shelfLongPressTimer);
      shelfLongPressTimer = setTimeout(() => {
        shelfIsLongPress = true;
        try { if (navigator.vibrate) navigator.vibrate(50); } catch (_) {}
        openBookActionModal(bookId, title, author, isWeb, sourceUrl);
      }, 500);
    }

    function onShelfBookTouchMove(e) {
      if (!e.touches || !e.touches.length) return;
      const t = e.touches[0];
      const dist = Math.hypot(t.clientX - shelfTouchStartX, t.clientY - shelfTouchStartY);
      if (dist > 12) {
        clearTimeout(shelfLongPressTimer);
      }
    }

    function onShelfBookTouchEnd(e) {
      clearTimeout(shelfLongPressTimer);
      if (shelfIsLongPress) {
        e.preventDefault();
        e.stopPropagation();
      }
    }

    function onShelfBookContextMenu(e, bookId, title, author, isWeb, sourceUrl) {
      e.preventDefault();
      e.stopPropagation();
      openBookActionModal(bookId, title, author, isWeb, sourceUrl);
      return false;
    }

    function onShelfBookClick(e, bookId) {
      if (shelfIsLongPress) {
        shelfIsLongPress = false;
        return;
      }
      loadNrBookById(bookId);
    }

    function openBookActionModal(bookId, title, author, isWeb, sourceUrl) {
      currentActionBook = { bookId, title, author, isWeb, sourceUrl };
      const tEl = document.getElementById('nrBookActionTitle');
      const sEl = document.getElementById('nrBookActionSub');
      if (tEl) tEl.textContent = title;
      if (sEl) sEl.textContent = `${author} • ${isWeb ? 'Truyện Online Web' : 'Sách EPUB / PDF'}`;
      const repairBtn = document.getElementById('nrBookActionRepairBtn');
      if (repairBtn) {
        repairBtn.style.display = (isWeb && sourceUrl) ? 'block' : 'none';
      }
      const modal = document.getElementById('nrBookActionModal');
      if (modal) modal.style.display = 'flex';
    }

    function closeBookActionModal() {
      const modal = document.getElementById('nrBookActionModal');
      if (modal) modal.style.display = 'none';
      currentActionBook = null;
    }

    function openBookFromActionModal() {
      if (!currentActionBook) return;
      const bId = currentActionBook.bookId;
      closeBookActionModal();
      loadNrBookById(bId);
    }

    async function deleteBookFromActionModal() {
      if (!currentActionBook) return;
      const b = currentActionBook;
      closeBookActionModal();
      confirmDeleteNrBook(b.bookId, b.title);
    }

    async function repairBookFromActionModal() {
      if (!currentActionBook || !currentActionBook.sourceUrl) return;
      const src = currentActionBook.sourceUrl;
      closeBookActionModal();
      showToast('🚀 Đang kết nối tải lại đầy đủ chương từ web...');
      const inp = document.getElementById('nrWebUrlInput');
      if (inp) inp.value = src;
      await submitNrWebUrl();
    }

    async function confirmDeleteNrBook(bookId, title) {
      if (!confirm(`Bạn có chắc muốn xoá "${title}" khỏi tủ sách không?`)) return;
      try {
        const res = await fetch('/api/books/' + bookId, { method: 'DELETE' });
        const data = await res.json();
        if (data.success || res.ok) {
          showToast(`🗑️ Đã xoá thành công: ${title}`);
          if (bookData && bookData.id === bookId) {
            bookData = null;
            const r = document.getElementById('readerContent');
            if (r) {
              r.innerHTML = `
                <div class="empty-state">
                  <div class="empty-dropzone" onclick="switchNrTab('home')">
                    <h3 style="margin-bottom:8px;">Đã xoá truyện</h3>
                    <p>Bấm vào đây để tìm truyện mới hoặc mở sách khác trong Tủ Sách!</p>
                  </div>
                </div>`;
            }
          }
          loadNrBookshelf();
        } else {
          showToast('❌ Không thể xoá sách: ' + (data.error || 'Lỗi server'));
        }
      } catch (e) {
        showToast('❌ Lỗi khi xoá sách: ' + e.message);
      }
    }

    async function loadNrBookshelf() {
      const container = document.getElementById('nrShelfList');
      if (!container) return;
      try {
        const res = await fetch('/api/books');
        const books = await res.json();
        updateLibraryCountUI(books.length);

        if (!books || books.length === 0) {
          container.innerHTML = `
            <div style="text-align:center; padding:40px 20px; color:#7c7e8e;">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="margin-bottom:12px; opacity:0.6;"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
              <div style="font-size:0.95rem; font-weight:600; color:#b8bac8; margin-bottom:4px;">Tủ sách đang trống</div>
              <div style="font-size:0.8rem;">Hãy dán link truyện online ở Trang chủ hoặc bấm nút (+) để nạp truyện EPUB!</div>
            </div>`;
          return;
        }

        let filtered = books;
        if (nrShelfFilter === 'web') {
          filtered = books.filter(b => b.is_web || (b.title && b.title.startsWith('Web:')));
        } else if (nrShelfFilter === 'epub') {
          filtered = books.filter(b => !b.is_web && !(b.title && b.title.startsWith('Web:')));
        }

        if (filtered.length === 0) {
          container.innerHTML = `<div style="text-align:center; padding:30px; color:#7c7e8e; font-size:0.85rem;">Không có sách nào trong mục này.</div>`;
          return;
        }

        container.innerHTML = filtered.map(b => {
          const isWeb = b.is_web || (b.title && b.title.startsWith('Web:'));
          const displayTitle = (b.title || 'Truyện chưa đặt tên').replace(/^Web:\s*/, '');
          const safeTitle = displayTitle.replace(/'/g, "\\'").replace(/"/g, '&quot;');
          const safeAuthor = (b.author || 'Tác giả').replace(/'/g, "\\'").replace(/"/g, '&quot;');
          const safeSrc = (b.source_url || '').replace(/'/g, "\\'");
          const badgeHtml = isWeb
            ? '<span style="background:rgba(228,92,101,0.18); color:#e45c65; padding:1px 6px; border-radius:4px; font-size:0.7rem; font-weight:600;">ONLINE</span>'
            : '<span style="background:rgba(74,222,128,0.15); color:#4ade80; padding:1px 6px; border-radius:4px; font-size:0.7rem; font-weight:600;">EPUB</span>';

          return `
            <div class="nr-book-item"
                 data-book-id="${b.id}"
                 onclick="onShelfBookClick(event, '${b.id}')"
                 ontouchstart="onShelfBookTouchStart(event, '${b.id}', '${safeTitle}', '${safeAuthor}', ${isWeb ? 'true' : 'false'}, '${safeSrc}')"
                 ontouchmove="onShelfBookTouchMove(event)"
                 ontouchend="onShelfBookTouchEnd(event)"
                 oncontextmenu="onShelfBookContextMenu(event, '${b.id}', '${safeTitle}', '${safeAuthor}', ${isWeb ? 'true' : 'false'}, '${safeSrc}')">
              <div class="nr-book-cover">
                ${isWeb ? '🌐' : '📖'}
              </div>
              <div class="nr-book-details">
                <div class="nr-book-title">${displayTitle}</div>
                <div class="nr-book-sub">
                  ${badgeHtml}
                  <span>${b.chapters_count || b.totalChapters || 1} chương</span>
                  <span>•</span>
                  <span>${b.author || 'Tác giả'}</span>
                </div>
              </div>
              <button class="nr-book-del-btn" onclick="event.stopPropagation(); confirmDeleteNrBook('${b.id}', '${safeTitle}');" title="Xoá sách">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
              </button>
            </div>`;
        }).join('');
      } catch (e) {
        container.innerHTML = `<div style="text-align:center; padding:20px; color:#e45c65;">Lỗi kết nối tủ sách: ${e.message}</div>`;
      }
    }

    function filterNrShelf(filter, btn) {
      nrShelfFilter = filter;
      document.querySelectorAll('.nr-shelf-tab').forEach(b => b.classList.remove('active'));
      if (btn) btn.classList.add('active');
      loadNrBookshelf();
    }

    function isValidChapterContent(ch) {
      if (!ch || !Array.isArray(ch.paragraphs) || ch.paragraphs.length === 0) return false;
      const totalChars = ch.paragraphs.reduce((sum, p) => sum + (typeof p === 'string' ? p.trim().length : 0), 0);
      if (ch.paragraphs.length < 3 && totalChars < 120) return false;
      if (totalChars < 50) return false;
      return true;
    }

    window.submitNrWebUrlFromSrc = function(url) {
      const title = (bookData && bookData.title) ? bookData.title : '';
      const author = (bookData && bookData.author) ? bookData.author : '';
      submitNrWebUrl(url, title, author);
    };

    async function loadNrBookById(bookId) {
      showToast('Đang mở sách...');
      try {
        const res = await fetch('/api/books/' + bookId);
        const data = await res.json();
        if (data && data.chapters && data.chapters.length > 0) {
          const chLen = Array.isArray(data.chapters) ? data.chapters.length : 1;
          const targetCh = Math.min(Math.max(0, data.lastChapter || 0), Math.max(0, chLen - 1));
          const targetPara = data.lastParagraph || 0;
          const curCh = data.chapters[targetCh];

          // Nếu là truyện web mà chương bị rỗng nội dung hoặc chỉ có từ giả (do lỗi cào cũ), tự động cào lại!
          if (data.is_web && data.source_url && (!curCh || !isValidChapterContent(curCh))) {
            showToast('🔄 Nội dung đang thiếu hoặc lỗi chữ, đang tự động nạp lại từ web...');
            const pInput = document.getElementById('nrWebUrlInput');
            if (pInput) pInput.value = data.source_url;
            await submitNrWebUrl(data.source_url, data.title, data.author);
            return;
          }

          // Chuẩn hóa và lọc sạch tiêu đề chương nếu bị lặp từ
          data.chapters.forEach((ch, idx) => {
            if (!ch.title || ch.title.length > 80 || (ch.title.match(/chương/gi) || []).length > 2) {
              ch.title = `Chương ${idx + 1}`;
            }
          });

          bookData = data;
          if (typeof renderDrawerChapters === 'function') {
            renderDrawerChapters();
          }
          if (document.getElementById('bookMetaInfo')) {
            document.getElementById('bookMetaInfo').textContent = `${data.title} - ${data.author || 'Tác giả'}`;
          }
          if (typeof loadChapter === 'function') {
            loadChapter(targetCh, targetPara, true);
          }
          updateNrPlayerUI();
          switchNrTab('reader');
        } else {
          showToast('❌ Không thể nạp dữ liệu cuốn sách này');
        }
      } catch (e) {
        showToast('❌ Lỗi khi tải sách: ' + e.message);
      }
    }

    function onNrSpeedChange(val) {
      const num = parseFloat(val);
      document.getElementById('nrSpeedVal').textContent = num.toFixed(2).replace('.', ',');
      const min = 0.5, max = 3.0;
      const pct = ((num - min) / (max - min)) * 100;
      document.getElementById('nrSpeedFill').style.width = pct + '%';
      if (typeof window.setVoiceSpeed === 'function') {
        window.setVoiceSpeed(num);
      } else {
        const sInp = document.getElementById('speedSlider');
        if (sInp) {
          sInp.value = num;
          sInp.dispatchEvent(new Event('input'));
        }
      }
    }

    function setNrVoiceType(type) {
      document.getElementById('nrRadioRowGoogle')?.classList.toggle('active', type === 'google');
      document.getElementById('nrRadioRowAi')?.classList.toggle('active', type === 'ai');
      if (type === 'google') {
        showToast('Đã chọn giọng Google cơ bản');
      } else {
        showToast('Đã kích hoạt hệ thống giọng AI đa năng');
      }
    }

    function updateNrSettingsUI() {
      try {
        const curSpd = (typeof currentVoiceSpeed !== 'undefined') ? currentVoiceSpeed : 1.0;
        const spdInput = document.getElementById('nrSpeedSlider');
        if (spdInput) {
          spdInput.value = curSpd;
          onNrSpeedChange(curSpd);
        }

        const eyeActive = (window.eyeTrackingEnabled !== false);
        const eyeBtn = document.getElementById('nrEyeToggleBtn');
        if (eyeBtn) eyeBtn.classList.toggle('active', eyeActive);

        const curFont = document.documentElement.style.getPropertyValue('--reader-font-size') || '18px';
        const fontDisp = document.getElementById('nrFontSizeDisplay');
        if (fontDisp) fontDisp.textContent = curFont;

        const isSepia = document.body.classList.contains('theme-sepia');
        const isLight = document.body.classList.contains('theme-light');
        document.getElementById('nrThemeDarkBtn')?.classList.toggle('active', !isSepia && !isLight);
        document.getElementById('nrThemeSepiaBtn')?.classList.toggle('active', isSepia);
        document.getElementById('nrThemeLightBtn')?.classList.toggle('active', isLight);
      } catch (e) {}
    }

    async function parseNovelClientSideDirect(url, prefTitle = '', prefAuthor = '') {
      try {
        let html = '';
        try {
          const r = await fetch(url);
          if (r.ok) html = await r.text();
        } catch (e) {}
        if (!html) {
          try {
            const proxy = 'https://api.allorigins.win/raw?url=' + encodeURIComponent(url);
            const r2 = await fetch(proxy);
            if (r2.ok) html = await r2.text();
          } catch(e) {}
        }
        if (!html) return null;
        
        const parser = new DOMParser();
        let doc = parser.parseFromString(html, 'text/html');
        
        let contentEl = doc.querySelector('#chapter-content, .chapter-c, .entry-content, .reading-content, div.content-inner, div.content, #content, .content-body, #chapter-c, .reading-detail, .box-chap, #bookContentBody, .chap-content, .txt-content, #chr-content, .chr-c, #vungdoc, .vung-doc, .vungdoc');
        let chapUrl = url;
        
        // Nếu là trang giới thiệu truyện thì tìm link chương 1
        if (!contentEl || contentEl.textContent.trim().length < 50) {
          let ch1Link = doc.querySelector("a[href*='chuong-1.'], a[href*='chuong-1/'], a[href*='chuong-1-'], a[href*='chuong-01'], a[href*='chapter-1'], a[href*='chuong_1'], a[href*='/c1-']");
          if (!ch1Link) {
            for (const a of doc.querySelectorAll('a[href]')) {
              const txt = a.textContent.trim().toLowerCase();
              if (txt.includes('đọc từ đầu') || txt.includes('đọc ngay') || txt.includes('chương 1') || txt.includes('chuong 1')) {
                ch1Link = a;
                break;
              }
            }
          }
          if (ch1Link && ch1Link.getAttribute('href')) {
            const href = ch1Link.getAttribute('href').trim();
            chapUrl = new URL(href, url).href;
            let chHtml = '';
            try {
              const r = await fetch(chapUrl);
              if (r.ok) chHtml = await r.text();
            } catch(e) {}
            if (!chHtml) {
              try {
                const proxy = 'https://api.allorigins.win/raw?url=' + encodeURIComponent(chapUrl);
                const r2 = await fetch(proxy);
                if (r2.ok) chHtml = await r2.text();
              } catch(e) {}
            }
            if (chHtml) {
              doc = parser.parseFromString(chHtml, 'text/html');
              contentEl = doc.querySelector('#chapter-content, .chapter-c, .entry-content, .reading-content, div.content-inner, div.content, #content, .content-body, #chapter-c, .reading-detail, .box-chap, #bookContentBody, .chap-content, .txt-content, #chr-content, .chr-c, #vungdoc, .vung-doc, .vungdoc');
            }
          }
        }
        
        if (!contentEl) return null;
        
        contentEl.querySelectorAll('script, style, ins, iframe, noscript, .ads, .ads-holder').forEach(el => el.remove());
        contentEl.querySelectorAll('br, hr').forEach(el => el.replaceWith('\n'));
        
        const paragraphs = [];
        const pTags = contentEl.querySelectorAll('p, div.line, .paragraph');
        pTags.forEach(p => {
          const t = p.textContent.trim();
          if (t.length > 2 && !t.toLowerCase().includes('quảng cáo') && !t.toLowerCase().includes('tải app')) {
            paragraphs.push(t);
          }
        });
        
        if (paragraphs.length < 3) {
          paragraphs.length = 0;
          const rawText = contentEl.innerText || contentEl.textContent || '';
          const lines = rawText.split('\n');
          lines.forEach(l => {
            const t = l.trim();
            if (t.length > 1 && !t.toLowerCase().includes('quảng cáo') && !t.toLowerCase().includes('tải app')) {
              paragraphs.push(t);
            }
          });
        }
        
        const totalChars = paragraphs.reduce((sum, p) => sum + p.length, 0);
        if (paragraphs.length === 0 || (paragraphs.length < 3 && totalChars < 120) || totalChars < 50) return null;
        
        const stEl = doc.querySelector('a.truyen-title, .story-title, .truyen-title, .rv-full-story-title, .rv-heading-story, .truyen-name, .book-info h1, .book-title, .novel-title, h1.title, h1');
        const finalTitle = prefTitle || (stEl ? stEl.textContent.trim() : 'Truyện Web Online');
        const chEl = doc.querySelector('a.chapter-title, .chapter-title, .chapter-name, .rv-chapt-title, .rv-heading-chapter, h2.chapter-title, .chr-title');
        const finalChapTitle = chEl ? chEl.textContent.trim() : 'Chương 1';
        
        return {
          id: 'web_' + Date.now().toString(16),
          title: finalTitle,
          author: prefAuthor || 'Tác giả Online',
          totalChapters: 1,
          lastChapter: 0,
          lastParagraph: 0,
          is_web: true,
          source_url: chapUrl,
          chapters: [{
            id: 'ch_1',
            title: finalChapTitle,
            paragraphs: paragraphs
          }]
        };
      } catch (e) {
        console.warn('parseNovelClientSideDirect error:', e);
        return null;
      }
    }

    async function submitNrWebUrl(overrideUrl = null, prefTitle = '', prefAuthor = '') {
      const input = document.getElementById('nrWebUrlInput');
      const val = overrideUrl ? overrideUrl.trim() : (input ? input.value.trim() : '');
      if (!val) {
        showToast('Vui lòng nhập tên truyện hoặc dán link truyện!');
        return;
      }

      if (val.startsWith('http://') || val.startsWith('https://')) {
        // 1. Chuyển ngay lập tức sang màn hình đọc (ưu tiên hiển thị trạng thái tải chữ trước)
        switchNrTab('reader');
        
        let reader = document.getElementById('readerContent');
        if (!reader) {
          const sc = document.getElementById('readerScrollArea');
          if (sc) {
            let mc = sc.querySelector('.main-container');
            if (!mc) {
              mc = document.createElement('div');
              mc.className = 'main-container';
              sc.appendChild(mc);
            }
            reader = document.createElement('div');
            reader.id = 'readerContent';
            reader.className = 'reader-content';
            mc.appendChild(reader);
          }
        }
        
        const welcomeEl = document.getElementById('readerEmptyWelcome');
        if (welcomeEl) welcomeEl.style.display = 'none';
        
        const safeTitle = prefTitle || (input ? input.value : '') || 'Truyện Web Online';
        const safeAuthor = prefAuthor || 'Đang kết nối trang web...';
        
        if (document.getElementById('bookMetaInfo')) {
          document.getElementById('bookMetaInfo').textContent = `${safeTitle} - ${safeAuthor}`;
        }
        
        if (reader) {
          reader.innerHTML = `
            <div id="nrWebLoadingBanner" style="display:flex; flex-direction:column; align-items:center; justify-content:center; padding: 48px 20px; text-align:center; min-height: 55vh;">
              <div style="font-size: 3.2rem; margin-bottom: 14px; animation: nrPulse 1.6s infinite ease-in-out;">📖</div>
              <h3 id="nrWebLoadingTitle" style="font-size: 1.25rem; font-weight: 700; color: var(--text-color); margin-bottom: 6px; max-width: 90%;">${safeTitle}</h3>
              <div id="nrWebLoadingAuthor" style="font-size: 0.88rem; color: var(--text-muted); margin-bottom: 22px;">${safeAuthor}</div>
              <div class="spinner" style="width: 32px; height: 32px; border-width: 3px; margin-bottom: 16px;"></div>
              <div id="nrWebLoadingMsg" style="font-size: 0.95rem; color: #2563eb; font-weight: 600; margin-bottom: 6px;">⚡ Đang tải chữ và nội dung chương truyện...</div>
              <div style="font-size: 0.8rem; color: var(--text-muted); max-width: 320px; line-height: 1.4;">Hệ thống đang trích xuất từng đoạn văn để sẵn sàng đọc và phát âm thanh</div>
              <button class="btn" onclick="switchNrTab('home')" style="margin-top: 26px; font-size: 0.84rem; padding: 7px 18px; border: 1px solid rgba(140,140,160,0.3); border-radius: 20px;">
                ⬅️ Quay lại tìm kiếm
              </button>
            </div>
          `;
        }

        const updateLoadingMsg = (msg) => {
          const el = document.getElementById('nrWebLoadingMsg');
          if (el) el.textContent = msg;
        };

        const mainBtn = document.getElementById('nrMainSearchBtn');
        const originalText = mainBtn ? mainBtn.innerHTML : '';
        if (mainBtn) {
          mainBtn.disabled = true;
          mainBtn.innerHTML = `<span class="spinner" style="width:14px;height:14px;border-width:2px;display:inline-block;vertical-align:middle;margin-right:6px;"></span> Đang nạp...`;
        }

        try {
          const pcServer = localStorage.getItem('honor_pc_server') || 'http://192.168.1.204:5000';
          let data = null;

          // 1. Thử cào bằng server local của điện thoại
          updateLoadingMsg('⚡ Đang trích xuất chữ từ trang web...');
          try {
            const res = await fetch('/api/web-novel/parse', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ url: val })
            });
            if (res.ok) {
              const resJson = await res.json();
              if (resJson && resJson.chapters && resJson.chapters.length > 0 && isValidChapterContent(resJson.chapters[0])) {
                data = resJson;
              }
            }
          } catch (e1) {
            console.warn('Lỗi cào local:', e1);
          }

          // 2. Thử qua PC server
          if (!data) {
            updateLoadingMsg('⚡ Đang kết nối máy chủ máy tính để lấy chữ...');
            try {
              const res2 = await fetch(pcServer + '/api/web-novel/parse', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: val })
              });
              if (res2.ok) {
                const resJson2 = await res2.json();
                if (resJson2 && resJson2.chapters && resJson2.chapters.length > 0 && isValidChapterContent(resJson2.chapters[0])) {
                  data = resJson2;
                }
              }
            } catch (e2) {
              console.warn('Lỗi cào PC server:', e2);
            }
          }

          // 3. Fallback bóc tách trực tiếp client-side
          if (!data) {
            updateLoadingMsg('⚡ Đang bóc tách chữ trực tiếp trên thiết bị...');
            data = await parseNovelClientSideDirect(val, safeTitle, safeAuthor);
          }

          if (data && data.chapters && data.chapters.length > 0 && isValidChapterContent(data.chapters[0])) {
            // Chuẩn hóa và lọc sạch tiêu đề chương nếu bị lặp từ
            data.chapters.forEach((ch, idx) => {
              if (!ch.title || ch.title.length > 80 || (ch.title.match(/chương/gi) || []).length > 2) {
                ch.title = `Chương ${idx + 1}`;
              }
            });
            if (safeTitle && (!data.title || data.title === 'Truyện Web' || data.title.length < 3)) {
              data.title = safeTitle;
            }
            if (safeAuthor && (!data.author || data.author === 'Tác giả Online')) {
              data.author = safeAuthor;
            }

            bookData = data;
            const chLen = Array.isArray(data.chapters) ? data.chapters.length : 1;
            const targetCh = Math.min(Math.max(0, data.lastChapter || 0), Math.max(0, chLen - 1));
            const targetPara = data.lastParagraph || 0;

            if (typeof renderDrawerChapters === 'function') {
              renderDrawerChapters();
            }
            if (document.getElementById('bookMetaInfo')) {
              document.getElementById('bookMetaInfo').textContent = `${data.title} - ${data.author || 'Tác giả'}`;
            }
            if (typeof loadChapter === 'function') {
              loadChapter(targetCh, targetPara, true);
            }
            updateNrPlayerUI();
            showToast(`🎉 Đã tải xong chữ (${data.chapters[0].paragraphs.length} đoạn): ${data.title}`);
            loadNrBookshelf();
            if (input) input.value = '';
          } else {
            // Hiển thị thông báo lỗi ngay trong màn hình đọc
            let curReader = document.getElementById('readerContent');
            if (curReader) {
              const escUrl = val.replace(/"/g, '&quot;');
              const escTitle = (safeTitle || '').replace(/'/g, "\\'");
              const escAuthor = (safeAuthor || '').replace(/'/g, "\\'");
              curReader.innerHTML = `
                <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; padding:50px 20px; text-align:center; min-height:50vh;">
                  <div style="font-size:3rem; margin-bottom:12px;">⚠️</div>
                  <h3 style="font-size:1.15rem; color:#ef4444; margin-bottom:8px;">Chưa tải được nội dung chữ</h3>
                  <p style="font-size:0.85rem; color:var(--text-muted); max-width:360px; line-height:1.5; margin-bottom:22px;">
                    Không thể bóc tách các đoạn văn từ nguồn web này. Có thể liên kết không phải là trang đọc truyện hoặc trang web đang hạn chế truy cập.
                  </p>
                  <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
                    <button class="btn btn-primary" onclick="submitNrWebUrl('${escUrl}', '${escTitle}', '${escAuthor}')" style="font-size:0.85rem; padding:8px 18px;">
                      🔄 Thử tải lại
                    </button>
                    <button class="btn" onclick="switchNrTab('home')" style="font-size:0.85rem; padding:8px 18px;">
                      🔍 Tìm truyện khác
                    </button>
                  </div>
                </div>
              `;
            }
            showToast('❌ Không thể tải truyện từ link này. Vui lòng thử lại!');
          }
        } catch (e) {
          showToast('❌ Lỗi kết nối: ' + e.message);
          let curReader = document.getElementById('readerContent');
          if (curReader) {
            curReader.innerHTML = `
              <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; padding:50px 20px; text-align:center; min-height:50vh;">
                <div style="font-size:3rem; margin-bottom:12px;">❌</div>
                <h3 style="font-size:1.15rem; color:#ef4444; margin-bottom:8px;">Lỗi kết nối tải truyện</h3>
                <p style="font-size:0.85rem; color:var(--text-muted); margin-bottom:20px;">${e.message}</p>
                <button class="btn" onclick="switchNrTab('home')">⬅️ Quay lại</button>
              </div>
            `;
          }
        } finally {
          if (mainBtn) {
            mainBtn.disabled = false;
            mainBtn.innerHTML = originalText;
          }
        }
        return;
      }

      searchWebNovelAcrossSites(val);
    }

    async function searchNovelClientSideDirect(keyword) {
      const q = encodeURIComponent(keyword.trim());
      const results = [];

      // Thử 1: Quét từ API / kho truyện công khai truyenfullmoi
      try {
        const targetUrl = 'https://truyenfullmoi.net/tim-kiem?tukhoa=' + q;
        let html = '';
        try {
          const r = await fetch(targetUrl);
          if (r.ok) html = await r.text();
        } catch(e) {}

        if (!html) {
          try {
            const proxy = 'https://api.allorigins.win/raw?url=' + encodeURIComponent(targetUrl);
            const r2 = await fetch(proxy);
            if (r2.ok) html = await r2.text();
          } catch(e) {}
        }

        if (html) {
          const parser = new DOMParser();
          const doc = parser.parseFromString(html, 'text/html');
          const rows = doc.querySelectorAll('.list-truyen .row');
          rows.forEach((row, i) => {
            if (i >= 15) return;
            const tEl = row.querySelector('h3.truyen-title a');
            const aEl = row.querySelector('.author');
            const chEl = row.querySelector('.text-info a');
            if (tEl && tEl.getAttribute('href')) {
              let bUrl = tEl.getAttribute('href').trim();
              if (bUrl.startsWith('/')) bUrl = 'https://truyenfullmoi.net' + bUrl;
              results.push({
                title: tEl.textContent.trim(),
                url: bUrl,
                site: 'Truyện Full Mới',
                source: 'Truyện Full Mới',
                author: aEl ? aEl.textContent.trim() : 'Nhiều tác giả',
                latest_chapter: chEl ? chEl.textContent.trim() : ''
              });
            }
          });
        }
      } catch(err) {
        console.warn('[searchNovelClientSideDirect] Lỗi:', err);
      }

      // Thử 2: Quét từ truyenhoan nếu chưa có kết quả
      if (results.length === 0) {
        try {
          const targetUrl2 = 'https://truyenhoan.com/tim-kiem/?tukhoa=' + q;
          let html2 = '';
          try {
            const r = await fetch(targetUrl2);
            if (r.ok) html2 = await r.text();
          } catch(e) {}

          if (!html2) {
            try {
              const proxy = 'https://api.allorigins.win/raw?url=' + encodeURIComponent(targetUrl2);
              const r2 = await fetch(proxy);
              if (r2.ok) html2 = await r2.text();
            } catch(e) {}
          }

          if (html2) {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html2, 'text/html');
            const rows = doc.querySelectorAll('.list-truyen .row');
            rows.forEach((row, i) => {
              if (i >= 15) return;
              const tEl = row.querySelector('h3.truyen-title a');
              const aEl = row.querySelector('.author');
              const chEl = row.querySelector('.text-info a');
              if (tEl && tEl.getAttribute('href')) {
                let bUrl = tEl.getAttribute('href').trim();
                if (bUrl.startsWith('/')) bUrl = 'https://truyenhoan.com' + bUrl;
                results.push({
                  title: tEl.textContent.trim(),
                  url: bUrl,
                  site: 'Truyện Hoàn',
                  source: 'Truyện Hoàn',
                  author: aEl ? aEl.textContent.trim() : 'Nhiều tác giả',
                  latest_chapter: chEl ? chEl.textContent.trim() : ''
                });
              }
            });
          }
        } catch(e) {}
      }

      return {
        success: results.length > 0,
        results: results,
        count: results.length
      };
    }

    async function searchWebNovelAcrossSites(keyword) {
      const resultsContainer = document.getElementById('nrSearchResultsContainer');
      const mainBtn = document.getElementById('nrMainSearchBtn');
      const originalText = mainBtn ? mainBtn.innerHTML : '';

      if (resultsContainer) {
        resultsContainer.style.display = 'flex';
        resultsContainer.innerHTML = `
          <div style="text-align:center; padding:18px; color:#8b8d9e; font-size:0.85rem;">
            <div class="spinner" style="width:20px;height:20px;margin:0 auto 8px auto;border-width:2px;"></div>
            Đang quét trên tất cả các trang web hỗ trợ...
          </div>`;
      }

      if (mainBtn) {
        mainBtn.disabled = true;
        mainBtn.innerHTML = `<span class="spinner" style="width:14px;height:14px;border-width:2px;display:inline-block;vertical-align:middle;margin-right:6px;"></span> Đang tìm...`;
      }

      try {
        const pcServer = localStorage.getItem('honor_pc_server') || 'http://192.168.1.204:5000';
        let data = null;

        // 1. Thử gọi API tìm kiếm local
        try {
          const res = await fetch('/api/web-novel/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: keyword, keyword: keyword })
          });
          if (res.ok) {
            const ct = res.headers.get('content-type') || '';
            if (ct.includes('application/json')) {
              data = await res.json();
            }
          }
        } catch (e1) {
          console.warn('Lỗi local search:', e1);
        }

        // 2. Nếu local chưa có hoặc trả về lỗi, gọi sang PC Server
        if (!data || !data.success) {
          try {
            const res2 = await fetch(pcServer + '/api/web-novel/search', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ query: keyword, keyword: keyword })
            });
            if (res2.ok) {
              const ct2 = res2.headers.get('content-type') || '';
              if (ct2.includes('application/json')) {
                data = await res2.json();
              }
            }
          } catch (e2) {
            console.warn('Lỗi PC server search:', e2);
          }
        }

        // 3. Fallback client-side tìm kiếm qua mạng
        if (!data || !data.success || !data.results || data.results.length === 0) {
          data = await searchNovelClientSideDirect(keyword);
        }

        if (data && data.success && data.results && data.results.length > 0) {
          resultsContainer.innerHTML = data.results.map((item, idx) => {
            const safeTitle = item.title.replace(/"/g, '&quot;');
            const safeUrl = item.url.replace(/"/g, '&quot;');
            const safeAuthor = (item.author || '').replace(/'/g, "\\'").replace(/"/g, '&quot;');
            return `
              <div class="nr-search-item" onclick="openSearchResultUrl('${safeUrl}', '${safeTitle}', '${safeAuthor}')">
                <div class="nr-search-item-info">
                  <div class="nr-search-item-title">${safeTitle}</div>
                  <div class="nr-search-item-site">
                    <span class="nr-search-badge">${item.site || 'Website'}</span>
                    ${item.latest_chapter ? `<span>• ${item.latest_chapter}</span>` : ''}
                  </div>
                </div>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color:#e45c65;flex-shrink:0;"><polyline points="9 18 15 12 9 6"/></svg>
              </div>`;
          }).join('');
        } else {
          resultsContainer.innerHTML = `
            <div style="text-align:center; padding:20px 10px; color:#8b8d9e; font-size:0.85rem;">
              Không tìm thấy truyện phù hợp cho "${keyword}".<br>
              <span style="font-size:0.75rem; color:#6c6e7e;">Gợi ý: Thử nhập tên không dấu hoặc dán trực tiếp link truyện vào ô trên.</span>
            </div>`;
        }
      } catch (err) {
        if (resultsContainer) {
          resultsContainer.innerHTML = `<div style="text-align:center; padding:15px; color:#e45c65; font-size:0.82rem;">Lỗi tìm kiếm: ${err.message}</div>`;
        }
      } finally {
        if (mainBtn) {
          mainBtn.disabled = false;
          mainBtn.innerHTML = originalText;
        }
      }
    }

    function openSearchResultUrl(url, title = '', author = '') {
      const input = document.getElementById('nrWebUrlInput');
      if (input) input.value = url;
      submitNrWebUrl(url, title, author);
    }

    function clearNrSearchResults() {
      const resultsContainer = document.getElementById('nrSearchResultsContainer');
      const input = document.getElementById('nrWebUrlInput');
      if (input) input.value = '';
      if (resultsContainer) {
        resultsContainer.innerHTML = '';
        resultsContainer.style.display = 'none';
      }
    }

    // =====================================================================
    // KHỞI TẠO BỘ ĐIỀU KHIỂN & GỬI CỬ CHỈ VUỐT TOUCH SWIPE
    // =====================================================================
    document.addEventListener('DOMContentLoaded', () => {
      // 1. Hook vào updatePlayBtn, highlightActiveParagraph để cập nhật Player
      const origUpdatePlayBtn = window.updatePlayBtn;
      if (typeof origUpdatePlayBtn === 'function') {
        window.updatePlayBtn = function() {
          origUpdatePlayBtn();
          updateNrPlayerUI();
        };
      }

      const origHighlight = window.highlightActiveParagraph;
      if (typeof origHighlight === 'function') {
        window.highlightActiveParagraph = function(idx) {
          origHighlight(idx);
          updateNrPlayerUI();
        };
      }

      // 2. Hook vào nextChapter, prevChapter để cập nhật số chương
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
      };

      // 3. Hook vào renderCurrentChapter
      const origRenderCh = window.renderCurrentChapter;
      if (typeof origRenderCh === 'function') {
        window.renderCurrentChapter = function() {
          origRenderCh();
          updateNrPlayerUI();
          syncNrReaderLayout();
        };
      }

      // 4. Hook vào changeTheme
      const origChangeTheme = window.changeTheme;
      if (typeof origChangeTheme === 'function') {
        window.changeTheme = function(theme) {
          origChangeTheme(theme);
          updateNrSettingsUI();
        };
      }

      // 5. Hook vào updateVoicePickerDisplay
      const origUpdateVoiceDisplay = window.updateVoicePickerDisplay;
      if (typeof origUpdateVoiceDisplay === 'function') {
        window.updateVoicePickerDisplay = function() {
          origUpdateVoiceDisplay();
          updateNrPlayerUI();
        };
      }

      // 6. Hook vào isUIOverlayActive
      const origIsOverlay = window.isUIOverlayActive;
      if (typeof origIsOverlay === 'function') {
        window.isUIOverlayActive = function() {
          const readerView = document.getElementById('nrViewReader');
          if (readerView && readerView.classList.contains('active')) {
            nrCurrentTab = 'reader'; if (typeof initHonorTapZone === 'function') initHonorTapZone();
          }
          const baseActive = origIsOverlay();
          const finalActive = (nrCurrentTab !== 'reader') ? true : baseActive;
          if (window.HonorBridge && typeof window.HonorBridge.setUiOverlayActive === 'function') {
            try { window.HonorBridge.setUiOverlayActive(finalActive); } catch (e) {}
          }
          return finalActive;
        };
      }

      // 7. Cử chỉ vuốt tay ngang (Touch Swipe) chuyển tab Home <-> Shelf <-> Settings mượt mà
      const trackEl = document.getElementById('nrViewPagerTrack');
      if (trackEl) {
        let touchStartX = 0;
        let touchStartY = 0;
        let isSwipingHoriz = false;

        trackEl.addEventListener('touchstart', (e) => {
          if (nrCurrentTab === 'reader') return;
          touchStartX = e.touches[0].clientX;
          touchStartY = e.touches[0].clientY;
          isSwipingHoriz = false;
        }, { passive: true });

        trackEl.addEventListener('touchmove', (e) => {
          if (nrCurrentTab === 'reader') return;
          const dx = e.touches[0].clientX - touchStartX;
          const dy = e.touches[0].clientY - touchStartY;
          if (Math.abs(dx) > Math.abs(dy) + 12 && Math.abs(dx) > 20) {
            isSwipingHoriz = true;
          }
        }, { passive: true });

        trackEl.addEventListener('touchend', (e) => {
          if (nrCurrentTab === 'reader' || !isSwipingHoriz) return;
          const dx = e.changedTouches[0].clientX - touchStartX;
          if (Math.abs(dx) > 48) {
            if (dx < 0) {
              // Vuốt sang trái -> chuyển sang tab tiếp theo
              if (nrCurrentTab === 'home') switchNrTab('shelf');
              else if (nrCurrentTab === 'shelf') switchNrTab('settings');
            } else {
              // Vuốt sang phải -> chuyển về tab trước
              if (nrCurrentTab === 'settings') switchNrTab('shelf');
              else if (nrCurrentTab === 'shelf') switchNrTab('home');
            }
          }
        }, { passive: true });
      }

      // 8. Đảm bảo chạm trên Mini Player / Bottom Nav không bị chặn
      const dockEl = document.getElementById('nrBottomDock');
      if (dockEl) {
        ['touchstart', 'touchmove', 'touchend'].forEach(evt => {
          dockEl.addEventListener(evt, (e) => {
            e.stopPropagation();
          }, { passive: true });
        });
      }

      // Tự động mở sách khi nạp xong file
      const fileInp = document.getElementById('epubFileInput');
      if (fileInp) {
        fileInp.addEventListener('change', () => {
          const checkLoaded = setInterval(() => {
            if (bookData) {
              clearInterval(checkLoaded);
              updateNrPlayerUI();
              switchNrTab('reader');
            }
          }, 400);
          setTimeout(() => clearInterval(checkLoaded), 15000);
        });
      }

      setTimeout(() => {
        switchNrTab('home');
        updateNrPlayerUI();
        loadNrBookshelf();
        if (typeof isUIOverlayActive === 'function') {
          try { isUIOverlayActive(); } catch (e) {}
        }
      }, 300);
    });

    // =====================================================================
    // QUẢN LÝ DANH SÁCH CÂU BỎ QUA (SKIP RULES)
    // =====================================================================
    let skipRules = [];

    function normalizeForCompare(str) {
      return (str || '').replace(/\s+/g, ' ').trim().toLowerCase();
    }

    function isParagraphSkipped(text) {
      if (!text) return true;
      // Tự động bỏ qua câu nếu phát hiện chữ tiếng Hán
      if (/[\u4e00-\u9fff]/.test(text)) return true;
      if (!skipRules || skipRules.length === 0) return false;
      const norm = normalizeForCompare(text);
      return skipRules.some(r => norm === normalizeForCompare(r));
    }

    async function loadSkipRules(bookId = null) {
      try {
        const curId = bookId || (bookData ? bookData.id : null);
        const url = curId ? `/api/skip-rules?bookId=${encodeURIComponent(curId)}` : '/api/skip-rules';
        const res = await fetch(url);
        skipRules = await res.json();
        if (!Array.isArray(skipRules)) skipRules = [];
        updateSkipBadge();
        updateSkippedParagraphsInDOM();
      } catch (e) {
        console.error('Lỗi nạp skip rules:', e);
      }
    }

    function updateSkippedParagraphsInDOM() {
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
    }

    function updateSkipBadge() {
      const b = document.getElementById('skipCountBadge');
      if (b) b.textContent = `(${skipRules.length})`;
      const mob = document.getElementById('skipCountBadgeMobile');
      if (mob) mob.textContent = `(${skipRules.length})`;
      const mb = document.getElementById('modalSkipCount');
      if (mb) mb.textContent = skipRules.length;
    }

    async function saveSkipRulesToServer() {
      try {
        const curId = bookData ? bookData.id : null;
        const res = await fetch('/api/skip-rules', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            bookId: curId,
            rules: skipRules 
          })
        });
        const data = await res.json();
        if (data.rules && Array.isArray(data.rules)) skipRules = data.rules;
        updateSkipBadge();
        if (bookData) {
          loadChapter(currentChapterIndex, currentParagraphIndex);
        }
      } catch (e) {
        alert('Lỗi lưu danh sách bỏ qua: ' + e);
      }
    }

    function addSkipRule(ruleText) {
      const clean = (ruleText || '').trim();
      if (!clean) return;
      const norm = normalizeForCompare(clean);
      if (skipRules.some(r => normalizeForCompare(r) === norm)) {
        showToast(`ℹ️ Câu này đã có trong danh sách bỏ qua của sách!`);
        return;
      }
      skipRules.push(clean);
      saveSkipRulesToServer();
      showToast(`🚫 Đã thêm vào danh sách bỏ qua: "${clean.length > 35 ? clean.substring(0, 35) + '...' : clean}"`);
      renderSkipRulesList();
    }

    function removeSkipRule(ruleText) {
      const norm = normalizeForCompare(ruleText);
      skipRules = skipRules.filter(r => normalizeForCompare(r) !== norm);
      saveSkipRulesToServer();
      showToast(`✅ Đã khôi phục (không còn bỏ qua): "${ruleText.length > 35 ? ruleText.substring(0, 35) + '...' : ruleText}"`);
      renderSkipRulesList();
    }

    function addSkipRuleFromInput() {
      const input = document.getElementById('newSkipInput');
      const val = input.value.trim();
      if (!val) {
        alert('Vui lòng nhập câu muốn bỏ qua!');
        return;
      }
      addSkipRule(val);
      input.value = '';
    }

    function quickAddSample(sampleText) {
      addSkipRule(sampleText);
    }

    function openSkipRulesModal() {
      const scopeBadge = document.getElementById('skipRulesBookScope');
      if (scopeBadge) {
        scopeBadge.textContent = bookData ? `(Sách: ${bookData.title})` : `(Chung)`;
      }
      renderSkipRulesList();
      document.getElementById('skipRulesModalOverlay').classList.add('open');
      setTimeout(() => document.getElementById('newSkipInput').focus(), 100);
    }

    function closeSkipRulesModal(e) {
      if (e && e.target !== e.currentTarget) return;
      document.getElementById('skipRulesModalOverlay').classList.remove('open');
    }

    function renderSkipRulesList() {
      const container = document.getElementById('skipRulesListContainer');
      if (!container) return;
      updateSkipBadge();
      if (skipRules.length === 0) {
        container.innerHTML = '<div style="padding: 20px; text-align: center; color: var(--text-muted); font-size: 0.88rem;">Chưa có câu nào trong danh sách bỏ qua.</div>';
        return;
      }
      container.innerHTML = '';
      skipRules.forEach((rule) => {
        const item = document.createElement('div');
        item.style.cssText = 'display:flex; justify-content:space-between; align-items:center; padding:8px 12px; margin-bottom:6px; border-radius:6px; background:var(--card-bg); border:1px solid var(--border-color); font-size:0.88rem;';
        
        const textSpan = document.createElement('span');
        textSpan.style.cssText = 'font-weight:500; word-break:break-word; margin-right:10px;';
        textSpan.textContent = rule;
        
        const delBtn = document.createElement('button');
        delBtn.className = 'btn';
        delBtn.style.cssText = 'padding:3px 8px; font-size:0.75rem; color:#ef4444; border-color:rgba(239,68,68,0.3);';
        delBtn.textContent = '🗑 Xoá';
        delBtn.onclick = () => removeSkipRule(rule);
        
        item.appendChild(textSpan);
        item.appendChild(delBtn);
        container.appendChild(item);
      });
    }

    // =====================================================================
    // QUẢN LÝ 18 GIỌNG ĐỌC OFFLINE AI (PIPER VITS / SHERPA-ONNX)
    // =====================================================================
    let offlineVoicesData = [];
    let currentOfflineFilter = 'all';
    let demoAudioPlayer = new Audio();
    let playingDemoVoiceId = null;

    function openOfflineVoicesModal() {
      document.getElementById('offlineVoicesModalOverlay').classList.add('open');
      loadOfflineVoicesData();
    }

    function closeOfflineVoicesModal(e) {
      if (e && e.target !== e.currentTarget) return;
      if (demoAudioPlayer) {
        demoAudioPlayer.pause();
        playingDemoVoiceId = null;
      }
      document.getElementById('offlineVoicesModalOverlay').classList.remove('open');
    }

    async function loadOfflineVoicesData() {
      const container = document.getElementById('offlineVoicesListContainer');
      if (!container) return;
      try {
        const res = await fetch('/api/offline_voices');
        offlineVoicesData = await res.json();
        renderOfflineVoicesList();
      } catch (err) {
        container.innerHTML = `<div style="text-align:center; padding:20px; color:#ef4444;">Lỗi kết nối tải danh sách giọng: ${err.message}</div>`;
      }
    }

    function filterOfflineVoices(type, btn) {
      currentOfflineFilter = type;
      document.querySelectorAll('.voice-tab-btn').forEach(b => b.classList.remove('active'));
      if (btn) btn.classList.add('active');
      renderOfflineVoicesList();
    }

    function playOfflineVoiceDemo(voiceId) {
      if (playingDemoVoiceId === voiceId && !demoAudioPlayer.paused) {
        demoAudioPlayer.pause();
        playingDemoVoiceId = null;
        renderOfflineVoicesList();
        return;
      }

      demoAudioPlayer.pause();
      playingDemoVoiceId = voiceId;
      demoAudioPlayer.src = `/api/offline_voices/demo/${voiceId}`;
      demoAudioPlayer.play().catch(e => {
        console.error('Play demo error:', e);
        showToast('⚠️ Không thể phát âm thanh demo');
      });
      renderOfflineVoicesList();

      demoAudioPlayer.onended = () => {
        playingDemoVoiceId = null;
        renderOfflineVoicesList();
      };
    }

    async function downloadOfflineVoice(voiceId) {
      const btn = document.getElementById(`btnDl_${voiceId}`);
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = `⏳ Đang kết nối...`;
      }
      try {
        const res = await fetch('/api/offline_voices/download', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ voice_id: voiceId })
        });
        showToast(`⏳ Đang tải mô hình offline (~63.5 MB)...`);
        pollOfflineVoiceDownload(voiceId);
      } catch (e) {
        alert('Lỗi tải: ' + e);
        loadOfflineVoicesData();
      }
    }

    function pollOfflineVoiceDownload(voiceId) {
      const interval = setInterval(async () => {
        try {
          const res = await fetch('/api/offline_voices');
          const data = await res.json();
          offlineVoicesData = data;
          const v = data.find(x => x.id === voiceId);
          if (v) {
            const btn = document.getElementById(`btnDl_${voiceId}`);
            if (v.is_downloaded) {
              clearInterval(interval);
              showToast(`✅ Đã tải xong giọng "${v.name}"! Bạn có thể chọn đọc ngay.`);
              renderOfflineVoicesList();
              loadVoices(); // Cập nhật dropdown giọng đọc chính
            } else if (v.download_status && v.download_status.startsWith('downloading')) {
              const pct = v.download_status.replace('downloading_', '');
              if (btn) btn.innerHTML = `⏳ ${pct.includes('%') ? pct : 'Đang tải...'}`;
            } else if (v.download_status && v.download_status.startsWith('error')) {
              clearInterval(interval);
              alert('Lỗi tải giọng: ' + v.download_status);
              renderOfflineVoicesList();
            }
          }
        } catch (e) {
          clearInterval(interval);
        }
      }, 1200);
    }

    async function deleteOfflineVoice(voiceId, voiceName) {
      if (!confirm(`Bạn có chắc muốn xóa file mô hình của giọng "${voiceName}" để giải phóng bộ nhớ (~63.5 MB)?`)) return;
      try {
        await fetch('/api/offline_voices/delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ voice_id: voiceId })
        });
        showToast(`🗑️ Đã xóa file giọng "${voiceName}".`);
        loadOfflineVoicesData();
        loadVoices();
      } catch (e) {
        alert('Lỗi xóa: ' + e);
      }
    }

    function selectOfflineVoice(fullId, voiceName) {
      const select = document.getElementById('voiceSelect');
      if (select) {
        select.value = fullId;
        onVoiceChange(fullId);
      }
      showToast(`🎙️ Đã chọn giọng đọc: ${voiceName}`);
      renderOfflineVoicesList();
      closeOfflineVoicesModal();
    }

    function renderOfflineVoicesList() {
      const container = document.getElementById('offlineVoicesListContainer');
      if (!container) return;

      const currentSelectedVoice = localStorage.getItem('reader_saved_voice') || '';

      let filtered = offlineVoicesData;
      if (currentOfflineFilter === 'female') {
        filtered = offlineVoicesData.filter(v => v.gender === 'Nữ');
      } else if (currentOfflineFilter === 'male') {
        filtered = offlineVoicesData.filter(v => v.gender === 'Nam');
      } else if (currentOfflineFilter === 'downloaded') {
        filtered = offlineVoicesData.filter(v => v.is_downloaded);
      }

      if (filtered.length === 0) {
        container.innerHTML = `<div style="text-align:center; padding:30px; color:var(--text-muted); font-size:0.9rem;">
          ${currentOfflineFilter === 'downloaded' ? 'Chưa có giọng nào được tải về máy. Hãy bấm "Tải về" giọng bạn thích!' : 'Không có giọng nào phù hợp.'}
        </div>`;
        return;
      }

      container.innerHTML = filtered.map(v => {
        const isPlaying = (playingDemoVoiceId === v.id);
        const isCurrentActive = (currentSelectedVoice === v.full_id);
        const isDl = v.is_downloaded;
        const isDownloading = v.download_status && v.download_status.startsWith('downloading');

        return `
          <div class="offline-voice-card ${isCurrentActive ? 'is-active-voice' : ''}">
            <div class="voice-info-left">
              <div class="voice-avatar" style="${v.gender === 'Nữ' ? 'background:rgba(236,72,153,0.12); color:#ec4899;' : 'background:rgba(59,130,246,0.12); color:#2563eb;'}">
                ${v.gender === 'Nữ' ? '👩' : '👨'}
              </div>
              <div class="voice-meta">
                <h4>
                  <span>${v.name}</span>
                  <span class="voice-badge-gender">${v.gender} • ${v.accent || 'Bắc'}</span>
                  ${isCurrentActive ? '<span style="font-size:0.72rem; color:#10b981; font-weight:700;">(Đang dùng ⭐)</span>' : ''}
                </h4>
                <p>${v.desc || ''}</p>
              </div>
            </div>

            <div class="voice-actions">
              <!-- Nút nghe thử -->
              <button class="btn" style="padding:2px 6px; font-size:0.66rem; gap:3px; ${isPlaying ? 'background:#d946ef; color:#fff; border-color:#d946ef;' : ''}" onclick="playOfflineVoiceDemo('${v.id}')" title="Nghe đoạn đọc mẫu trực tiếp">
                ${isPlaying ? '⏸️ Dừng' : '▶️ Thử'}
              </button>

              <!-- Trạng thái & Thao tác tải / Chọn -->
              ${isDl ? `
                <button class="btn btn-primary" style="padding:2px 7px; font-size:0.66rem; font-weight:700; background:#10b981; border-color:#10b981;" onclick="selectOfflineVoice('${v.full_id}', '${v.name}')" title="Đặt làm giọng đọc sách">
                  ${isCurrentActive ? 'Đang dùng ⭐' : 'Dùng'}
                </button>
                <button class="btn" style="padding:2px 4px; font-size:0.66rem; color:#ef4444; border-color:rgba(239,68,68,0.3);" onclick="deleteOfflineVoice('${v.id}', '${v.name}')" title="Xóa file mô hình giải phóng bộ nhớ">
                  🗑️
                </button>
              ` : `
                <button id="btnDl_${v.id}" class="btn" style="padding:2px 7px; font-size:0.66rem; font-weight:700; background:rgba(79,70,229,0.1); color:var(--primary); border-color:var(--primary);" onclick="downloadOfflineVoice('${v.id}')" ${isDownloading ? 'disabled' : ''}>
                  ${isDownloading ? '⏳ Đang tải...' : '⬇️ Tải (~63M)'}
                </button>
              `}
            </div>
          </div>
        `;
      }).join('');
    }

    // =====================================================================
    // CONTEXT MENU NHẤN GIỮ / CHUỘT PHẢI ĐOẠN VĂN
    // =====================================================================
    // =====================================================================
    // HỆ THỐNG CHỌN TỪ / CÂU & GÁN ĐỌC TIẾNG ANH (SELECTION TOOLBAR)
    // Cho phép người dùng nhấn giữ chọn từng từ, nhiều từ hoặc cả câu
    // =====================================================================
    let currentSelectedText = '';
    let currentSelectedParaEl = null;
    let isInteractingWithSelToolbar = false;
    let selCheckTimer = null;

    function isWordCharacter(c) {
      if (!c) return false;
      return /[\p{L}\p{N}\-_]/u.test(c);
    }

    // Tự động mở rộng viền chọn ra trọn vẹn từng từ (Word Snapping) để không bị thiếu 1-2 ký tự đầu/cuối
    function expandRangeToWordBoundaries(range) {
      if (!range) return range;
      try {
        // 1. Mở rộng start về đầu từ nếu vị trí chạm nằm giữa từ
        const sNode = range.startContainer;
        if (sNode && sNode.nodeType === Node.TEXT_NODE) {
          const sText = sNode.textContent;
          let sOff = range.startOffset;
          if (sOff > 0 && isWordCharacter(sText[sOff - 1])) {
            while (sOff > 0 && isWordCharacter(sText[sOff - 1])) {
              sOff--;
            }
            range.setStart(sNode, sOff);
          }
        }

        // 2. Mở rộng end về hết từ nếu vị trí nhả chạm nằm giữa từ
        const eNode = range.endContainer;
        if (eNode && eNode.nodeType === Node.TEXT_NODE) {
          const eText = eNode.textContent;
          let eOff = range.endOffset;
          if (eOff < eText.length && (eOff === 0 || isWordCharacter(eText[eOff - 1]) || isWordCharacter(eText[eOff]))) {
            while (eOff < eText.length && isWordCharacter(eText[eOff])) {
              eOff++;
            }
            range.setEnd(eNode, eOff);
          }
        }
      } catch (err) {
        console.warn('Lỗi expandRangeToWordBoundaries:', err);
      }
      return range;
    }

    function getWordRangeAtPoint(x, y) {
      let range = null;
      if (document.caretRangeFromPoint) {
        range = document.caretRangeFromPoint(x, y);
      } else if (document.caretPositionFromPoint) {
        const pos = document.caretPositionFromPoint(x, y);
        if (pos && pos.offsetNode) {
          range = document.createRange();
          range.setStart(pos.offsetNode, pos.offset);
          range.collapse(true);
        }
      }
      if (!range || !range.startContainer) return null;
      let node = range.startContainer;
      let offset = range.startOffset;

      if (node.nodeType === Node.ELEMENT_NODE) {
        if (node.childNodes && node.childNodes.length > 0) {
          const childIdx = Math.min(Math.max(0, offset), node.childNodes.length - 1);
          let targetChild = node.childNodes[childIdx];
          while (targetChild && targetChild.nodeType === Node.ELEMENT_NODE && targetChild.firstChild) {
            targetChild = targetChild.firstChild;
          }
          if (targetChild && targetChild.nodeType === Node.TEXT_NODE) {
            node = targetChild;
            offset = 0;
          }
        }
      }

      if (!node || node.nodeType !== Node.TEXT_NODE) {
        const el = document.elementFromPoint(x, y);
        if (el) {
          const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, null, false);
          const firstText = walker.nextNode();
          if (firstText) {
            node = firstText;
            offset = 0;
          }
        }
      }

      if (!node || node.nodeType !== Node.TEXT_NODE) return null;
      const text = node.textContent;
      if (!text) return null;

      let start = Math.min(offset, text.length);
      while (start > 0 && isWordCharacter(text[start - 1])) {
        start--;
      }
      let end = Math.min(offset, text.length);
      while (end < text.length && isWordCharacter(text[end])) {
        end++;
      }

      while (start < end && /^[^\p{L}\p{N}\-_]/u.test(text[start])) start++;
      while (end > start && /[^\p{L}\p{N}\-_]$/u.test(text[end - 1])) end--;

      if (start < end) {
        const wordRange = document.createRange();
        wordRange.setStart(node, start);
        wordRange.setEnd(node, end);
        return wordRange;
      }
      return null;
    }

    function showTextSelectionToolbar(rect, text, paraEl) {
      const bar = document.getElementById('textSelectionToolbar');
      if (!bar) return;
      currentSelectedText = text;
      currentSelectedParaEl = paraEl;

      const preview = document.getElementById('selToolbarPreview');
      if (preview) {
        const display = text.length > 24 ? text.substring(0, 24) + '...' : text;
        preview.textContent = `"${display}"`;
      }

      bar.style.display = 'flex';
      const barRect = bar.getBoundingClientRect();

      let left = rect.left + (rect.width / 2) - (barRect.width / 2);
      let top = rect.top - barRect.height - 10;

      if (top < 10) {
        top = rect.bottom + 10;
      }
      if (top + barRect.height > window.innerHeight - 10) {
        top = Math.max(10, window.innerHeight - barRect.height - 10);
      }
      if (left < 10) left = 10;
      if (left + barRect.width > window.innerWidth - 10) {
        left = Math.max(10, window.innerWidth - barRect.width - 10);
      }

      bar.style.left = left + 'px';
      bar.style.top = top + 'px';
    }

    function hideTextSelectionToolbar() {
      const bar = document.getElementById('textSelectionToolbar');
      if (bar) bar.style.display = 'none';
      currentSelectedText = '';
    }

    function dismissSelectionToolbar() {
      hideTextSelectionToolbar();
      hideContextMenu();
      try {
        const sel = window.getSelection();
        if (sel) sel.removeAllRanges();
      } catch (e) {}
    }

    async function markSelectionAsEnglish(openModalForCustomPhonetic = false) {
      let text = currentSelectedText;
      if (!text) {
        const sel = window.getSelection();
        if (sel) text = sel.toString().trim();
      }
      if (!text) {
        showToast('⚠️ Vui lòng chọn từ hoặc cụm từ trước!');
        return;
      }

      if (openModalForCustomPhonetic) {
        hideTextSelectionToolbar();
        openBilingualModal();
        const wordInput = document.getElementById('newEnglishWordInput');
        const phInput = document.getElementById('newEnglishPhoneticInput');
        if (wordInput) wordInput.value = text;
        if (phInput) {
          phInput.value = '';
          setTimeout(() => phInput.focus(), 250);
        }
        return;
      }

      try {
        const res = await fetch('/api/custom-english-words', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ word: text, phonetic: '', desc: 'Thao tác chọn từ' })
        });
        const data = await res.json();
        if (data.success) {
          showToast(`✅ Đã lưu "${text}" vào danh sách đọc tiếng Anh!`);
          fetchCustomEnglishWords();
          dismissSelectionToolbar();

          // Nếu câu này đang phát, phát lại ngay với phát âm tiếng Anh mới
          if (isPlaying && currentSelectedParaEl) {
            const pIdx = parseInt(currentSelectedParaEl.dataset.index);
            if (!isNaN(pIdx) && pIdx === currentParagraphIndex) {
              currentPlaybackSessionId++;
              if (audio) { audio.pause(); audio.onended = null; }
              playParagraph(pIdx);
            }
          }
        } else {
          showToast('❌ ' + (data.error || 'Không thể lưu từ'));
        }
      } catch (err) {
        console.error('Lỗi lưu từ tiếng Anh:', err);
        showToast('❌ Lỗi kết nối máy chủ');
      }
    }

    function expandSelectionToSentence() {
      if (!currentSelectedParaEl) {
        const sel = window.getSelection();
        if (sel && sel.anchorNode) {
          const p = (sel.anchorNode.nodeType === Node.TEXT_NODE ? sel.anchorNode.parentElement : sel.anchorNode).closest('.paragraph-item');
          if (p) currentSelectedParaEl = p;
        }
      }
      if (!currentSelectedParaEl) return;

      const sel = window.getSelection();
      const range = document.createRange();
      range.selectNodeContents(currentSelectedParaEl);
      sel.removeAllRanges();
      sel.addRange(range);

      const text = currentSelectedParaEl.textContent.trim();
      const rect = range.getBoundingClientRect();
      showTextSelectionToolbar(rect, text, currentSelectedParaEl);
    }

    function previewSelectionEnglishAudio() {
      let text = currentSelectedText;
      if (!text) {
        const sel = window.getSelection();
        if (sel) text = sel.toString().trim();
      }
      if (!text) return;
      speakWithReaderEngine(text);
    }

    function copySelectedText() {
      let text = currentSelectedText;
      if (!text) {
        const sel = window.getSelection();
        if (sel) text = sel.toString().trim();
      }
      if (!text) return;
      navigator.clipboard.writeText(text).then(() => {
        showToast('📋 Đã sao chép văn bản đã chọn!');
      }).catch(() => {
        showToast('📋 Đã sao chép!');
      });
      dismissSelectionToolbar();
    }

    function openContextMenuFromSelection() {
      if (!currentSelectedParaEl) {
        const sel = window.getSelection();
        if (sel && sel.anchorNode) {
          const p = (sel.anchorNode.nodeType === Node.TEXT_NODE ? sel.anchorNode.parentElement : sel.anchorNode).closest('.paragraph-item');
          if (p) currentSelectedParaEl = p;
        }
      }
      if (!currentSelectedParaEl) return;
      const pIdx = parseInt(currentSelectedParaEl.dataset.index);
      const text = currentSelectedParaEl.textContent;
      const rect = currentSelectedParaEl.getBoundingClientRect();
      dismissSelectionToolbar();
      showContextMenu(rect.left + 20, rect.top + 20, text, pIdx, true);
    }

    // =====================================================================
    // TÍCH HỢP TỪ ĐIỂN & DỊCH THUẬT OFFLINE DICTIONARY (132K từ & AI NMT)
    // =====================================================================
    let currentDictData = null;
    let currentDictWord = '';
    let dictAudioPlayer = null;

    function isVietnameseText(text) {
      if (!text) return false;
      const str = text.trim();
      if (/[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđĐ]/i.test(str)) {
        return true;
      }
      if (/[\u4e00-\u9fa5\u3040-\u30ff\uac00-\ud7af\u0400-\u04ff\u0e00-\u0e7f\u0600-\u06ff]/.test(str)) {
        return false;
      }
      const vnCommonUnaccented = new Set([
        'toi', 'tao', 'minh', 'chung', 'anh', 'em', 'chi', 'co', 'ong', 'ba', 'bac',
        'con', 'chau', 'la', 'va', 'cua', 'trong', 'tren', 'duoi', 'cho', 'voi', 've',
        'khong', 'chua', 'da', 'dang', 'se', 'nhung', 'ma', 'neu', 'vi', 'thi', 'nguoi',
        'ngay', 'thang', 'nam', 'sach', 'doc', 'viet', 'hoc', 'di', 'den', 'lam', 'an',
        'uong', 'ngu', 'choi', 'tot', 'xau', 'dep', 'hay', 'nhieu', 'it', 'cam', 'on',
        'chao', 'buoi', 'sang', 'chieu', 'toi', 'tam', 'biet', 'xin', 'loi', 'hen', 'gap',
        'ban', 'be', 'gia', 'dinh', 'bo', 'me', 'cha', 'nha', 'cua', 'xe', 'duong'
      ]);
      const words = str.toLowerCase().replace(/[.,\/#!$%\^&\*;:{}=\-_`~()?"'’‘“”]/g, ' ').trim().split(/\s+/).filter(Boolean);
      if (words.length > 0) {
        const vnCount = words.filter(w => vnCommonUnaccented.has(w)).length;
        if (vnCount / words.length >= 0.5) return true;
      }
      return false;
    }

    function isEnglishText(text) {
      if (!text) return false;
      const str = text.trim();
      if (isVietnameseText(str)) return false;
      if (/[\u4e00-\u9fa5\u3040-\u30ff\uac00-\ud7af\u0400-\u04ff\u0e00-\u0e7f\u0600-\u06ff]/.test(str)) {
        return false;
      }
      return /^[a-zA-Z0-9\s.,?!'\-_:;()"'’‘“”\/\\#%&@+*]+$/.test(str);
    }

    function openTranslateForSelection() {
      let text = currentSelectedText;
      if (!text) {
        const sel = window.getSelection();
        if (sel) text = sel.toString().trim();
      }
      dismissSelectionToolbar();
      hideContextMenu();
      if (text) lastShownSelectionText = text;
      try {
        const sel = window.getSelection();
        if (sel) sel.removeAllRanges();
      } catch (_) {}
      openTranslateModal(text);
    }

    function openTranslateModal(text = '') {
      hideContextMenu();
      hideTextSelectionToolbar();
      if (text) lastShownSelectionText = text;
      try {
        const sel = window.getSelection();
        if (sel) sel.removeAllRanges();
      } catch (_) {}

      const modal = document.getElementById('translateModalOverlay');
      if (!modal) return;
      modal.classList.add('open');

      const input = document.getElementById('dictSearchInput');
      if (text) {
        if (input) input.value = text;
        const targetSelect = document.getElementById('dictTargetLangSelect');
        if (targetSelect) {
          const isVn = isVietnameseText(text);
          targetSelect.value = isVn ? 'en' : 'vi';
        }
        executeTranslation(false);
      } else {
        if (input) setTimeout(() => input.focus(), 150);
      }
    }

    function closeTranslateModal(e) {
      if (e && e.target && e.target !== document.getElementById('translateModalOverlay')) {
        return;
      }
      const modal = document.getElementById('translateModalOverlay');
      if (modal) modal.classList.remove('open');
      hideContextMenu();
      hideTextSelectionToolbar();
      try {
        const sel = window.getSelection();
        if (sel) sel.removeAllRanges();
      } catch (_) {}
      lastDismissTime = Date.now();
      if (dictAudioPlayer) {
        try { dictAudioPlayer.pause(); } catch(err) {}
      }
    }

    async function executeTranslation(autoDetectLang = true) {
      const input = document.getElementById('dictSearchInput');
      const text = input ? input.value.trim() : '';
      if (!text) {
        showToast('⚠️ Vui lòng nhập từ hoặc câu cần dịch');
        return;
      }

      currentDictWord = text;
      const targetSelect = document.getElementById('dictTargetLangSelect');
      if (autoDetectLang && targetSelect) {
        const isVn = isVietnameseText(text);
        targetSelect.value = isVn ? 'en' : 'vi';
      }

      const mode = document.getElementById('dictModeSelect')?.value || 'auto';
      const targetLang = targetSelect?.value || 'vi';

      const loadingBox = document.getElementById('dictLoadingBox');
      const resultContainer = document.getElementById('dictResultContainer');
      const emptyBox = document.getElementById('dictEmptyBox');

      if (loadingBox) loadingBox.style.display = 'block';
      if (resultContainer) resultContainer.style.display = 'none';
      if (emptyBox) emptyBox.style.display = 'none';

      try {
        const res = await fetch('/api/dictionary/translate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            text: text,
            source_lang: 'auto',
            target_lang: targetLang,
            mode: mode
          })
        });
        const data = await res.json();
        if (loadingBox) loadingBox.style.display = 'none';

        if (data.success) {
          currentDictData = data;
          renderTranslationResult(text, data);
          // Tự động tải trước âm thanh phát âm ở chế độ nền (Pre-fetch audio)
          // để khi người dùng bấm "🔊 Nghe" là phát ra tiếng NGAY LẬP TỨC 0s!
          prefetchDictAudio(text);
          if (data.translated_text) {
            prefetchDictAudio(data.translated_text);
          }
        } else {
          if (emptyBox) {
            emptyBox.style.display = 'block';
            emptyBox.innerHTML = `⚠️ <span style="color:#ef4444;">${data.error || 'Không thể tra cứu hoặc dịch'}</span>`;
          }
        }
      } catch (err) {
        console.error('Lỗi tra từ điển:', err);
        if (loadingBox) loadingBox.style.display = 'none';
        if (emptyBox) {
          emptyBox.style.display = 'block';
          emptyBox.innerHTML = `❌ <span style="color:#ef4444;">Lỗi kết nối máy chủ từ điển: ${err.message}</span>`;
        }
      }
    }

    const dictAudioCache = new Map();
    const dictPrefetchPromises = new Map();

    async function prefetchDictAudio(text) {
      if (!text) return;
      const cleanText = text.trim();
      if (!cleanText || cleanText === '...' || cleanText === '(Không có kết quả dịch)') return;
      if (dictAudioCache.has(cleanText) || dictPrefetchPromises.has(cleanText)) return;

      const isEn = isEnglishText(cleanText);
      const voiceSelect = document.getElementById('voiceSelect');
      const selectedOpt = voiceSelect ? (voiceSelect.options[voiceSelect.selectedIndex] || {}) : {};
      
      let voiceId = isEn ? 'eleven_IRHApOXLvnW57QJPQH2P' : (selectedOpt.value || 'BV074_streaming');
      let provider = isEn ? 'elevenlabs' : (selectedOpt.dataset?.provider || 'capcut');
      const speed = currentSpeed || 1.0;

      const p = (async () => {
        try {
          const res = await fetch('/api/tts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json; charset=utf-8' },
            body: JSON.stringify({
              text: cleanText,
              voice_id: voiceId,
              provider: provider,
              speed: speed,
              bilingual_mode: currentBilingualMode || 'auto'
            })
          });
          if (!res.ok) return;
          const blob = await res.blob();
          if (blob.size > 300) {
            const url = URL.createObjectURL(blob);
            dictAudioCache.set(cleanText, url);
          }
        } catch (_) {} finally {
          dictPrefetchPromises.delete(cleanText);
        }
      })();

      dictPrefetchPromises.set(cleanText, p);
    }

    function renderTranslationResult(originalText, data) {
      const resultContainer = document.getElementById('dictResultContainer');
      const titleEl = document.getElementById('dictWordTitle');
      const ipaEl = document.getElementById('dictWordIpa');
      const shortTransEl = document.getElementById('dictShortTranslation');
      const engineBadge = document.getElementById('dictEngineBadge');
      const detailsWrapper = document.getElementById('dictDetailsWrapper');
      const detailsHtml = document.getElementById('dictDetailsHtml');
      const addEngBtn = document.getElementById('btnDictAddEnglish');
      const btnSpeakSource = document.getElementById('btnDictSpeakSource');
      const btnSpeakTarget = document.getElementById('btnDictSpeakTarget');

      if (titleEl) titleEl.textContent = originalText;
      if (ipaEl) {
        ipaEl.textContent = data.ipa ? `/${data.ipa}/` : '';
      }

      // Cập nhật nhãn nút phát âm: Tiếng Anh hiển thị rõ Adam, Tiếng Việt hiển thị giọng đọc sách
      if (btnSpeakSource) {
        const isSrcEn = isEnglishText(originalText);
        btnSpeakSource.innerHTML = isSrcEn ? '<span>🔊 Nghe gốc (Adam)</span>' : '<span>🔊 Nghe gốc</span>';
        btnSpeakSource.title = isSrcEn ? 'Phát âm tiếng Anh chuẩn bằng giọng Adam (ElevenLabs)' : 'Phát âm từ gốc bằng giọng đọc sách hiện tại';
      }
      if (btnSpeakTarget) {
        const isTgtEn = isEnglishText(data.translated_text || '');
        btnSpeakTarget.innerHTML = isTgtEn ? '<span>🔊 Nghe dịch (Adam)</span>' : '<span>🔊 Nghe dịch</span>';
        btnSpeakTarget.title = isTgtEn ? 'Phát âm bản dịch tiếng Anh bằng giọng Adam (ElevenLabs)' : 'Phát âm bản dịch bằng giọng đọc sách hiện tại';
      }

      // Ẩn/hiện nút "Đọc tiếng Anh" nếu là từ đơn tiếng Anh
      const isSingleEnglishWord = /^[a-zA-Z\s\-]{2,30}$/.test(originalText.trim());
      if (addEngBtn) {
        addEngBtn.style.display = isSingleEnglishWord ? 'inline-block' : 'none';
      }

      if (shortTransEl) {
        shortTransEl.textContent = data.translated_text || '(Không có kết quả dịch)';
      }

      if (engineBadge) {
        if (data.engine === 'offline_dict') {
          engineBadge.textContent = '📚 Từ điển';
          engineBadge.style.color = '#059669';
          engineBadge.style.background = 'rgba(16,185,129,0.12)';
        } else if (data.engine === 'offline_nmt' || data.engine === 'offline_cache') {
          engineBadge.textContent = '💾 Offline';
          engineBadge.style.color = '#2563eb';
          engineBadge.style.background = 'rgba(37,99,235,0.12)';
        } else {
          engineBadge.textContent = '🌐 Online';
          engineBadge.style.color = '#d97706';
          engineBadge.style.background = 'rgba(217,119,6,0.12)';
        }
      }

      // Render chi tiết HTML từ điển (nếu có từ bảng dict_hh.db)
      if (data.dict_details && data.dict_details.html) {
        if (detailsWrapper) detailsWrapper.style.display = 'block';
        if (detailsHtml) detailsHtml.innerHTML = data.dict_details.html;
      } else {
        if (detailsWrapper) detailsWrapper.style.display = 'none';
      }

      if (resultContainer) resultContainer.style.display = 'block';
    }

    async function speakWithReaderEngine(text) {
      if (!text) return;
      const cleanText = text.trim();
      if (!cleanText || cleanText === '...' || cleanText === '(Không có kết quả dịch)') return;

      const speed = currentSpeed || 1.0;

      if (dictAudioPlayer) {
        try { dictAudioPlayer.pause(); } catch(e) {}
      }

      // 1. Nếu đã có trong bộ nhớ đệm pre-fetch -> Phát ngay lập tức 0s!
      if (dictAudioCache.has(cleanText)) {
        try {
          const audioUrl = dictAudioCache.get(cleanText);
          dictAudioPlayer = new Audio(audioUrl);
          dictAudioPlayer.playbackRate = speed;
          await dictAudioPlayer.play();
          return;
        } catch(e) {
          console.warn('Lỗi phát cached audio:', e);
        }
      }

      // 2. Nếu đang tải trước ở nền -> Chờ tải xong và phát ngay
      if (dictPrefetchPromises.has(cleanText)) {
        try {
          await dictPrefetchPromises.get(cleanText);
          if (dictAudioCache.has(cleanText)) {
            const audioUrl = dictAudioCache.get(cleanText);
            dictAudioPlayer = new Audio(audioUrl);
            dictAudioPlayer.playbackRate = speed;
            await dictAudioPlayer.play();
            return;
          }
        } catch(_) {}
      }

      const isEn = isEnglishText(cleanText);
      const voiceSelect = document.getElementById('voiceSelect');
      const selectedOpt = voiceSelect ? (voiceSelect.options[voiceSelect.selectedIndex] || {}) : {};
      
      let voiceId = selectedOpt.value || 'BV074_streaming';
      let provider = selectedOpt.dataset?.provider || 'capcut';

      // Nếu là tiếng Anh -> Mặc định dùng giọng Adam (ElevenLabs)
      if (isEn) {
        voiceId = 'eleven_IRHApOXLvnW57QJPQH2P'; // Adam-Mỹ (ElevenLabs)
        provider = 'elevenlabs';
      }

      const isOfflineVoice = (!isEn && (provider === 'offline' || provider === 'native' || voiceId === 'android_native' || voiceId.startsWith('offline_')));

      // 3. Nếu đọc tiếng Việt bằng giọng máy offline:
      if (isOfflineVoice) {
        if (window.HonorBridge && window.HonorBridge.speakNative) {
          window.HonorBridge.speakNative(cleanText, speed);
          return;
        }
        if ('speechSynthesis' in window) {
          window.speechSynthesis.cancel();
          const utt = new SpeechSynthesisUtterance(cleanText);
          utt.lang = 'vi-VN';
          utt.rate = speed;
          window.speechSynthesis.speak(utt);
          return;
        }
      }

      // 4. Thử phát qua API /api/tts (Hỗ trợ Adam ElevenLabs và toàn bộ các giọng đọc sách)
      try {
        const res = await fetch('/api/tts', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json; charset=utf-8' },
          body: JSON.stringify({
            text: cleanText,
            voice_id: voiceId,
            provider: provider,
            speed: speed,
            bilingual_mode: currentBilingualMode || 'auto'
          })
        });

        if (!res.ok) throw new Error('Lỗi máy chủ TTS: ' + res.status);
        const blob = await res.blob();
        if (blob.size < 300) throw new Error('Dữ liệu audio quá ngắn');

        const audioUrl = URL.createObjectURL(blob);
        dictAudioCache.set(cleanText, audioUrl);
        dictAudioPlayer = new Audio(audioUrl);
        dictAudioPlayer.playbackRate = speed;
        await dictAudioPlayer.play();
        return;
      } catch (err) {
        console.warn('Phát âm qua /api/tts không thành công, thử fallback từ điển:', err);
      }

      // 5. Fallback dự phòng 1: /api/dictionary/tts (Piper offline / Google TTS)
      try {
        const dictFallbackUrl = `/api/dictionary/tts?text=${encodeURIComponent(cleanText)}&lang=${isEn ? 'en' : 'vi'}&speed=${speed}`;
        const dictRes = await fetch(dictFallbackUrl);
        if (dictRes.ok) {
          const dictBlob = await dictRes.blob();
          if (dictBlob.size > 300) {
            const audioUrl = URL.createObjectURL(dictBlob);
            dictAudioCache.set(cleanText, audioUrl);
            dictAudioPlayer = new Audio(audioUrl);
            dictAudioPlayer.playbackRate = speed;
            await dictAudioPlayer.play();
            return;
          }
        }
      } catch (err2) {
        console.warn('Fallback /api/dictionary/tts lỗi:', err2);
      }

      // 6. Fallback dự phòng cuối: Web Speech API của trình duyệt
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const utt = new SpeechSynthesisUtterance(cleanText);
        utt.lang = isEn ? 'en-US' : 'vi-VN';
        utt.rate = speed;
        if (isEn) {
          const voices = window.speechSynthesis.getVoices();
          const enVoice = voices.find(v => v.lang.startsWith('en') || v.name.toLowerCase().includes('english') || v.name.toLowerCase().includes('adam'));
          if (enVoice) utt.voice = enVoice;
        }
        window.speechSynthesis.speak(utt);
      }
    }

    async function playDictAudio(type = 'source') {
      let text = '';
      if (type === 'source') {
        text = currentDictWord || document.getElementById('dictSearchInput')?.value?.trim();
      } else {
        text = currentDictData?.translated_text || document.getElementById('dictShortTranslation')?.textContent?.trim();
      }
      if (!text || text === '...' || text === '(Không có kết quả dịch)') return;

      const btnId = (type === 'source') ? 'btnDictSpeakSource' : 'btnDictSpeakTarget';
      const btn = document.getElementById(btnId);
      const originalHtml = btn ? btn.innerHTML : '';
      if (btn) btn.innerHTML = '<span>⏳ Đang đọc...</span>';

      try {
        await speakWithReaderEngine(text);
      } catch (err) {
        console.warn('Lỗi playDictAudio:', err);
      } finally {
        if (btn) btn.innerHTML = originalHtml;
      }
    }

    function copyDictTranslation() {
      const text = document.getElementById('dictShortTranslation')?.textContent;
      if (text) {
        navigator.clipboard.writeText(text).then(() => {
          showToast('📋 Đã sao chép bản dịch!');
        }).catch(() => {
          showToast('📋 Đã sao chép bản dịch');
        });
      }
    }

    async function addCurrentWordToEnglishList() {
      const word = currentDictWord || document.getElementById('dictSearchInput')?.value?.trim();
      if (!word) return;

      try {
        const res = await fetch('/api/custom-english-words', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ word: word, phonetic: '', desc: 'Thêm từ từ điển Offline' })
        });
        const data = await res.json();
        if (data.success) {
          showToast(`✅ Đã lưu "${word}" vào danh sách đọc tiếng Anh!`);
          fetchCustomEnglishWords();
        } else {
          showToast('❌ ' + (data.error || 'Không thể lưu từ'));
        }
      } catch (err) {
        showToast('❌ Lỗi kết nối');
      }
    }

    // =====================================================================
    // QUẢN LÝ GÓI DỮ LIỆU TỪ ĐIỂN & DỊCH NGOẠI TUYẾN (OFFLINE PACKAGES)
    // =====================================================================
    let dictPackagesData = [];
    let dictProgressInterval = null;

    function openDictPackagesModal() {
      const modal = document.getElementById('dictPackagesModalOverlay');
      if (modal) modal.classList.add('open');
      loadDictPackages();
    }

    function closeDictPackagesModal(e) {
      if (e && e.target !== e.currentTarget) return;
      const modal = document.getElementById('dictPackagesModalOverlay');
      if (modal) modal.classList.remove('open');
      if (dictProgressInterval) {
        clearInterval(dictProgressInterval);
        dictProgressInterval = null;
      }
    }

    async function loadDictPackages() {
      const container = document.getElementById('dictPackagesListContainer');
      if (!container) return;
      try {
        const res = await fetch('/api/dictionary/packages');
        const data = await res.json();
        if (data.success && data.packages) {
          dictPackagesData = data.packages;
          renderDictPackagesList(data.packages);
          if (data.download_state && data.download_state.active) {
            startDictProgressPolling();
          }
        } else {
          container.innerHTML = `<div style="text-align:center; padding:20px; color:#ef4444;">${data.error || 'Không tải được danh sách gói'}</div>`;
        }
      } catch (err) {
        container.innerHTML = `<div style="text-align:center; padding:20px; color:#ef4444;">Lỗi kết nối: ${err.message}</div>`;
      }
    }

    function renderDictPackagesList(packages) {
      const container = document.getElementById('dictPackagesListContainer');
      if (!container) return;

      container.innerHTML = packages.map(pkg => {
        const isInstalled = pkg.installed;
        const icon = pkg.id.includes('dict') ? '📚' : (pkg.id.includes('tts') ? '🔊' : '🧠');
        return `
          <div style="display:flex; justify-content:space-between; align-items:center; gap:12px; padding:12px; border-radius:10px; border:1px solid var(--border-color); background:var(--card-bg);">
            <div style="flex:1; min-width:0;">
              <div style="display:flex; align-items:center; gap:6px; margin-bottom:3px;">
                <span style="font-size:1.05rem;">${icon}</span>
                <span style="font-weight:700; font-size:0.86rem; color:var(--text-color);">${pkg.name}</span>
              </div>
              <div style="font-size:0.75rem; color:var(--text-muted); line-height:1.35; margin-bottom:5px;">
                ${pkg.description}
              </div>
              <div style="font-size:0.72rem; display:flex; gap:10px; align-items:center; flex-wrap:wrap;">
                <span>Dung lượng: <b>${pkg.size}</b></span>
                <span style="color:${isInstalled ? '#059669' : '#d97706'}; font-weight:600;">
                  ${isInstalled ? '● Đã tải về máy (' + pkg.size_on_disk_mb + ' MB)' : '○ Chưa tải'}
                </span>
              </div>
            </div>
            <div style="flex-shrink:0;">
              ${isInstalled ? `
                <button class="btn" style="color:#ef4444; border-color:rgba(239,68,68,0.4); font-size:0.74rem; padding:4px 10px;" onclick="deleteDictPackage('${pkg.id}')">
                  🗑️ Xóa
                </button>
              ` : `
                <button class="btn btn-primary" style="font-size:0.74rem; padding:5px 12px; font-weight:700; background:#059669; border-color:#059669;" onclick="startDictPackageDownload('${pkg.id}')">
                  📥 Tải Về Máy
                </button>
              `}
            </div>
          </div>
        `;
      }).join('');
    }

    async function startDictPackageDownload(packageId) {
      try {
        const res = await fetch('/api/dictionary/download/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ package_id: packageId })
        });
        const data = await res.json();
        if (data.success) {
          startDictProgressPolling();
        } else {
          alert(data.message || 'Không thể bắt đầu tải');
        }
      } catch (err) {
        alert('Lỗi: ' + err.message);
      }
    }

    function startDictProgressPolling() {
      if (dictProgressInterval) clearInterval(dictProgressInterval);
      const box = document.getElementById('dictDownloadProgressBox');
      const msg = document.getElementById('dictDownloadMsg');
      const pct = document.getElementById('dictDownloadPercent');
      const bar = document.getElementById('dictDownloadProgressBar');
      if (box) box.style.display = 'block';

      dictProgressInterval = setInterval(async () => {
        try {
          const res = await fetch('/api/dictionary/download/progress');
          const data = await res.json();
          if (msg) msg.textContent = data.message || 'Đang tải...';
          if (pct) pct.textContent = (data.progress_percent || 0) + '%';
          if (bar) bar.style.width = (data.progress_percent || 0) + '%';

          if (!data.active) {
            clearInterval(dictProgressInterval);
            dictProgressInterval = null;
            setTimeout(() => {
              if (box) box.style.display = 'none';
              loadDictPackages();
            }, 1000);
          }
        } catch (e) {
          console.error('Lỗi kiểm tra tiến trình tải:', e);
        }
      }, 800);
    }

    async function deleteDictPackage(packageId) {
      if (!confirm('Bạn có chắc muốn xóa gói dữ liệu này để giải phóng ổ đĩa?')) return;
      try {
        const res = await fetch('/api/dictionary/packages/delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ package_id: packageId })
        });
        const data = await res.json();
        if (data.success) {
          await loadDictPackages();
        } else {
          alert(data.message || 'Không thể xóa');
        }
      } catch (err) {
        alert('Lỗi: ' + err.message);
      }
    }

    let isGlobalTouchActive = false;
    window.addEventListener('touchstart', () => { isGlobalTouchActive = true; }, { passive: true });
    window.addEventListener('touchend', () => { setTimeout(() => { isGlobalTouchActive = false; }, 100); }, { passive: true });
    window.addEventListener('touchcancel', () => { isGlobalTouchActive = false; }, { passive: true });

    let lastShownSelectionText = '';
    let lastDismissTime = 0;

    function onSelectionChange() {
      // Không tự ý mở menu khi đang kéo chọn chữ để tránh nhấp nháy / lỗi lặp lại
      return;
    }

    document.addEventListener('selectionchange', onSelectionChange);
    document.addEventListener('mouseup', onSelectionChange);
    document.addEventListener('touchend', onSelectionChange);

    // =====================================================================
    // CONTEXT MENU NHẤN GIỮ / CHUỘT PHẢI ĐOẠN VĂN
    // =====================================================================
    let contextMenuTargetText = null;
    let contextMenuTargetIndex = -1;
    let contextMenuSelectedWord = '';
    let lastContextMenuOpenTime = 0;

    function hideContextMenu() {
      const menu = document.getElementById('paraContextMenu');
      if (menu) menu.style.display = 'none';
      contextMenuTargetText = null;
      contextMenuTargetIndex = -1;
      contextMenuSelectedWord = '';
      lastDismissTime = Date.now();
    }

    function showContextMenu(clientX, clientY, text, pIdx, isExplicitLongPress = false) {
      // 1. Tuyệt đối không mở nếu modal dịch hoặc popup khác đang mở
      const transModal = document.getElementById('translateModalOverlay');
      if (transModal && transModal.classList.contains('open')) {
        return;
      }
      const openModal = document.querySelector('.modal-overlay.open, .modal.open, .library-modal.open, .drawer.open');
      if (openModal) {
        return;
      }

      // 2. Chống ghost touch / click nhầm ngay sau khi vừa tắt menu
      if (Date.now() - lastDismissTime < 200) {
        return;
      }

      contextMenuTargetText = text || '';
      contextMenuTargetIndex = (typeof pIdx === 'number') ? pIdx : -1;

      // 3. Nhận diện từ hoặc chuỗi đang được bôi đen / chọn
      const sel = window.getSelection();
      let targetWord = (sel && !sel.isCollapsed) ? sel.toString().trim() : '';

      if (!targetWord && clientX && clientY) {
        const wr = getWordRangeAtPoint(clientX, clientY);
        if (wr) {
          targetWord = wr.toString().trim();
          try {
            if (sel) {
              sel.removeAllRanges();
              sel.addRange(wr);
            }
          } catch (_) {}
        }
      }

      if (!targetWord && text) {
        const m = text.match(/\b[a-zA-Z]+(?:-[a-zA-Z]+)?\b/);
        if (m) targetWord = m[0];
      }
      contextMenuSelectedWord = targetWord;

      const currentSelected = targetWord || (sel && !sel.isCollapsed ? sel.toString().trim() : '') || text;

      // 4. QUY TẮC: Menu chỉ hiện 1 lần lúc chọn.
      // Nếu là cùng 1 từ/câu đã chọn lúc trước VÀ KHÔNG PHẢI là một lần nhấn giữ chủ động mới -> KHÔNG HIỆN LẶP LẠI!
      if (!isExplicitLongPress && currentSelected && currentSelected === lastShownSelectionText) {
        return;
      }

      // Ghi nhận chuỗi hiển thị lần này
      if (currentSelected) {
        lastShownSelectionText = currentSelected;
      }

      const menu = document.getElementById('paraContextMenu');
      if (!menu) return;

      const preview = document.getElementById('contextMenuPreview');
      const skipItem = document.getElementById('menuOptionSkip');
      const skipText = document.getElementById('menuOptionSkipText');
      const enItemText = document.getElementById('menuOptionEnglishWordText');
      const phoneticItem = document.getElementById('menuOptionPhonetic');
      const previewAudioItem = document.getElementById('menuOptionPreviewAudio');
      const copyItemText = document.getElementById('menuOptionCopyText');

      const shortText = text.length > 32 ? text.substring(0, 32) + '...' : text;
      if (preview) {
        preview.textContent = targetWord ? `"${targetWord}"` : `"${shortText}"`;
      }

      if (enItemText) {
        if (targetWord) {
          const displayW = targetWord.length > 20 ? targetWord.substring(0, 20) + '...' : targetWord;
          enItemText.textContent = `🔤 Thêm từ đọc tiếng Anh: "${displayW}"`;
        } else {
          enItemText.textContent = `🔤 Thêm từ đọc tiếng Anh`;
        }
      }

      if (phoneticItem) {
        phoneticItem.style.display = targetWord ? 'flex' : 'none';
      }
      if (previewAudioItem) {
        previewAudioItem.style.display = targetWord ? 'flex' : 'none';
      }
      if (copyItemText) {
        copyItemText.textContent = targetWord ? `📋 Sao chép từ "${targetWord.length > 16 ? targetWord.substring(0, 16) + '...' : targetWord}"` : '📋 Sao chép câu này';
      }

      if (skipItem && skipText) {
        if (isParagraphSkipped(text)) {
          skipItem.className = 'context-menu-item success';
          skipText.textContent = '✅ Khôi phục câu này (không bỏ qua nữa)';
        } else {
          skipItem.className = 'context-menu-item danger';
          skipText.textContent = '🚫 Bỏ qua câu này (không đọc ở mọi chương)';
        }
      }

      lastContextMenuOpenTime = Date.now();
      menu.style.display = 'block';

      // Định vị menu thông minh trong khung hình
      const menuRect = menu.getBoundingClientRect();
      let left = clientX || 20;
      let top = clientY || 50;

      if (left + menuRect.width > window.innerWidth - 10) {
        left = Math.max(10, window.innerWidth - menuRect.width - 15);
      }
      if (top + menuRect.height > window.innerHeight - 10) {
        top = Math.max(10, (clientY || 50) - menuRect.height - 10);
      }
      if (top + menuRect.height > window.innerHeight - 10) {
        top = Math.max(10, window.innerHeight - menuRect.height - 10);
      }
      if (left < 10) left = 10;
      if (top < 10) top = 10;

      menu.style.left = left + 'px';
      menu.style.top = top + 'px';
    }

    function onContextMenuAction(action) {
      const text = contextMenuTargetText;
      const idx = contextMenuTargetIndex;
      const targetW = (contextMenuSelectedWord || (window.getSelection() ? window.getSelection().toString() : '')).trim();

      // 1. TẮT MENU CHUỘT PHẢI & THANH CÔNG CỤ NGAY LẬP TỨC
      hideContextMenu();
      hideTextSelectionToolbar();

      // 2. GHI NHẬN CHUỖI ĐÃ CHỌN ĐỂ KHÔNG TỰ ĐỘNG HIỆN LẠI CHO CÙNG 1 TỪ NÀY
      if (targetW) {
        lastShownSelectionText = targetW;
      } else if (text) {
        lastShownSelectionText = text;
      }

      // 3. XOÁ VÙNG BÔI ĐEN (CLEAR SELECTION) ĐỂ TRÁNH TRÌNH DUYỆT TỰ BẮT LẠI SELECTION VÀ HIỆN LẠI
      try {
        const sel = window.getSelection();
        if (sel) sel.removeAllRanges();
      } catch (_) {}

      if (!text) return;

      if (action === 'toggle_skip') {
        if (isParagraphSkipped(text)) {
          removeSkipRule(text);
        } else {
          addSkipRule(text);
        }
      } else if (action === 'pronounce') {
        openPronounceModal(text);
      } else if (action === 'phonetic') {
        markSelectionAsEnglish(true);
      } else if (action === 'preview_audio') {
        previewSelectionEnglishAudio();
      } else if (action === 'add_english_word') {
        const w = targetW;
        if (w) {
          fetch('/api/custom-english-words', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ word: w, phonetic: '', desc: 'Thêm từ menu ngữ cảnh' })
          }).then(res => res.json()).then(data => {
            if (data.success) {
              showToast(`✅ Đã lưu "${w}" vào danh sách đọc tiếng Anh!`);
              fetchCustomEnglishWords();
              if (isPlaying && idx === currentParagraphIndex) {
                currentPlaybackSessionId++;
                if (audio) { audio.pause(); audio.onended = null; }
                playParagraph(idx);
              }
            } else {
              showToast('❌ Lỗi: ' + (data.error || 'Không thể lưu từ'));
            }
          }).catch(() => showToast('❌ Lỗi kết nối'));
        } else {
          openBilingualModal();
        }
      } else if (action === 'play') {
        jumpToParagraph(idx);
      } else if (action === 'copy') {
        const copyContent = targetW || text;
        navigator.clipboard.writeText(copyContent).then(() => {
          showToast(`📋 Đã sao chép: "${copyContent.length > 20 ? copyContent.substring(0, 20) + '...' : copyContent}"`);
        }).catch(() => {
          showToast('📋 Đã sao chép!');
        });
      } else if (action === 'translate') {
        openTranslateModal(targetW || text);
      }
    }

    // =====================================================================
    // QUẢN LÝ TỪ ĐIỂN PHÁT ÂM (PRONUNCIATION RULES)
    // Sửa các từ bị đọc sai trước khi phát âm
    // =====================================================================
    let pronounceRules = [];

    async function loadPronounceRules() {
      try {
        const res = await fetch('/api/pronunciation-rules');
        pronounceRules = await res.json();
        updatePronounceBadge();
      } catch (e) {
        console.error('Lỗi nạp từ điển phát âm:', e);
      }
    }

    function updatePronounceBadge() {
      const b = document.getElementById('pronounceCountBadge');
      if (b) b.textContent = `(${pronounceRules.length})`;
      const mob = document.getElementById('pronounceCountBadgeMobile');
      if (mob) mob.textContent = `(${pronounceRules.length})`;
      const mb = document.getElementById('modalPronounceCount');
      if (mb) mb.textContent = pronounceRules.length;
    }

    async function savePronounceRulesToServer() {
      try {
        const res = await fetch('/api/pronunciation-rules', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ rules: pronounceRules })
        });
        const data = await res.json();
        if (data.rules) pronounceRules = data.rules;
        updatePronounceBadge();
        showToast('💾 Đã lưu và áp dụng quy tắc phát âm mới!');
        renderPronounceList();
      } catch (e) {
        alert('Lỗi lưu từ điển phát âm: ' + e);
      }
    }

    function addPronounceRule(findWord, replaceWord, matchWord = true) {
      const f = (findWord || '').trim();
      const r = (replaceWord || '').trim();
      if (!f || !r) {
        alert('Vui lòng nhập cả từ gốc và từ đọc thay thế!');
        return;
      }
      const idx = pronounceRules.findIndex(item => item.find.toLowerCase() === f.toLowerCase());
      if (idx >= 0) {
        pronounceRules[idx] = { find: f, replace: r, match_word: matchWord };
      } else {
        pronounceRules.unshift({ find: f, replace: r, match_word: matchWord });
      }
      savePronounceRulesToServer();
    }

    function removePronounceRule(index) {
      if (index >= 0 && index < pronounceRules.length) {
        const removed = pronounceRules.splice(index, 1)[0];
        savePronounceRulesToServer();
        showToast(`🗑 Đã xoá quy tắc: "${removed.find}" ➔ "${removed.replace}"`);
      }
    }

    function addPronounceRuleFromInput() {
      const fInput = document.getElementById('pronounceFindInput');
      const rInput = document.getElementById('pronounceReplaceInput');
      const chk = document.getElementById('pronounceMatchWordCheckbox');
      const fVal = fInput.value.trim();
      const rVal = rInput.value.trim();
      if (!fVal || !rVal) {
        alert('Vui lòng nhập đủ từ gốc và từ thay thế!');
        return;
      }
      addPronounceRule(fVal, rVal, chk.checked);
      fInput.value = '';
      rInput.value = '';
    }

    function quickAddPronounceSample(f, r) {
      addPronounceRule(f, r, true);
    }

    function openPronounceModal(prefillFind = '') {
      renderPronounceList();
      const overlay = document.getElementById('pronounceModalOverlay');
      overlay.classList.add('open');
      const fInput = document.getElementById('pronounceFindInput');
      const rInput = document.getElementById('pronounceReplaceInput');
      if (prefillFind) {
        fInput.value = '';
        fInput.placeholder = `Từ cần sửa trong câu này...`;
        setTimeout(() => fInput.focus(), 100);
      } else {
        fInput.placeholder = 'Ví dụ: boss, lv, PK';
        setTimeout(() => fInput.focus(), 100);
      }
    }

    function closePronounceModal(e) {
      if (e && e.target !== e.currentTarget) return;
      document.getElementById('pronounceModalOverlay').classList.remove('open');
    }

    function renderPronounceList() {
      const container = document.getElementById('pronounceRulesListContainer');
      if (!container) return;
      updatePronounceBadge();
      if (pronounceRules.length === 0) {
        container.innerHTML = '<div style="padding: 20px; text-align: center; color: var(--text-muted); font-size: 0.88rem;">Chưa có từ nào trong từ điển phát âm.</div>';
        return;
      }
      container.innerHTML = '';
      pronounceRules.forEach((rule, idx) => {
        const item = document.createElement('div');
        item.style.cssText = 'display:flex; justify-content:space-between; align-items:center; padding:9px 12px; margin-bottom:6px; border-radius:6px; background:var(--card-bg); border:1px solid var(--border-color); font-size:0.88rem;';
        
        const infoDiv = document.createElement('div');
        infoDiv.innerHTML = `
          <b style="color:var(--primary);">${escapeHtml(rule.find)}</b>
          <span style="color:var(--text-muted); margin: 0 6px;">➔ đọc thành:</span>
          <b style="color:#059669;">${escapeHtml(rule.replace)}</b>
          ${rule.match_word ? '<span style="font-size:0.75rem; color:var(--text-muted); margin-left:6px;">(nguyên từ)</span>' : ''}
        `;
        
        const delBtn = document.createElement('button');
        delBtn.className = 'btn';
        delBtn.style.cssText = 'padding:3px 8px; font-size:0.75rem; color:#ef4444; border-color:rgba(239,68,68,0.3);';
        delBtn.textContent = '🗑 Xoá';
        delBtn.onclick = () => removePronounceRule(idx);
        
        item.appendChild(infoDiv);
        item.appendChild(delBtn);
        container.appendChild(item);
      });
    }

    function escapeHtml(text) {
      return (text || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    // =====================================================================
    // QUẢN LÝ CHẾ ĐỘ ĐỌC SONG NGỮ ANH - VIỆT (BILINGUAL TTS)
    // 'off' (Tắt) | 'native' (Song ngữ bản xứ) | 'phonetic' (Phiên âm thuần Việt)
    // =====================================================================
    let currentBilingualMode = 'off';

    async function loadBilingualMode() {
      try {
        const res = await fetch('/api/bilingual-mode');
        const data = await res.json();
        if (data && data.mode) {
          currentBilingualMode = data.mode;
        }
      } catch (e) {
        currentBilingualMode = localStorage.getItem('bilingual_mode') || 'off';
      }
      updateBilingualUI();
    }

    async function selectBilingualMode(mode) {
      currentBilingualMode = mode;
      localStorage.setItem('bilingual_mode', mode);
      updateBilingualUI();
      try {
        await fetch('/api/bilingual-mode', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ mode: mode })
        });
        const modeLabels = {
          'off': 'Tắt chế độ song ngữ',
          'native': 'Song ngữ bản xứ (Giọng lai Việt - Mỹ)',
          'phonetic': 'Phiên âm thuần Việt (Một giọng đồng nhất)'
        };
        showToast(`🌐 Đã chuyển sang: ${modeLabels[mode] || mode}`);
      } catch (e) {
        console.error('Lỗi lưu bilingual mode:', e);
      }
    }

    function updateBilingualUI() {
      const shortText = currentBilingualMode === 'native' ? 'Bản Xứ' : (currentBilingualMode === 'phonetic' ? 'Phiên Âm' : 'Tắt');
      const badgeColor = currentBilingualMode === 'native' ? '#2563eb' : (currentBilingualMode === 'phonetic' ? '#059669' : 'inherit');

      const mobileText = document.getElementById('bilingualModeStatusText');
      if (mobileText) {
        mobileText.textContent = shortText;
        mobileText.style.color = badgeColor;
      }
      const desktopText = document.getElementById('bilingualModeStatusTextDesktop');
      if (desktopText) {
        desktopText.textContent = shortText;
        desktopText.style.color = badgeColor;
      }

      ['off', 'native', 'phonetic'].forEach(m => {
        const radio = document.getElementById(`bilingualRadio_${m}`);
        const card = document.getElementById(`bilingualCard_${m}`);
        if (radio) radio.checked = (currentBilingualMode === m);
        if (card) {
          if (currentBilingualMode === m) {
            card.style.borderColor = (m === 'native' ? '#2563eb' : (m === 'phonetic' ? '#059669' : 'var(--primary)'));
            card.style.background = (m === 'native' ? 'rgba(37,99,235,0.08)' : (m === 'phonetic' ? 'rgba(5,150,105,0.08)' : 'rgba(79,70,229,0.08)'));
          } else {
            card.style.borderColor = 'var(--border-color)';
            card.style.background = 'var(--bg-color)';
          }
        }
      });
    }

    function openBilingualModal() {
      updateBilingualUI();
      fetchCustomEnglishWords();
      const overlay = document.getElementById('bilingualModalOverlay');
      if (overlay) overlay.classList.add('open');
    }

    function closeBilingualModal(e) {
      if (e && e.target !== e.currentTarget) return;
      const overlay = document.getElementById('bilingualModalOverlay');
      if (overlay) overlay.classList.remove('open');
    }

    // =====================================================================
    // QUẢN LÝ DANH SÁCH TỪ TIẾNG ANH TÙY CHỈNH
    // =====================================================================
    let customEnglishWords = [];

    async function fetchCustomEnglishWords() {
      try {
        const res = await fetch('/api/custom-english-words');
        if (res.ok) {
          customEnglishWords = await res.json();
          renderCustomEnglishWords();
        }
      } catch (e) {
        console.error('Lỗi nạp custom english words:', e);
      }
    }

    function renderCustomEnglishWords() {
      const container = document.getElementById('customWordsListContainer');
      const badge = document.getElementById('customWordsCountBadge');
      if (badge) badge.textContent = `(${customEnglishWords.length})`;
      if (!container) return;

      if (!customEnglishWords || customEnglishWords.length === 0) {
        container.innerHTML = '<div style="font-size:0.75rem; color:var(--text-muted); font-style:italic; padding:6px 2px;">Chưa có từ tùy chỉnh nào. Thêm từ mới ở khung trên!</div>';
        return;
      }

      container.innerHTML = customEnglishWords.map(item => {
        const w = (typeof item === 'object') ? item.word : item;
        const ph = (typeof item === 'object' && item.phonetic) ? ` ➔ ${item.phonetic}` : '';
        const safeW = String(w).replace(/'/g, "\\'");
        return `
          <div style="display:inline-flex; align-items:center; gap:6px; padding:4px 8px; border-radius:6px; background:rgba(37,99,235,0.08); border:1px solid rgba(37,99,235,0.25); font-size:0.76rem; color:var(--text-color);">
            <span style="font-weight:700; color:#2563eb;">${escapeHtml(w)}</span>
            ${ph ? `<span style="color:#059669; font-size:0.72rem;">${escapeHtml(ph)}</span>` : ''}
            <button onclick="deleteCustomEnglishWord('${safeW}')" style="background:none; border:none; cursor:pointer; color:#dc2626; font-size:0.78rem; padding:0 2px; line-height:1; opacity:0.75;" title="Xóa từ này" onmouseover="this.style.opacity='1'" onmouseout="this.style.opacity='0.75'">✕</button>
          </div>
        `;
      }).join('');
    }

    async function addCustomEnglishWord() {
      const wordInput = document.getElementById('newEnglishWordInput');
      const phInput = document.getElementById('newEnglishPhoneticInput');
      if (!wordInput) return;
      const word = wordInput.value.trim();
      const phonetic = phInput ? phInput.value.trim() : '';
      if (!word) {
        showToast('⚠️ Vui lòng nhập từ tiếng Anh cần thêm');
        return;
      }

      try {
        const res = await fetch('/api/custom-english-words', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ word: word, phonetic: phonetic })
        });
        const data = await res.json();
        if (data.success) {
          customEnglishWords = data.words || [];
          renderCustomEnglishWords();
          wordInput.value = '';
          if (phInput) phInput.value = '';
          showToast(`✅ Đã thêm từ "${word}" vào danh sách tiếng Anh!`);
        } else {
          showToast('❌ Lỗi: ' + (data.error || 'Thao tác thất bại'));
        }
      } catch (e) {
        showToast('❌ Lỗi kết nối máy chủ');
      }
    }

    async function deleteCustomEnglishWord(word) {
      try {
        const res = await fetch('/api/custom-english-words/delete', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ word: word })
        });
        const data = await res.json();
        if (data.success) {
          customEnglishWords = data.words || [];
          renderCustomEnglishWords();
          showToast(`🗑️ Đã xóa từ "${word}"`);
        } else {
          showToast('❌ Không thể xóa từ');
        }
      } catch (e) {
        showToast('❌ Lỗi kết nối máy chủ');
      }
    }

    // Tự động ẩn context menu khi chạm ra ngoài hoặc cuộn trang
    document.addEventListener('pointerdown', (e) => {
      if (Date.now() - lastContextMenuOpenTime < 150) return;
      const menu = document.getElementById('paraContextMenu');
      if (menu && menu.style.display !== 'none' && !e.target.closest('#paraContextMenu')) {
        hideContextMenu();
        hideTextSelectionToolbar();
        try {
          const sel = window.getSelection();
          if (sel) {
            sel.removeAllRanges();
          }
        } catch (_) {}
      }
    });
    window.addEventListener('scroll', () => {
      if (isGlobalTouchActive || (Date.now() - lastContextMenuOpenTime < 600)) return;
      hideContextMenu();
      hideTextSelectionToolbar();
    }, true);

    function showToast(msg) {
      // Đã tắt hoàn toàn tất cả thông báo pop-up theo yêu cầu của người dùng
      return;
    }

    // Toggle Drawer Mục Lục Chương
    function toggleChapterDrawer() {
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
    }

    async function manualPreloadWebChapters(count = 50) {
      if (!bookData || !bookData.is_web) return;
      const btn = document.getElementById('btnDrawerFetch50');
      if (btn) {
        btn.disabled = true;
        btn.textContent = '⏳ Đang nạp 50 chương...';
      }
      showToast(`🌐 Đang nạp thêm ${count} chương từ web vào bộ đệm...`);
      try {
        const res = await fetch('/api/web-novel/preload-batch', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ bookId: bookData.id, count: count })
        });
        const data = await res.json();
        if (data.success && data.added > 0) {
          showToast(`🎉 Đã nạp thành công thêm ${data.added} chương mới từ web! Tổng: ${data.totalChapters} chương.`);
          const bRes = await fetch(`/api/books/${bookData.id}`);
          const bData = await bRes.json();
          if (bData && bData.chapters) {
            bookData = bData;
            renderDrawerChapters();
          }
          notifyPreloader();
        } else {
          showToast(data.message || '⚠️ Không thể nạp thêm chương hoặc đã đến chương mới nhất!');
        }
      } catch (e) {
        alert('Lỗi nạp chương: ' + e);
      } finally {
        if (btn) {
          btn.disabled = false;
          btn.textContent = '📥 Tải trước 50 ch. tiếp';
        }
      }
    }

    // Modal Tủ Sách (Lưu tối đa 10 cuốn)
    async function openLibraryModal() {
      await loadLibraryList();
      document.getElementById('libraryModalOverlay').classList.add('open');
    }

    function closeLibraryModal() {
      document.getElementById('libraryModalOverlay').classList.remove('open');
    }

    async function loadLibraryList() {
      const container = document.getElementById('libraryBooksContainer');
      container.innerHTML = '<div style="text-align:center; padding:20px;">Đang tải danh sách...</div>';
      try {
        const res = await fetch('/api/books');
        const books = await res.json();
        updateLibraryCountUI(books.length);

        if (!books || books.length === 0) {
          container.innerHTML = '<div style="text-align:center; padding:40px; color:var(--text-muted);">Chưa có cuốn truyện nào trong tủ sách.<br>Hãy bấm "Nạp thêm file EPUB" bên dưới.</div>';
          return;
        }

        container.innerHTML = '';
        books.forEach((b) => {
          const isCurrent = bookData && bookData.id === b.id;
          const card = document.createElement('div');
          card.className = 'book-card';
          card.innerHTML = `
            <div class="book-card-left">
              <div style="width:40px; height:40px; border-radius:8px; background:${isCurrent ? 'var(--primary)' : (b.is_web ? '#2563eb' : 'var(--border-color)')}; color:#fff; display:flex; align-items:center; justify-content:center; font-weight:bold; font-size:1.1rem;">
                ${b.is_web ? '🌐' : '📖'}
              </div>
              <div class="book-card-info">
                <h4>${escapeHtml(b.title)} ${b.is_web ? '<span style="font-size:0.72rem; background:rgba(37,99,235,0.12); color:#2563eb; border:1px solid rgba(37,99,235,0.3); padding:2px 6px; border-radius:4px; margin-left:6px; font-weight:600;">Web Online</span>' : ''}</h4>
                <p>${escapeHtml(b.author)} • ${b.totalChapters} chương • <strong>Đang đọc: Chương ${(b.lastChapter || 0) + 1}</strong></p>
              </div>
            </div>
            <div style="display:flex; align-items:center; gap:8px;">
              <button class="btn ${isCurrent ? '' : 'btn-primary'}" onclick="selectBookFromLibrary('${b.id}')">
                ${isCurrent ? 'Đang mở' : 'Đọc tiếp'}
              </button>
              <button class="btn" style="color:#ef4444;" onclick="deleteBookFromLibrary('${b.id}', '${escapeHtml(b.title)}')" title="Xoá khỏi tủ sách">
                🗑
              </button>
            </div>
          `;
          container.appendChild(card);
        });
      } catch (err) {
        container.innerHTML = '<div style="color:red; text-align:center;">Lỗi tải tủ sách: ' + err.message + '</div>';
      }
    }

    // Modal Đọc Web Online
    function openWebNovelModal() {
      document.getElementById('webNovelModalOverlay').classList.add('open');
      const box = document.getElementById('webNovelLoadingBox');
      if (box) box.style.display = 'none';
      const btn = document.getElementById('btnSubmitWebNovel');
      if (btn) btn.disabled = false;
      setTimeout(() => {
        const inp = document.getElementById('webNovelUrlInput');
        if (inp) inp.focus();
      }, 100);
    }

    function closeWebNovelModal(e) {
      if (e && e.target !== e.currentTarget) return;
      document.getElementById('webNovelModalOverlay').classList.remove('open');
    }

    function setWebNovelSample(sampleUrl) {
      const inp = document.getElementById('webNovelUrlInput');
      if (inp) inp.value = sampleUrl;
    }

    async function submitWebNovel() {
      const inp = document.getElementById('webNovelUrlInput');
      const url = (inp ? inp.value : '').trim();
      if (!url) {
        alert('Vui lòng nhập hoặc dán đường link truyện!');
        if (inp) inp.focus();
        return;
      }

      const box = document.getElementById('webNovelLoadingBox');
      const statusText = document.getElementById('webNovelStatusText');
      const btn = document.getElementById('btnSubmitWebNovel');

      if (box) box.style.display = 'flex';
      if (statusText) statusText.textContent = 'Đang phân tích website và tải trước 50 chương đầu...';
      if (btn) btn.disabled = true;

      try {
        const res = await fetch('/api/web-novel/parse', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url: url })
        });
        const data = await res.json();
        if (data.error) throw new Error(data.error);

        closeWebNovelModal();
        bookData = data;
        document.getElementById('bookMetaInfo').textContent = `${data.title} - ${data.author}`;
        renderDrawerChapters();

        const chLen = Array.isArray(data.chapters) ? data.chapters.length : 1;
        const targetCh = Math.min(Math.max(0, data.lastChapter || 0), Math.max(0, chLen - 1));
        const targetPara = data.lastParagraph || 0;
        loadChapter(targetCh, targetPara, true);
        showToast(`🎉 Nạp truyện thành công: ${data.title} (${data.totalChapters} chương đã sẵn sàng!)`);

        // Cập nhật số lượng sách trong tủ
        const bRes = await fetch('/api/books');
        const bList = await bRes.json();
        updateLibraryCountUI(bList.length);

        if (inp) inp.value = '';
      } catch (err) {
        alert('Lỗi nạp truyện từ web: ' + err.message);
      } finally {
        if (box) box.style.display = 'none';
        if (btn) btn.disabled = false;
      }
    }

    // Tự động nạp thêm chương từ web khi người đọc gần chạm đáy bộ đệm
    let isFetchingMoreWeb = false;
    async function fetchMoreWebChapters(count = 5) {
      if (!bookData || !bookData.is_web || isFetchingMoreWeb) return 0;
      isFetchingMoreWeb = true;
      try {
        const lastCh = (bookData.chapters && bookData.chapters.length > 0) ? bookData.chapters[bookData.chapters.length - 1] : null;
        const lastUrl = (lastCh && lastCh.next_url) ? lastCh.next_url : (bookData.last_crawl_url || '');
        const res = await fetch('/api/web-novel/fetch-more', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ bookId: bookData.id, count: count, lastUrl: lastUrl })
        });
        const data = await res.json();
        if (data.success && data.added > 0) {
          if (data.newChapters) {
            bookData.chapters.push(...data.newChapters);
          }
          bookData.totalChapters = bookData.chapters.length;
          renderDrawerChapters();
          console.log(`[WebNovel] Đã tải thêm ${data.added} chương mới. Tổng: ${bookData.totalChapters}`);
          return data.added;
        }
      } catch (err) {
        console.error('Lỗi khi fetchMoreWebChapters:', err);
      } finally {
        isFetchingMoreWeb = false;
      }
      return 0;
    }

    async function selectBookFromLibrary(bookId) {
      closeLibraryModal();
      try {
        const res = await fetch(`/api/books/${bookId}`);
        const data = await res.json();
        if (data.error) throw new Error(data.error);

        bookData = data;
        document.getElementById('bookMetaInfo').textContent = `${data.title} - ${data.author}`;
        const chLen = Array.isArray(data.chapters) ? data.chapters.length : 1;
        const targetCh = Math.min(Math.max(0, data.lastChapter || 0), Math.max(0, chLen - 1));
        const targetPara = data.lastParagraph || 0;
        loadChapter(targetCh, targetPara, true);
        loadSkipRules(data.id);
        showToast(`✨ Đã mở: ${data.title} (Chương ${targetCh + 1}, Đoạn ${targetPara + 1})`);
      } catch (err) {
        alert('Lỗi mở sách: ' + err.message);
      }
    }

    async function deleteBookFromLibrary(bookId, title) {
      if (!confirm(`Bạn có chắc muốn xoá "${title}" khỏi tủ sách không?`)) return;
      try {
        await fetch(`/api/books/${bookId}`, { method: 'DELETE' });
        await loadLibraryList();
        if (bookData && bookData.id === bookId) {
          bookData = null;
          document.getElementById('bookMetaInfo').textContent = 'Chưa mở truyện';
          const rc = document.getElementById('readerContent');
          if (rc) {
            rc.innerHTML = `
              <div class="empty-state">
                <div class="empty-dropzone" onclick="document.getElementById('epubFileInput').click()">
                  <h3>Đã xoá truyện. Bấm vào đây để nạp truyện mới hoặc mở từ Tủ Sách!</h3>
                </div>
              </div>`;
          }
          updateProgressBadge();
        }
      } catch (err) {
        alert('Lỗi xoá sách: ' + err.message);
      }
    }

    // Tải danh sách giọng đọc (Kết hợp Giọng Offline AI đã tải & Giọng Online)
    async function loadVoices() {
      try {
        const [resOnline, resOffline] = await Promise.all([
          fetch('/api/voices').then(r => r.json()).catch(() => []),
          fetch('/api/offline_voices').then(r => r.json()).catch(() => [])
        ]);

        voices = resOnline;
        const select = document.getElementById('voiceSelect');
        select.innerHTML = '';
        const savedVoice = localStorage.getItem('reader_saved_voice');

        // 0. Nhóm Giọng Máy (100% Offline)
        const grpNative = document.createElement('optgroup');
        grpNative.label = '📱 Giọng Máy (100% Offline)';
        const optNative = document.createElement('option');
        optNative.value = 'android_native';
        optNative.textContent = '🔊 Giọng Hệ Thống Máy (100% Offline)';
        optNative.dataset.provider = 'native';
        if (savedVoice === 'android_native') {
          optNative.selected = true;
        }
        grpNative.appendChild(optNative);
        select.appendChild(grpNative);

        // 1. Nhóm Giọng Offline AI (Đã tải về máy)
        const downloadedOffline = (resOffline || []).filter(v => v.is_downloaded);
        if (downloadedOffline.length > 0) {
          const grpOffline = document.createElement('optgroup');
          grpOffline.label = '🎙️ Offline AI (Đã tải)';
          downloadedOffline.forEach(v => {
            const opt = document.createElement('option');
            opt.value = v.full_id; // e.g. "offline_banmai"
            opt.textContent = `★ ${v.name} (${v.gender})`;
            opt.dataset.provider = 'offline';
            if (savedVoice && savedVoice === v.full_id) {
              opt.selected = true;
            }
            grpOffline.appendChild(opt);
          });
          select.appendChild(grpOffline);
        }

        // 2. Nhóm Giọng Online (CapCut, ElevenLabs, Edge-TTS)
        const grpOnline = document.createElement('optgroup');
        grpOnline.label = '🌐 Giọng Online';
        (resOnline || []).forEach(v => {
          const opt = document.createElement('option');
          opt.value = v.id;
          let cleanName = (v.name || '').replace(/\s*\((Edge|CapCut|ElevenLabs)\)/gi, '').trim();
          let provLabel = 'Edge';
          if (v.provider === 'capcut') provLabel = 'CapCut';
          else if (v.provider === 'elevenlabs') provLabel = 'ElevenLabs';
          opt.textContent = `${cleanName} (${provLabel})`;
          opt.dataset.provider = v.provider;
          if (savedVoice && savedVoice === v.id) {
            opt.selected = true;
          }
          grpOnline.appendChild(opt);
        });
        select.appendChild(grpOnline);

        // 3. Tùy chọn quản lý & tải thêm
        const optManage = document.createElement('option');
        optManage.value = '__manage_offline__';
        optManage.textContent = '➕ Thêm giọng Offline...';
        select.appendChild(optManage);

        // Đồng bộ giá trị đã lưu hoặc mặc định giọng chuẩn CapCut
        const defaultVoice = savedVoice || 'BV074_streaming';
        select.value = defaultVoice;
        if (!select.value && select.options.length > 0) {
          select.selectedIndex = 0;
        }

        // Cập nhật giao diện nút Custom Picker
        updateVoicePickerDisplay();

        // Nếu modal chọn giọng đang mở thì cập nhật lại danh sách
        const pickerModal = document.getElementById('voicePickerModalOverlay');
        if (pickerModal && pickerModal.classList.contains('open')) {
          renderCustomVoicePickerList();
        }

      } catch (err) {
        console.error('Lỗi nạp giọng:', err);
      }
    }

    function onVoiceChange(val) {
      if (val === '__manage_offline__') {
        openOfflineVoicesModal();
        const saved = localStorage.getItem('reader_saved_voice') || 'BV074_streaming';
        document.getElementById('voiceSelect').value = saved;
        updateVoicePickerDisplay();
        return;
      }
      localStorage.setItem('reader_saved_voice', val);
      updateVoicePickerDisplay();
      notifyPreloader();
    }

    // =====================================================================
    // CUSTOM VOICE PICKER (MODAL THAY THẾ SELECT MẶC ĐỊNH ANDROID)
    // =====================================================================
    function openVoicePickerModal() {
      renderCustomVoicePickerList();
      const modal = document.getElementById('voicePickerModalOverlay');
      if (modal) modal.classList.add('open');
    }

    function closeVoicePickerModal(e) {
      if (e && e.target !== e.currentTarget) return;
      const modal = document.getElementById('voicePickerModalOverlay');
      if (modal) modal.classList.remove('open');
    }

    function selectVoiceFromCustomPicker(val) {
      const select = document.getElementById('voiceSelect');
      if (select) {
        select.value = val;
        onVoiceChange(val);
      }
      updateVoicePickerDisplay();
      closeVoicePickerModal();
    }

    function updateVoicePickerDisplay() {
      const select = document.getElementById('voiceSelect');
      const displaySpan = document.getElementById('voicePickerDisplay');
      if (!select || !displaySpan) return;

      const selectedOpt = select.options[select.selectedIndex];
      if (selectedOpt && selectedOpt.value !== '__manage_offline__') {
        const isOffline = selectedOpt.dataset.provider === 'offline';
        const isElevenLabs = selectedOpt.dataset.provider === 'elevenlabs';
        const icon = isOffline ? '⭐' : (isElevenLabs ? '✨' : '🎙️');
        displaySpan.innerHTML = `${icon} <span style="font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${selectedOpt.textContent}</span>`;
      } else {
        displaySpan.innerHTML = `🎙️ <span>Chọn giọng đọc...</span>`;
      }
    }

    function renderCustomVoicePickerList() {
      const container = document.getElementById('voicePickerList');
      const select = document.getElementById('voiceSelect');
      if (!container || !select) return;

      const currentVal = select.value || localStorage.getItem('reader_saved_voice') || '';
      let html = '';

      const children = Array.from(select.children);
      children.forEach(child => {
        if (child.tagName === 'OPTGROUP') {
          html += `<div class="voice-picker-section-title">${child.label}</div>`;
          Array.from(child.children).forEach(opt => {
            const isSelected = (opt.value === currentVal);
            const isOffline = (opt.dataset.provider === 'offline');
            const isElevenLabs = (opt.dataset.provider === 'elevenlabs');
            const icon = isOffline ? '⭐' : (isElevenLabs ? '✨' : '🌐');
            html += `
              <div class="custom-voice-item ${isSelected ? 'active' : ''}" onclick="selectVoiceFromCustomPicker('${opt.value}')">
                <div style="display: flex; align-items: center; gap: 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                  <span style="font-size: 0.82rem; flex-shrink: 0;">${icon}</span>
                  <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 0.74rem;">${opt.textContent}</span>
                </div>
                <div style="display: flex; align-items: center; gap: 4px; flex-shrink: 0; margin-left: 8px;">
                  ${isSelected ? '<span style="color: var(--primary); font-size: 0.8rem; font-weight: bold;">✔</span>' : ''}
                </div>
              </div>
            `;
          });
        }
      });

      container.innerHTML = html;
    }

    // Chỉnh tốc độ đọc mượt mà bằng thanh trượt
    function onSpeedSliderChange(val) {
      currentSpeed = parseFloat(val);
      const valStr = currentSpeed.toFixed(2) + 'x';
      const speedValEl = document.getElementById('speedValue');
      if (speedValEl) speedValEl.textContent = valStr;
      const speedSliderEl = document.getElementById('speedSlider');
      if (speedSliderEl) speedSliderEl.value = currentSpeed;
      const mobSpeedText = document.getElementById('mobileSpeedText');
      if (mobSpeedText) mobSpeedText.textContent = valStr;
      const mobSpeedSlider = document.getElementById('mobileSpeedSlider');
      if (mobSpeedSlider) mobSpeedSlider.value = currentSpeed;
      const mobDisplay = document.getElementById('mobileSpeedSliderDisplay');
      if (mobDisplay) mobDisplay.textContent = valStr;
      audio.playbackRate = currentSpeed;
      localStorage.setItem('reader_speed', currentSpeed.toString());
      notifyPreloader();
    }

    // Cơ chế tự động đệm trước 30 chương (Sliding Window Preloader)
    async function notifyPreloader(overrideCh = null) {
      if (!bookData) return;
      const chIdx = overrideCh !== null ? overrideCh : currentChapterIndex;
      const voiceSelect = document.getElementById('voiceSelect');
      const selectedOpt = voiceSelect.options[voiceSelect.selectedIndex] || {};
      try {
        await fetch('/api/preload/update', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            bookId: bookData.id,
            chapterIndex: chIdx,
            voiceId: selectedOpt.value || 'BV074_streaming',
            provider: selectedOpt.dataset?.provider || 'capcut',
            speed: currentSpeed,
            windowSize: 30
          })
        });
      } catch (e) {
        console.error('Lỗi thông báo preloader:', e);
      }
    }

    async function togglePreloader() {
      try {
        const res = await fetch('/api/preload/toggle', { method: 'POST' });
        const data = await res.json();
        showToast(data.enabled ? '⚡ Đã BẬT tự động đệm 30 chương tiếp theo!' : '⏸ Đã TẮT tự động đệm 30 chương.');
        pollPreloadStatus();
      } catch (e) {
        alert('Lỗi: ' + e);
      }
    }

    async function pollPreloadStatus() {
      if (!bookData) return;
      try {
        const res = await fetch('/api/preload/status');
        const st = await res.json();
        window.latestPreloadStatus = st;
        const miniBuffer = document.getElementById('nrPlayerBuffer');
        if (miniBuffer && st && st.cachedCount !== undefined) {
          miniBuffer.textContent = `Đệm: ${st.cachedCount}/${st.windowTotal || 30}`;
        }
        const badge = document.getElementById('preloadBadge');
        const statusText = document.getElementById('bufferStatusText');
        
        if (!st.enabled) {
          if (badge) badge.style.display = 'none';
          if (statusText) statusText.textContent = 'Đã tắt';
          return;
        }

        // Tự động đồng bộ số chương nếu preloader tải thêm chương mới từ web
        if (st.totalBookChapters && bookData.chapters && st.totalBookChapters > bookData.chapters.length && bookData.id === st.bookId) {
          fetch(`/api/books/${bookData.id}`)
            .then(r => r.json())
            .then(updated => {
              if (updated && updated.chapters && updated.chapters.length > bookData.chapters.length) {
                bookData.chapters = updated.chapters;
                bookData.totalChapters = updated.chapters.length;
                renderDrawerChapters();
                console.log(`[Sync] Đã tự động cập nhật ${updated.chapters.length} chương`);
              }
            }).catch(() => {});
        }

        const badgeMob = document.getElementById('preloadBadgeMobile');
        if (badgeMob) {
          badgeMob.style.display = 'flex';
          const icon = st.isWorking ? '🔄' : '⚡';
          if (st.isWorking && st.workingChapter !== null) {
            badgeMob.innerHTML = `${icon} Đệm Ch.${st.workingChapter + 1} (${st.workingPara}/${st.totalWorkingParas || '...'}) • <b>${st.cachedCount}/${st.windowTotal}</b> ch.`;
          } else {
            badgeMob.innerHTML = `⚡ Đã đệm: <b>${st.cachedCount}/${st.windowTotal}</b> ch.`;
          }
        }
        if (badge) {
          badge.style.display = 'inline-flex';
          const icon = st.isWorking ? '🔄' : '⚡';
          if (st.isWorking && st.workingChapter !== null) {
            badge.innerHTML = `${icon} Đệm Ch.${st.workingChapter + 1} (${st.workingPara}/${st.totalWorkingParas || '...'}) • <b>${st.cachedCount}/${st.windowTotal}</b> ch.`;
            badge.title = `Đang tải trước câu ${st.workingPara}/${st.totalWorkingParas} của Chương ${st.workingChapter + 1} (Luôn duy trì 30 chương dự trữ)`;
          } else {
            badge.innerHTML = `⚡ Đã đệm: <b>${st.cachedCount}/${st.windowTotal}</b> ch.`;
            badge.title = `Đã đệm đủ 30 chương tiếp theo! Sẵn sàng nghe offline không lo gián đoạn mạng.`;
          }
        }

        if (statusText) {
          if (st.isWorking && st.workingChapter !== null) {
            statusText.textContent = `Ch.${st.workingChapter + 1} [${st.workingPara}/${st.totalWorkingParas || '...'}] (${st.cachedCount}/${st.windowTotal})`;
          } else {
            statusText.textContent = `${st.cachedCount}/${st.windowTotal} đã sẵn sàng`;
          }
        }
      } catch (_) {}
    }

    // Lưu vị trí đọc sách & tạo Snapshot siêu tốc để mở app là hiện ngay (0ms)
    function saveProgress() {
      if (!bookData) return;
      const progress = {
        bookId: bookData.id,
        bookTitle: bookData.title,
        chapterIndex: currentChapterIndex,
        paragraphIndex: currentParagraphIndex,
        chapterTitle: (bookData.chapters && bookData.chapters[currentChapterIndex]?.title) || `Chương ${currentChapterIndex + 1}`,
        updatedAt: new Date().toISOString()
      };

      localStorage.setItem('progress_' + bookData.id, JSON.stringify(progress));
      localStorage.setItem('last_active_book_id', bookData.id);

      // Lưu Quick Resume Snapshot để mở app là hiện ngay lập tức (<20ms)
      try {
        const curCh = bookData.chapters && bookData.chapters[currentChapterIndex];
        if (curCh && curCh.paragraphs && curCh.paragraphs.length > 0) {
          const quickCache = {
            id: bookData.id,
            title: bookData.title,
            author: bookData.author || '',
            chapterIndex: currentChapterIndex,
            paragraphIndex: currentParagraphIndex,
            chapterTitle: curCh.title,
            paragraphs: curCh.paragraphs,
            totalChapters: bookData.chapters.length
          };
          localStorage.setItem('quick_resume_cache', JSON.stringify(quickCache));
        }
      } catch (_) {}

      fetch('/api/progress', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(progress)
      }).catch(() => {});

      updateProgressBadge();
    }

    function updateProgressBadge() {
      const badge = document.getElementById('progressBadge');
      const text = (bookData && bookData.chapters && bookData.chapters.length > 0)
        ? `📍 Chương ${currentChapterIndex + 1} • Đoạn ${currentParagraphIndex + 1}`
        : '📍 Chưa mở truyện';
      if (badge) {
        if (bookData && bookData.chapters && bookData.chapters.length > 0) {
          badge.style.display = 'inline-flex';
          badge.textContent = text;
        } else {
          badge.style.display = 'none';
        }
      }
      const chIndicator = document.getElementById('mobileChapterIndicator');
      if (chIndicator) {
        chIndicator.textContent = (bookData && bookData.chapters && bookData.chapters.length > 0)
          ? `Chương ${currentChapterIndex + 1}`
          : 'Chương 1';
      }
    }

    function scrollParagraphToCenter(activeEl, isInstant = false) {
      if (!activeEl) return;
      const scrollArea = document.getElementById('readerScrollArea') || document.querySelector('main');
      if (scrollArea) {
        const elRect = activeEl.getBoundingClientRect();
        const areaRect = scrollArea.getBoundingClientRect();
        const targetScroll = scrollArea.scrollTop + (elRect.top - areaRect.top) - (areaRect.height / 2) + (elRect.height / 2);
        if (isInstant) {
          scrollArea.scrollTop = targetScroll;
        } else {
          scrollArea.scrollTo({ top: targetScroll, behavior: 'smooth' });
        }
      }
    }

    function scrollToActiveParagraph(isInstant = false) {
      const activeEl = document.getElementById(`sent-${currentSentenceIndex}`) || document.getElementById(`para-${currentParagraphIndex}`);
      if (activeEl) {
        if (typeof scrollSentenceToView === 'function') {
          scrollSentenceToView(activeEl, isInstant);
        } else {
          scrollParagraphToCenter(activeEl, isInstant);
        }
      } else {
        const scrollArea = document.getElementById('readerScrollArea') || document.querySelector('main');
        if (scrollArea) {
          scrollArea.scrollTop = 0;
          scrollArea.scrollLeft = 0;
        }
      }
    }

    // Khởi tạo tự động mở sách và khôi phục vị trí đọc siêu tốc
    async function initAutoResume() {
      // 1. Phục hồi ngay lập tức cài đặt giao diện đồng bộ (0ms)
      const savedTheme = localStorage.getItem('reader_theme') || 'sepia';
      changeTheme(savedTheme);
      const themeSelect = document.getElementById('themeSelect');
      if (themeSelect) themeSelect.value = savedTheme;

      const savedFontSize = localStorage.getItem('reader_font_size');
      if (savedFontSize) {
        currentFontSize = parseInt(savedFontSize);
        const rc = document.getElementById('readerContent');
        if (rc) rc.style.fontSize = currentFontSize + 'px';
      }

      const savedSpeed = localStorage.getItem('reader_speed');
      if (savedSpeed) {
        currentSpeed = parseFloat(savedSpeed);
        const valStr = currentSpeed.toFixed(2) + 'x';
        const speedSlider = document.getElementById('speedSlider');
        if (speedSlider) speedSlider.value = currentSpeed;
        const speedValue = document.getElementById('speedValue');
        if (speedValue) speedValue.textContent = valStr;
        const mobText = document.getElementById('mobileSpeedText');
        if (mobText) mobText.textContent = valStr;
        const mobSlider = document.getElementById('mobileSpeedSlider');
        if (mobSlider) mobSlider.value = currentSpeed;
        const mobDisplay = document.getElementById('mobileSpeedSliderDisplay');
        if (mobDisplay) mobDisplay.textContent = valStr;
        if (audio) audio.playbackRate = currentSpeed;
      }

      // 2. TỐC ĐỘ ÁNH SÁNG: Khôi phục tức thì (<20ms) nội dung chương & vị trí đọc từ cache cục bộ
      let restoredFromQuickCache = false;
      try {
        const quickCacheStr = localStorage.getItem('quick_resume_cache');
        if (quickCacheStr) {
          const qc = JSON.parse(quickCacheStr);
          if (qc && qc.id && Array.isArray(qc.paragraphs) && qc.paragraphs.length > 0) {
            bookData = {
              id: qc.id,
              title: qc.title || 'Đang tải sách...',
              author: qc.author || '',
              chapters: []
            };
            bookData.chapters[qc.chapterIndex || 0] = {
              title: qc.chapterTitle || `Chương ${(qc.chapterIndex || 0) + 1}`,
              paragraphs: qc.paragraphs
            };
            document.getElementById('bookMetaInfo').textContent = `${qc.title} - ${qc.author || ''}`;
            loadChapter(qc.chapterIndex || 0, qc.paragraphIndex || 0, true);
            restoredFromQuickCache = true;
          }
        }
      } catch (e) {
        console.warn('Lỗi khôi phục quick resume cache:', e);
      }

      // 3. Khởi chạy song song không đồng bộ tải sách từ Server và toàn bộ cài đặt phụ
      const lastBookPromise = fetch('/api/last-book').then(r => r.json()).catch(() => null);

      // Tải song song danh sách giọng, luật phiên âm, song ngữ (không làm chậm render chữ)
      Promise.allSettled([
        loadVoices(),
        loadPronounceRules(),
        loadBilingualMode(),
        typeof fetchCustomEnglishWords === 'function' ? fetchCustomEnglishWords() : Promise.resolve()
      ]);

      // 4. Khi dữ liệu sách từ Server hoàn tất
      try {
        let lastBook = await lastBookPromise;

        // Dự phòng: Nếu /api/last-book null, thử lấy theo last_active_book_id đã lưu
        if (!lastBook || !lastBook.chapters) {
          const cachedId = localStorage.getItem('last_active_book_id');
          if (cachedId) {
            try {
              const bRes = await fetch(`/api/books/${cachedId}`);
              const bData = await bRes.json();
              if (bData && bData.chapters) lastBook = bData;
            } catch (_) {}
          }
        }

        if (lastBook && lastBook.chapters && lastBook.chapters.length > 0) {
          const isSameBookAsCache = (bookData && bookData.id === lastBook.id);
          bookData = lastBook;
          document.getElementById('bookMetaInfo').textContent = `${lastBook.title} - ${lastBook.author}`;
          await loadSkipRules(lastBook.id);

          // Kiểm tra xem localStorage có tiến độ mới hơn không
          let targetCh = lastBook.lastChapter || 0;
          let targetPara = lastBook.lastParagraph || 0;

          try {
            const localProgStr = localStorage.getItem('progress_' + lastBook.id);
            if (localProgStr) {
              const localProg = JSON.parse(localProgStr);
              if (localProg && (localProg.chapterIndex > targetCh || (localProg.chapterIndex === targetCh && localProg.paragraphIndex > targetPara))) {
                targetCh = localProg.chapterIndex;
                targetPara = localProg.paragraphIndex;
              }
            }
          } catch (_) {}

          targetCh = Math.min(Math.max(0, targetCh), lastBook.chapters.length - 1);

          if (restoredFromQuickCache && isSameBookAsCache && currentChapterIndex === targetCh && currentParagraphIndex === targetPara) {
            // Đã hiển thị đúng chương & đoạn từ cache -> chỉ cần cập nhật trạng thái skip và báo preloader
            updateSkippedParagraphsInDOM();
            notifyPreloader(targetCh);
          } else {
            loadChapter(targetCh, targetPara, true);
          }
          showToast(`✨ Đã mở: ${lastBook.title} (Chương ${targetCh + 1}, Đoạn ${targetPara + 1})`);
        } else if (!restoredFromQuickCache) {
          document.getElementById('bookMetaInfo').textContent = 'Chưa nạp truyện';
        }
      } catch (err) {
        console.error('Lỗi khi khôi phục vị trí từ server:', err);
      }

      // Cập nhật số lượng sách trong tủ (chạy nền)
      fetch('/api/books')
        .then(r => r.json())
        .then(bList => updateLibraryCountUI(bList.length))
        .catch(() => {});

      // Khởi động đồng bộ bộ đệm
      setInterval(pollPreloadStatus, 2000);
      pollPreloadStatus();

      // Kích hoạt tính năng cuộn con lăn chuyển chương
      initScrollChapterSwitcher();
    }

    // Nạp file EPUB mới vào tủ sách
    document.getElementById('epubFileInput').addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (!file) return;

      const formData = new FormData();
      formData.append('file', file);

      document.getElementById('bookMetaInfo').textContent = 'Đang phân tích tài liệu...';

      try {
        const res = await fetch('/api/parse-epub', { method: 'POST', body: formData });
        const data = await res.json();
        if (data.error) throw new Error(data.error);

        bookData = data;
        document.getElementById('bookMetaInfo').textContent = `${data.title} - ${data.author}`;

        const targetCh = data.lastChapter || 0;
        const targetPara = data.lastParagraph || 0;
        loadChapter(targetCh, targetPara, true);
        showToast(`📚 Đã lưu vào Tủ Sách & mở: Chương ${targetCh + 1}`);

        // Cập nhật badge số lượng sách
        const bRes = await fetch('/api/books');
        const bList = await bRes.json();
        updateLibraryCountUI(bList.length);
        notifyPreloader(targetCh);
      } catch (err) {
        alert('Lỗi nạp sách / tài liệu: ' + err.message);
        document.getElementById('bookMetaInfo').textContent = 'Lỗi nạp file';
      }
    });

    
    // =====================================================================
    // BỘ PHÂN TÍCH TÁCH TỪNG CÂU (SENTENCE-LEVEL PARSER CHUẨN DẤU CHẤM)
    // =====================================================================
    let allSentences = [];
    let sentenceMeta = [];
    let currentSentenceIndex = 0;

    function splitIntoSentences(text) {
      if (!text) return [];
      text = text.trim().replace(/\.{3,}/g, '…');
      if (!text) return [];

      // Tách câu chuẩn xác theo các dấu kết câu . ! ? … \n
      const regex = /([^.!?…\n]+(?:[.!?…]+|[\n]+|$))/g;
      const matches = text.match(regex);
      if (!matches) return [text];

      const sentences = [];
      let buffer = '';

      for (let i = 0; i < matches.length; i++) {
        let part = matches[i].trim();
        if (!part) continue;

        // Tránh tách nhầm số thập phân ví dụ "3." trong "3.14" hoặc "$1." trong "$1.500"
        if (/^\d+\.$/.test(part) || /^\$\d+\.$/.test(part)) {
          buffer += (buffer ? ' ' : '') + part;
          continue;
        }

        if (buffer) {
          part = buffer + ' ' + part;
          buffer = '';
        }

        // Nếu một câu quá dài (> 180 ký tự không có dấu chấm), tách tiếp theo dấu phẩy / chấm phẩy
        if (part.length > 180) {
          const subParts = part.split(/([,;:—]\s+)/);
          let subBuf = '';
          for (const s of subParts) {
            if (subBuf.length + s.length > 140 && subBuf.length > 25) {
              sentences.push(subBuf.trim());
              subBuf = s;
            } else {
              subBuf += s;
            }
          }
          if (subBuf.trim()) sentences.push(subBuf.trim());
        } else {
          sentences.push(part);
        }
      }

      if (buffer.trim()) sentences.push(buffer.trim());
      return sentences.filter(s => s.length > 0);
    }

    let currentPlaybackSessionId = 0;

    function loadChapter(idx, targetParagraph = 0, isInitialJump = false) {
      // Dừng ngay lập tức âm thanh cũ và huỷ mọi request TTS đang chờ của chương trước
      currentPlaybackSessionId++;
      if (audio) {
        audio.pause();
        audio.onended = null;
        audio.src = '';
      }
      if (typeof paragraphAudioCache !== 'undefined') {
        paragraphAudioCache.clear();
      }
      if (typeof paragraphPrefetchInFlight !== 'undefined') {
        paragraphPrefetchInFlight.clear();
      }
      setLoading(false);

      // Failsafe: Giải phóng tuyệt đối trạng thái lật trang & xóa sạch clone cũ
      isPageFlipping = false;
      isChapterTransitioning = false;
      try {
        const strayClone = document.getElementById('pageTurnClone');
        if (strayClone && strayClone.parentNode) {
          strayClone.parentNode.removeChild(strayClone);
        }
      } catch (_) {}

      if (!bookData || !Array.isArray(bookData.chapters) || bookData.chapters.length === 0) {
        console.warn('loadChapter: bookData hoặc chapters chưa sẵn sàng!');
        return;
      }
      idx = Math.min(Math.max(0, idx), bookData.chapters.length - 1);

      nrCurrentTab = 'reader';
      const rv = document.getElementById('nrViewReader');
      if (rv) rv.classList.add('active');
      document.body.classList.add('in-reader-tab');
      currentChapterIndex = idx;
      currentParagraphIndex = targetParagraph;
      currentSentenceIndex = targetParagraph;

      const sc = document.getElementById('readerScrollArea') || document.querySelector('main');
      if (sc) {
        sc.scrollTop = 0;
        sc.scrollLeft = 0;
      }

      const chIndicator = document.getElementById('mobileChapterIndicator');
      if (chIndicator) {
        chIndicator.textContent = `Chương ${idx + 1}`;
      }

      const ch = bookData.chapters[idx];
      if (!ch) return;
      let displayTitle = ch.title || `Chương ${idx + 1}`;
      if (displayTitle.length > 80 || (displayTitle.match(/chương/gi) || []).length > 2) {
        displayTitle = `Chương ${idx + 1}`;
      }
      let reader = document.getElementById('readerContent');
      if (!reader) {
        const sc = document.getElementById('readerScrollArea');
        if (sc) {
          let mc = sc.querySelector('.main-container');
          if (!mc) {
            mc = document.createElement('div');
            mc.className = 'main-container';
            sc.appendChild(mc);
          }
          reader = document.createElement('div');
          reader.id = 'readerContent';
          reader.className = 'reader-content';
          mc.appendChild(reader);
        }
      }
      if (!reader) return;
      reader.innerHTML = `
        <div class="chapter-title-heading">
          <span>${escapeHtml(displayTitle)}</span>
          <div style="display:flex; gap:8px;">
            <button class="btn" style="font-size:0.8rem; padding:4px 10px;" onclick="toggleChapterDrawer()">
              📑 Đổi chương
            </button>
            <button class="btn" style="font-size:0.8rem; padding:4px 10px;" onclick="jumpToParagraph(0)">
              🔄 Đầu chương
            </button>
          </div>
        </div>
      `;

      allSentences = [];
      sentenceMeta = [];

      if (!isValidChapterContent(ch)) {
        const emptyDiv = document.createElement('div');
        emptyDiv.style.cssText = 'text-align:center; padding:40px 16px; color:#8e90a2; font-size:0.95rem;';
        const srcUrl = (bookData && bookData.source_url) ? bookData.source_url.replace(/'/g, "\\'") : '';
        const bTitle = (bookData && bookData.title) ? bookData.title.replace(/'/g, "\\'") : '';
        const bAuthor = (bookData && bookData.author) ? bookData.author.replace(/'/g, "\\'") : '';
        emptyDiv.innerHTML = `
          <div style="margin-bottom:12px; font-size:1.15rem; font-weight:700; color:#e45c65;">⚠️ Chương này chưa có đủ nội dung chữ</div>
          <p style="margin-bottom:18px; color:#a0a2b4; line-height:1.5;">Nội dung bị thiếu hoặc trang web nguồn chưa nạp xong các đoạn văn.</p>
          ${srcUrl ? `
            <button class="btn btn-primary" onclick="submitNrWebUrl('${srcUrl}', '${bTitle}', '${bAuthor}')" style="padding:10px 20px; font-size:0.9rem; font-weight:700;">
              🔄 Tự động cào lại &amp; Sửa chương này
            </button>
          ` : ''}
        `;
        reader.appendChild(emptyDiv);
        return;
      }

      ch.paragraphs.forEach((p, pIdx) => {
        const skipped = isParagraphSkipped(p);
        const div = document.createElement('div');
        div.className = 'paragraph-item' + (skipped ? ' skipped' : '');
        div.id = `para-${pIdx}`;
        div.dataset.index = pIdx;

        const sentList = splitIntoSentences(p);
        if (sentList.length === 0) sentList.push(p);

        sentList.forEach((sentText) => {
          const sIdx = allSentences.length;
          allSentences.push(sentText);
          sentenceMeta.push({ paraIndex: pIdx, text: sentText, id: sIdx });

          const span = document.createElement('span');
          span.className = 'sentence-item' + (sIdx === currentSentenceIndex ? ' active' : '');
          span.id = `sent-${sIdx}`;
          span.dataset.index = sIdx;
          span.dataset.paraIndex = pIdx;
          span.textContent = sentText + ' ';

// Bấm vào câu trong sách không tự ý phát giọng (chuẩn app gốc)

          div.appendChild(span);
        });

        let isLongPress = false;
        let touchStartTime = 0;
        let touchStartX = 0, touchStartY = 0;
        let lastTouchX = 0, lastTouchY = 0;
        let touchSelectionTimer = null;
        let touchSelectionActive = false;
        let touchSelectionStartRange = null;
        let isTouchDown = false;
        let pendingContextMenu = null;

        div.addEventListener('touchstart', (e) => {
          if (e.touches.length !== 1) return;
          const t = e.touches[0];
          touchStartTime = Date.now();
          touchStartX = t.clientX;
          touchStartY = t.clientY;
          lastTouchX = t.clientX;
          lastTouchY = t.clientY;
          isTouchDown = true;
          touchSelectionActive = false;
          touchSelectionStartRange = null;
          pendingContextMenu = null;
          isLongPress = false;
          clearTimeout(touchSelectionTimer);

          touchSelectionTimer = setTimeout(() => {
            touchSelectionActive = true;
            isLongPress = true;
            try { if (navigator.vibrate) navigator.vibrate(25); } catch (_) {}

            let startPointRange = null;
            if (document.caretRangeFromPoint) {
              startPointRange = document.caretRangeFromPoint(touchStartX, touchStartY);
            } else if (document.caretPositionFromPoint) {
              const pos = document.caretPositionFromPoint(touchStartX, touchStartY);
              if (pos && pos.offsetNode) {
                startPointRange = document.createRange();
                startPointRange.setStart(pos.offsetNode, pos.offset);
                startPointRange.collapse(true);
              }
            }

            if (startPointRange && startPointRange.startContainer) {
              touchSelectionStartRange = startPointRange;
              const wr = getWordRangeAtPoint(touchStartX, touchStartY);
              const sel = window.getSelection();
              if (sel) {
                sel.removeAllRanges();
                if (wr) sel.addRange(wr);
                else sel.addRange(startPointRange);
              }
            }
          }, 200);
        }, { passive: false });

        div.addEventListener('touchmove', (e) => {
          if (!isTouchDown || e.touches.length !== 1) return;
          const t = e.touches[0];
          lastTouchX = t.clientX;
          lastTouchY = t.clientY;
          const dist = Math.hypot(t.clientX - touchStartX, t.clientY - touchStartY);

          if (!touchSelectionActive && dist > 15) {
            clearTimeout(touchSelectionTimer);
            return;
          }

          if (touchSelectionActive && touchSelectionStartRange) {
            e.preventDefault();
            let curPointRange = null;
            if (document.caretRangeFromPoint) {
              curPointRange = document.caretRangeFromPoint(t.clientX, t.clientY);
            } else if (document.caretPositionFromPoint) {
              const pos = document.caretPositionFromPoint(t.clientX, t.clientY);
              if (pos && pos.offsetNode) {
                curPointRange = document.createRange();
                curPointRange.setStart(pos.offsetNode, pos.offset);
                curPointRange.collapse(true);
              }
            }

            if (!curPointRange || !curPointRange.startContainer) return;

            const sel = window.getSelection();
            if (!sel) return;

            try {
              const newRange = document.createRange();
              const comp = touchSelectionStartRange.compareBoundaryPoints(Range.START_TO_START, curPointRange);
              if (comp === 0) {
                const startOffset = Math.min(touchSelectionStartRange.startOffset, curPointRange.startOffset);
                const endOffset = Math.max(touchSelectionStartRange.startOffset, curPointRange.startOffset);
                newRange.setStart(touchSelectionStartRange.startContainer, startOffset);
                newRange.setEnd(touchSelectionStartRange.startContainer, endOffset);
              } else if (comp & Node.DOCUMENT_POSITION_FOLLOWING) {
                newRange.setStart(touchSelectionStartRange.startContainer, touchSelectionStartRange.startOffset);
                newRange.setEnd(curPointRange.startContainer, curPointRange.startOffset);
              } else {
                newRange.setStart(curPointRange.startContainer, curPointRange.startOffset);
                newRange.setEnd(touchSelectionStartRange.startContainer, touchSelectionStartRange.startOffset);
              }
              expandRangeToWordBoundaries(newRange);
              sel.removeAllRanges();
              sel.addRange(newRange);
            } catch (_) {}
          }
        }, { passive: false });

        const handleTouchRelease = () => {
          clearTimeout(touchSelectionTimer);
          const touchDuration = Date.now() - touchStartTime;
          const touchDist = Math.hypot((lastTouchX || touchStartX) - touchStartX, (lastTouchY || touchStartY) - touchStartY);
          isTouchDown = false;

          if (touchDist > 30 && !touchSelectionActive) {
            touchSelectionActive = false;
            pendingContextMenu = null;
            setTimeout(() => { isLongPress = false; }, 120);
            return;
          }

          if (!touchSelectionActive && !isLongPress && touchDuration < 240 && touchDist < 15) {
            const menu = document.getElementById('paraContextMenu');
            if (menu && menu.style.display !== 'none') {
              hideContextMenu();
              try { const s = window.getSelection(); if (s) s.removeAllRanges(); } catch (_) {}
            }
            touchSelectionActive = false;
            pendingContextMenu = null;
            setTimeout(() => { isLongPress = false; }, 120);
            return;
          }

          const isHoldGesture = (touchDuration >= 240 && touchDist <= 30) || touchSelectionActive || isLongPress || !!pendingContextMenu;
          if (isHoldGesture) {
            setTimeout(() => {
              const transModal = document.getElementById('translateModalOverlay');
              if (transModal && transModal.classList.contains('open')) {
                pendingContextMenu = null;
                setTimeout(() => { isLongPress = false; }, 120);
                return;
              }
              const openModal = document.querySelector('.modal-overlay.open, .modal.open, .library-modal.open, .drawer.open');
              if (openModal) {
                pendingContextMenu = null;
                setTimeout(() => { isLongPress = false; }, 120);
                return;
              }

              const sel = window.getSelection();
              if (sel && !sel.isCollapsed && sel.rangeCount > 0) {
                try {
                  const range = sel.getRangeAt(0);
                  expandRangeToWordBoundaries(range);
                  sel.removeAllRanges();
                  sel.addRange(range);
                } catch (_) {}
              }
              let hasSelection = sel && !sel.isCollapsed && sel.toString().trim().length > 0;
              if (isHoldGesture && !hasSelection) {
                const wr = getWordRangeAtPoint(lastTouchX || touchStartX, lastTouchY || touchStartY);
                if (wr && sel) {
                  try {
                    sel.removeAllRanges();
                    sel.addRange(wr);
                    hasSelection = true;
                  } catch (_) {}
                }
              }

              let menuX = lastTouchX || touchStartX;
              let menuY = lastTouchY || touchStartY;
              if (hasSelection && sel && sel.rangeCount > 0) {
                try {
                  const range = sel.getRangeAt(0);
                  const rect = range.getBoundingClientRect();
                  if (rect.width > 0 && rect.height > 0) {
                    menuX = rect.left + (rect.width / 2);
                    menuY = rect.bottom + 8;
                  }
                } catch (_) {}
              }
              showContextMenu(menuX, menuY, p, pIdx, isHoldGesture);
              pendingContextMenu = null;
              touchSelectionActive = false;
              setTimeout(() => { isLongPress = false; }, 400);
            }, 30);
            return;
          }
          touchSelectionActive = false;
          pendingContextMenu = null;
          setTimeout(() => { isLongPress = false; }, 120);
        };

        div.addEventListener('touchend', handleTouchRelease);
        div.addEventListener('touchcancel', handleTouchRelease);

        div.addEventListener('contextmenu', (e) => {
          e.preventDefault();
          const targetX = e.clientX || lastTouchX || touchStartX;
          const targetY = e.clientY || lastTouchY || touchStartY;
          showContextMenu(targetX, targetY, p, pIdx, true);
          return false;
        });

        reader.appendChild(div);
      });

      // Thêm chỉ báo cuối chương & gợi ý cuộn sang chương kế tiếp
      const endIndicator = document.createElement('div');
      endIndicator.className = 'chapter-end-indicator';
      endIndicator.id = 'chapterEndIndicator';
      if (idx + 1 < bookData.chapters.length) {
        const nextCh = bookData.chapters[idx + 1];
        endIndicator.innerHTML = `
          <div class="end-divider"></div>
          <div class="end-badge" onclick="triggerNextChapterByScroll()" title="Bấm hoặc cuộn con lăn chuột xuống để sang chương">
            <span>⏬ Cuộn tiếp con lăn chuột để sang: <b>${escapeHtml(nextCh.title)}</b></span>
          </div>
        `;
      } else {
        endIndicator.innerHTML = `
          <div class="end-divider"></div>
          <div class="end-badge">
            <span>🎉 Bạn đã đọc đến chương mới nhất của bộ truyện</span>
          </div>
        `;
      }
      reader.appendChild(endIndicator);

      if (isInitialJump) {
        requestAnimationFrame(() => {
          scrollToActiveParagraph(true);
        });
      } else {
        setTimeout(() => {
          scrollToActiveParagraph(false);
        }, 80);
      }

      saveProgress();
      if (bookData && bookData.chapters && bookData.chapters.length > 1) {
        notifyPreloader(idx);
      }
      if (bookData && bookData.is_web && idx + 4 >= bookData.chapters.length) {
        fetchMoreWebChapters(5);
      }

      if (window.isHonorApp && !document.body.classList.contains('zen-mode')) {
        setTimeout(() => {
          window.enterZenMode();
        }, 300);
      }

      if (typeof updateHonorTitles === 'function') updateHonorTitles();
      if (typeof updateHonorPageCounter === 'function') setTimeout(updateHonorPageCounter, 60);

      if (isPlaying) {
        playParagraph(currentParagraphIndex);
      }
    }

    // =====================================================================
    // TỰ ĐỘNG CHUYỂN CHƯƠNG KHI CUỘN CON LĂN ĐẾN CUỐI TRANG
    // =====================================================================
    let isChapterTransitioning = false;
    let wheelOverScrollAccumulator = 0;
    let lastLastChapterToastTime = 0;

    async function triggerNextChapterByScroll() {
      if (!bookData || isChapterTransitioning) return;
      if (typeof isUIOverlayActive === 'function' && isUIOverlayActive()) return;
      if (currentChapterIndex + 1 >= bookData.chapters.length) {
        if (bookData.is_web) {
          isChapterTransitioning = true;
          showToast('⏳ Đang tải thêm chương tiếp theo từ web...');
          const added = await fetchMoreWebChapters(5);
          if (added > 0) {
            triggerNextChapterByScroll();
          } else {
            showToast('🎉 Đã là chương mới nhất của truyện!');
          }
          setTimeout(() => { isChapterTransitioning = false; }, 800);
          return;
        }
        const now = Date.now();
        if (now - lastLastChapterToastTime > 3000) {
          lastLastChapterToastTime = now;
          showToast('🎉 Đã là chương cuối cùng của quyển truyện!');
        }
        return;
      }
      isChapterTransitioning = true;
      const nextIdx = currentChapterIndex + 1;
      const nextTitle = bookData.chapters[nextIdx]?.title || `Chương ${nextIdx + 1}`;
      showToast(`📖 Đang chuyển sang: ${nextTitle}`);

      // Dừng ngay lập tức audio hiện tại để tránh đọc lệch với chữ chương mới
      currentPlaybackSessionId++;
      if (audio) {
        audio.pause();
        audio.onended = null;
        audio.src = '';
      }
      setLoading(false);

      // Nếu là web novel và còn dưới 5 chương trong danh sách, tự động tải thêm
      if (bookData.is_web && currentChapterIndex + 5 >= bookData.chapters.length) {
        fetchMoreWebChapters(5);
      }

      const scrollArea = document.getElementById('readerScrollArea');
      if (scrollArea) {
        scrollArea.scrollTo({ top: 0, behavior: 'instant' });
      }

      loadChapter(nextIdx, 0);

      setTimeout(() => {
        isChapterTransitioning = false;
      }, 600);
    }

    function initScrollChapterSwitcher() {
      const scrollArea = document.getElementById('readerScrollArea');
      if (!scrollArea) return;

      // 1. Cuộn con lăn chuột (Mouse Wheel / Trackpad)
      scrollArea.addEventListener('wheel', (e) => {
        if (!bookData || isChapterTransitioning || (typeof isUIOverlayActive === 'function' && isUIOverlayActive())) return;
        if (e.deltaY > 0) { // Đang lăn XUỐNG
          const atBottom = (scrollArea.scrollTop + scrollArea.clientHeight) >= (scrollArea.scrollHeight - 30);
          if (atBottom) {
            wheelOverScrollAccumulator += e.deltaY;
            if (wheelOverScrollAccumulator > 55) {
              wheelOverScrollAccumulator = 0;
              triggerNextChapterByScroll();
            }
          } else {
            wheelOverScrollAccumulator = 0;
          }
        } else {
          wheelOverScrollAccumulator = 0;
        }
      }, { passive: true });

      // Ghi chú: Cử chỉ vuốt chạm và lật trang MagicOS được điều khiển đồng bộ bởi Unified Gesture Engine bên dưới
    }

    function jumpToParagraph(pIdx) {
      currentPlaybackSessionId++;
      if (audio) {
        audio.pause();
        audio.onended = null;
        audio.src = '';
      }
      if (typeof paragraphAudioCache !== 'undefined') {
        paragraphAudioCache.clear();
      }
      if (typeof paragraphPrefetchInFlight !== 'undefined') {
        paragraphPrefetchInFlight.clear();
      }
      setLoading(false);

      if (bookData) {
        const ch = bookData.chapters[currentChapterIndex];
        while (ch && pIdx < ch.paragraphs.length && isParagraphSkipped(ch.paragraphs[pIdx])) {
          pIdx++;
        }
      }
      currentParagraphIndex = pIdx;
      highlightActiveParagraph();
      saveProgress();

      if (isPlaying) {
        playParagraph(pIdx);
      } else {
        togglePlay();
      }
    }

    function scrollSentenceToView(activeEl, isInstant = false) {
      if (!activeEl) return;
      const scrollArea = document.getElementById('readerScrollArea') || document.querySelector('main');
      if (!scrollArea) {
        try { activeEl.scrollIntoView({ behavior: isInstant ? 'auto' : 'smooth', block: 'center' }); } catch (_) {}
        return;
      }

      const dock = document.getElementById('nrBottomDock');
      const isZen = document.body.classList.contains('zen-mode');
      const dockH = (!isZen && dock) ? Math.max(70, dock.offsetHeight || 130) : 0;

      const elRect = activeEl.getBoundingClientRect();
      const areaRect = scrollArea.getBoundingClientRect();

      // Vùng nhìn thấy thực tế phía trên thanh dock
      const visibleZoneH = Math.max(120, areaRect.height - dockH);
      const relTop = elRect.top - areaRect.top;
      const relBottom = elRect.bottom - areaRect.top;

      // Giữ cho câu đọc luôn ở khu vực dễ quan sát nhất: từ 15% đến 55% vùng nhìn thấy
      const safeTop = visibleZoneH * 0.15;
      const safeBottom = visibleZoneH * 0.55;

      // Nếu câu đang đọc nằm hoàn toàn trong vùng thoáng đãng -> giữ nguyên mắt đọc
      if (!isInstant && relTop >= safeTop && relBottom <= safeBottom) {
        return;
      }

      // Đưa câu đang đọc về khoảng 25% chiều cao vùng nhìn thấy
      const targetScroll = Math.max(0, scrollArea.scrollTop + relTop - (visibleZoneH * 0.25));
      const prevScroll = scrollArea.scrollTop;

      try {
        if (isInstant) {
          scrollArea.scrollTop = targetScroll;
        } else {
          scrollArea.scrollTo({ top: targetScroll, behavior: 'smooth' });
        }
      } catch (e) {
        scrollArea.scrollTop = targetScroll;
      }

      // Fallback nếu scrollTop không cuộn được
      setTimeout(() => {
        if (Math.abs(scrollArea.scrollTop - prevScroll) < 2 && Math.abs(scrollArea.scrollTop - targetScroll) > 10) {
          try {
            activeEl.scrollIntoView({ behavior: isInstant ? 'auto' : 'smooth', block: 'center' });
          } catch (_) {}
        }
      }, 50);
    }

    function highlightActiveSentence(sIdx, shouldScroll = true) {
      document.querySelectorAll('.sentence-item.active').forEach(el => el.classList.remove('active'));
      document.querySelectorAll('.paragraph-item.active').forEach(el => el.classList.remove('active'));
      const activeSpan = document.getElementById(`sent-${sIdx}`);
      if (activeSpan) {
        activeSpan.classList.add('active');
        if (shouldScroll) {
          scrollSentenceToView(activeSpan);
        }
      }
      updateProgressBadge();
    }

    function highlightActiveParagraph(shouldScroll = true) {
      highlightActiveSentence(currentParagraphIndex, shouldScroll);
    }

    // =====================================================================
    // BỘ ĐỆM TẢI TRƯỚC ÂM THANH TỪNG CÂU (SENTENCE-LEVEL ZERO-LATENCY PRE-FETCH)
    // =====================================================================
    const paragraphAudioCache = new Map(); // key: `${chIdx}_${sIdx}_${vId}` -> Blob
    const paragraphPrefetchInFlight = new Set();

    function getAudioCacheKey(chIdx, sIdx, vId) {
      return `${chIdx}_${sIdx}_${vId}`;
    }

    async function prefetchSentenceAudio(chIdx, sIdx) {
      if (!allSentences || sIdx >= allSentences.length) return;

      const text = allSentences[sIdx].trim();
      if (!text || isParagraphSkipped(text)) return;

      const voiceSelect = document.getElementById('voiceSelect');
      const selectedOpt = voiceSelect ? (voiceSelect.options[voiceSelect.selectedIndex] || {}) : {};
      const voiceId = selectedOpt.value || 'BV074_streaming';
      const provider = selectedOpt.dataset?.provider || 'capcut';

      if (provider === 'native' || voiceId === 'android_native') return;

      const key = getAudioCacheKey(chIdx, sIdx, voiceId);
      if (paragraphAudioCache.has(key) || paragraphPrefetchInFlight.has(key)) return;

      paragraphPrefetchInFlight.add(key);
      try {
        const res = await fetch('/api/tts', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json; charset=utf-8' },
          body: JSON.stringify({
            text: text,
            voice_id: voiceId,
            provider: provider,
            speed: currentSpeed,
            bilingual_mode: currentBilingualMode
          })
        });
        if (res.ok) {
          const blob = await res.blob();
          if (blob.size >= 300) {
            paragraphAudioCache.set(key, blob);
            // Giới hạn bộ đệm 20 câu gần nhất
            if (paragraphAudioCache.size > 20) {
              const firstKey = paragraphAudioCache.keys().next().value;
              paragraphAudioCache.delete(firstKey);
            }
          }
        }
      } catch (_) {} finally {
        paragraphPrefetchInFlight.delete(key);
      }
    }

    function triggerPrefetchAhead(startIdx, count = 2) {
      if (!allSentences || allSentences.length === 0) return;

      for (let i = 1; i <= count; i++) {
        const targetIdx = startIdx + i;
        if (targetIdx < allSentences.length) {
          prefetchSentenceAudio(currentChapterIndex, targetIdx);
        }
      }
    }

    // =====================================================================
    // PHÁT GIỌNG ĐỌC ĐỒNG BỘ 100% VỚI ĐOẠN VĂN (ANTI-DESYNC ENGINE)
    // =====================================================================
    async function playParagraph(idx) {
      if (!bookData) return;
      const ch = bookData.chapters[currentChapterIndex];
      if (!ch) return;

      if (!allSentences || allSentences.length === 0) {
        const paragraphs = ch.paragraphs || [];
        allSentences = [];
        sentenceMeta = [];
        paragraphs.forEach((p, pIdx) => {
          const sList = splitIntoSentences(p);
          sList.forEach(s => {
            const sIdx = allSentences.length;
            allSentences.push(s);
            sentenceMeta.push({ paraIndex: pIdx, text: s, id: sIdx });
          });
        });
      }

      const mySessionId = ++currentPlaybackSessionId;
      const targetChapter = currentChapterIndex;

      if (audio) {
        audio.pause();
        audio.onended = null;
      }

      while (idx < allSentences.length && isParagraphSkipped(allSentences[idx])) {
        console.log(`[Skip] Bỏ qua câu: "${allSentences[idx]}"`);
        idx++;
      }

      if (idx >= allSentences.length) {
        if (sleepTimerMode === 'chapter') {
          triggerSleepTimerExpired();
          return;
        }
        if (currentChapterIndex + 1 < bookData.chapters.length) {
          if (bookData.is_web && currentChapterIndex + 5 >= bookData.chapters.length) {
            fetchMoreWebChapters(5);
          }
          loadChapter(currentChapterIndex + 1, 0);
          return;
        } else if (bookData.is_web) {
          showToast('⏳ Đang tải thêm chương tiếp theo từ web...');
          fetchMoreWebChapters(5).then(added => {
            if (mySessionId !== currentPlaybackSessionId) return;
            if (added > 0) {
              loadChapter(currentChapterIndex + 1, 0);
            } else {
              pauseAudio();
              showToast('🎉 Bạn đã nghe hết các chương hiện có của truyện!');
            }
          });
          return;
        } else {
          pauseAudio();
          showToast('🎉 Bạn đã nghe hết quyển truyện!');
          return;
        }
      }

      currentSentenceIndex = idx;
      currentParagraphIndex = idx;
      const targetUnit = idx;

      // NỔI BẬT CHÍNH XÁC CÂU ĐANG ĐỌC & ĐƯA VÀO VÙNG NHÌN TỰ NHIÊN
      highlightActiveSentence(idx, true);
      saveProgress();
      window.isPlaying = true;
      if (typeof updateHonorMediaPillState === 'function') updateHonorMediaPillState();

      let text = allSentences[idx].trim();
      if (!text) {
        nextParagraph();
        return;
      }

      const voiceSelect = document.getElementById('voiceSelect');
      const selectedOpt = voiceSelect ? (voiceSelect.options[voiceSelect.selectedIndex] || {}) : {};
      const voiceId = selectedOpt.value || 'BV074_streaming';
      const provider = selectedOpt.dataset?.provider || 'capcut';

      // 1. Giọng hệ thống máy Android (android_native)
      const isSystemNativeVoice = (provider === 'native' || voiceId === 'android_native');
      if (isSystemNativeVoice) {
        if (window.HonorBridge && window.HonorBridge.speakNative) {
          setLoading(false);
          updateMediaSession(ch.title, text);
          const ok = window.HonorBridge.speakNative(text, currentSpeed);
          if (!ok) {
            console.warn('[Native TTS] Thử lại câu...');
            setTimeout(() => {
              if (isPlaying && mySessionId === currentPlaybackSessionId) {
                playParagraph(idx + 1);
              }
            }, 300);
          }
          return;
        }
        if ('speechSynthesis' in window) {
          setLoading(false);
          window.speechSynthesis.cancel();
          const utt = new SpeechSynthesisUtterance(text);
          utt.lang = 'vi-VN';
          utt.rate = currentSpeed;
          utt.onend = () => { if (isPlaying && mySessionId === currentPlaybackSessionId) nextParagraph(); };
          utt.onerror = () => { if (isPlaying && mySessionId === currentPlaybackSessionId) nextParagraph(); };
          updateMediaSession(ch.title, text);
          window.speechSynthesis.speak(utt);
          return;
        }
      }

      // 2. Giọng Online & Giọng Offline AI đã tải về
      const cacheKey = getAudioCacheKey(currentChapterIndex, idx, voiceId);
      let blob = paragraphAudioCache.get(cacheKey);

      if (blob) {
        paragraphAudioCache.delete(cacheKey);
      } else {
        setLoading(true);
        try {
          const res = await fetch('/api/tts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json; charset=utf-8' },
            body: JSON.stringify({
              text: text,
              voice_id: voiceId,
              provider: provider,
              speed: currentSpeed,
              bilingual_mode: currentBilingualMode
            })
          });

          if (mySessionId !== currentPlaybackSessionId || 
              targetChapter !== currentChapterIndex || 
              targetUnit !== currentSentenceIndex || 
              !isPlaying) {
            setLoading(false);
            return;
          }

          if (!res.ok) throw new Error('Lỗi server TTS (' + res.status + ')');
          blob = await res.blob();
          if (blob.size < 300) throw new Error('Dữ liệu âm thanh nhận về quá ngắn');
        } catch (err) {
          console.error(`[Audio Error] Lỗi phát âm thanh Ch.${targetChapter + 1} Câu ${targetUnit + 1}:`, err);
          if (mySessionId !== currentPlaybackSessionId) return;

          setLoading(false);
          setTimeout(() => {
            if (mySessionId === currentPlaybackSessionId && 
                targetChapter === currentChapterIndex && 
                targetUnit === currentSentenceIndex && 
                isPlaying) {
              console.log('[AudioSync] Thử phát lại câu...');
              playParagraph(targetUnit);
            }
          }, 1200);
          return;
        }
      }

      if (mySessionId !== currentPlaybackSessionId || 
          targetChapter !== currentChapterIndex || 
          targetUnit !== currentSentenceIndex || 
          !isPlaying) {
        setLoading(false);
        return;
      }

      const audioUrl = URL.createObjectURL(blob);
      audio.src = audioUrl;
      audio.playbackRate = 1.0;
      updateMediaSession(ch.title, text);

      audio.onended = () => {
        setLoading(false);
        URL.revokeObjectURL(audioUrl);
        if (isPlaying && mySessionId === currentPlaybackSessionId) {
          nextParagraph();
        }
      };

      audio.onerror = (e) => {
        console.error('Audio playback error:', e);
        setLoading(false);
        URL.revokeObjectURL(audioUrl);
        if (isPlaying && mySessionId === currentPlaybackSessionId) {
          setTimeout(() => nextParagraph(), 400);
        }
      };

      try {
        await audio.play();
        setLoading(false);
      } catch (err) {
        console.warn('Lỗi audio.play():', err);
        setLoading(false);
      }

      triggerPrefetchAhead(idx, 2);
    }

    window.onNativeTtsStart = function() {
      setLoading(false);
    };
    window.onNativeTtsDone = function() {
      if (isPlaying) {
        nextParagraph();
      }
    };
    window.onNativeTtsError = function() {
      console.warn('[Native TTS Error] Giọng offline máy gặp lỗi tạm thời trên câu hiện tại, tiếp tục sang câu kế tiếp');
      setTimeout(() => {
        if (isPlaying) nextParagraph();
      }, 300);
    };

    function togglePlay() {
      try {
        if (!bookData) {
          showToast('⚠️ Vui lòng nạp truyện hoặc chọn từ Tủ Sách trước khi nghe!');
          return;
        }
        if (isPlaying) {
          pauseAudio();
        } else {
          isPlaying = true;
          updatePlayBtn();
          requestWakeLock();
          initMediaSessionHandlers();
          playParagraph(currentParagraphIndex);
        }
      } catch (err) {
        console.error('Lỗi togglePlay:', err);
      }
    }

    function pauseAudio() {
      currentPlaybackSessionId++;
      isPlaying = false;
      window.isPlaying = false;
      if (audio) {
        audio.pause();
        audio.onended = null;
      }
      if (window.HonorBridge && window.HonorBridge.stopNativeSpeak) {
        window.HonorBridge.stopNativeSpeak();
      }
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
      setLoading(false);
      updatePlayBtn();
      releaseWakeLock();
      if (!window.HonorBridge && !window.isHonorApp && ('mediaSession' in navigator)) {
        try { navigator.mediaSession.playbackState = 'paused'; } catch(e){}
      }
      setLoading(false);
      updatePlayBtn();
    }

    // =====================================================================
    // MEDIA SESSION API (HIỂN THỊ TRÊN THANH THÔNG BÁO VÀ MÀN HÌNH KHÓA ĐIỆN THOẠI)
    // =====================================================================
    const AUDIO_COVER_ARTWORK = [
      {
        src: 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=512&auto=format&fit=crop&q=80',
        sizes: '512x512',
        type: 'image/jpeg'
      },
      {
        src: 'https://images.unsplash.com/photo-1512820790803-83ca734da794?w=192&auto=format&fit=crop&q=80',
        sizes: '192x192',
        type: 'image/jpeg'
      }
    ];

    let mediaSessionInitialized = false;
    function initMediaSessionHandlers() {
      // Trên Android APK WebView, tắt MediaSession để tránh bị hệ điều hành đóng băng hoặc văng ứng dụng
      if (window.HonorBridge || window.isHonorApp || !('mediaSession' in navigator) || mediaSessionInitialized) return;
      mediaSessionInitialized = true;

      try {
        navigator.mediaSession.setActionHandler('play', () => {
          if (!isPlaying) togglePlay();
        });
        navigator.mediaSession.setActionHandler('pause', () => {
          if (isPlaying) pauseAudio();
        });
        navigator.mediaSession.setActionHandler('previoustrack', () => {
          prevParagraph();
        });
        navigator.mediaSession.setActionHandler('nexttrack', () => {
          nextParagraph();
        });
        navigator.mediaSession.setActionHandler('seekbackward', () => {
          prevParagraph();
        });
        navigator.mediaSession.setActionHandler('seekforward', () => {
          nextParagraph();
        });
      } catch (err) {
        console.warn('Lỗi gán action handler MediaSession:', err);
      }
    }

    function updateMediaSession(chapterTitle, currentSentence) {
      // Trên Android APK WebView, tắt MediaSession để an toàn 100%
      if (window.HonorBridge || window.isHonorApp || !('mediaSession' in navigator) || !bookData) return;
      try {
        const ch = bookData.chapters[currentChapterIndex];
        const title = chapterTitle || ch?.title || `Chương ${currentChapterIndex + 1}`;
        const artist = bookData.title || 'Trình Đọc Truyện AI';
        const album = `Đoạn ${currentParagraphIndex + 1}/${ch?.paragraphs?.length || 0} • ${bookData.author || 'AI Voice'}`;

        navigator.mediaSession.metadata = new MediaMetadata({
          title: title,
          artist: artist,
          album: album,
          artwork: AUDIO_COVER_ARTWORK
        });
        navigator.mediaSession.playbackState = 'playing';
      } catch (e) {
        console.warn('Lỗi updateMediaSession:', e);
      }
    }

    // =====================================================================
    // WAKE LOCK (HỖ TRỢ NGHE LIÊN TỤC KHI TẮT MÀN HÌNH HOẶC CHẠY NỀN)
    // =====================================================================
    let wakeLockSentinel = null;
    async function requestWakeLock() {
      // App Android Native đã có cờ FLAG_KEEP_SCREEN_ON ở tầng Java/Kotlin
      if (window.HonorBridge || window.isHonorApp) return;
      try {
        if ('wakeLock' in navigator) {
          wakeLockSentinel = await navigator.wakeLock.request('screen');
          wakeLockSentinel.addEventListener('release', () => {
            wakeLockSentinel = null;
          });
        }
      } catch (_) {}
    }

    function releaseWakeLock() {
      if (wakeLockSentinel) {
        wakeLockSentinel.release().catch(() => {});
        wakeLockSentinel = null;
      }
    }

    document.addEventListener('visibilitychange', async () => {
      if (document.visibilityState === 'visible' && isPlaying) {
        await requestWakeLock();
      }
    });

    // =====================================================================
    // HẸN GIỜ TẮT ĐỌC (SLEEP TIMER)
    // =====================================================================
    let sleepTimerEndTime = null;
    let sleepTimerInterval = null;
    let sleepTimerMode = null; // 'minutes' hoặc 'chapter'

    function openSleepTimerModal() {
      document.getElementById('sleepTimerModalOverlay').classList.add('open');
      updateSleepTimerModalUI();
    }

    function closeSleepTimerModal(e) {
      if (e && e.target && e.target.id !== 'sleepTimerModalOverlay') return;
      document.getElementById('sleepTimerModalOverlay').classList.remove('open');
    }

    function updateSleepTimerModalUI() {
      const banner = document.getElementById('activeTimerBanner');
      const countdownEl = document.getElementById('activeTimerCountdown');
      if (sleepTimerMode === 'minutes' && sleepTimerEndTime) {
        const leftSec = Math.max(0, Math.round((sleepTimerEndTime - Date.now()) / 1000));
        const m = Math.floor(leftSec / 60);
        const s = leftSec % 60;
        if (banner) banner.style.display = 'block';
        if (countdownEl) countdownEl.textContent = `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
      } else if (sleepTimerMode === 'chapter') {
        if (banner) banner.style.display = 'block';
        if (countdownEl) countdownEl.textContent = 'Dừng khi đọc xong chương hiện tại';
      } else {
        if (banner) banner.style.display = 'none';
      }
    }

    function setSleepTimer(val) {
      if (val === 'chapter') {
        sleepTimerMode = 'chapter';
        sleepTimerEndTime = null;
        if (sleepTimerInterval) clearInterval(sleepTimerInterval);
        setTimerButtonLabel('Hết ch.');
        showToast('⏱️ Đã đặt hẹn giờ: Dừng đọc khi hết chương này!');
      } else {
        const mins = parseInt(val);
        if (!mins || mins <= 0) return;
        sleepTimerMode = 'minutes';
        sleepTimerEndTime = Date.now() + mins * 60 * 1000;
        
        if (sleepTimerInterval) clearInterval(sleepTimerInterval);
        sleepTimerInterval = setInterval(checkSleepTimerTick, 1000);
        
        updateSleepTimerButtonText();
        showToast(`⏱️ Đã đặt hẹn giờ tắt đọc sau ${mins} phút!`);
      }
      document.getElementById('sleepTimerModalOverlay').classList.remove('open');
    }

    function setCustomSleepTimer() {
      const inp = document.getElementById('customMinutesInput');
      const mins = parseInt(inp?.value);
      if (!mins || mins <= 0) {
        alert('Vui lòng nhập số phút hợp lệ!');
        return;
      }
      setSleepTimer(mins);
    }

    function checkSleepTimerTick() {
      if (sleepTimerMode !== 'minutes' || !sleepTimerEndTime) return;
      const now = Date.now();
      if (now >= sleepTimerEndTime) {
        triggerSleepTimerExpired();
        return;
      }
      updateSleepTimerButtonText();
      updateSleepTimerModalUI();
    }

    function setTimerButtonLabel(label) {
      const btnText = document.getElementById('sleepTimerText');
      const headText = document.getElementById('headerTimerText'); const headTextMob = document.getElementById('headerTimerTextMobile'); if (headTextMob) headTextMob.textContent = label;
      if (btnText) btnText.textContent = label;
      if (headText) headText.textContent = label;
    }

    function updateSleepTimerButtonText() {
      if (sleepTimerMode === 'minutes' && sleepTimerEndTime) {
        const leftSec = Math.max(0, Math.round((sleepTimerEndTime - Date.now()) / 1000));
        const m = Math.floor(leftSec / 60);
        const s = leftSec % 60;
        const timeStr = `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
        setTimerButtonLabel(timeStr);
      }
    }

    function triggerSleepTimerExpired() {
      cancelSleepTimer(false);
      if (isPlaying) {
        pauseAudio();
      }
      showToast('😴 Đã hết giờ hẹn! Trình đọc tự động dừng để bạn nghỉ ngơi.');
    }

    function cancelSleepTimer(showNotify = true) {
      if (sleepTimerInterval) {
        clearInterval(sleepTimerInterval);
        sleepTimerInterval = null;
      }
      sleepTimerEndTime = null;
      sleepTimerMode = null;
      setTimerButtonLabel('Hẹn giờ');
      updateSleepTimerModalUI();
      if (showNotify) showToast('🛑 Đã hủy hẹn giờ tắt đọc.');
    }

    function nextParagraph() {
      currentPlaybackSessionId++;
      if (audio) {
        audio.pause();
        audio.onended = null;
      }
      currentParagraphIndex++;
      playParagraph(currentParagraphIndex);
    }

    function prevParagraph() {
      if (currentParagraphIndex > 0) {
        currentPlaybackSessionId++;
        if (audio) {
          audio.pause();
          audio.onended = null;
        }
        currentParagraphIndex--;
        playParagraph(currentParagraphIndex);
      }
    }

    function setLoading(loading) {
      isLoading = loading;
      const btn = document.getElementById('playBtn');
      const fIcon = document.getElementById('floatingEdgeIcon');
      const nrPlayBtn = document.getElementById('nrPlayBtn');
      if (loading) {
        const sp = '<div class="spinner" style="width:20px; height:20px; border-width:2.5px; border-top-color:#fff;"></div>';
        if (btn) btn.innerHTML = sp;
        if (fIcon) fIcon.innerHTML = sp;
        if (nrPlayBtn) nrPlayBtn.classList.add('is-loading');
      } else {
        if (nrPlayBtn) nrPlayBtn.classList.remove('is-loading');
        updatePlayBtn();
      }
    }

    function updatePlayBtn() {
      const playIcon = document.getElementById('nrPlayIcon');
      const pauseIcon = document.getElementById('nrPauseIcon');
      const playBtn = document.getElementById('nrPlayBtn');

      if (playIcon) playIcon.style.display = isPlaying ? 'none' : 'block';
      if (pauseIcon) pauseIcon.style.display = isPlaying ? 'block' : 'none';
      if (playBtn) {
        playBtn.title = isPlaying ? 'Tạm dừng' : 'Phát tiếp';
        if (isPlaying) playBtn.classList.add('is-playing');
        else playBtn.classList.remove('is-playing');
      }

      const playSvg = `<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>`;
      const pauseSvg = `<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>`;
      const icon = isPlaying ? pauseSvg : playSvg;

      const oldBtn = document.getElementById('playBtn');
      if (oldBtn) oldBtn.innerHTML = icon;

      const fIcon = document.getElementById('floatingEdgeIcon');
      if (fIcon) fIcon.innerHTML = icon;

      const widget = document.getElementById('floatingEdgeMediaWidget');
      if (widget) {
        if (isPlaying) widget.classList.add('is-playing');
        else widget.classList.remove('is-playing');
      }

      window.isPlaying = isPlaying;
      updateNrPlayerUI();
      syncMediaSensorState(isPlaying);
      if (typeof updateHonorMediaPillState === 'function') updateHonorMediaPillState();
    }

    let eyeTrackingSuspendedByMedia = false;

    function syncMediaSensorState(playing) {
      if (window.HonorBridge && typeof window.HonorBridge.setMediaPlaying === 'function') {
        try { window.HonorBridge.setMediaPlaying(playing); } catch(e){}
      }
    }

    function changeTheme(theme) {
      if (!theme || !['sepia', 'dark', 'light'].includes(theme)) {
        theme = 'sepia';
      }

      // Giữ nguyên các class đặc biệt khác trên body (zen-mode, hide-audio-bar, ...)
      document.body.classList.remove('theme-sepia', 'theme-dark', 'theme-light');
      document.body.classList.add('theme-' + theme);
      localStorage.setItem('reader_theme', theme);

      // Cập nhật thẻ select trên Desktop
      const sel = document.getElementById('themeSelect');
      if (sel && sel.value !== theme) {
        sel.value = theme;
      }

      // Cập nhật trạng thái active trực quan trên các nút ở mobile popover menu
      const btnSepia = document.getElementById('themeBtnSepia');
      const btnDark = document.getElementById('themeBtnDark');
      const btnLight = document.getElementById('themeBtnLight');
      const activeStyle = 'flex: 1; padding: 6px 2px; font-size: 0.78rem; font-weight: 700; justify-content: center; background: var(--primary) !important; color: #ffffff !important; border-color: var(--primary) !important; box-shadow: 0 2px 8px rgba(79, 70, 229, 0.4);';
      const normalStyle = 'flex: 1; padding: 6px 2px; font-size: 0.78rem; font-weight: 600; justify-content: center;';

      if (btnSepia) btnSepia.style.cssText = (theme === 'sepia' ? activeStyle : normalStyle);
      if (btnDark) btnDark.style.cssText = (theme === 'dark' ? activeStyle : normalStyle);
      if (btnLight) btnLight.style.cssText = (theme === 'light' ? activeStyle : normalStyle);

      // Cập nhật icon trên nút đổi màu nhanh ở header mobile
      const mThemeIcon = document.getElementById('mobileThemeIcon');
      if (mThemeIcon) {
        if (theme === 'dark') mThemeIcon.textContent = '🌙';
        else if (theme === 'light') mThemeIcon.textContent = '☀️';
        else mThemeIcon.textContent = '📜';
      }

      const themeNames = {
        sepia: '📜 Nền Giấy Vàng Sepia',
        dark: '🌙 Chế Độ Tối (Dark Mode)',
        light: '☀️ Nền Sáng Chuẩn'
      };
      if (typeof showToast === 'function') {
        showToast('🎨 Đã chuyển sang: ' + (themeNames[theme] || theme));
      }

      if (window.HonorBridge && typeof window.HonorBridge.setAppTheme === 'function') {
        try {
          window.HonorBridge.setAppTheme(theme);
        } catch (e) {}
      }
    }
    window.changeTheme = changeTheme;

    function cycleThemeMobile() {
      const themes = ['sepia', 'dark', 'light'];
      const saved = localStorage.getItem('reader_theme') || 'sepia';
      const next = themes[(themes.indexOf(saved) + 1) % themes.length];
      changeTheme(next);
    }
    window.cycleThemeMobile = cycleThemeMobile;

    function adjustFontSize(delta) {
      currentFontSize = Math.max(14, Math.min(28, currentFontSize + delta));
      document.getElementById('readerContent').style.fontSize = currentFontSize + 'px';
      const badge = document.getElementById('mobileFontSizeBadge');
      if (badge) badge.textContent = currentFontSize + 'px';
      localStorage.setItem('reader_font_size', currentFontSize);
      showToast('Cỡ chữ: ' + currentFontSize + 'px');
    }



    async function preloadCurrentChapter() {
      if (!bookData) return;
      const ch = bookData.chapters[currentChapterIndex];
      const voiceSelect = document.getElementById('voiceSelect');
      const selectedOpt = voiceSelect.options[voiceSelect.selectedIndex];
      
      const confirmPreload = confirm(`Bạn có muốn tải trước toàn bộ ${ch.paragraphs.length} câu của "${ch.title}" vào cache máy không?`);
      if (!confirmPreload) return;

      let count = 0;
      for (const p of ch.paragraphs) {
        count++;
        document.getElementById('bookMetaInfo').textContent = `Đang tải trước câu ${count}/${ch.paragraphs.length}...`;
        await fetch('/api/tts', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json; charset=utf-8' },
          body: JSON.stringify({
            text: p,
            voice_id: selectedOpt.value,
            provider: selectedOpt.dataset.provider,
            speed: currentSpeed,
            bilingual_mode: currentBilingualMode
          })
        });
        await new Promise(r => setTimeout(r, 600));
      }

      document.getElementById('bookMetaInfo').textContent = `${bookData.title} - ${bookData.author}`;
      alert('Đã tải trước toàn bộ chương vào máy thành công! Bạn có thể nghe mượt mà không tốn mạng.');
    }

    
    // Hỗ trợ Click chuột: Ấn ở PHÍA DƯỚI CÙNG của màn hình mới hiện thanh công cụ
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
      if (clickY >= h - 28) {
        if (typeof toggleHonorOverlay === 'function') {
          toggleHonorOverlay();
        }
      }
    }, true);

    window.addEventListener('keydown', (e) => {
      if (e.code === 'Space' && e.target.tagName !== 'INPUT' && e.target.tagName !== 'SELECT') {
        e.preventDefault();
        togglePlay();
      }
      if (e.key === 'Escape' && document.body.classList.contains('zen-mode')) {
        window.exitZenMode();
      }
      if (e.key === 'ArrowRight' || e.key === 'PageDown') {
        if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
          window.safeTurnNextPage();
        }
      }
      if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
        if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
          window.safeTurnPrevPage();
        }
      }
    });

    // Honor MagicOS Eye Tracking & Remote Page Flipping
    let lastPageTurnTime = 0;
    let pageFlipWatchdogTimer = null;
    window.eyeTrackingEnabled = (localStorage.getItem('honor_eye_enabled') !== 'false');

    function isUIOverlayActive() {
      // 1. Kiểm tra các modal overlay, drawer, dropdown
      const overlays = document.querySelectorAll('.modal-overlay.open, .modal.open, .library-modal.open, .drawer.open, #mobileMenuDropdown.open, .mobile-menu-dropdown.open');
      let active = false;
      for (const el of overlays) {
        if (el && (el.offsetParent !== null || window.getComputedStyle(el).display !== 'none')) {
          active = true;
          break;
        }
      }

      // 2. Khóa chuyển trang khi menu nhấn giữ (paraContextMenu) hoặc thanh công cụ chọn từ (textSelectionToolbar) đang mở
      if (!active) {
        const contextMenu = document.getElementById('paraContextMenu');
        if (contextMenu && contextMenu.style.display !== 'none' && window.getComputedStyle(contextMenu).display !== 'none') {
          active = true;
        }
      }
      if (!active) {
        const selBar = document.getElementById('textSelectionToolbar');
        if (selBar && selBar.style.display !== 'none' && window.getComputedStyle(selBar).display !== 'none') {
          active = true;
        }
      }

      // 3. Khóa chuyển trang khi người dùng đang bôi đen / chọn chữ
      if (!active) {
        const currentSel = window.getSelection();
        if (currentSel && !currentSel.isCollapsed && currentSel.toString().trim()) {
          active = true;
        }
      }

      if (window.HonorBridge && typeof window.HonorBridge.setUiOverlayActive === 'function') {
        try {
          window.HonorBridge.setUiOverlayActive(active);
        } catch (e) {}
      }
      return active;
    }

    try {
      const uiObserver = new MutationObserver(() => {
        isUIOverlayActive();
      });
      uiObserver.observe(document.body, { attributes: true, subtree: true, attributeFilter: ['class'] });
    } catch (e) {}

    window.safeTurnNextPage = function() {
      if (isPlaying) {
        console.log('[SafeTurn] Bỏ qua tự lật trang vì Media đang phát');
        return;
      }
      if (typeof isTouchStartedInTopSafeZone !== 'undefined' && isTouchStartedInTopSafeZone) {
        console.log('[SafeTurn] Bỏ qua lật trang vì thao tác ở vùng an toàn 1/5 phía trên');
        return;
      }
      if (isUIOverlayActive()) return;
      const now = Date.now();
      if (now - lastPageTurnTime < 260) return;
      lastPageTurnTime = now;
      window.nextPage();
    };

    window.safeTurnPrevPage = function() {
      if (isPlaying) {
        console.log('[SafeTurn] Bỏ qua tự lật trang vì Media đang phát');
        return;
      }
      if (typeof isTouchStartedInTopSafeZone !== 'undefined' && isTouchStartedInTopSafeZone) {
        console.log('[SafeTurn] Bỏ qua lật trang vì thao tác ở vùng an toàn 1/5 phía trên');
        return;
      }
      if (isUIOverlayActive()) return;
      const now = Date.now();
      if (now - lastPageTurnTime < 260) return;
      lastPageTurnTime = now;
      window.prevPage();
    };

    window.turnNextPage = window.safeTurnNextPage;
    window.turnPrevPage = window.safeTurnPrevPage;

    // Mặc định sử dụng hiệu ứng Lật Trang 3D Sách Thật (CURL) của Honor Reader gốc
    window.currentReaderPageMode = localStorage.getItem('reader_page_mode') || 'curl';

    window.setReaderPageMode = function(mode) {
      if (['slide', 'scroll', 'curl'].includes(mode)) {
        window.currentReaderPageMode = mode;
        localStorage.setItem('reader_page_mode', mode);
        console.log('[Reader] Chế độ lật trang Honor Reader:', mode);
        if (typeof updateNrSettingsUI === 'function') updateNrSettingsUI();
      }
    };

    // Hàm cuộn cực mượt 120Hz (Butter-smooth Glide) dành cho chế độ Cuộn Dọc
    function smoothGlideScroll(sc, distance, duration = 280) {
      const start = sc.scrollTop;
      const maxScroll = Math.max(0, sc.scrollHeight - sc.clientHeight);
      const target = Math.max(0, Math.min(start + distance, maxScroll));
      const delta = target - start;
      if (Math.abs(delta) < 2) return;
      
      const startTime = performance.now();
      function tick(now) {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const ease = 1 - Math.pow(1 - progress, 4);
        sc.scrollTop = start + delta * ease;
        if (progress < 1) {
          requestAnimationFrame(tick);
        }
      }
      requestAnimationFrame(tick);
    }

    let isPageFlipping = false;

    // LẬT SANG TRANG KẾ TIẾP (HONOR READER NATIVE PAGE TURN NEXT)
    window.nextPage = function() {
      if (isPageFlipping) {
        const activeClone = document.getElementById('pageTurnClone');
        if (!activeClone) {
          isPageFlipping = false;
        } else {
          return;
        }
      }
      if (isUIOverlayActive()) return;
      const sc = document.getElementById('readerScrollArea') || window;
      const maxScroll = Math.max(0, sc.scrollHeight - sc.clientHeight);
      const atBottom = maxScroll > 60 && (sc.scrollTop + sc.clientHeight) >= (sc.scrollHeight - 25);

      if (atBottom) {
        if (typeof triggerNextChapterByScroll === 'function') {
          triggerNextChapterByScroll();
        }
        return;
      }

      // Khoảng cách lật trang đúng bằng chiều cao khung nhìn viewport
      const turnDistance = Math.max(260, sc.clientHeight);

      if (window.currentReaderPageMode === 'slide' || window.currentReaderPageMode === 'curl') {
        isPageFlipping = true;
        clearTimeout(pageFlipWatchdogTimer);
        pageFlipWatchdogTimer = setTimeout(() => {
          isPageFlipping = false;
          const strayClone = document.getElementById('pageTurnClone');
          if (strayClone && strayClone.parentNode) strayClone.parentNode.removeChild(strayClone);
          if (sc) { sc.style.filter = ''; sc.style.transition = ''; }
        }, 650);

        // Khung gắn clone: Gắn trực tiếp vào nrViewReader để clone không bị cuộn theo nội dung bên trong sc!
        const readerView = document.getElementById('nrViewReader') || sc.parentNode || document.body;
        let clone = null;

        try {
          const oldClone = document.getElementById('pageTurnClone');
          if (oldClone && oldClone.parentNode) oldClone.parentNode.removeChild(oldClone);

          const currentScroll = sc.scrollTop;
          sc.scrollLeft = 0;

          // Nhân bản khung hiển thị trang hiện tại
          clone = sc.cloneNode(true);
          clone.id = 'pageTurnClone';
          clone.className = 'page-turn-clone';

          // Căn chuẩn tuyệt đối theo tọa độ sc trong nrViewReader
          const scRect = sc.getBoundingClientRect();
          const viewRect = readerView.getBoundingClientRect();
          clone.style.top = (scRect.top - viewRect.top) + 'px';
          clone.style.left = (scRect.left - viewRect.left) + 'px';
          clone.style.width = scRect.width + 'px';
          clone.style.height = scRect.height + 'px';

          readerView.appendChild(clone);
          clone.scrollTop = currentScroll;
          clone.scrollLeft = 0;

          // Lật trang ngầm bên dưới ngay lập tức để trang mới sẵn sàng dưới lớp clone lật
          sc.scrollTop = Math.min(sc.scrollTop + turnDistance, maxScroll);
          sc.scrollLeft = 0;

          // Hiệu ứng ánh sáng trang ngầm dịu sáng dần chuẩn Honor Reader
          sc.style.transition = 'filter 0.52s cubic-bezier(0.25, 1, 0.35, 1)';
          sc.style.filter = 'brightness(0.92)';
          requestAnimationFrame(() => {
            sc.style.filter = 'brightness(1)';
          });

          const isCurl = (window.currentReaderPageMode === 'curl');
          const animClass = isCurl ? 'anim-honor-curl-left' : 'anim-honor-slide-left';
          clone.classList.add(animClass);

          const duration = isCurl ? 520 : 320;
          setTimeout(() => {
            if (clone && clone.parentNode) {
              clone.parentNode.removeChild(clone);
            }
            if (sc) { sc.style.filter = ''; sc.style.transition = ''; }
            isPageFlipping = false;
            sc.scrollLeft = 0;
            if (typeof updateHonorPageCounter === 'function') updateHonorPageCounter();
          }, duration);
        } catch (err) {
          console.error('[PageTurn] Lỗi lật trang nextPage:', err);
          if (clone && clone.parentNode) clone.parentNode.removeChild(clone);
          if (sc) { sc.style.filter = ''; sc.style.transition = ''; }
          isPageFlipping = false;
          sc.scrollTop = Math.min(sc.scrollTop + turnDistance, maxScroll);
          sc.scrollLeft = 0;
        }
      } else {
        sc.scrollLeft = 0;
        smoothGlideScroll(sc, turnDistance, 280);
      }
    };

    // LẬT VỀ TRANG TRƯỚC (HONOR READER NATIVE PAGE TURN PREV)
    window.prevPage = function() {
      if (isPageFlipping) {
        const activeClone = document.getElementById('pageTurnClone');
        if (!activeClone) {
          isPageFlipping = false;
        } else {
          return;
        }
      }
      if (isUIOverlayActive()) return;
      const sc = document.getElementById('readerScrollArea') || window;
      sc.scrollLeft = 0;
      const maxScroll = Math.max(0, sc.scrollHeight - sc.clientHeight);
      const atTop = maxScroll > 60 && sc.scrollTop <= 15;

      if (atTop) {
        if (typeof triggerPrevChapter === 'function') {
          triggerPrevChapter();
        }
        return;
      }

      const turnDistance = Math.max(260, sc.clientHeight);

      if (window.currentReaderPageMode === 'slide' || window.currentReaderPageMode === 'curl') {
        isPageFlipping = true;
        clearTimeout(pageFlipWatchdogTimer);
        pageFlipWatchdogTimer = setTimeout(() => {
          isPageFlipping = false;
          const strayClone = document.getElementById('pageTurnClone');
          if (strayClone && strayClone.parentNode) strayClone.parentNode.removeChild(strayClone);
          if (sc) { sc.style.filter = ''; sc.style.transition = ''; }
        }, 650);

        const readerView = document.getElementById('nrViewReader') || sc.parentNode || document.body;
        let clone = null;

        try {
          const oldClone = document.getElementById('pageTurnClone');
          if (oldClone && oldClone.parentNode) oldClone.parentNode.removeChild(oldClone);

          const currentScroll = sc.scrollTop;
          sc.scrollLeft = 0;

          clone = sc.cloneNode(true);
          clone.id = 'pageTurnClone';
          clone.className = 'page-turn-clone';

          const scRect = sc.getBoundingClientRect();
          const viewRect = readerView.getBoundingClientRect();
          clone.style.top = (scRect.top - viewRect.top) + 'px';
          clone.style.left = (scRect.left - viewRect.left) + 'px';
          clone.style.width = scRect.width + 'px';
          clone.style.height = scRect.height + 'px';

          readerView.appendChild(clone);
          clone.scrollTop = currentScroll;
          clone.scrollLeft = 0;

          // Lật ngầm trang bên dưới về trang trước
          sc.scrollTop = Math.max(0, sc.scrollTop - turnDistance);
          sc.scrollLeft = 0;

          // Hiệu ứng ánh sáng trang ngầm
          sc.style.transition = 'filter 0.52s cubic-bezier(0.25, 1, 0.35, 1)';
          sc.style.filter = 'brightness(0.92)';
          requestAnimationFrame(() => {
            sc.style.filter = 'brightness(1)';
          });

          const isCurl = (window.currentReaderPageMode === 'curl');
          const animClass = isCurl ? 'anim-honor-curl-right' : 'anim-honor-slide-right';
          clone.classList.add(animClass);

          const duration = isCurl ? 520 : 320;
          setTimeout(() => {
            if (clone && clone.parentNode) {
              clone.parentNode.removeChild(clone);
            }
            if (sc) { sc.style.filter = ''; sc.style.transition = ''; }
            isPageFlipping = false;
            sc.scrollLeft = 0;
            if (typeof updateHonorPageCounter === 'function') updateHonorPageCounter();
          }, duration);
        } catch (err) {
          console.error('[PageTurn] Lỗi lật trang prevPage:', err);
          if (clone && clone.parentNode) clone.parentNode.removeChild(clone);
          if (sc) { sc.style.filter = ''; sc.style.transition = ''; }
          isPageFlipping = false;
          sc.scrollTop = Math.max(0, sc.scrollTop - turnDistance);
          sc.scrollLeft = 0;
        }
      } else {
        sc.scrollLeft = 0;
        smoothGlideScroll(sc, -turnDistance, 280);
      }
    };

    // Khóa tuyệt đối cuộn ngang cho readerScrollArea
    try {
      const _rArea = document.getElementById('readerScrollArea');
      if (_rArea) {
        _rArea.addEventListener('scroll', function() {
          if (_rArea.scrollLeft !== 0) _rArea.scrollLeft = 0;
        }, { passive: true });
      }
    } catch (_) {}

    // =====================================================================
    // QUẢN LÝ THANH ÂM THANH & CHẾ ĐỘ ĐỌC TRÀN VIỀN CƯỠNG BỨC (ZEN MODE)
    // =====================================================================
    window.toggleAudioBar = function() {
      const body = document.body;
      const isHidden = body.classList.toggle('hide-audio-bar');
      const showBtn = document.getElementById('showAudioBarBtn');
      const collapseBtn = document.getElementById('collapsePlayerBtn');
      if (showBtn) {
        showBtn.style.display = (isHidden && !body.classList.contains('zen-mode')) ? 'block' : 'none';
      }
      if (collapseBtn) {
        collapseBtn.innerHTML = isHidden ? '🔼 Hiện' : '🔽 Ẩn';
      }
      showToast(isHidden ? '🔇 Đã ẩn thanh âm thanh (giọng đọc vẫn phát bình thường)' : '🔊 Đã hiện thanh âm thanh');
    };

    window.enterZenMode = function() {
      if (document.body.classList.contains('zen-mode')) return;
      if (typeof closeMobileMenu === 'function') closeMobileMenu();
      if (typeof dismissSelectionToolbar === 'function') dismissSelectionToolbar();
      document.body.classList.add('zen-mode');
      const showBtn = document.getElementById('showAudioBarBtn');
      if (showBtn) showBtn.style.display = 'none';
      const zenBtn = document.getElementById('mobileZenBtn');
      if (zenBtn) {
        zenBtn.style.display = 'none';
      }
      showToast('📱 Đã bật chế độ đọc tràn viền');
      try {
        history.pushState({ zen: true }, '');
      } catch (e) {}
      if (typeof isUIOverlayActive === 'function') isUIOverlayActive();
    };

    window.exitZenMode = function() {
      if (!document.body.classList.contains('zen-mode')) return;
      document.body.classList.remove('zen-mode');
      const showBtn = document.getElementById('showAudioBarBtn');
      if (showBtn && document.body.classList.contains('hide-audio-bar')) {
        showBtn.style.display = 'block';
      }
      const zenBtn = document.getElementById('mobileZenBtn');
      if (zenBtn) {
        zenBtn.style.display = '';
        zenBtn.classList.remove('active');
      }
      showToast('📖 Đã thoát chế độ tràn viền');
      if (typeof isUIOverlayActive === 'function') isUIOverlayActive();
    };

    window.addEventListener('popstate', function() {
      if (document.body.classList.contains('zen-mode')) {
        window.exitZenMode();
      }
    });

    window.toggleZenMode = function() {
      if (document.body.classList.contains('zen-mode')) {
        // Tuyệt đối không thoát tràn viền khi bấm màn hình / nút; chỉ phím Back mới thoát tràn viền
        return;
      } else {
        window.enterZenMode();
      }
    };
    function toggleZenMode() { window.toggleZenMode(); }
    function enterZenMode() { window.enterZenMode(); }
    function exitZenMode() { window.exitZenMode(); }

    // =====================================================================
    // BỘ ĐIỀU KHIỂN CỬ CHỈ DUY NHẤT (UNIFIED GESTURE & TOUCH ENGINE)
    // Hỗ trợ cả ngón tay vuốt/chạm và sự kiện do Honor MagicOS bơm vào
    // =====================================================================
    let touchGestureStartX = 0;
    let touchGestureStartY = 0;
    let touchGestureStartTime = 0;
    let isTouchGestureHandled = false;
    let isTouchStartedInTopSafeZone = false;

    // Hàm kiểm tra tọa độ Y có nằm trong 1/5 không gian phía trên màn hình không (Top Safe Zone)
    window.isCoordinateInTopSafeZone = function(y) {
      if (typeof y !== 'number' || isNaN(y)) return false;
      // Vùng 1/5 màn hình (tối thiểu 22% chiều cao màn hình hoặc 170px để bao trùm notch, status bar và 1/5 phía trên)
      const threshold = Math.max(window.innerHeight * 0.22, 170);
      return y < threshold;
    };

    window.addEventListener('touchstart', function(e) {
      if (e.touches && e.touches.length === 1) {
        const touch = e.touches[0];
        touchGestureStartX = touch.clientX;
        touchGestureStartY = touch.clientY;
        touchGestureStartTime = Date.now();
        isTouchGestureHandled = false;

        isTouchStartedInTopSafeZone = window.isCoordinateInTopSafeZone(touch.clientY);

        const target = e.target;
        if (target && target.closest && target.closest('button, a, input, select, textarea, .modal, .modal-overlay, .library-modal, .drawer, #mobileMenuDropdown, #mobileMenuBackdrop, #floatingEdgeMediaWidget, .audio-player-bar, .popover, .text-selection-toolbar, #textSelectionToolbar, .para-context-menu, #paraContextMenu, #honorTopToolbar, #honorBottomToolbar, #honorFloatingMediaPill, #honorFabListen, #honorFontPanel, .honor-pill-skip-btn, .honor-pill-play-btn, .honor-pill-close-btn')) {
          isTouchGestureHandled = true;
          return;
        }
      }
    }, { passive: true });

    window.addEventListener('touchmove', function(e) {
      if (isTouchGestureHandled || isUIOverlayActive() || !bookData || isChapterTransitioning) return;
      if (e.touches && e.touches.length === 1) {
        if (isTouchStartedInTopSafeZone || window.isCoordinateInTopSafeZone(touchGestureStartY) || window.isCoordinateInTopSafeZone(e.touches[0].clientY)) {
          return;
        }

        const dx = e.touches[0].clientX - touchGestureStartX;
        const dy = e.touches[0].clientY - touchGestureStartY;
        const absX = Math.abs(dx);
        const absY = Math.abs(dy);

        // 1. Nh?n di?n vu?t ngang d?t kho?t ?? l?t trang
        if (absX > 35 && absX > absY * 1.5) {
          if (isPlaying) return;
          const curSel = window.getSelection();
          if (curSel && !curSel.isCollapsed && curSel.toString().trim()) {
            try { curSel.removeAllRanges(); } catch(e){}
          }
          isTouchGestureHandled = true;
          if (dx < 0) {
            window.safeTurnNextPage();
          } else {
            window.safeTurnPrevPage();
          }
        }
      }
    }, { passive: true });

    window.addEventListener('touchend', function(e) {
      const readerView = document.getElementById('nrViewReader');
      const inReader = readerView && readerView.classList.contains('active');

      if (isTouchGestureHandled || !bookData || isChapterTransitioning) {
        isTouchGestureHandled = false;
        isTouchStartedInTopSafeZone = false;
        return;
      }

      // Ki?m tra modal ?ang m? th?c t?
      const modalOpen = document.querySelector('.modal-overlay.open, .modal.open, .library-modal.open, .drawer.open');
      if (modalOpen) {
        isTouchGestureHandled = false;
        return;
      }

      if (e.changedTouches && e.changedTouches.length === 1) {
        const touch = e.changedTouches[0];

        const target = touch.target || e.target;
        if (target && target.closest && target.closest('button, a, input, select, textarea, .modal, .modal-overlay, .library-modal, .drawer, #mobileMenuDropdown, #mobileMenuBackdrop, #floatingEdgeMediaWidget, .audio-player-bar, .popover, .text-selection-toolbar, #textSelectionToolbar, .para-context-menu, #paraContextMenu, #honorTopToolbar, #honorBottomToolbar, #honorFloatingMediaPill, #honorFabListen, #honorFontPanel, .honor-pill-skip-btn, .honor-pill-play-btn, .honor-pill-close-btn')) {
          isTouchGestureHandled = false;
          isTouchStartedInTopSafeZone = false;
          return;
        }

        const diffX = touch.clientX - touchGestureStartX;
        const diffY = touch.clientY - touchGestureStartY;
        const absX = Math.abs(diffX);
        const absY = Math.abs(diffY);
        const duration = Date.now() - touchGestureStartTime;

        // 1. Vu?t nhanh nh? tay ?? l?t trang 3D
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

        // 2. Ch?m (Tap): Hi?n thanh c?ng c? khi ?n ? PH?A D??I C?NG m?n h?nh (30% c?nh ??y)
        if (absX < 25 && absY < 25 && duration < 500) {
          const h = window.innerHeight;
          const clickY = touch.clientY;

          // N?u thanh c?ng c? ?ang m?: ch?m ? ??u c?ng ??ng thanh c?ng c?
          if (typeof honorOverlayVisible !== 'undefined' && honorOverlayVisible) {
            if (typeof toggleHonorOverlay === 'function') {
              toggleHonorOverlay();
            }
            return;
          }

          // Theo y?u c?u ng??i d?ng: ?n ? PH?A D??I C?NG (ch? pop up media / footer) th? hi?n thanh c?ng c? v? n?t nghe!
          if (clickY >= h - 28) {
            if (typeof toggleHonorOverlay === 'function') {
              toggleHonorOverlay();
            }
          }
        }
      }
      isTouchGestureHandled = false;
      isTouchStartedInTopSafeZone = false;
    }, { passive: true });

    window.addEventListener('touchcancel', function() {
      isTouchGestureHandled = false;
      isTouchStartedInTopSafeZone = false;
    }, { passive: true });

    // Khóa chuột phải mặc định ngoài phạm vi đoạn văn / menu
    document.addEventListener('contextmenu', function(e) {
      if (e.target && e.target.closest && e.target.closest('.paragraph-item, #paraContextMenu, #textSelectionToolbar')) {
        return;
      }
      e.preventDefault();
      return false;
    });
    // =====================================================================
    // HỖ TRỢ GIAO DIỆN MENU XỔ RA & TỐI ƯU ĐIỆN THOẠI
    // =====================================================================
    function toggleMobileSpeedSlider(e) {
      if (e) e.stopPropagation();
      const row = document.getElementById('mobileSpeedSliderRow');
      const btn = document.getElementById('mobileSpeedBtn');
      if (!row) return;
      const isHidden = (row.style.display === 'none' || !row.style.display);
      row.style.display = isHidden ? 'flex' : 'none';
      if (btn) {
        if (isHidden) {
          btn.style.background = 'var(--primary)';
          btn.style.color = '#ffffff';
        } else {
          btn.style.background = 'rgba(79, 70, 229, 0.1)';
          btn.style.color = 'var(--primary)';
        }
      }
    }

    const SPEED_STEPS = [0.75, 1.0, 1.25, 1.5, 1.75, 2.0];
    function cycleSpeed() {
      let idx = SPEED_STEPS.findIndex(s => Math.abs(s - currentSpeed) < 0.05);
      if (idx === -1) idx = 1;
      let nextIdx = (idx + 1) % SPEED_STEPS.length;
      let newSpeed = SPEED_STEPS[nextIdx];
      onSpeedSliderChange(newSpeed);
      showToast(`⚡ Tốc độ đọc: ${newSpeed.toFixed(2)}x`);
    }

    function toggleMobileMenu() {
      const menu = document.getElementById('mobileMenuDropdown');
      const backdrop = document.getElementById('mobileMenuBackdrop');
      const btn = document.getElementById('mobileMenuBtn');
      if (menu) {
        const isOpen = menu.classList.toggle('open');
        if (backdrop) backdrop.classList.toggle('open', isOpen);
        if (btn) btn.classList.toggle('active', isOpen);
      }
    }

    function closeMobileMenu() {
      const menu = document.getElementById('mobileMenuDropdown');
      const backdrop = document.getElementById('mobileMenuBackdrop');
      const btn = document.getElementById('mobileMenuBtn');
      if (menu) menu.classList.remove('open');
      if (backdrop) backdrop.classList.remove('open');
      if (btn) btn.classList.remove('active');
    }

    function updateLibraryCountUI(count) {
      const el = document.getElementById('libraryCountBadge');
      if (el) el.textContent = `(${count}/10)`;
      const mob = document.getElementById('libraryCountBadgeMobile');
      if (mob) mob.textContent = `(${count}/10)`;
    }

    window.eyeTrackingEnabled = (localStorage.getItem('honor_eye_enabled') !== 'false');

    window.triggerEyeSettings = function() {
      window.eyeTrackingEnabled = !window.eyeTrackingEnabled;
      localStorage.setItem('honor_eye_enabled', window.eyeTrackingEnabled ? 'true' : 'false');
      eyeTrackingSuspendedByMedia = false;
      const targetMode = window.eyeTrackingEnabled ? 3 : 0;
      if (window.HonorBridge) {
        if (typeof window.HonorBridge.toggleEyeTracking === 'function') {
          try { window.HonorBridge.toggleEyeTracking(); } catch (e) {}
        } else if (typeof window.HonorBridge.setAnimMode === 'function') {
          try { window.HonorBridge.setAnimMode(targetMode); } catch (e) {}
        }
      }
      updateEyeButtonState();
      showToast(window.eyeTrackingEnabled ? '👁️ MagicOS: Đã BẬT lật trang 3D' : '👁️ MagicOS: Đã TẮT theo dõi mắt');
    };

    window.updateEyeTrackingState = function(enabled, modeName) {
      window.eyeTrackingEnabled = enabled;
      localStorage.setItem('honor_eye_enabled', enabled ? 'true' : 'false');
      updateEyeButtonState();
    };

    function updateEyeButtonState() {
      const btn = document.getElementById('webFloatingEyeBtn');
      const menuBtn = document.getElementById('menuMagicEyeBtn');
      const isEn = (window.eyeTrackingEnabled !== false);
      const label = isEn ? '👁️ MagicOS: Lật 3D (Bật)' : '👁️ MagicOS: Lật Mắt (Tắt)';
      if (btn) btn.innerHTML = label;
      if (menuBtn) {
        menuBtn.innerHTML = label;
        if (isEn) {
          menuBtn.style.background = 'rgba(16, 185, 129, 0.15)';
          menuBtn.style.color = '#059669';
          menuBtn.style.borderColor = 'rgba(16, 185, 129, 0.4)';
        } else {
          menuBtn.style.background = 'rgba(100, 116, 139, 0.12)';
          menuBtn.style.color = '#64748b';
          menuBtn.style.borderColor = 'rgba(100, 116, 139, 0.3)';
        }
      }
    }

    try {
      setTimeout(updateEyeButtonState, 150);
    } catch(e) {}

    // =====================================================================
    // NÚT TRÒN MEDIA CẠNH TRÁI THÔNG MINH (EDGE FLOATING MEDIA BUTTON)
    // Tự thu vào cạnh sau 3 giây, chạm hoặc vuốt sang phải để mở rộng
    // =====================================================================
    let floatingEdgeCollapseTimer = null;

    function resetFloatingEdgeTimer(delay = 3000) {
      clearTimeout(floatingEdgeCollapseTimer);
      const widget = document.getElementById('floatingEdgeMediaWidget');
      if (widget) {
        widget.classList.remove('docked');
      }
      floatingEdgeCollapseTimer = setTimeout(() => {
        const w = document.getElementById('floatingEdgeMediaWidget');
        if (w) {
          w.classList.add('docked');
        }
      }, delay);
    }

    function expandFloatingEdge(andReset = true) {
      const widget = document.getElementById('floatingEdgeMediaWidget');
      if (widget) {
        widget.classList.remove('docked');
      }
      if (andReset) resetFloatingEdgeTimer(3000);
    }

    function handleFloatingEdgeClick(e) {
      if (e) e.stopPropagation();
      togglePlay();
      resetFloatingEdgeTimer(3000);
    }

    function handleFloatingEdgeTabClick(e) {
      if (e) e.stopPropagation();
      const widget = document.getElementById('floatingEdgeMediaWidget');
      if (widget && widget.classList.contains('docked')) {
        expandFloatingEdge(true);
      } else {
        handleFloatingEdgeClick(e);
      }
    }

    function initFloatingEdgeGestures() {
      const widget = document.getElementById('floatingEdgeMediaWidget');
      if (!widget) return;

      let touchStartX = 0;
      let touchStartY = 0;

      widget.addEventListener('touchstart', (e) => {
        if (!e.touches || e.touches.length === 0) return;
        touchStartX = e.touches[0].clientX;
        touchStartY = e.touches[0].clientY;
      }, { passive: true });

      widget.addEventListener('touchmove', (e) => {
        if (!e.touches || e.touches.length === 0) return;
        const curX = e.touches[0].clientX;
        const curY = e.touches[0].clientY;
        const dx = curX - touchStartX;
        const dy = Math.abs(curY - touchStartY);

        if (dx > 10 && dy < 35) {
          // Vuốt sang phải -> Mở rộng ngay
          expandFloatingEdge(true);
        } else if (dx < -15 && dy < 35) {
          // Vuốt sang trái -> Thu gọn vào cạnh ngay
          clearTimeout(floatingEdgeCollapseTimer);
          widget.classList.add('docked');
        }
      }, { passive: true });

      // Khởi động hẹn giờ 3 giây tự thu vào
      resetFloatingEdgeTimer(3000);
    }

    window.triggerAppReload = function() {
      showToast('🔄 Đang làm mới trang...');
      if (window.HonorBridge && typeof window.HonorBridge.reloadApp === 'function') {
        window.HonorBridge.reloadApp();
      } else {
        const u = new URL(window.location.href);
        u.searchParams.set('_v', Date.now());
        window.location.href = u.toString();
      }
    };

    
    // ==========================================
    // OTA UPDATE ENGINE (Cập nhật siêu nhẹ ~370KB không cần cài APK)
    // ==========================================
    async function checkAndUpdateOta() {
      const statusEl = document.getElementById('nrOtaStatusText');
      const btn = document.getElementById('btnNrCheckOta');
      if (statusEl) {
        statusEl.style.display = 'block';
        statusEl.style.color = '#38bdf8';
        statusEl.innerHTML = '⏳ Đang kết nối máy chủ OTA...';
      }
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span>⏳ Đang cập nhật...</span>';
      }

      try {
        const pcServer = localStorage.getItem('honor_pc_server') || 'http://192.168.1.204:5000';
        let updateOk = false;
        let updateMsg = '';

        // 1. Thử gọi API cập nhật của HonorLocalServer trên Android
        try {
          const res = await fetch('/api/ota/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ server_url: pcServer })
          });
          if (res.ok) {
            const d = await res.json();
            if (d.success) {
              updateOk = true;
              updateMsg = d.message || 'Cập nhật thành công!';
            } else {
              updateMsg = d.error || 'Lỗi cập nhật OTA';
            }
          }
        } catch (e1) {
          console.warn('Lỗi gọi /api/ota/update trực tiếp:', e1);
        }

        // 2. Nếu bước 1 chưa được, thử fetch bundle trực tiếp từ PC server và gửi nội dung HTML
        if (!updateOk) {
          try {
            if (statusEl) statusEl.innerHTML = '⏳ Đang tải gói cập nhật từ máy tính (' + pcServer + ')...';
            const bundleRes = await fetch(pcServer + '/api/ota/bundle?t=' + Date.now());
            if (bundleRes.ok) {
              const htmlContent = await bundleRes.text();
              if (htmlContent && htmlContent.length > 50000 && htmlContent.includes('<html')) {
                const res2 = await fetch('/api/ota/update', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ html_content: htmlContent })
                });
                const d2 = await res2.json();
                if (d2.success) {
                  updateOk = true;
                  updateMsg = d2.message || 'Cập nhật thành công!';
                }
              }
            }
          } catch(e2) {
            console.warn('Lỗi kéo bundle trực tiếp từ PC:', e2);
          }
        }

        if (updateOk) {
          if (statusEl) {
            statusEl.style.color = '#4ade80';
            statusEl.innerHTML = '✅ ' + updateMsg + '<br><b>Giao diện sẽ tự khởi động lại ngay...</b>';
          }
          if (typeof showHonorToast === 'function') {
            showHonorToast('⚡ Cập nhật OTA thành công!');
          }
          setTimeout(() => {
            window.location.reload(true);
          }, 1200);
        } else {
          if (statusEl) {
            statusEl.style.color = '#f87171';
            statusEl.innerHTML = '❌ ' + (updateMsg || 'Không kết nối được máy chủ cập nhật.') + '<br><span style="color:#94a3b8;font-size:0.75rem;">Mẹo: Đảm bảo điện thoại và máy tính kết nối chung mạng Wi-Fi và máy chủ 192.168.1.204:5000 đang mở.</span>';
          }
          if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/></svg><span>Thử lại</span>';
          }
        }
      } catch (err) {
        if (statusEl) {
          statusEl.style.color = '#f87171';
          statusEl.innerHTML = '❌ Lỗi: ' + err.message;
        }
        if (btn) {
          btn.disabled = false;
          btn.innerHTML = '<span>Thử lại</span>';
        }
      }
    }

    async function resetOta() {
      if (!confirm('Bạn có muốn khôi phục lại giao diện gốc tích hợp sẵn trong APK?')) return;
      const statusEl = document.getElementById('nrOtaStatusText');
      try {
        const res = await fetch('/api/ota/reset', { method: 'POST' });
        const d = await res.json();
        if (statusEl) {
          statusEl.style.display = 'block';
          statusEl.style.color = '#fbbf24';
          statusEl.innerHTML = '🔄 ' + (d.message || 'Đã khôi phục giao diện gốc. Đang khởi động lại...');
        }
        setTimeout(() => {
          window.location.reload(true);
        }, 1200);
      } catch (e) {
        alert('Không thể khôi phục: ' + e.message);
      }
    }

    async function checkOtaStatusBadge() {
      try {
        const res = await fetch('/api/ota/status');
        if (res.ok) {
          const d = await res.json();
          const badge = document.getElementById('nrOtaBadge');
          if (badge && d.has_ota) {
            const kb = Math.round((d.ota_size || 0) / 1024);
            badge.textContent = `OTA ${kb}KB`;
            badge.style.background = 'rgba(34, 197, 94, 0.2)';
            badge.style.color = '#22c55e';
          }
        }
      } catch(e) {}
    }

    window.addEventListener('DOMContentLoaded', () => {
      checkOtaStatusBadge();
      initAutoResume();
      setTimeout(updateEyeButtonState, 500);
      initFloatingEdgeGestures();
      fetchCustomEnglishWords();

      ['textSelectionToolbar', 'paraContextMenu'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
          ['touchstart', 'touchmove', 'touchend'].forEach(evt => {
            el.addEventListener(evt, (e) => {
              e.stopPropagation();
            }, { passive: true });
          });
        }
      });

      const headerEl = document.querySelector('header');
      if (headerEl) {
        let lastTap = 0;
        headerEl.addEventListener('click', function(e) {
          if (e.target && e.target.closest('button, .mobile-ch-pill, select, input, svg')) return;
          const now = Date.now();
          if (now - lastTap < 350) {
            triggerAppReload();
          }
          lastTap = now;
        });
      }
    });

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
      const dismissBackdrop = document.getElementById('honorDismissBackdrop');
      const tapZone = document.getElementById('honorBottomTapZone');

      honorOverlayVisible = !honorOverlayVisible;

      if (topToolbar) topToolbar.classList.toggle('open', honorOverlayVisible);
      if (bottomToolbar) bottomToolbar.classList.toggle('open', honorOverlayVisible);
      if (dismissBackdrop) dismissBackdrop.classList.toggle('open', honorOverlayVisible);
      if (tapZone) tapZone.classList.toggle('hidden', honorOverlayVisible);

      if (fontPanel && !honorOverlayVisible) {
        fontPanel.classList.remove('open');
      }

      // ?n ? ph?a d??i c?ng: Hi?n/?n thanh c?ng c? v? n?t nghe
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

    function initHonorTapZone() {
      const zone = document.getElementById('honorBottomTapZone');
      const bottomStatus = document.getElementById('honorReaderBottomStatus');
      const dismissBackdrop = document.getElementById('honorDismissBackdrop');

      if (zone && !zone.dataset.tapInit) {
        zone.dataset.tapInit = '1';
        let touchStartX = 0, touchStartY = 0, touchStartTime = 0;

        zone.addEventListener('touchstart', function(e) {
          if (e.touches && e.touches.length === 1) {
            touchStartX = e.touches[0].clientX;
            touchStartY = e.touches[0].clientY;
            touchStartTime = Date.now();
          }
        }, { passive: true });

        zone.addEventListener('touchend', function(e) {
          if (!e.changedTouches || e.changedTouches.length !== 1) return;
          const touch = e.changedTouches[0];
          const dx = touch.clientX - touchStartX;
          const dy = touch.clientY - touchStartY;
          const absX = Math.abs(dx);
          const absY = Math.abs(dy);
          const duration = Date.now() - touchStartTime;

          // N?u l? vu?t ngang d?t kho?t -> Cho ph?p l?t trang 3D
          if (duration < 650 && absX > 35 && absX > absY * 1.5) {
            if (!isPlaying) {
              if (dx < 0) window.safeTurnNextPage();
              else window.safeTurnPrevPage();
            }
            return;
          }

          // Ch?m nh? / Tap t?i v?ng d??i c?ng: M? ngay thanh c?ng c? v? n?t nghe!
          if (absX < 25 && absY < 25 && duration < 550) {
            e.preventDefault();
            e.stopPropagation();
            toggleHonorOverlay();
          }
        }, { passive: false });

        zone.addEventListener('click', function(e) {
          e.preventDefault();
          e.stopPropagation();
          toggleHonorOverlay();
        });
      }

      if (bottomStatus && !bottomStatus.dataset.tapInit) {
        bottomStatus.dataset.tapInit = '1';
        bottomStatus.addEventListener('click', function(e) {
          e.preventDefault();
          e.stopPropagation();
          toggleHonorOverlay();
        });
        bottomStatus.addEventListener('touchend', function(e) {
          e.preventDefault();
          e.stopPropagation();
          toggleHonorOverlay();
        });
      }

      if (dismissBackdrop && !dismissBackdrop.dataset.tapInit) {
        dismissBackdrop.dataset.tapInit = '1';
        dismissBackdrop.addEventListener('click', function(e) {
          e.preventDefault();
          e.stopPropagation();
          if (honorOverlayVisible) toggleHonorOverlay();
        });
        dismissBackdrop.addEventListener('touchend', function(e) {
          e.preventDefault();
          e.stopPropagation();
          if (honorOverlayVisible) toggleHonorOverlay();
        });
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
      if (topBook) { topBook.textContent = ''; topBook.style.display = 'none'; }

      let cTitle = '';
      if (bookData && bookData.chapters && bookData.chapters[currentChapterIndex]) {
        const ch = bookData.chapters[currentChapterIndex];
        cTitle = ch.title || `Chương ${currentChapterIndex + 1}`;
      } else {
        cTitle = `Chương ${(currentChapterIndex || 0) + 1}`;
      }

      if (topChap) { topChap.textContent = ''; topChap.style.display = 'none'; }
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
      const turnDistance = Math.max(260, sc.clientHeight);
      const totalPages = Math.max(1, Math.ceil(sc.scrollHeight / turnDistance));
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
    updateHonorClockAndBattery();
  