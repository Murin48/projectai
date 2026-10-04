"""ชุดทดสอบความแม่นยำของ LeaseCheck
 
วิธีรัน:  python accuracy_test.py
ป้ายกำกับ (expected) ในไฟล์นี้เป็นดุลยพินิจของผู้เขียน ควรให้ผู้รู้กฎหมายหรือ สคบ. ตรวจก่อนใช้เป็นเกณฑ์จริง
 
  high = ต้องได้ risk "high"
  flag = ต้องได้ "medium" หรือ "high" (แอปต้องเตือน)
  ok   = ต้องได้ "low" (ถ้าเตือนถือว่าเตือนเกินจริง)
"""
import json
from extract import split_clauses
from analyze import analyze_clauses
from overview import summarize_contract
 
CONTRACTS = {
    "A_เอาเปรียบ": [
        ("ค่าเช่าห้องเดือนละ 4,500 บาท ชำระภายในวันที่ 5 ของทุกเดือน ตลอดอายุสัญญา 12 เดือน", "ok"),
        ("ผู้เช่าไม่มีสิทธิ์ขอคืนเงินประกันในทุกกรณี หากย้ายออกก่อนครบสัญญา ไม่ว่าด้วยเหตุใดก็ตาม", "high"),
        ("ผู้ให้เช่ามีสิทธิ์เข้าห้องพักได้ทุกเวลาโดยไม่ต้องแจ้งให้ผู้เช่าทราบล่วงหน้า", "flag"),
        ("ผู้ให้เช่าปรับขึ้นค่าเช่าได้ทุกเมื่อตามที่เห็นสมควร โดยไม่ต้องแจ้งผู้เช่าล่วงหน้า", "flag"),
        ("ค่าไฟหน่วยละ 15 บาท ค่าน้ำหน่วยละ 100 บาท โดยผู้ให้เช่ากำหนดและเปลี่ยนอัตราได้เอง", "flag"),
        ("หากผู้เช่าชำระค่าเช่าล่าช้าเกิน 1 วัน ต้องเสียค่าปรับวันละ 500 บาท และผู้ให้เช่ายึดทรัพย์สินในห้องได้ทันที", "flag"),
        ("ผู้ให้เช่าหักเงินประกันเป็นค่าทำความสะอาดและค่าเสียหายตามจำนวนที่ผู้ให้เช่ากำหนดฝ่ายเดียว โดยไม่ต้องแสดงหลักฐาน", "flag"),
        ("ผู้เช่าต้องไม่นำสัตว์เลี้ยงเข้ามาเลี้ยงในห้องพัก", "ok"),
    ],
    "B_เป็นธรรม": [
        ("ค่าเช่าห้องเดือนละ 4,500 บาท ชำระภายในวันที่ 5 ของทุกเดือน", "ok"),
        ("ผู้เช่าวางเงินประกัน 2 เดือน เป็นเงิน 9,000 บาท ผู้ให้เช่าจะคืนภายใน 30 วันนับแต่ผู้เช่าส่งมอบห้อง "
         "หลังหักค่าเสียหายที่เกิดขึ้นจริงพร้อมแสดงหลักฐานให้ผู้เช่าตรวจสอบ", "ok"),
        ("ผู้ให้เช่าจะแจ้งผู้เช่าล่วงหน้าอย่างน้อย 24 ชั่วโมงก่อนเข้าห้อง ยกเว้นกรณีฉุกเฉิน เช่น ไฟไหม้หรือน้ำรั่ว", "ok"),
        ("ค่าน้ำค่าไฟคิดตามมิเตอร์ในอัตราเดียวกับที่หน่วยงานรัฐเรียกเก็บ ไม่บวกเพิ่ม", "ok"),
        ("ผู้เช่าบอกเลิกสัญญาก่อนกำหนดได้ โดยแจ้งเป็นหนังสือล่วงหน้า 30 วัน", "ok"),
        ("ค่าเช่าคงที่ตลอดอายุสัญญา 12 เดือน หากจะปรับเมื่อต่อสัญญา ต้องตกลงร่วมกันเป็นลายลักษณ์อักษร", "ok"),
        ("ผู้ให้เช่ารับผิดชอบซ่อมแซมโครงสร้างอาคารและระบบน้ำไฟที่ชำรุดจากการใช้งานตามปกติ", "ok"),
        ("ผู้เช่าต้องไม่ส่งเสียงดังรบกวนผู้พักอาศัยห้องอื่นหลังเวลา 22.00 น.", "ok"),
    ],
    "C_ขาดเงื่อนไข": [
        ("ค่าเช่าห้องเดือนละ 5,000 บาท ชำระภายในวันที่ 1 ของทุกเดือน", "ok"),
        ("สัญญาเช่ามีอายุ 12 เดือน นับตั้งแต่วันที่ผู้เช่าเข้าพักวันแรก", "ok"),
        ("ผู้เช่าวางเงินประกัน 10,000 บาท ในวันทำสัญญา", "ok"),
        ("ค่าน้ำค่าไฟคิดตามมิเตอร์ ตามอัตราที่หน่วยงานรัฐกำหนด", "ok"),
        ("ผู้เช่าต้องไม่ดัดแปลงต่อเติมห้องพักโดยไม่ได้รับอนุญาตจากผู้ให้เช่า", "ok"),
    ],
}
 
