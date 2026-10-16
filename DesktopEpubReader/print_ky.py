import marshal

code = marshal.loads(open('decomp_tts_service.bin', 'rb').read())
for c in code.co_consts:
    if hasattr(c, 'co_consts') and c.co_name in ['_ky_payload', '_ky_header', '_tao_task', '_hoi_task']:
        print(f"=== {c.co_name} ===")
        print("Constants:", c.co_consts)
        print("Varnames:", c.co_varnames)
        print("Names:", c.co_names)
