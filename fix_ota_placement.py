import re

html_path = r'D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\templates\index.html'
assets_path = r'c:\Users\VANLUC\Downloads\Share tool -20261010T221918Z-1-001\Share tool\TTS_STT_vip_v1.6.0\HonorEpubReader\app\src\main\assets\index.html'

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Xóa khối OTA cũ bị đặt ngoài nrViewSettings
stray_ota_pattern = r'<!-- 7\. Cập nhật ứng dụng OTA Siêu Nhẹ[\s\S]*?</div>\s*</div>\s*(?=\s*</div>\s*<!-- KẾT THÚC nrViewPagerTrack -->)'
if re.search(stray_ota_pattern, content):
    content = re.sub(stray_ota_pattern, '', content)
    print("Đã xóa khối OTA lạc bên ngoài nrViewPagerTrack!")

# 2. Tạo Card Cập nhật OTA chuẩn, nổi bật đặt NGAY ĐẦU tab Cài Đặt (dưới tiêu đề Cài đặt)
ota_card_top = """
        <!-- CẬP NHẬT ỨNG DỤNG OTA SIÊU TỐC (~370KB) -->
        <div class="nr-card-title" style="color:var(--nr-accent); font-weight:700; display:flex; justify-content:space-between; align-items:center;">
          <span>⚡ Cập nhật ứng dụng OTA</span>
          <span id="nrOtaBadge" style="font-size:0.75rem; padding:2px 8px; border-radius:99px; background:rgba(239,68,68,0.18); color:#ef4444; font-weight:700;">v1.6.1</span>
        </div>
        <div class="nr-card" style="border: 1.5px solid rgba(239, 68, 68, 0.35); background: linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(249, 115, 22, 0.05)); border-radius: 18px; padding: 12px 16px; margin-bottom: 14px;">
          <div style="font-size:0.78rem; color:#b0b2c4; line-height:1.45; margin-bottom:10px;">
            Cập nhật giao diện, thuật toán đọc ngắt từng câu, sửa lỗi trong <b>1 giây (~370 KB)</b> mà <b>không cần tải lại file APK 60MB</b>.
          </div>

          <div style="display:flex; gap:8px;">
            <button id="btnNrCheckOta" class="nr-chip-btn active" style="flex:1; padding:9px 12px; background:#ef4444; border-color:#ef4444; color:#fff; font-weight:700; font-size:0.84rem; display:flex; align-items:center; justify-content:center; gap:6px; box-shadow: 0 4px 12px rgba(239, 68, 68, 0.35);" onclick="checkAndUpdateOta()">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/></svg>
              <span>Cập nhật OTA ngay</span>
            </button>
            <button id="btnNrResetOta" class="nr-chip-btn" style="padding:9px 12px; font-size:0.78rem; border-color:#404254; color:#a0a2b8;" onclick="resetOta()">
              Khôi phục gốc
            </button>
          </div>
          <div id="nrOtaStatusText" style="font-size:0.78rem; margin-top:10px; display:none; line-height:1.45; padding:8px 10px; border-radius:8px; background:rgba(0,0,0,0.35);"></div>
        </div>
"""

# Chèn ngay sau <div class="nr-page-title-center">Cài đặt</div>
target_anchor = '<div class="nr-page-title-center">Cài đặt</div>'
if target_anchor in content:
    content = content.replace(target_anchor, target_anchor + "\n" + ota_card_top, 1)
    print("Đã chèn OTA Card chuẩn ngay đầu nrViewSettings!")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Đã cập nhật file DesktopEpubReader/templates/index.html")

with open(assets_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Đã đồng bộ sang HonorEpubReader/app/src/main/assets/index.html")
