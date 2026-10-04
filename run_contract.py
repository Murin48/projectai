import json
import sys
from extract import read_pdf, split_clauses
from analyze import analyze_clauses
 
if len(sys.argv) < 2:
    sys.exit("วิธีใช้: python run_contract.py samples/contract.pdf")
 
clauses = split_clauses(read_pdf(sys.argv[1]))
print(f"แบ่งได้ {len(clauses)} ข้อ")
analysed = analyze_clauses(clauses)
 
results = []
for r, c in zip(analysed, clauses):
    r = dict(r)
    r["clause"] = c
    results.append(r)
 
with open("result.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
 
high = sum(1 for r in results if r.get("risk") == "high")
failed = [i for i, r in enumerate(results, 1) if r.get("risk") == "unknown"]
print(f"เสร็จแล้ว: {len(results)} ข้อ, เสี่ยงสูง {high} ข้อ → result.json")
if failed:
    print(f"⚠️  ข้อที่วิเคราะห์ไม่สำเร็จ: {failed} รันใหม่อีกครั้ง (ข้อที่สำเร็จแล้วไม่เสียโควตาซ้ำ)")
 