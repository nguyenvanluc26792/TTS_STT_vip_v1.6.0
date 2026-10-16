import sys
from loguru import logger
logger.remove()
logger.add(sys.stderr, level="ERROR")

from androguard.core.apk import APK

apk = APK(r"c:\Users\VANLUC\Downloads\阅读_8.2.7.300_1.apk")
print("=== PERMISSIONS ===")
for p in apk.get_permissions():
    if any(k in p.lower() for k in ["honor", "huawei", "sensor", "eye", "input", "system"]):
        print("  Permission:", p)

manifest = apk.get_android_manifest_xml()
print("\n=== METADATA ===")
for elem in manifest.iter():
    if elem.tag.endswith('meta-data'):
        name = elem.attrib.get('{http://schemas.android.com/apk/res/android}name', '')
        val = elem.attrib.get('{http://schemas.android.com/apk/res/android}value', '')
        print(f"  {name} = {val}")

print("\n=== READER ACTIVITY IN MANIFEST ===")
for elem in manifest.iter():
    if elem.tag.endswith('activity') or elem.tag.endswith('activity-alias'):
        name = elem.attrib.get('{http://schemas.android.com/apk/res/android}name', '')
        if "ReaderActivity" in name:
            print(f"Tag: {elem.tag}, Name: {name}")
            for k, v in elem.attrib.items():
                print(f"    {k.split('}')[-1]}: {v}")