# สัญญา C ต้องถูกชี้ว่าขาดเรื่องเหล่านี้ (ตรงกับคำใดคำหนึ่งในแต่ละกลุ่มถือว่าผ่าน)
C_EXPECT_MISSING = {
    "กำหนดคืนเงินประกัน": ("คืน",),
    "ความรับผิดชอบการซ่อมแซม": ("ซ่อม",),
    "การต่อสัญญา": ("ต่อสัญญา", "ต่ออายุ"),
}
 
 
def check(expected: str, risk: str) -> bool:
    if expected == "high":
        return risk == "high"
    if expected == "flag":
        return risk in ("medium", "high")
    return risk == "low"
 
 
def main():
    report, bad = [], {"n": 0, "caught": 0}
    high = {"n": 0, "ok": 0}
    good = {"n": 0, "false_alarm": 0}
    unknown = 0
 
    for name, items in CONTRACTS.items():
        print(f"\n===== {name} =====")
        texts = [t for t, _ in items]
        raw = "\n".join(f"ข้อ {i} {t}" for i, t in enumerate(texts, 1))
        clauses = split_clauses(raw)
        if len(clauses) != len(texts):
            print(f"⚠️  แบ่งข้อได้ {len(clauses)} จาก {len(texts)} ข้อ (ตัวแบ่งข้อมีปัญหา) ใช้รายการตรงแทน")
            clauses = texts
        results = analyze_clauses(clauses)
 
        for (text, exp), r in zip(items, results):
            risk = r.get("risk", "unknown")
            if risk == "unknown":
                unknown += 1
                print(f"⚪ ข้ามผล (วิเคราะห์ไม่สำเร็จ): {text[:40]}...")
                continue
            passed = check(exp, risk)
            if exp in ("flag", "high"):
                bad["n"] += 1
                bad["caught"] += risk in ("medium", "high")
            if exp == "high":
                high["n"] += 1
                high["ok"] += risk == "high"
            if exp == "ok":
                good["n"] += 1
                good["false_alarm"] += risk != "low"
            print(f"{'✅' if passed else '❌'} คาด={exp:<4} ได้={risk:<6} {text[:45]}...")
            report.append({"contract": name, "clause": text, "expected": exp, "got": risk,
                           "passed": passed, "summary": r.get("summary"), "issues": r.get("issues"),
                           "law_ref": r.get("law_ref")})
 
        if name.startswith("C_"):
            ov = summarize_contract(clauses)
            missing = " ".join(ov["missing"]) if ov else ""
            print("--- ตรวจช่อง 'สัญญาไม่ได้พูดถึง' ---")
            if ov is None:
                print("⚪ สรุปภาพรวมไม่สำเร็จ ข้ามการตรวจ")
            for label, kws in C_EXPECT_MISSING.items():
                if ov is not None:
                    print(f"{'✅' if any(k in missing for k in kws) else '❌'} {label}")
 
    print("\n===== สรุปผล =====")
    if bad["n"]:
        print(f"จับข้อเอาเปรียบได้: {bad['caught']}/{bad['n']} ({bad['caught'] / bad['n']:.0%})")
    if high["n"]:
        print(f"ข้อที่ควรเป็น 'เสี่ยงสูง' ได้ถูก: {high['ok']}/{high['n']}")
    if good["n"]:
        print(f"เตือนเกินจริงในข้อปกติ: {good['false_alarm']}/{good['n']} ({good['false_alarm'] / good['n']:.0%})")
    if unknown:
        print(f"วิเคราะห์ไม่สำเร็จ {unknown} ข้อ (ไม่นับในคะแนน) รันใหม่เพื่อเติมให้ครบ")
 
    with open("accuracy_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("บันทึกรายละเอียดที่ accuracy_report.json")
 
 
if __name__ == "__main__":
    main()