import os
from pathlib import Path
from dotenv import load_dotenv
 
load_dotenv()
 
BASE_DIR = Path(__file__).parent
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.7-flash")
REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "5"))
LAW_FILE = BASE_DIR / "laws" / "law_context.md"
 
DISCLAIMER = "⚠️ ข้อมูลนี้เป็นเพียงคำอธิบายเบื้องต้น ไม่ใช่คำปรึกษาทางกฎหมาย ควรตรวจสอบกับผู้เชี่ยวชาญก่อนตัดสินใจเรื่องสำคัญ"
 
if not os.getenv("GEMINI_API_KEY"):
    print("⚠️  ยังไม่ได้ตั้งค่า GEMINI_API_KEY (ดูไฟล์ .env.example)")
