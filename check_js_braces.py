with open(r'D:\3. DOCUMENT\Antigravity\TTS_STT_vip_v1.6.0\DesktopEpubReader\templates\index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
script_start = text.find('<script')
idx = text.find('>', script_start) + 1
code = text[idx:text.find('</script>', idx)]

in_single = False
in_double = False
in_template = False
in_block_comment = False
stack = []
extra_closes = []

for line_no, line in enumerate(code.split('\n'), 1):
    i = 0
    while i < len(line):
        c = line[i]
        nxt = line[i+1] if i+1 < len(line) else ''
        if in_block_comment:
            if c == '*' and nxt == '/':
                in_block_comment = False
                i += 1
        elif in_single:
            if c == '\\':
                i += 1
            elif c == "'":
                in_single = False
        elif in_double:
            if c == '\\':
                i += 1
            elif c == '"':
                in_double = False
        elif in_template:
            if c == '\\':
                i += 1
            elif c == '`':
                in_template = False
            elif c == '$' and nxt == '{':
                stack.append(('${', line_no))
                i += 1
        else:
            if c == '/' and nxt == '/':
                break
            elif c == '/' and nxt == '*':
                in_block_comment = True
                i += 1
            elif c == "'":
                in_single = True
            elif c == '"':
                in_double = True
            elif c == '`':
                in_template = True
            elif c == '{':
                stack.append(('{', line_no))
            elif c == '}':
                if not stack:
                    extra_closes.append((line_no, line.strip()))
                else:
                    stack.pop()
        i += 1

print(f'Extra closing braces: {len(extra_closes)}')
for ec in extra_closes:
    print(f'  Line {ec[0]}: {ec[1]}')
print(f'Unclosed opening braces: {len(stack)}')
for op in stack[:10]:
    print(f'  Line {op[1]}: {op[0]}')
