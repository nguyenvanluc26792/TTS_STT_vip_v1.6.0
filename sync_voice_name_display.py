# -*- coding: utf-8 -*-
import os, sys, re

assets_html = r"c:\Users\VANLUC\Downloads\Share tool -20261010T221918Z-1-001\Share tool\TTS_STT_vip_v1.6.0\HonorEpubReader\app\src\main\assets\index.html"
desktop_html_d = r"D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\templates\index.html"
desktop_html_c = r"c:\Users\VANLUC\Downloads\Share tool -20261010T221918Z-1-001\Share tool\DesktopEpubReader\templates\index.html"
desktop_server_d = r"D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\server.py"
desktop_server_c = r"c:\Users\VANLUC\Downloads\Share tool -20261010T221918Z-1-001\Share tool\DesktopEpubReader\server.py"

print("Reading assets index.html...")
with open(assets_html, "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

# 1. Add syncVoiceUIElements function and update onVoiceChange, updateVoicePickerDisplay, selectVoiceFromCustomPicker
old_picker_block = """    function selectVoiceFromCustomPicker(val) {
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
    }"""

new_picker_block = """    function syncVoiceUIElements(val) {
      const select = document.getElementById('voiceSelect');
      if (!select) return;
      const targetVal = val || select.value || localStorage.getItem('reader_saved_voice') || 'BV074_streaming';
      const opt = select.querySelector(`option[value="${targetVal}"]`) || (select.options ? select.options[select.selectedIndex] : null);
      if (!opt) return;

      const isNative = (opt.value === 'android_native' || opt.dataset.provider === 'native');
      document.getElementById('nrRadioRowGoogle')?.classList.toggle('active', isNative);
      document.getElementById('nrRadioRowAi')?.classList.toggle('active', !isNative);

      let cleanName = opt.textContent.replace(/^[\\s\\p{Emoji}\\u200d\\uFE0F\\uD83C-\\uDBFF\\uDC00-\\uDFFF\\u2600-\\u27BF]+/gu, '').trim();
      if (isNative) cleanName = 'Giọng Google';
      if (!cleanName) cleanName = opt.textContent || 'Ngọc Huyền';

      // 1. Cập nhật trong tab Cài đặt
      const selText = document.getElementById('nrSelectedVoiceText');
      if (selText) selText.textContent = cleanName;

      // 2. Cập nhật ở ngoài (nút Quick Action trên thanh Dock nổi / Mini player)
      const quickVoice = document.getElementById('nrQuickVoiceName');
      if (quickVoice) quickVoice.textContent = cleanName;

      // 3. Cập nhật tên hiển thị ở Custom Picker
      updateVoicePickerDisplay();

      // Lưu lại giọng AI gần nhất nếu không phải native
      if (!isNative && opt.value !== '__manage_offline__') {
        localStorage.setItem('reader_last_ai_voice', opt.value);
      }
    }

    function selectVoiceFromCustomPicker(val) {
      const select = document.getElementById('voiceSelect');
      if (select) {
        select.value = val;
        onVoiceChange(val);
      }
      syncVoiceUIElements(val);
      closeVoicePickerModal();
    }

    function updateVoicePickerDisplay() {
      const select = document.getElementById('voiceSelect');
      const displaySpan = document.getElementById('voicePickerDisplay');
      if (!select) return;

      const selectedOpt = select.options[select.selectedIndex];
      if (displaySpan) {
        if (selectedOpt && selectedOpt.value !== '__manage_offline__') {
          const isOffline = selectedOpt.dataset.provider === 'offline';
          const isElevenLabs = selectedOpt.dataset.provider === 'elevenlabs';
          const icon = isOffline ? '⭐' : (isElevenLabs ? '✨' : '🎙️');
          displaySpan.innerHTML = `${icon} <span style="font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${selectedOpt.textContent}</span>`;
        } else {
          displaySpan.innerHTML = `🎙️ <span>Chọn giọng đọc...</span>`;
        }
      }

      // Luôn đồng bộ tên giọng ra ngoài giao diện
      if (selectedOpt) {
        let cleanName = selectedOpt.textContent.replace(/^[\\s\\p{Emoji}\\u200d\\uFE0F\\uD83C-\\uDBFF\\uDC00-\\uDFFF\\u2600-\\u27BF]+/gu, '').trim();
        if (selectedOpt.value === 'android_native' || selectedOpt.dataset.provider === 'native') cleanName = 'Giọng Google';
        const selText = document.getElementById('nrSelectedVoiceText');
        if (selText) selText.textContent = cleanName || selectedOpt.textContent;
        const quickVoice = document.getElementById('nrQuickVoiceName');
        if (quickVoice) quickVoice.textContent = cleanName || selectedOpt.textContent;
      }
    }"""

if old_picker_block in content:
    content = content.replace(old_picker_block, new_picker_block, 1)
    print("1. Replaced selectVoiceFromCustomPicker & updateVoicePickerDisplay with syncVoiceUIElements")
else:
    print("1. Error: old_picker_block not found!")
    sys.exit(1)

# 2. Update onVoiceChange
old_on_voice = """    function onVoiceChange(val) {
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
    }"""

new_on_voice = """    function onVoiceChange(val) {
      if (val === '__manage_offline__') {
        openOfflineVoicesModal();
        const saved = localStorage.getItem('reader_saved_voice') || 'BV074_streaming';
        const select = document.getElementById('voiceSelect');
        if (select) select.value = saved;
        syncVoiceUIElements(saved);
        return;
      }
      localStorage.setItem('reader_saved_voice', val);
      syncVoiceUIElements(val);
      notifyPreloader();
    }"""

if old_on_voice in content:
    content = content.replace(old_on_voice, new_on_voice, 1)
    print("2. Updated onVoiceChange with syncVoiceUIElements")
else:
    print("2. Warning: old_on_voice not found verbatim!")

# 3. Update loadVoices end to sync voice UI on load
content = content.replace(
    "updateVoicePickerDisplay();\n\n        // Nếu modal chọn giọng đang mở",
    "updateVoicePickerDisplay();\n        syncVoiceUIElements(defaultVoice);\n\n        // Nếu modal chọn giọng đang mở"
)
print("3. Added syncVoiceUIElements in loadVoices")

# 4. Update setNrVoiceType to actually switch voices and sync UI
old_set_type = """    function setNrVoiceType(type) {
      document.getElementById('nrRadioRowGoogle')?.classList.toggle('active', type === 'google');
      document.getElementById('nrRadioRowAi')?.classList.toggle('active', type === 'ai');
      if (type === 'google') {
        showToast('Đã chọn giọng Google cơ bản');
      } else {
        showToast('Đã kích hoạt hệ thống giọng AI đa năng');
      }
    }"""

new_set_type = """    function setNrVoiceType(type) {
      const select = document.getElementById('voiceSelect');
      if (type === 'google') {
        if (select) {
          select.value = 'android_native';
          onVoiceChange('android_native');
        }
        showToast('Đã chuyển sang giọng Google cơ bản');
      } else {
        let lastAi = localStorage.getItem('reader_last_ai_voice') || 'BV074_streaming';
        if (lastAi === 'android_native') lastAi = 'BV074_streaming';
        if (select) {
          select.value = lastAi;
          onVoiceChange(lastAi);
        }
        showToast('Đã kích hoạt hệ thống giọng AI đa năng');
      }
    }"""

if old_set_type in content:
    content = content.replace(old_set_type, new_set_type, 1)
    print("4. Updated setNrVoiceType with actual voice switching & UI sync")
else:
    print("4. Warning: old_set_type not found verbatim!")

# 5. In updateNrPlayerUI: make sure quickVoiceEl gets the real voice from select
content = content.replace(
    "const vText = document.getElementById('nrSelectedVoiceText')?.textContent || 'Ngọc Huyền';\n          quickVoiceEl.textContent = vText;",
    """const select = document.getElementById('voiceSelect');
          const opt = select ? (select.options[select.selectedIndex] || select.querySelector(`option[value="${select.value}"]`)) : null;
          let vName = 'Ngọc Huyền';
          if (opt) {
            vName = (opt.value === 'android_native' || opt.dataset.provider === 'native') ? 'Giọng Google' : opt.textContent.replace(/^[\\s\\p{Emoji}\\u200d\\uFE0F\\uD83C-\\uDBFF\\uDC00-\\uDFFF\\u2600-\\u27BF]+/gu, '').trim();
          }
          quickVoiceEl.textContent = vName || 'Ngọc Huyền';"""
)
print("5. Updated updateNrPlayerUI to read direct option text")

# 6. In updateNrSettingsUI: call syncVoiceUIElements
content = content.replace(
    "if (typeof initOtaSettingsUI === 'function') initOtaSettingsUI();",
    "if (typeof initOtaSettingsUI === 'function') initOtaSettingsUI();\n        if (typeof syncVoiceUIElements === 'function') syncVoiceUIElements();"
)
print("6. Added syncVoiceUIElements to updateNrSettingsUI")

# 7. Bump app version to v1.6.8 (build 168)
content = content.replace("v1.6.7", "v1.6.8")
content = content.replace("CURRENT_APP_BUILD = 167;", "CURRENT_APP_BUILD = 168;")
print("7. Bumped version to v1.6.8 (build 168) in index.html")

# Write to assets and desktop templates
with open(assets_html, "w", encoding="utf-8") as f:
    f.write(content)
print(f"Saved {assets_html}")

with open(desktop_html_d, "w", encoding="utf-8") as f:
    f.write(content)
print(f"Saved {desktop_html_d}")

with open(desktop_html_c, "w", encoding="utf-8") as f:
    f.write(content)
print(f"Saved {desktop_html_c}")

# 8. Bump server.py version to v1.6.8, build 168
for s_path in [desktop_server_d, desktop_server_c]:
    with open(s_path, "r", encoding="utf-8", errors="ignore") as f:
        s_code = f.read()
    s_code = re.sub(r'"version":\s*"[^"]+"', '"version": "v1.6.8"', s_code, count=1)
    s_code = re.sub(r'"version_code":\s*\d+', '"version_code": 168', s_code, count=1)
    old_cl = r'"changelog":\s*\[[^\]]+\]'
    new_cl = '''"changelog": [
                "Đồng bộ tên giọng đọc ra toàn bộ giao diện bên ngoài (Mini player, thanh điều khiển nổi, Cài đặt)",
                "Chuyển đổi tức thì giữa Giọng Google và Giọng AI khi bấm nút chọn",
                "Hiển thị tên giọng chính xác theo thời gian thực"
            ]'''
    s_code = re.sub(old_cl, new_cl, s_code, count=1)
    with open(s_path, "w", encoding="utf-8") as f:
        f.write(s_code)
    print(f"8. Updated {s_path} with v1.6.8 & changelog")

print("\nALL FILES UPDATED WITH VOICE SYNC SUCCESSFULLY!")
