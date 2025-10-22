"""
Deepseek OCR benchmark harness.

Provides quality and performance sampling across a document corpus.
"""
from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from statistics import mean
from typing import Iterable, List, Optional

from jina_rag_pipeline.ingestion.deepseek_loader import DeepseekLoader
from jina_rag_pipeline.ingestion.ocr_config import OCRConfig
from jina_rag_pipeline.ingestion.semantic_region import SemanticRegion

SUPPORTED_EXTENSIONS = {".pdf", ".pptx", ".ppt", ".png", ".jpg", ".jpeg"}


@dataclass
class DocumentMetrics:
    path: str
    duration_seconds: float
    page_count: Optional[int]
    slide_count: Optional[int]
    region_count: int
    grounded_regions: int
    compression_enabled: bool

    def to_dict(self) -> dict:
        return asdict(self)


def _iter_documents(corpus: Path) -> Iterable[Path]:
    if corpus.is_file():
        if corpus.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield corpus
        return

    for path in sorted(corpus.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield path


def _collect_metrics(loader: DeepseekLoader, path: Path) -> DocumentMetrics:
    start = time.perf_counter()
    document = loader.load(path)
    duration = time.perf_counter() - start

    metadata = document.metadata
    regions: List[SemanticRegion] = metadata.get("regions", []) or []
    grounded = sum(1 for region in regions if getattr(region, "bbox", None))

    return DocumentMetrics(
        path=str(path),
        duration_seconds=duration,
        page_count=metadata.get("page_count"),
        slide_count=metadata.get("slide_count"),
        region_count=len(regions),
        grounded_regions=grounded,
        compression_enabled=bool(metadata.get("compression_enabled", True)),
    )


def _summarise(metrics: List[DocumentMetrics], mode: str) -> dict:
    if not metrics:
        return {"documents_processed": 0}

    durations = [m.duration_seconds for m in metrics]
    pages = [
        m.page_count if m.page_count is not None else m.slide_count or 0
        for m in metrics
    ]
    regions = [m.region_count for m in metrics]
    grounded = [m.grounded_regions for m in metrics]

    return {
        "documents_processed": len(metrics),
        "avg_duration_seconds": mean(durations),
        "avg_pages_or_slides": mean(pages) if any(pages) else None,
        "avg_regions": mean(regions),
        "avg_grounded_regions": mean(grounded),
        "throughput_docs_per_min": len(metrics) / (sum(durations) / 60.0),
    }


def _create_loader(args: argparse.Namespace) -> DeepseekLoader:
    preset = getattr(OCRConfig, f"deepseek_{args.preset}")() if args.preset else OCRConfig.deepseek_balanced()

    if args.resolution_mode:
        preset.resolution_mode = args.resolution_mode
    if args.batch_size:
        preset.batch_size = args.batch_size
    if args.render_workers:
        preset.render_workers = args.render_workers
    if args.analysis_workers:
        preset.analysis_workers = args.analysis_workers

    preset.enable_grounding = not args.disable_grounding
    preset.enable_compression = not args.disable_compression
    preset.use_vllm = args.use_vllm

    return DeepseekLoader(config=preset)


def run_benchmark(args: argparse.Namespace) -> None:
    corpus = Path(args.corpus).expanduser().resolve()
    if not corpus.exists():
        raise FileNotFoundError(f"Corpus path does not exist: {corpus}")

    loader = _create_loader(args)
    documents = list(_iter_documents(corpus))

    if args.limit:
        documents = documents[: args.limit]

    if not documents:
        raise RuntimeError(f"No supported documents found in {corpus}")

    metrics: List[DocumentMetrics] = []
    failures: List[str] = []

    for path in documents:
        try:
            metrics.append(_collect_metrics(loader, path))
        except Exception as exc:  # pragma: no cover - runtime feedback
            failures.append(f"{path}: {exc}")
            if args.stop_on_error:
                break

    summary = _summarise(metrics, args.mode)

    if summary["documents_processed"] and args.mode == "performance":
        total_duration = sum(m.duration_seconds for m in metrics)
        total_pages = sum(
            (m.page_count if m.page_count is not None else m.slide_count or 0)
            for m in metrics
        )
        summary["total_duration_seconds"] = total_duration
        summary["pages_per_second"] = (
            total_pages / total_duration if total_pages and total_duration else None
        )
    result = {
        "mode": args.mode,
        "corpus": str(corpus),
        "config": {
            "resolution_mode": loader.config.resolution_mode,
            "enable_grounding": loader.config.enable_grounding,
            "enable_compression": loader.config.enable_compression,
            "use_vllm": loader.config.use_vllm,
            "batch_size": loader.config.batch_size,
            "render_workers": loader.config.render_workers,
            "analysis_workers": loader.config.analysis_workers,
        },
        "summary": summary,
        "documents": [m.to_dict() for m in metrics],
        "failures": failures,
    }

    print(json.dumps(result if args.verbose else summary, indent=2))

    if args.output:
        output_path = Path(args.output).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, indent=2))
        print(f"\nWrote benchmark report to {output_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Deepseek OCR benchmark harness")
    parser.add_argument("--corpus", required=True, help="Path to a document corpus or single file")
    parser.add_argument(
        "--mode",
        choices=["quality", "performance"],
        default="quality",
        help="Benchmark mode (quality collects grounding stats, performance focuses on throughput)",
    )
    parser.add_argument("--preset", choices=["tiny", "small", "balanced", "high_quality", "gundam", "production"])
    parser.add_argument("--resolution-mode", choices=["tiny", "small", "base", "large", "gundam"])
    parser.add_argument("--batch-size", type=int)
    parser.add_argument("--render-workers", type=int)
    parser.add_argument("--analysis-workers", type=int)
    parser.add_argument("--disable-grounding", action="store_true")
    parser.add_argument("--disable-compression", action="store_true")
    parser.add_argument("--use-vllm", action="store_true")
    parser.add_argument("--limit", type=int, help="Limit number of documents processed")
    parser.add_argument("--stop-on-error", action="store_true", help="Abort on first failure")
    parser.add_argument("--output", help="Optional JSON report path")
    parser.add_argument("--verbose", action="store_true", help="Include per-document metrics in stdout")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    run_benchmark(args)


if __name__ == "__main__":
    main()
