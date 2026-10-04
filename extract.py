import re
from pypdf import PdfReader

THAI_DIGITS = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")

# รูปแบบหัวข้อที่ลองตามลำดับ (ต้องอยู่ต้นบรรทัดเท่านั้น)
PATTERNS = [
    r"^[ \t]*ข้อ[ \t]*\d+",       # ข้อ 1
    r"^[ \t]*\d+[.)][ \t]+",      # 1.  หรือ  1)
]


def clean_thai(text: str) -> str:
    """แก้ตัวอักษรไทยเพี้ยนที่ pypdf มักทำกับ PDF บางไฟล์ เช่น 'ท า' -> 'ทำ', 'น ้า' -> 'น้ำ'"""
    text = re.sub(r"[\u0600-\u06FF]", "", text)                        # ตัวอักษรอาหรับที่หลุดมา
    text = re.sub(r"([ก-ฮ])[ \t]+([\u0e48-\u0e4b])า", r"\1\2ำ", text)  # น ้า -> น้ำ, ต ่า -> ต่ำ
    text = re.sub(r"([ก-ฮ])[ \t]+า", r"\1ำ", text)                     # ท า -> ทำ
    text = re.sub("\u0e47[ \t]+", "\u0e47", text)                       # เป็ น -> เป็น
    return text


   
def read_pdf(source) -> str:   # รับได้ทั้ง path และไฟล์ที่อัปโหลด
    """ดึงข้อความจาก PDF (ใช้ไม่ได้กับไฟล์สแกนที่เป็นรูปภาพ)"""
    reader = PdfReader(source)
    raw = "\n".join(page.extract_text() or "" for page in reader.pages)
    return clean_thai(raw)


def split_clauses(text: str) -> list[str]:
    """แบ่งสัญญาเป็นข้อ ๆ โดยลองหลายรูปแบบ แล้วใช้รูปแบบแรกที่แบ่งได้อย่างน้อย 3 ข้อ"""
    text = text.translate(THAI_DIGITS)  # แปลงเลขไทยเป็นเลขอารบิก
    for pat in PATTERNS:
        parts = re.split(f"(?m)(?={pat})", text)
        # ทิ้งส่วนนำก่อนข้อ 1 (เช่น 'สัญญานี้ทำขึ้นระหว่าง...') ที่ไม่ได้ขึ้นต้นด้วยหัวข้อ
        parts = [p.strip() for p in parts if re.match(pat, p.lstrip("\n"), re.M)]
        parts = [p for p in parts if len(p) > 20]
        if len(parts) >= 3:
            return parts
    # แบ่งไม่ได้เลย: ส่งทั้งฉบับเป็นก้อนเดียว ดีกว่าตัดผิด
    return [text.strip()] if text.strip() else []