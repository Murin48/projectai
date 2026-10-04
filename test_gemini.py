from google import genai
from config import MODEL

client = genai.Client()

print("โมเดลที่ตั้งไว้ใน .env:", MODEL)
print()

try:
    r = client.models.generate_content(model=MODEL, contents="ตอบว่า OK")
    print("✅ เรียกสำเร็จ:", r.text)
except Exception as e:
    print("❌ error เต็ม:")
    print(e)

print()
print("โมเดลที่บัญชีคุณเรียกใช้ได้:")
try:
    for m in client.models.list():
        if "generateContent" in (m.supported_actions or []):
            print(" -", m.name)
except Exception as e:
    print("ดึงรายชื่อไม่สำเร็จ:", e)