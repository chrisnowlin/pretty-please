#!/usr/bin/env python3
"""Inspect the test PDF to understand what content it should have."""

import fitz  # PyMuPDF
from pathlib import Path

pdf_path = Path("test_2pages.pdf")
doc = fitz.open(pdf_path)

print(f"PDF: {pdf_path}")
print(f"Pages: {len(doc)}")
print("\n" + "="*70)

for page_num in range(len(doc)):
    page = doc[page_num]
    text = page.get_text()
    print(f"\nPage {page_num + 1} - Raw Text Extract (first 500 chars):")
    print("="*70)
    print(text[:500] if text else "[No text found]")
    print("="*70)
    
doc.close()
