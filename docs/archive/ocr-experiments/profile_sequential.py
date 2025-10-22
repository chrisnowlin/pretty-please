#!/usr/bin/env python3
"""
Profile sequential processing to identify bottlenecks.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import fitz  # PyMuPDF
from jina_rag_pipeline.ingestion.nanonets_mlx import NanonetsMLXAnalyzer

# Configuration
MODEL_PATH = "./models/nanonets-ocr2-3b-mlx"
PDF_PATH = "./tests/fixtures/classroom_music_5pages.pdf"
OUTPUT_DIR = Path("./output/profiling")
RENDER_DPI = 200
PAGE_NUM = 0  # Profile just first page

print("=" * 80)
print("PROFILING SEQUENTIAL PROCESSING")
print("=" * 80)
print()

# Load model
print("Loading MLX model...")
load_start = time.time()
analyzer = NanonetsMLXAnalyzer(model_path=MODEL_PATH)
load_time = time.time() - load_start
print(f"✓ Model loaded: {load_time:.2f} sec")
print()

# Create output dir
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
temp_dir = OUTPUT_DIR / "temp"
temp_dir.mkdir(parents=True, exist_ok=True)

print("-" * 80)
print(f"Processing page {PAGE_NUM}...")
print("-" * 80)
print()

# Step 1: Open PDF
t1 = time.time()
doc = fitz.open(PDF_PATH)
page = doc[PAGE_NUM]
t_open = time.time() - t1
print(f"1. Open PDF: {t_open:.3f} sec")

# Step 2: Render to pixmap
t2 = time.time()
zoom = RENDER_DPI / 72.0
mat = fitz.Matrix(zoom, zoom)
pix = page.get_pixmap(matrix=mat)
t_render = time.time() - t2
print(f"2. Render pixmap: {t_render:.3f} sec")

# Step 3: Save to disk
t3 = time.time()
image_path = temp_dir / f"page_{PAGE_NUM:04d}.png"
pix.save(str(image_path))
t_save = time.time() - t3
print(f"3. Save image: {t_save:.3f} sec")

# Step 4: Close PDF
t4 = time.time()
doc.close()
t_close = time.time() - t4
print(f"4. Close PDF: {t_close:.3f} sec")

print()
print(f"   PDF Pipeline Total: {t_open + t_render + t_save + t_close:.3f} sec")
print()

# Step 5: analyze_document (markdown extraction)
t5 = time.time()
markdown = analyzer.analyze_document(str(image_path))
t_analyze = time.time() - t5
print(f"5. analyze_document(): {t_analyze:.2f} sec")

# Step 6: extract_regions (region extraction)
t6 = time.time()
regions = analyzer.extract_regions(str(image_path), page_number=PAGE_NUM)
t_regions = time.time() - t6
print(f"6. extract_regions(): {t_regions:.2f} sec")

print()
print(f"   MLX Analysis Total: {t_analyze + t_regions:.2f} sec")
print()

# Step 7: Cleanup
t7 = time.time()
image_path.unlink()
t_cleanup = time.time() - t7
print(f"7. Cleanup: {t_cleanup:.3f} sec")

print()
print("=" * 80)
print("BREAKDOWN SUMMARY")
print("=" * 80)
print()

total_time = t_open + t_render + t_save + t_close + t_analyze + t_regions + t_cleanup

print(f"{'Operation':<30} {'Time (sec)':<15} {'% of Total':<15}")
print("-" * 60)
print(f"{'1. Open PDF':<30} {t_open:<15.3f} {t_open/total_time*100:<15.1f}")
print(f"{'2. Render pixmap':<30} {t_render:<15.3f} {t_render/total_time*100:<15.1f}")
print(f"{'3. Save image':<30} {t_save:<15.3f} {t_save/total_time*100:<15.1f}")
print(f"{'4. Close PDF':<30} {t_close:<15.3f} {t_close/total_time*100:<15.1f}")
print(f"{'5. analyze_document()':<30} {t_analyze:<15.2f} {t_analyze/total_time*100:<15.1f}")
print(f"{'6. extract_regions()':<30} {t_regions:<15.2f} {t_regions/total_time*100:<15.1f}")
print(f"{'7. Cleanup':<30} {t_cleanup:<15.3f} {t_cleanup/total_time*100:<15.1f}")
print("-" * 60)
print(f"{'TOTAL':<30} {total_time:<15.2f} {'100.0':<15}")
print()

# Analysis
print("=" * 80)
print("FINDINGS")
print("=" * 80)
print()

if t_analyze + t_regions > total_time * 0.9:
    print("✓ MLX inference is the dominant cost (>90% of time)")
    print()

    if abs(t_analyze - t_regions) < t_analyze * 0.2:
        print("⚠️  ISSUE IDENTIFIED: Both analyze_document() and extract_regions()")
        print("    take similar time, suggesting TWO full model inference calls!")
        print()
        print(f"    analyze_document(): {t_analyze:.1f} sec")
        print(f"    extract_regions():  {t_regions:.1f} sec")
        print(f"    Combined:           {t_analyze + t_regions:.1f} sec")
        print()
        print("💡 OPTIMIZATION: If you don't need regions, skip extract_regions()")
        print(f"    Potential speedup: {(t_analyze + t_regions) / t_analyze:.2f}x")
        print(f"    New time per page: {t_analyze:.1f} sec (vs {total_time:.1f} sec)")
        print()
    elif t_analyze > t_regions * 2:
        print("⚠️  analyze_document() is much slower than extract_regions()")
        print("    This is expected - markdown generation is the heavy operation")
    else:
        print("ℹ️  extract_regions() is slower than expected")
        print(f"    Might be doing redundant work or separate inference")

else:
    print("⚠️  MLX inference is NOT the bottleneck (<90% of time)")
    print("    This is unexpected - investigate PDF/image pipeline")

print()
print(f"Markdown length: {len(markdown)} characters")
print(f"Regions found: {len(regions)}")
print()
