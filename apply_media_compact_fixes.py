import os
import re

html_path = r'D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\templates\index.html'
assets_path = r'c:\Users\VANLUC\Downloads\Share tool -20261010T221918Z-1-001\Share tool\TTS_STT_vip_v1.6.0\HonorEpubReader\app\src\main\assets\index.html'

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# ==========================================
# 1. XÓA BỎ HOÀN TOÀN KHỐI TIẾN TRÌNH 100% TRONG HTML
# ==========================================
# Tìm khối nr-player-progress-bar
progress_pattern = r'<div class="nr-player-progress-bar">[\s\S]*?</div>\s*</div>'
if re.search(progress_pattern, content):
    content = re.sub(progress_pattern, '<!-- Thanh tiến trình đã xóa để tăng tối đa diện tích đọc chữ -->', content, count=1)
    print("Đã xóa khối nr-player-progress-bar khỏi HTML!")

# ==========================================
# 2. CẬP NHẬT CSS: THU GỌN THANH MEDIA, GIẢM CHIỀU CAO VÀ TĂNG ĐỆM ĐÁY VÙNG ĐỌC
# ==========================================
# Cập nhật .nr-bottom-sheet
old_bottom_sheet_css = """.nr-bottom-sheet {
  background: #14151b;
  border-radius: 26px 26px 0 0;
  padding: 14px 18px calc(max(10px, env(safe-area-inset-bottom, 10px)) + 4px) 18px;
  box-shadow: 0 -8px 28px rgba(0, 0, 0, 0.55);
  display: flex;
  flex-direction: column;
  gap: 12px;
}"""

new_bottom_sheet_css = """.nr-bottom-sheet {
  background: #14151b;
  border-radius: 20px 20px 0 0;
  padding: 6px 14px calc(max(6px, env(safe-area-inset-bottom, 6px))) 14px;
  box-shadow: 0 -6px 22px rgba(0, 0, 0, 0.55);
  display: flex;
  flex-direction: column;
  gap: 4px;
}"""

if old_bottom_sheet_css in content:
    content = content.replace(old_bottom_sheet_css, new_bottom_sheet_css)
    print("Đã cập nhật CSS .nr-bottom-sheet siêu gọn!")

# Cập nhật .nr-mini-player
old_mini_player_css = """.nr-mini-player {
  display: flex;
  flex-direction: column;
  gap: 10px;
}"""

new_mini_player_css = """.nr-mini-player {
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.nr-player-progress-bar {
  display: none !important;
}"""

if old_mini_player_css in content:
    content = content.replace(old_mini_player_css, new_mini_player_css)
    print("Đã cập nhật CSS .nr-mini-player!")

# Cập nhật nút điều khiển & thanh nav
controls_pattern = r'\.nr-player-controls-row \{[\s\S]*?padding: 2px 0 3px 0;\s*\}'
new_controls_css = """.nr-player-controls-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 18px;
  width: 100%;
  padding: 1px 0 2px 0;
}"""
content = re.sub(controls_pattern, new_controls_css, content)

# Nút tròn ở giữa play
old_circle_btn = """.nr-play-btn-circle {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--nr-accent);
  color: #fff;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 14px var(--nr-accent-glow);
  transition: transform 0.1s;
}"""

new_circle_btn = """.nr-play-btn-circle {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: var(--nr-accent);
  color: #fff;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 3px 12px var(--nr-accent-glow);
  transition: transform 0.1s, background-color 0.15s;
}
.nr-play-btn-circle.is-playing {
  background: #f43f5e;
  box-shadow: 0 3px 14px rgba(244, 63, 94, 0.45);
}"""

if old_circle_btn in content:
    content = content.replace(old_circle_btn, new_circle_btn)
    print("Đã cập nhật CSS .nr-play-btn-circle!")

# Thu nhỏ thanh điều hướng .nr-bottom-nav
old_bottom_nav_css = """.nr-bottom-nav {
  width: 78%;
  max-width: 340px;
  height: 52px;
  margin: 0 auto;
  background: rgba(30, 31, 39, 0.95);
  backdrop-filter: blur(18px);
  border: 1px solid #353745;
  border-radius: 28px;
  display: flex;
  align-items: center;
  position: relative;
  padding: 4px 6px;
  box-sizing: border-box;
  box-shadow: 0 6px 24px rgba(0,0,0,0.5);
}"""

