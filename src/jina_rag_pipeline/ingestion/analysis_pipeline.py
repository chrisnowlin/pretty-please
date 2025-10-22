"""
Analysis pipeline component coordinating OCR analysis of rendered pages.
Provides batch processing interface compatible with existing loader.
"""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class AnalysisPipeline:
    def __init__(self, analysis_workers: int = 2) -> None:
        self.analysis_workers = analysis_workers

    def analyze_pages(
        self,
        rendered_pages: Dict[int, Path],
        analyzer,
    ) -> Tuple[List[Tuple[int, str, Path]], list]:
        """
        Analyze pages using batch processing when available.
        Returns (results, regions) like the legacy _analyze_pages_parallel.
        """
        # Try using batch methods first (much more efficient)
        if hasattr(analyzer, "extract_regions_batch"):
            try:
                # Prepare sorted lists for batch processing
                page_nums = sorted(rendered_pages.keys())
                img_paths = [rendered_pages[pn] for pn in page_nums]

                logger.info(f"Using batch processing for {len(page_nums)} pages")

                # Use extract_regions_batch which internally calls analyze_documents_batch
                all_regions_list = analyzer.extract_regions_batch(
                    file_paths=img_paths,
                    page_numbers=page_nums,
                    batch_size=len(page_nums)  # Process all at once for efficiency
                )

                # Format results
                results = []
                all_regions = []
                for page_num, img_path, regions in zip(page_nums, img_paths, all_regions_list):
                    # Extract text content from regions
                    content = "\n\n".join(r.content for r in regions if r.content)
                    results.append((page_num, content, img_path))
                    all_regions.extend(regions)

                return results, all_regions

            except Exception as e:
                logger.warning(f"Batch processing failed, falling back to individual: {e}")
                # Fall through to individual processing below

        # Fallback: Individual page processing with ThreadPool for parallelism
        logger.info("Using individual page processing (batch methods not available)")
        max_workers = max(1, self.analysis_workers)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._analyze_single, analyzer, page_num, img_path): page_num
                for page_num, img_path in rendered_pages.items()
            }
            results = []
            all_regions = []
            for fut in as_completed(futures):
                page_num, content, img_path, regions = fut.result()
                results.append((page_num, content, img_path))
                all_regions.extend(regions)
        results.sort(key=lambda x: x[0])
        return results, all_regions

    def _analyze_single(self, analyzer, page_num: int, img_path: Path):
        md = analyzer.analyze_document(img_path, page_number=page_num)
        content = md if md and md.strip() else ""
        regions = []
        if hasattr(analyzer, "extract_regions"):
            try:
                regions = analyzer.extract_regions(img_path, page_number=page_num)
            except Exception:
                regions = []
        return page_num, content, img_path, regions

