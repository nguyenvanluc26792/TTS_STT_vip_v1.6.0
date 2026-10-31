import os
import re

html_path = r'D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\templates\index.html'
assets_path = r'c:\Users\VANLUC\Downloads\Share tool -20261010T221918Z-1-001\Share tool\TTS_STT_vip_v1.6.0\HonorEpubReader\app\src\main\assets\index.html'

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Client-side fallback search function
client_search_code = """
    async function searchNovelClientSideDirect(keyword) {
      try {
        const q = encodeURIComponent(keyword.trim());
        const targetUrl = `https://truyenfullmoi.net/tim-kiem?tukhoa=${q}`;
        let html = '';
        try {
          const r = await fetch(targetUrl);
          if (r.ok) html = await r.text();
        } catch(e) {}

        if (!html) {
          try {
            const proxyUrl = `https://api.allorigins.win/raw?url=${encodeURIComponent(targetUrl)}`;
            const r2 = await fetch(proxyUrl);
            if (r2.ok) html = await r2.text();
          } catch(e2) {}
        }

        if (html) {
          const parser = new DOMParser();
          const doc = parser.parseFromString(html, 'text/html');
          const rows = doc.querySelectorAll('.list-truyen .row');
          const results = [];
          rows.forEach((row, i) => {
            if (i >= 12) return;
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
          if (results.length > 0) {
            return { success: true, results: results, count: results.length };
          }
        }
      } catch(e) {
        console.warn('Lỗi searchNovelClientSideDirect:', e);
      }
      return { success: false, results: [] };
    }
"""

if 'async function searchNovelClientSideDirect' not in content:
    content = content.replace('async function performWebNovelSearch(rawInput) {', client_search_code + '\n    async function performWebNovelSearch(rawInput) {')
    print("Đã thêm searchNovelClientSideDirect fallback!")

# Thay thế khối fetch trong performWebNovelSearch
old_fetch_block = """      try {
        const res = await fetch('/api/web-novel/search', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ keyword: keyword })
        });
        const data = await res.json();"""

new_fetch_block = """      try {
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
        }"""

if old_fetch_block in content:
    content = content.replace(old_fetch_block, new_fetch_block)
    print("Đã cập nhật fetch block trong performWebNovelSearch!")
else:
    print("WARN: Không tìm thấy old_fetch_block chính xác, kiểm tra lại regex!")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Đã lưu DesktopEpubReader/templates/index.html")

with open(assets_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Đã đồng bộ sang HonorEpubReader/app/src/main/assets/index.html")
