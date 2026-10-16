import marshal
import sys

sys.stdout.reconfigure(encoding="utf-8")
code = marshal.loads(open('decomp_module.bin', 'rb').read())
for i, const in enumerate(code.co_consts):
    if not hasattr(const, 'co_consts'):
        print(f"[{i}] {type(const).__name__}: {repr(const)[:100]}")
