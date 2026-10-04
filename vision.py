import io
from google.genai import types
from analyze import client, MODELS, _exhausted
from extract import read_pdf
 
MIN_TEXT_CHARS = 100  # PDF ที่ดึงข้อความได้น้อยกว่านี้ ถือว่าเป็นไฟล์สแกน
 
TRANSCRIBE_PROMPT = """ถอดข้อความทั้งหมดในไฟล์สัญญาเช่านี้ออกมาเป็นข้อความธรรมดา
- เรียงตามลำดับเดิม คงหัวข้อ เช่น "ข้อ 1", "ข้อ 2" ไว้ที่ต้นบรรทัดทุกข้อ
- คัดลอกตามที่เห็นเท่านั้น ห้ามสรุป ห้ามแปล ห้ามเติมหรือแก้ข้อความ
- ถ้ามีส่วนที่อ่านไม่ออก ให้ใส่ [อ่านไม่ออก] แทน อย่าเดา
- ไม่ต้องใช้ markdown ไม่ต้องมีคำอธิบายเพิ่ม"""
 
 
def transcribe(data: bytes, mime: str) -> str:
    """ให้ Gemini อ่านรูป/PDF สแกนแล้วคืนเป็นข้อความ"""
    part = types.Part.from_bytes(data=data, mime_type=mime)
    last_error = None
    for model in [m for m in MODELS if m not in _exhausted]:
        try:
            resp = client.models.generate_content(model=model, contents=[part, TRANSCRIBE_PROMPT])
            text = (resp.text or "").strip()
            if text:
                return text
        except Exception as e:
            last_error = e
            print(f"⚠️  {model} ถอดข้อความไม่สำเร็จ: {str(e)[:300]}")
    raise RuntimeError(f"ถอดข้อความจากไฟล์ไม่สำเร็จ ({last_error})")
 
 
def load_contract(files) -> str:
    """รับไฟล์ที่อัปโหลดได้หลายไฟล์ (PDF/รูป) คืนข้อความรวมตามลำดับไฟล์"""
    parts = []
    for f in files:
        data = f.getvalue()
        if f.type == "application/pdf":
            text = read_pdf(io.BytesIO(data))
            if len(text.strip()) >= MIN_TEXT_CHARS:
                parts.append(text)  # PDF ที่เลือกข้อความได้ ไม่ต้องเสียโควตา
                continue
        parts.append(transcribe(data, f.type))
    return "\n".join(parts)
 