import sys
from extract import read_pdf

text = read_pdf(sys.argv[1])
print(repr(text[:1500]))