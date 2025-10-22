#!/usr/bin/env python3
"""Compare OCR output quality between MPS and MLX backends."""

import logging
from pathlib import Path

logging.basicConfig(level=logging.WARNING)  # Reduce noise

from src.jina_rag_pipeline.ingestion.nanonets_loader import NanonetsLoader
from src.jina_rag_pipeline.ingestion.ocr_config import OCRConfig

def test_backend(backend_name: str, config: OCRConfig):
    print(f"\n{'='*70}")
    print(f"Testing {backend_name} Backend")
    print(f"{'='*70}\n")
    
    loader = NanonetsLoader(config=config)
    document = loader.load(Path("test_2pages.pdf"))
    
    print(f"Content length: {len(document.content)} characters")
    print(f"Semantic regions: {len(document.metadata.get('semantic_regions', []))} regions")
    print(f"\nFirst 500 characters of content:")
    print("=" * 70)
    print(document.content[:500])
    print("=" * 70)
    print(f"\nLast 500 characters of content:")
    print("=" * 70)
    print(document.content[-500:])
    print("=" * 70)
    
    # Show semantic regions structure
    regions = document.metadata.get('semantic_regions', [])
    if regions:
        print(f"\nSemantic regions breakdown:")
        for i, region in enumerate(regions[:5], 1):  # First 5 regions
            print(f"  Region {i}: {region.region_type} - {len(region.content)} chars")
    
    return document

if __name__ == "__main__":
    # Test MLX (current default)
    mlx_config = OCRConfig.mlx_optimized()
    mlx_doc = test_backend("MLX (8-bit)", mlx_config)
    
    print("\n" + "="*70)
    print("Saving full outputs for comparison...")
    print("="*70)
    
    Path("output_mlx.txt").write_text(mlx_doc.content)
    print(f"✓ MLX output saved to: output_mlx.txt")
