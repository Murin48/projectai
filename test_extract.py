import sys
from extract import read_pdf, split_clauses

if len(sys.argv) < 2:
    sys.exit("วิธีใช้: python test_extract.py samples/สัญญา.pdf")

text = read_pdf(sys.argv[1])
print(f"อ่านได้ {len(text)} ตัวอักษร")

clauses = split_clauses(text)
print(f"แบ่งได้ {len(clauses)} ข้อ\n")

for i, c in enumerate(clauses, 1):
    print(f"--- ข้อที่ {i} ---")
    print(c[:150], "...\n")