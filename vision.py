import os
from PIL import Image
from google import genai
from config import MODEL

client = genai.Client()

def load_contract(uploaded_files) -> str:
    """รองรับทั้งไฟล์ PDF และไฟล์รูปภาพ (PNG/JPG) โดยใช้ Gemini Vision อ่านข้อความ"""
    all_text = ""
    
    for f in uploaded_files:
        # ตรวจสอบนามสกุลไฟล์
        file_extension = f.name.split(".")[-1].lower()
        
        if file_extension in ["pdf"]:
            # ถ้าเป็น PDF ให้ใช้ pypdf ตามเดิม
            from extract import read_pdf
            all_text += "\n" + read_pdf(f)
            
        elif file_extension in ["png", "jpg", "jpeg"]:
            # ถ้าเป็นรูปภาพ ให้ใช้ Gemini Vision ช่วยอ่านข้อความในรูป
            image = Image.open(f)
            prompt = "ถอดข้อความทั้งหมดจากรูปภาพสัญญาเช่านี้ออกมาเป็นข้อความภาษาไทยอย่างถูกต้องและครบถ้วนที่สุด โดยคงลำดับข้อสัญญาเดิมไว้"
            
            # เรียกใช้งานโมเดล Gemini เพื่ออ่านรูปภาพ
            response = client.models.generate_content(
                model=MODEL,
                contents=[image, prompt]
            )
            extracted_text = response.text if response else ""
            all_text += "\n" + extracted_text
            
    return all_text
