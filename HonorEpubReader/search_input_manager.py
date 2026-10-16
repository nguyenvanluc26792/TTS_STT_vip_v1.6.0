import zipfile

apk_path = r"c:\Users\VANLUC\Downloads\阅读_8.2.7.300_1.apk"
with zipfile.ZipFile(apk_path, 'r') as z:
    for dex_name in z.namelist():
        if dex_name.endswith('.dex'):
            data = z.read(dex_name)
            if b'InputManager' in data:
                print(f"Found InputManager in {dex_name}")
                # check occurrences of strings
                for line in data.split(b'\x00'):
                    if b'InputManagerEx' in line:
                        print(f"  String: {line}")
                    if b'notifyEbook' in line:
                        print(f"  String: {line}")
