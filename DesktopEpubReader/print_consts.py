import marshal
import sys
sys.stdout.reconfigure(encoding="utf-8")

code = marshal.loads(open('decomp_module.bin', 'rb').read())
for c in code.co_consts:
    if hasattr(c, 'co_consts') and c.co_name == 'ElevenLabsCapCutTTS':
        for sc in c.co_consts:
            if hasattr(sc, 'co_consts'):
                print(f"=== {sc.co_name} ===")
                for i, const in enumerate(sc.co_consts):
                    print(f"  [{i}]: {repr(const)}")
