import os
from PIL import Image
from google import genai
from config import MODEL
from extract import read_pdf

client = genai.Client()

def load_contract(uploaded_files) -> str:
    """รองรับทั้งไฟล์ PDF และไฟล์รูปภาพ (PNG/JPG) พร้อมระบบป้องกัน Error และจัดการค่า None"""
    all_text = ""
    
    if not uploaded_files:
        return ""
        
    for f in uploaded_files:
        file_extension = f.name.split(".")[-1].lower()
        
        try:
            if file_extension in ["pdf"]:
                # อ่านไฟล์ PDF
                pdf_text = read_pdf(f)
                if pdf_text:
                    all_text += "\n" + str(pdf_text)
                    
            elif file_extension in ["png", "jpg", "jpeg"]:
                # อ่านไฟล์รูปภาพด้วย Gemini Vision
                image = Image.open(f)
                prompt = "ถอดข้อความทั้งหมดจากรูปภาพสัญญาเช่านี้ออกมาเป็นข้อความภาษาไทยอย่างถูกต้องและครบถ้วนที่สุด โดยคงลำดับข้อสัญญาเดิมไว้"
                
                response = None
                try:
                    response = client.models.generate_content(
                        model=MODEL,
                        contents=[image, prompt]
                    )
                except Exception as api_err:
                    print(f"⚠️ เกิดข้อผิดพลาดในการเรียกโมเดลอ่านรูปภาพ: {api_err}")
                
                # ตรวจสอบและดึงข้อความอย่างปลอดภัย ป้องกัน NoneType Error
                extracted_text = response.text if (response and hasattr(response, 'text') and response.text) else ""
                if extracted_text:
                    all_text += "\n" + str(extracted_text)
                    
        except Exception as e:
            print(f"⚠️️ เกิดข้อผิดพลาดในการประมวลผลไฟล์ {f.name}: {e}")
            
    return all_text.strip()
