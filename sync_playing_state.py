path = r'D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\templates\index.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update playParagraph highlight block
old_hl = '''      highlightActiveSentence(idx, true);
      saveProgress();'''

new_hl = '''      highlightActiveSentence(idx, true);
      saveProgress();
      window.isPlaying = true;
      if (typeof updateHonorMediaPillState === 'function') updateHonorMediaPillState();'''

if old_hl in content:
    content = content.replace(old_hl, new_hl, 1)
    print('1. playParagraph highlight sync updated!')
else:
    print('1. Warning: old_hl not found!')

# 2. Update updatePlayBtn to explicitly set window.isPlaying
old_upd_btn = '''      updateNrPlayerUI();
      syncMediaSensorState(isPlaying);'''

new_upd_btn = '''      window.isPlaying = isPlaying;
      updateNrPlayerUI();
      syncMediaSensorState(isPlaying);'''

if old_upd_btn in content:
    content = content.replace(old_upd_btn, new_upd_btn, 1)
    print('2. updatePlayBtn window.isPlaying updated!')
else:
    print('2. Warning: old_upd_btn not found!')

# 3. Update pauseAudio to explicitly set window.isPlaying = false
old_pause_audio = '''    function pauseAudio() {
      currentPlaybackSessionId++;
      isPlaying = false;'''

new_pause_audio = '''    function pauseAudio() {
      currentPlaybackSessionId++;
      isPlaying = false;
      window.isPlaying = false;'''

if old_pause_audio in content:
    content = content.replace(old_pause_audio, new_pause_audio, 1)
    print('3. pauseAudio window.isPlaying updated!')
else:
    print('3. Warning: old_pause_audio not found!')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Finished writing updates!')
