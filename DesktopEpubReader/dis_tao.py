import marshal

code = marshal.loads(open('decomp_tts_service.bin', 'rb').read())
for c in code.co_consts:
    if hasattr(c, 'co_consts') and c.co_name == '_tao_task':
        print("tao_task bytecode length:", len(c.co_code))
        # print byte by byte instructions
        co = c.co_code
        i = 0
        while i < len(co):
            op = co[i]
            arg = co[i+1] if i+1 < len(co) else 0
            # Opcode 100 is LOAD_CONST in many versions
            print(f"{i:4d}: op={op:3d} arg={arg:3d}")
            i += 2
            if i > 80: break