new_bottom_nav_css = """.nr-bottom-nav {
  width: 72%;
  max-width: 300px;
  height: 42px;
  margin: 0 auto;
  background: rgba(30, 31, 39, 0.95);
  backdrop-filter: blur(18px);
  border: 1px solid #353745;
  border-radius: 24px;
  display: flex;
  align-items: center;
  position: relative;
  padding: 3px 4px;
  box-sizing: border-box;
  box-shadow: 0 4px 18px rgba(0,0,0,0.5);
}"""

if old_bottom_nav_css in content:
    content = content.replace(old_bottom_nav_css, new_bottom_nav_css)
    print("Đã cập nhật CSS .nr-bottom-nav!")

# Cập nhật indicator và tab trong nav
indicator_pattern = r'\.nr-nav-indicator \{[\s\S]*?z-index: 1;\s*\}'
new_indicator_css = """.nr-nav-indicator {
  position: absolute;
  top: 3px;
  left: 4px;
  width: calc((100% - 8px) / 3);
  height: 36px;
  border-radius: 20px;
  background: #48272e;
  border: 1px solid #7c3b45;
  box-shadow: 0 2px 10px rgba(228, 92, 101, 0.25);
  transform: translateX(0%);
  transition: transform 0.34s cubic-bezier(0.34, 1.4, 0.64, 1);
  pointer-events: none;
  z-index: 1;
}"""
content = re.sub(indicator_pattern, new_indicator_css, content)

tab_pattern = r'\.nr-nav-tab \{[\s\S]*?transition: color 0\.2s ease;\s*\}'
new_tab_css = """.nr-nav-tab {
  flex: 1;
  background: transparent !important;
  border: none !important;
  color: #8b8d9e;
  cursor: pointer;
  height: 36px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  z-index: 2;
  transition: color 0.2s ease;
}"""
content = re.sub(tab_pattern, new_tab_css, content)

# ==========================================
# 3. FIX CHỮ BỊ ẨN DƯỚI MEDIA VÀ TĂNG ĐỆM CUỘN ĐÁY
# ==========================================
old_scroll_css = """.nr-view-reader #readerScrollArea {
  flex: 1 1 0px !important;
  min-height: 0 !important;
  overflow-y: auto !important;
  -webkit-overflow-scrolling: touch !important;
  padding: 6px 16px calc(var(--nr-dock-h, 170px) + 24px) 16px !important;
  box-sizing: border-box !important;
}"""

new_scroll_css = """.nr-view-reader #readerScrollArea {
  flex: 1 1 0px !important;
  min-height: 0 !important;
  overflow-y: auto !important;
  -webkit-overflow-scrolling: touch !important;
  padding: 6px 16px calc(var(--nr-dock-h, 120px) + 140px) 16px !important;
  box-sizing: border-box !important;
  scroll-padding-bottom: calc(var(--nr-dock-h, 120px) + 90px) !important;
}
.nr-view-reader .reader-content {
  padding-bottom: calc(var(--nr-dock-h, 120px) + 120px) !important;
}"""

if old_scroll_css in content:
    content = content.replace(old_scroll_css, new_scroll_css)
    print("Đã cập nhật đệm cuộn an toàn cho #readerScrollArea!")
else:
    # Thử regex
    content = re.sub(r'\.nr-view-reader #readerScrollArea\s*\{[\s\S]*?box-sizing: border-box !important;\s*\}', new_scroll_css, content)
    print("Đã regex thay thế #readerScrollArea padding!")

# ==========================================
# 4. FIX NÚT PLAY/PAUSE KHÔNG ĐỔI TRẠNG THÁI
# ==========================================
# Trong updateNrPlayerUI:
content = re.sub(
    r'const isPlaying = \(typeof isPlayingAudio !== [\'"]undefined[\'"]\) \? isPlayingAudio : false;',
    'const isPlayingNow = (typeof isPlaying !== "undefined") ? isPlaying : false;',
    content
)
content = re.sub(
    r'if \(playIcon\) playIcon\.style\.display = isPlaying \? [\'"]none[\'"] : [\'"]block[\'"];',
    'if (playIcon) playIcon.style.display = isPlayingNow ? "none" : "block";',
    content
)
content = re.sub(
    r'if \(pauseIcon\) pauseIcon\.style\.display = isPlaying \? [\'"]block[\'"] : [\'"]none[\'"];',
    '''if (pauseIcon) pauseIcon.style.display = isPlayingNow ? "block" : "none";
        const playBtnEl = document.getElementById("nrPlayBtn");
        if (playBtnEl) {
          if (isPlayingNow) playBtnEl.classList.add("is-playing");
          else playBtnEl.classList.remove("is-playing");
        }''',
    content
)

