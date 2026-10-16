import marshal
import dis

code = marshal.loads(open('decomp_module.bin', 'rb').read())
with open('decompiled_methods.txt', 'w', encoding='utf-8') as out:
    for c in code.co_consts:
        if hasattr(c, 'co_consts'):
            out.write(f"Class/Func: {c.co_name}\n")
            for sc in c.co_consts:
                if hasattr(sc, 'co_consts'):
                    out.write(f"\n--- Method: {sc.co_name} ---\n")
                    out.write(f"Constants: {sc.co_consts}\n")
                    out.write(f"Varnames: {sc.co_varnames}\n")
                    dis.dis(sc, file=out)

print("Saved to decompiled_methods.txt")
