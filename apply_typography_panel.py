import re
import os

files_to_update = [
    r"c:\Users\VANLUC\Downloads\Share tool -20261010T221918Z-1-001\Share tool\TTS_STT_vip_v1.6.0\HonorEpubReader\app\src\main\assets\index.html",
    r"D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\templates\index.html",
    r"c:\Users\VANLUC\Downloads\Share tool -20261010T221918Z-1-001\Share tool\DesktopEpubReader\templates\index.html"
]

def update_file(filepath):
    if not os.path.exists(filepath):
        print(f"[SKIP] {filepath} not found")
        return False
    print(f"[UPDATING] {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update CSS for honor-container and honor-content paragraph-item margins
    # We want .honor-container to use --honor-margin-horizontal
    # and .honor-content .paragraph-item to use --honor-paragraph-margin
    old_css_honor_container = r'''    .honor-container {
      background: #000000 !important;
      color: #a3a3a3 !important;
      max-width: 760px;
      margin: 0 auto;
    }'''

    new_css_honor_container = '''    .honor-container {
      background: #000000 !important;
      color: #a3a3a3 !important;
      max-width: 760px;
      margin: 0 auto;
      padding-left: var(--honor-margin-horizontal, 18px) !important;
      padding-right: var(--honor-margin-horizontal, 18px) !important;
      box-sizing: border-box !important;
    }'''

    if old_css_honor_container in content:
        content = content.replace(old_css_honor_container, new_css_honor_container)
        print("  -> Updated .honor-container padding in CSS")

    old_css_para = r'''    .honor-content .paragraph-item {
      color: #a3a3a3 !important;
      margin-bottom: 20px !important;
      text-indent: 0 !important;
      letter-spacing: 0.2px;
    }'''

    new_css_para = '''    .honor-content .paragraph-item {
      color: #a3a3a3 !important;
      margin-bottom: var(--honor-paragraph-margin, 16px) !important;
      text-indent: 0 !important;
      letter-spacing: 0.2px;
    }'''

    if old_css_para in content:
        content = content.replace(old_css_para, new_css_para)
        print("  -> Updated .honor-content .paragraph-item margin-bottom in CSS")

    # 2. Update .honor-font-panel CSS styling
    old_font_panel_css = r'''    /* POPUP CHỈNH CỠ CHỮ & GIÃN DÒNG */
    .honor-font-panel {
      position: absolute;
      bottom: 115px;
      left: 18px;
      right: 18px;
      background: rgba(28, 28, 30, 0.98);
      backdrop-filter: blur(25px);
      -webkit-backdrop-filter: blur(25px);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 18px;
      padding: 16px 20px;
      z-index: 1100;
      display: flex;
      flex-direction: column;
      gap: 14px;
      transform: translateY(20px) scale(0.96);
      opacity: 0;
      pointer-events: none;
      transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
      box-shadow: 0 16px 40px rgba(0, 0, 0, 0.6);
    }
    .honor-font-panel.open {
      transform: translateY(0) scale(1);
      opacity: 1;
      pointer-events: auto;
    }
    .honor-font-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .honor-font-label {
      font-size: 14px;
      font-weight: 500;
      color: #a1a1aa;
    }
    .honor-font-ctrls {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .honor-font-step-btn {
      background: #27272a;
      border: 1px solid #3f3f46;
      color: #f4f4f5;
      border-radius: 8px;
      padding: 4px 14px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
    }
    .honor-font-step-btn:active {
      background: #3f3f46;
    }
    .honor-font-val {
      font-size: 15px;
      font-weight: 600;
      color: #ffffff;
      min-width: 24px;
      text-align: center;
    }
    .honor-line-btn {
      background: #27272a;
      border: 1px solid #3f3f46;
      color: #a1a1aa;
      border-radius: 8px;
      padding: 4px 12px;
      font-size: 12px;
      font-weight: 500;
      cursor: pointer;
    }'''

    new_font_panel_css = '''    /* POPUP CHỈNH CỠ CHỮ, GIÃN DÒNG, GIÃN ĐOẠN, LỀ NGANG (HONOR TYPOGRAPHY PANEL) */
    .honor-font-panel {
      position: absolute;
      bottom: 110px;
      left: 14px;
      right: 14px;
      max-width: 500px;
      margin: 0 auto;
      background: rgba(22, 22, 26, 0.97);
      backdrop-filter: blur(28px);
      -webkit-backdrop-filter: blur(28px);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 20px;
      padding: 16px 18px 18px 18px;
      z-index: 1100;
      display: flex;
      flex-direction: column;
      gap: 13px;
      transform: translateY(20px) scale(0.96);
      opacity: 0;
      pointer-events: none;
      transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
      box-shadow: 0 16px 40px rgba(0, 0, 0, 0.7);
    }
    .honor-font-panel.open {
      transform: translateY(0) scale(1);
      opacity: 1;
      pointer-events: auto;
    }
    .honor-slider-item {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .honor-slider-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0 2px;
    }
    .honor-slider-title {
      font-size: 13.5px;
      font-weight: 500;
      color: #a1a1aa;
      letter-spacing: 0.1px;
    }
    .honor-slider-val {
      font-size: 13.5px;
      font-weight: 600;
      color: #ffffff;
      letter-spacing: 0.3px;
    }
    .honor-slider-row {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .honor-step-btn {
      width: 30px;
      height: 30px;
      min-width: 30px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #27272a;
      border: 1px solid #3f3f46;
      color: #f4f4f5;
      border-radius: 8px;
      font-size: 16px;
      font-weight: 600;
      cursor: pointer;
      user-select: none;
      padding: 0;
      line-height: 1;
    }
    .honor-step-btn:active {
      background: #3f3f46;
      transform: scale(0.94);
    }
    .honor-slider {
      flex: 1;
      height: 10px;
      -webkit-appearance: none;
      appearance: none;
      background: #333338;
      border-radius: 99px;
      outline: none;
      cursor: pointer;
      margin: 0;
      border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .honor-slider::-webkit-slider-thumb {
      -webkit-appearance: none;
      appearance: none;
      width: 6px;
      height: 24px;
      border-radius: 3px;
      background: #ffffff;
      box-shadow: 0 0 6px rgba(0,0,0,0.6);
      cursor: pointer;
      transition: transform 0.1s ease;
    }
    .honor-slider::-webkit-slider-thumb:active {
      transform: scaleY(1.15) scaleX(1.3);
    }
    .honor-slider::-moz-range-thumb {
      width: 6px;
      height: 24px;
      border-radius: 3px;
      background: #ffffff;
      box-shadow: 0 0 6px rgba(0,0,0,0.6);
      border: none;
      cursor: pointer;
    }'''

    if old_font_panel_css in content:
        content = content.replace(old_font_panel_css, new_font_panel_css)
        print("  -> Updated .honor-font-panel CSS")
    else:
        # Regex replacement if slightly different
        content = re.sub(
            r'/\* POPUP CHỈNH CỠ CHỮ & GIÃN DÒNG \*/[\s\S]*?\.honor-line-btn\s*\{[^}]*\}',
            lambda m: new_font_panel_css,
            content,
            count=1
        )
        print("  -> Updated .honor-font-panel CSS via regex")

    # 3. Update HTML markup of #honorFontPanel
    old_panel_html = r'''      <!-- POPUP CỠ CHỮ & GIÃN DÒNG NHANH -->
      <div id="honorFontPanel" class="honor-font-panel">
        <div class="honor-font-row">
          <span class="honor-font-label">Cỡ chữ</span>
          <div class="honor-font-ctrls">
            <button class="honor-font-step-btn" onclick="adjustHonorFontSize(-1)">A-</button>
            <span id="honorFontSizeDisplay" class="honor-font-val">19</span>
            <button class="honor-font-step-btn" onclick="adjustHonorFontSize(1)">A+</button>
          </div>
        </div>
        <div class="honor-font-row">
          <span class="honor-font-label">Dãn dòng</span>
          <div class="honor-font-ctrls">
            <button class="honor-line-btn" id="honorLineTight" onclick="setHonorLineHeight(1.5)">Gọn</button>
            <button class="honor-line-btn active" id="honorLineNormal" onclick="setHonorLineHeight(1.85)">Vừa</button>
            <button class="honor-line-btn" id="honorLineLoose" onclick="setHonorLineHeight(2.2)">Thoáng</button>
          </div>
        </div>
      </div>'''

    new_panel_html = '''      <!-- POPUP CỠ CHỮ, GIÃN DÒNG, GIÃN ĐOẠN, LỀ NGANG (HONOR TYPOGRAPHY PANEL) -->
      <div id="honorFontPanel" class="honor-font-panel" onclick="event.stopPropagation();">
        <!-- 1. Cỡ chữ -->
        <div class="honor-slider-item">
          <div class="honor-slider-header">
            <span class="honor-slider-title">Cỡ chữ</span>
            <span class="honor-slider-val" id="valHonorFontSize">18</span>
          </div>
          <div class="honor-slider-row">
            <button class="honor-step-btn" onclick="adjustHonorFontSize(-1)" title="Giảm cỡ chữ">−</button>
            <input type="range" class="honor-slider" id="sliderHonorFontSize" min="13" max="34" step="1" value="18" oninput="setHonorFontSize(this.value)">
            <button class="honor-step-btn" onclick="adjustHonorFontSize(1)" title="Tăng cỡ chữ">+</button>
          </div>
        </div>

        <!-- 2. Giãn dòng -->
        <div class="honor-slider-item">
          <div class="honor-slider-header">
            <span class="honor-slider-title">Giãn dòng</span>
            <span class="honor-slider-val" id="valHonorLineHeight">1,6x</span>
          </div>
          <div class="honor-slider-row">
            <button class="honor-step-btn" onclick="adjustHonorLineHeight(-0.05)" title="Giảm khoảng cách dòng">−</button>
            <input type="range" class="honor-slider" id="sliderHonorLineHeight" min="1.2" max="2.6" step="0.05" value="1.6" oninput="setHonorLineHeight(this.value)">
            <button class="honor-step-btn" onclick="adjustHonorLineHeight(0.05)" title="Tăng khoảng cách dòng">+</button>
          </div>
        </div>

        <!-- 3. Giãn đoạn -->
        <div class="honor-slider-item">
          <div class="honor-slider-header">
            <span class="honor-slider-title">Giãn đoạn</span>
            <span class="honor-slider-val" id="valHonorParaMargin">16dp</span>
          </div>
          <div class="honor-slider-row">
            <button class="honor-step-btn" onclick="adjustHonorParaMargin(-2)" title="Giảm khoảng cách đoạn">−</button>
            <input type="range" class="honor-slider" id="sliderHonorParaMargin" min="0" max="36" step="2" value="16" oninput="setHonorParaMargin(this.value)">
            <button class="honor-step-btn" onclick="adjustHonorParaMargin(2)" title="Tăng khoảng cách đoạn">+</button>
          </div>
        </div>

        <!-- 4. Lề ngang -->
        <div class="honor-slider-item">
          <div class="honor-slider-header">
            <span class="honor-slider-title">Lề ngang</span>
            <span class="honor-slider-val" id="valHonorMarginH">18dp</span>
          </div>
          <div class="honor-slider-row">
            <button class="honor-step-btn" onclick="adjustHonorMarginHorizontal(-2)" title="Giảm lề hai bên">−</button>
            <input type="range" class="honor-slider" id="sliderHonorMarginH" min="6" max="38" step="2" value="18" oninput="setHonorMarginHorizontal(this.value)">
            <button class="honor-step-btn" onclick="adjustHonorMarginHorizontal(2)" title="Tăng lề hai bên">+</button>
          </div>
        </div>
      </div>'''

    if old_panel_html in content:
        content = content.replace(old_panel_html, new_panel_html)
        print("  -> Replaced #honorFontPanel HTML markup")
    else:
        content = re.sub(
            r'<!-- POPUP CỠ CHỮ[^\n]*-->\s*<div id="honorFontPanel"[^>]*>[\s\S]*?</div>\s*</div>',
            lambda m: new_panel_html + "\n\n      </div>",
            content,
            count=1
        )
        print("  -> Replaced #honorFontPanel HTML markup via regex")

    # 4. Update JS functions for Honor Typography (Font size, Line height, Paragraph spacing, Horizontal margin)
    old_js_funcs = r'''    function toggleHonorFontPanel(e) {
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
    }'''

    new_js_funcs = '''    // =====================================================================
    // QUẢN LÝ THÔNG SỐ HIỂN THỊ ĐỌC SÁCH (TYPOGRAPHY ENGINE)
    // 1. Cỡ chữ (Font Size) | 2. Giãn dòng (Line Height)
    // 3. Giãn đoạn (Paragraph Spacing) | 4. Lề ngang (Horizontal Margin)
    // =====================================================================
    function updateSliderFill(slider) {
      if (!slider) return;
      const min = parseFloat(slider.min) || 0;
      const max = parseFloat(slider.max) || 100;
      const val = parseFloat(slider.value) || 0;
      const pct = Math.max(0, Math.min(100, ((val - min) / (max - min)) * 100));
      slider.style.background = `linear-gradient(to right, #e2e8f0 0%, #e2e8f0 ${pct}%, #333338 ${pct}%, #333338 100%)`;
    }

    function syncHonorTypographyUI() {
      const fontSize = parseInt(localStorage.getItem('honor_font_size') || '18', 10);
      const lineHeight = parseFloat(localStorage.getItem('honor_line_height') || '1.6');
      const paraMargin = parseInt(localStorage.getItem('honor_para_margin') || '16', 10);
      const marginH = parseInt(localStorage.getItem('honor_margin_horizontal') || '18', 10);

      const elValFont = document.getElementById('valHonorFontSize');
      const elSlFont = document.getElementById('sliderHonorFontSize');
      if (elValFont) elValFont.textContent = fontSize;
      if (elSlFont) { elSlFont.value = fontSize; updateSliderFill(elSlFont); }

      const elValLine = document.getElementById('valHonorLineHeight');
      const elSlLine = document.getElementById('sliderHonorLineHeight');
      const lineStr = lineHeight.toFixed(2).replace(/\\.00$/, '').replace(/\\.([1-9])0$/, '.$1').replace('.', ',') + 'x';
      if (elValLine) elValLine.textContent = lineStr;
      if (elSlLine) { elSlLine.value = lineHeight; updateSliderFill(elSlLine); }

      const elValPara = document.getElementById('valHonorParaMargin');
      const elSlPara = document.getElementById('sliderHonorParaMargin');
      if (elValPara) elValPara.textContent = paraMargin + 'dp';
      if (elSlPara) { elSlPara.value = paraMargin; updateSliderFill(elSlPara); }

      const elValH = document.getElementById('valHonorMarginH');
      const elSlH = document.getElementById('sliderHonorMarginH');
      if (elValH) elValH.textContent = marginH + 'dp';
      if (elSlH) { elSlH.value = marginH; updateSliderFill(elSlH); }
    }

    function initHonorTypography() {
      const fontSize = parseInt(localStorage.getItem('honor_font_size') || '18', 10);
      const lineHeight = parseFloat(localStorage.getItem('honor_line_height') || '1.6');
      const paraMargin = parseInt(localStorage.getItem('honor_para_margin') || '16', 10);
      const marginH = parseInt(localStorage.getItem('honor_margin_horizontal') || '18', 10);

      document.documentElement.style.setProperty('--honor-font-size', fontSize + 'px');
      document.documentElement.style.setProperty('--honor-line-height', lineHeight);
      document.documentElement.style.setProperty('--honor-paragraph-margin', paraMargin + 'px');
      document.documentElement.style.setProperty('--honor-margin-horizontal', marginH + 'px');

      syncHonorTypographyUI();
    }

    function toggleHonorFontPanel(e) {
      if (e) e.stopPropagation();
      const fontPanel = document.getElementById('honorFontPanel');
      if (fontPanel) {
        fontPanel.classList.toggle('open');
        if (fontPanel.classList.contains('open')) {
          syncHonorTypographyUI();
        }
      }
    }

    function setHonorFontSize(val) {
      const v = Math.min(36, Math.max(12, parseInt(val, 10)));
      localStorage.setItem('honor_font_size', v);
      document.documentElement.style.setProperty('--honor-font-size', v + 'px');
      const elVal = document.getElementById('valHonorFontSize');
      const elSl = document.getElementById('sliderHonorFontSize');
      if (elVal) elVal.textContent = v;
      if (elSl) { elSl.value = v; updateSliderFill(elSl); }
      if (typeof updateHonorPageCounter === 'function') setTimeout(updateHonorPageCounter, 60);
    }

    function adjustHonorFontSize(delta) {
      const cur = parseInt(localStorage.getItem('honor_font_size') || '18', 10);
      setHonorFontSize(cur + delta);
    }

    function setHonorLineHeight(val) {
      let v = parseFloat(val);
      v = Math.min(2.6, Math.max(1.2, Math.round(v * 20) / 20));
      localStorage.setItem('honor_line_height', v);
      document.documentElement.style.setProperty('--honor-line-height', v);
      const elVal = document.getElementById('valHonorLineHeight');
      const elSl = document.getElementById('sliderHonorLineHeight');
      const lineStr = v.toFixed(2).replace(/\\.00$/, '').replace(/\\.([1-9])0$/, '.$1').replace('.', ',') + 'x';
      if (elVal) elVal.textContent = lineStr;
      if (elSl) { elSl.value = v; updateSliderFill(elSl); }
      if (typeof updateHonorPageCounter === 'function') setTimeout(updateHonorPageCounter, 60);
    }

    function adjustHonorLineHeight(delta) {
      const cur = parseFloat(localStorage.getItem('honor_line_height') || '1.6');
      setHonorLineHeight(cur + delta);
    }

    function setHonorParaMargin(val) {
      const v = Math.min(40, Math.max(0, parseInt(val, 10)));
      localStorage.setItem('honor_para_margin', v);
      document.documentElement.style.setProperty('--honor-paragraph-margin', v + 'px');
      const elVal = document.getElementById('valHonorParaMargin');
      const elSl = document.getElementById('sliderHonorParaMargin');
      if (elVal) elVal.textContent = v + 'dp';
      if (elSl) { elSl.value = v; updateSliderFill(elSl); }
      if (typeof updateHonorPageCounter === 'function') setTimeout(updateHonorPageCounter, 60);
    }

    function adjustHonorParaMargin(delta) {
      const cur = parseInt(localStorage.getItem('honor_para_margin') || '16', 10);
      setHonorParaMargin(cur + delta);
    }

    function setHonorMarginHorizontal(val) {
      const v = Math.min(40, Math.max(6, parseInt(val, 10)));
      localStorage.setItem('honor_margin_horizontal', v);
      document.documentElement.style.setProperty('--honor-margin-horizontal', v + 'px');
      const elVal = document.getElementById('valHonorMarginH');
      const elSl = document.getElementById('sliderHonorMarginH');
      if (elVal) elVal.textContent = v + 'dp';
      if (elSl) { elSl.value = v; updateSliderFill(elSl); }
      if (typeof updateHonorPageCounter === 'function') setTimeout(updateHonorPageCounter, 60);
    }

    function adjustHonorMarginHorizontal(delta) {
      const cur = parseInt(localStorage.getItem('honor_margin_horizontal') || '18', 10);
      setHonorMarginHorizontal(cur + delta);
    }'''

    if old_js_funcs in content:
        content = content.replace(old_js_funcs, new_js_funcs)
        print("  -> Replaced typography JS functions")
    else:
        content = re.sub(
            r'function toggleHonorFontPanel\(e\)[\s\S]*?function setHonorLineHeight\(val\)\s*\{[\s\S]*?\}',
            lambda m: new_js_funcs,
            content,
            count=1
        )
        print("  -> Replaced typography JS functions via regex")

    # 5. Call initHonorTypography on load
    if 'initHonorTypography();' not in content:
        content = content.replace(
            "setTimeout(updateEyeButtonState, 500);",
            "setTimeout(updateEyeButtonState, 500);\n      initHonorTypography();"
        )
        print("  -> Added initHonorTypography() to DOMContentLoaded")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  [OK] Successfully updated {filepath}")
    return True

print("=== STARTING TYPOGRAPHY UPDATE ===")
for hf in files_to_update:
    update_file(hf)
print("=== COMPLETED ===")
