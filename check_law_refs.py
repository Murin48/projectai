"""ตรวจว่าคำตอบของโมเดลอ้างกฎหมาย/ตัวเลขที่ไม่อยู่ใน laws/law_context.md หรือไม่
 
วิธีใช้:
  python check_law_refs.py                      # ตรวจ accuracy_report.json
  python check_law_refs.py result.json          # ตรวจผลจาก run_contract.py
  python check_law_refs.py a.json b.json        # ตรวจหลายไฟล์
 
ไฟล์ผลลัพธ์ต้องเป็น list ของ object ที่มีฟิลด์ clause, issues, suggestion, law_ref
(ถ้าใช้ accuracy_report.json ต้องเพิ่ม "law_ref" ในรายงานก่อน ดูท้ายข้อความในแชท)
 
สิ่งที่สคริปต์นี้ตรวจได้: โมเดลอ้างอิงเรื่องที่ "ไม่มีในไฟล์" หรือไม่
สิ่งที่ตรวจไม่ได้: ตัวไฟล์ law_context.md ถูกต้องและเป็นฉบับปัจจุบันหรือไม่ ต้องตรวจกับราชกิจจาฯ เอง
"""
import json
import re
import sys
from config import LAW_FILE
 
THAI_DIGITS = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")
NUM_UNIT = re.compile(r"\d+(?:วัน|เดือน|ปี|หน่วย|ชั่วโมง)")
YEAR = re.compile(r"พ\.ศ\.?\d{4}")
SECTION = re.compile(r"มาตรา\d+(?:/\d+)?")
 
 
def norm(s: str) -> str:
    """แปลงเลขไทย ลบช่องว่างทั้งหมด เพื่อเทียบข้อความแบบไม่สนใจการเว้นวรรค"""
    return re.sub(r"\s+", "", str(s).translate(THAI_DIGITS))
 
 
def main(paths):
    if not LAW_FILE.exists():
        sys.exit(f"ไม่พบไฟล์กฎหมาย: {LAW_FILE}")
    law_raw = LAW_FILE.read_text(encoding="utf-8").translate(THAI_DIGITS)
    law_n = norm(law_raw)
    law_numbers = set(re.findall(r"\d+", law_raw))
 
    not_found, to_check, total_refs, total_items = [], [], 0, 0
 
    for path in paths:
        data = json.load(open(path, encoding="utf-8"))
        for idx, r in enumerate(data, 1):
            total_items += 1
            clause = r.get("clause", "")
            clause_n = norm(clause)
            label = f"{path} #{idx} | {clause[:40]}..."
 
            # 1) law_ref ต้องอยู่ในไฟล์กฎหมาย
            for ref in r.get("law_ref") or []:
                total_refs += 1
                ref_n = norm(ref)
                if ref_n in law_n:
                    continue
                missing = [n for n in re.findall(r"\d+", ref_n) if n not in law_numbers]
                if missing:
                    not_found.append((label, f"law_ref '{ref}' มีตัวเลขที่ไม่อยู่ในไฟล์กฎหมาย: {missing}"))
                else:
                    to_check.append((label, f"law_ref '{ref}' ตัวเลขอยู่ในไฟล์ แต่ข้อความไม่ตรงเป๊ะ ตรวจมือ"))
 
            # 2) ตัวเลข/มาตราในคำเตือน ต้องมาจากไฟล์กฎหมายหรือข้อสัญญานั้น
            text_n = norm(" ".join([*(r.get("issues") or []), r.get("suggestion") or ""]))
            for pat in (NUM_UNIT, YEAR, SECTION):
                for m in sorted(set(pat.findall(text_n))):
                    if m not in law_n and m not in clause_n:
                        not_found.append((label, f"คำเตือนมี '{m}' ซึ่งไม่อยู่ทั้งในไฟล์กฎหมายและในข้อสัญญา"))
 
    print(f"ตรวจ {total_items} ข้อ, law_ref ทั้งหมด {total_refs} รายการ\n")
    if not_found:
        print(f"❌ อาจมาจากความจำของโมเดล ({len(not_found)} จุด):")
        for label, msg in not_found:
            print(f"  - {label}\n      {msg}")
    if to_check:
        print(f"\n⚠️  ควรตรวจมือ ({len(to_check)} จุด):")
        for label, msg in to_check:
            print(f"  - {label}\n      {msg}")
    if not not_found and not to_check:
        print("✅ ไม่พบการอ้างอิงนอกไฟล์กฎหมาย")
    sys.exit(1 if not_found else 0)
 
 
if __name__ == "__main__":
    main(sys.argv[1:] or ["accuracy_report.json"])