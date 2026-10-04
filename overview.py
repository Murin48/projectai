from analyze import _call
from privacy import redact
 
OVERVIEW_SYSTEM = """คุณคือผู้ช่วยสรุปสัญญาเช่าที่พักในประเทศไทย อ่านสัญญาทั้งฉบับที่ได้รับ แล้วตอบเป็น JSON เท่านั้น ตามรูปแบบนี้:
{
  "rent": "ค่าเช่าต่อเดือน",
  "deposit": "เงินประกัน/มัดจำ และเงื่อนไขการคืน",
  "duration": "ระยะเวลาสัญญา",
  "utilities": "ค่าน้ำ ค่าไฟ ค่าส่วนกลาง อัตราที่ระบุ",
  "penalty": "ค่าปรับหรือเงื่อนไขการยกเลิกก่อนกำหนด",
  "missing": ["เรื่องสำคัญที่สัญญาไม่ได้พูดถึงเลย"]
}
กฎ:
- ใช้ข้อมูลที่เขียนในสัญญาเท่านั้น ห้ามเดาหรือเติมเอง
- ถ้าไม่พบข้อมูลในช่องใด ให้ใส่ "ไม่ระบุในสัญญา"
- ช่อง missing ให้ตรวจว่าสัญญามีเรื่องเหล่านี้หรือไม่: กำหนดวันคืนเงินประกัน, เงื่อนไขการหักเงินประกัน,
  การขึ้นค่าเช่าระหว่างสัญญา, การแจ้งล่วงหน้าก่อนเจ้าของเข้าห้อง, การซ่อมแซมว่าใครรับผิดชอบ, การต่อสัญญา
  ถ้าไม่มีให้ใส่ใน missing ถ้ามีครบให้ใส่ []
- ใช้ภาษาไทยที่เข้าใจง่าย"""
 
FIELDS = ["rent", "deposit", "duration", "utilities", "penalty"]
 
 
def summarize_contract(clauses: list[str]) -> dict | None:
    """สรุปภาพรวมทั้งฉบับ 1 คำขอ คืน None ถ้าไม่สำเร็จ (แอปยังใช้งานต่อได้)"""
    try:
        data = _call(OVERVIEW_SYSTEM, redact("\n\n".join(clauses)))
    except Exception as e:
        print(f"⚠️  สรุปภาพรวมไม่สำเร็จ: {e}")
        return None
    if not isinstance(data, dict) or not all(k in data for k in FIELDS):
        return None
    if not isinstance(data.get("missing"), list):
        data["missing"] = []
    return data