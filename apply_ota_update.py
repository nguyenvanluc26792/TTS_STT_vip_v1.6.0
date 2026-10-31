import os
import re

html_path = r'D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\templates\index.html'
assets_path = r'c:\Users\VANLUC\Downloads\Share tool -20261010T221918Z-1-001\Share tool\TTS_STT_vip_v1.6.0\HonorEpubReader\app\src\main\assets\index.html'

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Thêm Card Cập nhật OTA vào cuối nrViewSettings
ota_card_html = """
        <!-- 7. Cập nhật ứng dụng OTA Siêu Nhẹ (~370KB) -->
        <div class="nr-card-title">Cập nhật ứng dụng</div>
        <div class="nr-card" style="border: 1px solid rgba(239, 68, 68, 0.28); background: linear-gradient(135deg, rgba(239, 68, 68, 0.08), rgba(249, 115, 22, 0.04)); border-radius: 18px; padding: 14px 16px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <div style="display:flex; align-items:center; gap:8px;">
              <span style="font-size:1.2rem;">⚡</span>
              <div>
                <div class="nr-settings-row-label" style="font-weight:700; color:var(--nr-accent); font-size:0.95rem;">Cập nhật OTA Siêu Nhẹ</div>
                <div style="font-size:0.75rem; color:#888aa0;">Tải nhanh ~370 KB trong 1 giây (Không cần cài lại APK 60MB)</div>
              </div>
            </div>
            <span id="nrOtaBadge" style="font-size:0.75rem; padding:3px 9px; border-radius:99px; background:rgba(239,68,68,0.15); color:#ef4444; font-weight:700; letter-spacing:0.3px;">v1.6.1</span>
          </div>

          <div style="display:flex; gap:8px; margin-top:12px;">
            <button id="btnNrCheckOta" class="nr-chip-btn active" style="flex:1; padding:9px 12px; background:#ef4444; border-color:#ef4444; color:#fff; font-weight:600; font-size:0.84rem; display:flex; align-items:center; justify-content:center; gap:6px;" onclick="checkAndUpdateOta()">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/></svg>
              <span>Cập nhật OTA ngay</span>
            </button>
            <button id="btnNrResetOta" class="nr-chip-btn" style="padding:9px 12px; font-size:0.8rem; border-color:#404254; color:#a0a2b8;" onclick="resetOta()">
              Khôi phục gốc
            </button>
          </div>
          <div id="nrOtaStatusText" style="font-size:0.78rem; margin-top:10px; display:none; line-height:1.45; padding:8px 10px; border-radius:8px; background:rgba(0,0,0,0.25);"></div>
        </div>
"""

# Chèn trước </div> đóng của nrViewSettings
if 'id="nrOtaBadge"' not in content:
    # Tìm thẻ đóng của nrViewSettings
    match = re.search(r'(<!-- 6\. Hiển thị & Hẹn giờ -->[\s\S]*?</div>\s*</div>)(\s*</div>\s*<!-- KẾT THÚC nrViewPagerTrack -->)', content)
    if match:
        content = content[:match.end(1)] + "\n" + ota_card_html + content[match.end(1):]
        print("Đã chèn OTA Card vào nrViewSettings thành công!")
    else:
        print("WARN: Không tìm thấy vị trí chèn OTA Card regex 1!")

# 2. Thêm JS Engine cho OTA
ota_js = """
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
"""

if 'function checkAndUpdateOta()' not in content:
    content = content.replace('window.addEventListener(\'DOMContentLoaded\', () => {', ota_js + '\n    window.addEventListener(\'DOMContentLoaded\', () => {\n      checkOtaStatusBadge();')
    print("Đã thêm JS OTA Engine thành công!")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Đã ghi đè file DesktopEpubReader/templates/index.html")

with open(assets_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Đã đồng bộ sang HonorEpubReader/app/src/main/assets/index.html")