# Trong updatePlayBtn:
old_update_play_btn = """    function updatePlayBtn() {
      const playSvg = `<svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>`;
      const pauseSvg = `<svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>`;
      const icon = isPlaying ? pauseSvg : playSvg;

      const btn = document.getElementById('playBtn');
      if (btn) btn.innerHTML = icon;

      const fIcon = document.getElementById('floatingEdgeIcon');
      if (fIcon) fIcon.innerHTML = icon;

      const widget = document.getElementById('floatingEdgeMediaWidget');
      if (widget) {
        if (isPlaying) {
          widget.classList.add('is-playing');
        } else {
          widget.classList.remove('is-playing');
        }
      }

      syncMediaSensorState(isPlaying);
    }"""

new_update_play_btn = """    function updatePlayBtn() {
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

      updateNrPlayerUI();
      syncMediaSensorState(isPlaying);
    }"""

if old_update_play_btn in content:
    content = content.replace(old_update_play_btn, new_update_play_btn)
    print("Đã cập nhật updatePlayBtn() đồng bộ tuyệt đối trạng thái Play/Pause!")

# ==========================================
# 5. FIX CUỘN TỰ ĐỘNG THEO DÕI CÂU ĐANG ĐỌC (AUTO-SCROLL ENGINE)
# ==========================================
old_scroll_fn = """    function scrollSentenceToView(activeEl, isInstant = false) {
      if (!activeEl) return;
      const scrollArea = document.getElementById('readerScrollArea') || document.querySelector('main');
      if (!scrollArea) return;
      const elRect = activeEl.getBoundingClientRect();
      const areaRect = scrollArea.getBoundingClientRect();
      const relTop = elRect.top - areaRect.top;

      // Nếu câu đang đọc nằm trong vùng nhìn thoải mái (18% đến 62% chiều cao màn hình) -> không cuộn giật
      if (relTop >= areaRect.height * 0.18 && relTop <= areaRect.height * 0.62) {
        return;
      }

      // Đưa câu về khoảng 28% từ đỉnh màn hình xuống (vùng đọc tự nhiên của mắt)
      const targetScroll = Math.max(0, scrollArea.scrollTop + relTop - (areaRect.height * 0.28));
      if (isInstant) {
        scrollArea.scrollTop = targetScroll;
      } else {
        scrollArea.scrollTo({ top: targetScroll, behavior: 'smooth' });
      }
    }"""

new_scroll_fn = """    function scrollSentenceToView(activeEl, isInstant = false) {
      if (!activeEl) return;
      const scrollArea = document.getElementById('readerScrollArea') || document.querySelector('main');
      if (!scrollArea) return;

      const dock = document.getElementById('nrBottomDock');
      const isZen = document.body.classList.contains('zen-mode');
      const dockH = (!isZen && dock) ? Math.max(80, dock.offsetHeight) : 0;

      const elRect = activeEl.getBoundingClientRect();
      const areaRect = scrollArea.getBoundingClientRect();

      // Vùng nhìn thấy thực sự phía trên thanh media dock
      const visibleZoneH = Math.max(160, areaRect.height - dockH);
      const relTop = elRect.top - areaRect.top;
      const relBottom = elRect.bottom - areaRect.top;

      // Vùng đọc thoải mái và an toàn: từ 12% đến 60% của khoảng không trên thanh dock
      const safeTop = visibleZoneH * 0.12;
      const safeBottom = visibleZoneH * 0.60;

      // Nếu câu đang đọc nằm hoàn toàn trong vùng thoáng đãng -> giữ nguyên mắt đọc
      if (relTop >= safeTop && relBottom <= safeBottom) {
        return;
      }

      // Khi câu vượt quá 60% hoặc bị che khuất -> cuộn nhẹ nhàng đưa câu lên vị trí 22% từ đỉnh xuống
      const targetScroll = Math.max(0, scrollArea.scrollTop + relTop - (visibleZoneH * 0.22));
      try {
        if (isInstant) {
          scrollArea.scrollTop = targetScroll;
        } else {
          scrollArea.scrollTo({ top: targetScroll, behavior: 'smooth' });
        }
      } catch (e) {
        scrollArea.scrollTop = targetScroll;
      }
    }"""

if old_scroll_fn in content:
    content = content.replace(old_scroll_fn, new_scroll_fn)
    print("Đã cập nhật thuật toán scrollSentenceToView thông minh chống che khuất!")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Đã ghi đè DesktopEpubReader/templates/index.html")

with open(assets_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Đã đồng bộ sang HonorEpubReader/app/src/main/assets/index.html")
