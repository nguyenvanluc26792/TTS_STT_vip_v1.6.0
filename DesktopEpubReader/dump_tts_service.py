import marshal
import sys

sys.stdout.reconfigure(encoding="utf-8")
code = marshal.loads(open('decomp_tts_service.bin', 'rb').read())
print("Module co_name:", code.co_name)
for i, const in enumerate(code.co_consts):
    if hasattr(const, 'co_consts'):
        print(f"Func/Class: {const.co_name}")
        for j, sc in enumerate(const.co_consts):
            if isinstance(sc, (str, tuple)) and len(str(sc)) < 150:
                print(f"  {sc}")
    elif isinstance(const, str) and len(const) < 150:
        print(f"Const [{i}]: {const}")
