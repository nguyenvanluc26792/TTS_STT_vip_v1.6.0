import marshal

code = marshal.loads(open('decomp_tts_service.bin', 'rb').read())
for c in code.co_consts:
    if hasattr(c, 'co_consts') and c.co_name == '_nen_tang_giong':
        print("Constants:", c.co_consts)
        print("Varnames:", c.co_varnames)
        print("Names:", c.co_names)
