import os

file_path = r'D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\templates\index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = """        return {
          isDialogue: true,
          speaker: speaker,
          gender: gender,
          emotion: emotion,
          manner: manner,
          speedFactor: speedFactor,
          pitchFactor: pitchFactor
        };
      } catch (err) {
        console.warn('[Dialogue Attribution Exception]', err);
        return { isDialogue: false, gender: 'narration', emotion: 'normal', speedFactor: 1.0, pitchFactor: 1.0, speaker: '' };
      }
    }
    }

    function analyzeDialogueGender"""

replacement = """        return {
          isDialogue: true,
          speaker: speaker,
          gender: gender,
          emotion: emotion,
          manner: manner,
          speedFactor: speedFactor,
          pitchFactor: pitchFactor
        };
      } catch (err) {
        console.warn('[Dialogue Attribution Exception]', err);
        return { isDialogue: false, gender: 'narration', emotion: 'normal', speedFactor: 1.0, pitchFactor: 1.0, speaker: '' };
      }
    }

    function analyzeDialogueGender"""

if target in content:
    content = content.replace(target, replacement, 1)
    print("Target found and replaced directly!")
else:
    # try crlf / lf normalizing
    target_lf = target.replace('\r\n', '\n')
    replacement_lf = replacement.replace('\r\n', '\n')
    content_lf = content.replace('\r\n', '\n')
    if target_lf in content_lf:
        content = content_lf.replace(target_lf, replacement_lf, 1)
        print("Target found and replaced with LF normalization!")
    else:
        print("ERROR: Target not found in file!")
        exit(1)

# Bump version to v1.6.37 / 197
content = content.replace('v1.6.36</span>', 'v1.6.37</span>')
content = content.replace('v1.6.36</b>', 'v1.6.37</b>')
content = content.replace("const CURRENT_APP_VERSION = 'v1.6.36';", "const CURRENT_APP_VERSION = 'v1.6.37';")
content = content.replace("const CURRENT_APP_BUILD = 196;", "const CURRENT_APP_BUILD = 197;")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated DesktopEpubReader/templates/index.html successfully!")
