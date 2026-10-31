import re

p1 = re.compile(r'(?<=[^\W\d_]),\s*(?=[^\W\d_“\"«])')
t1 = 'thế, nhưng cô ấy'
print("Replaced:", p1.sub(', —— ', t1).encode('utf-8'))
