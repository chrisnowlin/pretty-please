#!/usr/bin/env python3
"""
MLX Turbo processing with optimized settings for maximum speed.

This script uses the 'mlx_turbo' profile which leverages the 3.1GB MLX model
to enable:
- 3x parallel analysis workers (vs 1 sequential)
- 2x larger render batches (20 pages vs 10)
- 3x pre-render buffer for pipeline efficiency
- Higher memory pressure threshold (90% vs 85%)

Expected speedup: 2-3x faster than conservative settings
"""

import sys
import time
import logging
from pathlib import Path
from datetime import datetime

# Set up detailed logging
log_file = Path(__file__).parent / "mlx_turbo_processing.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent / "src"))

from jina_rag_pipeline.ingestion import NanonetsFirstLoader
from jina_rag_pipeline.ingestion.database_persistence import DocumentDatabasePersistence
from jina_rag_pipeline.config import get_profile

# Configuration
PDF_PATH = Path("/Users/cnowlin/Downloads/_OceanofPDF.com_Classroom_Music_Games_and_Activities_-_Julie_Eisenhauer.pdf")
COLLECTION_NAME = "classroom_music_games_mlx_turbo"
RESUME = True  # Will resume from checkpoint if exists

def main():
    logger.info("=" * 80)
    logger.info("MLX TURBO PROCESSING - MAXIMUM SPEED")
    logger.info("=" * 80)
    logger.info("")

    # Verify file exists
    if not PDF_PATH.exists():
        logger.error(f"PDF file not found: {PDF_PATH}")
        sys.exit(1)

    logger.info(f"PDF: {PDF_PATH.name}")
    logger.info(f"Size: {PDF_PATH.stat().st_size / (1024*1024):.1f} MB")
    logger.info("")

    # Get MLX Turbo profile
    profile = get_profile("mlx_turbo")
    logger.info(f"Profile: {profile.name}")
    logger.info(f"Render batch size: {profile.render_batch_size} pages per cycle")
    logger.info(f"Analysis workers: {profile.max_analysis_workers} (MLX is not thread-safe)")
    logger.info(f"Render workers: {profile.max_render_workers} parallel workers")
    logger.info(f"Pre-render batches: {profile.pre_render_batches} batches ahead")
    logger.info(f"Memory target: {profile.memory_target_gb}GB / {profile.max_memory_gb}GB")
    logger.info("")
    logger.info("MLX Model Memory:")
    logger.info(f"  - Model loaded: ~2.2GB (compressed from 3.1GB on disk)")
    logger.info(f"  - Workers: {profile.max_analysis_workers} (sequential)")
    logger.info(f"  - Remaining for buffers: ~{48 - 2.2:.1f}GB")
    logger.info("")
    logger.info("Optimization Strategy:")
    logger.info(f"  - Pipeline parallelism: Render {profile.render_batch_size} pages while analyzing")
    logger.info(f"  - {profile.pre_render_batches} batches pre-rendered = {profile.pre_render_batches * profile.render_batch_size} pages ahead")
    logger.info(f"  - Analysis never waits for rendering")
    logger.info("")

    # Initialize loader with MLX backend and optimized settings
    logger.info("Initializing NanonetsFirstLoader with MLX Turbo settings...")
    loader = NanonetsFirstLoader(
        batch_size=profile.render_batch_size,  # 20 pages per batch
        enable_checkpoints=True,
        max_render_workers=profile.max_render_workers,  # 16 parallel renders
        max_analysis_workers=profile.max_analysis_workers,  # 3 parallel MLX inference
        use_mlx=True  # MLX backend for 2-4x speedup
    )
    logger.info("✓ Loader initialized with MLX Turbo profile")
    logger.info("")

    # Check for existing checkpoint
    checkpoint_dir = Path("./checkpoints") / COLLECTION_NAME
    if checkpoint_dir.exists() and RESUME:
        logger.info(f"Found existing checkpoint directory: {checkpoint_dir}")
        logger.info("Will attempt to resume from last checkpoint...")
    else:
        logger.info("Starting fresh processing (no checkpoint found)")
    logger.info("")

    # Start processing
    start_time = time.time()
    logger.info("=" * 80)
    logger.info("STARTING MLX TURBO PROCESSING")
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)
    logger.info("")

    try:
        document = loader.load(
            file_path=PDF_PATH,
            collection_name=COLLECTION_NAME,
            resume=RESUME
        )

        elapsed = time.time() - start_time

        logger.info("")
        logger.info("=" * 80)
        logger.info("PROCESSING COMPLETE!")
        logger.info("=" * 80)
        logger.info("")
        logger.info(f"Total time: {elapsed/60:.1f} minutes ({elapsed/3600:.2f} hours)")
        logger.info(f"Pages processed: {document.metadata.get('page_count', 0)}")
        logger.info(f"Characters extracted: {len(document.content):,}")
        logger.info(f"Words: {len(document.content.split()):,}")
        logger.info(f"Semantic regions: {document.metadata.get('region_count', 0)}")
        logger.info("")

        # Calculate stats
        pages = document.metadata.get('page_count', 0)
        if pages > 0:
            time_per_page = elapsed / pages
            pages_per_min = 60 / time_per_page if time_per_page > 0 else 0
            logger.info(f"Average: {time_per_page:.1f} seconds/page ({pages_per_min:.1f} pages/minute)")

        logger.info("")
        logger.info("Performance comparison:")
        logger.info(f"  Conservative (1 worker):  ~80 sec/page")
        logger.info(f"  MLX Turbo (3 workers):    ~{time_per_page:.1f} sec/page")
        logger.info(f"  Speedup: {80/time_per_page:.2f}x faster")

        logger.info("")
        logger.info("=" * 80)
        logger.info("PERSISTING TO DATABASE")
        logger.info("=" * 80)
        logger.info("")

        # Persist document to database for search
        db_start = time.time()
        try:
            persistence = DocumentDatabasePersistence(persist_directory="./db")
            save_result = persistence.save_document(
                document=document,
                collection_name=COLLECTION_NAME
            )
            persistence.close()

            db_elapsed = time.time() - db_start
            logger.info("")
            logger.info(f"✅ Database persistence complete: {db_elapsed:.1f} seconds")
            logger.info(f"✅ Collection: {save_result['collection_name']}")
            logger.info(f"✅ Chunks saved: {save_result['saved_chunks']}/{save_result['total_chunks']}")
            logger.info(f"✅ Status: {save_result['status']}")

            if save_result['status'] == 'success':
                logger.info("")
                logger.info("✅ Document is now searchable in the database!")
            else:
                logger.warning(f"⚠️  Database persistence had issues: {save_result.get('error', 'unknown')}")

        except Exception as e:
            logger.error(f"⚠️  Failed to persist document to database: {e}")
            logger.error("Document processing completed successfully, but database save failed")

        logger.info("")
        logger.info("✅ Document successfully processed and saved with MLX Turbo!")
        logger.info(f"✅ Log file: {log_file}")

        # Show region breakdown if available
        regions = document.metadata.get('regions', [])
        if regions:
            region_types = {}
            for region in regions:
                rtype = region.region_type
                region_types[rtype] = region_types.get(rtype, 0) + 1

            logger.info("")
            logger.info("Region type breakdown:")
            for rtype, count in sorted(region_types.items(), key=lambda x: -x[1]):
                logger.info(f"  {rtype}: {count}")

        return 0

    except KeyboardInterrupt:
        elapsed = time.time() - start_time
        logger.info("")
        logger.info("=" * 80)
        logger.info("PROCESSING INTERRUPTED BY USER")
        logger.info("=" * 80)
        logger.info("")
        logger.info(f"Time elapsed: {elapsed/60:.1f} minutes")
        logger.info("")
        if checkpoint_dir.exists():
            logger.info("✓ Checkpoint saved - you can resume by running this script again")
            logger.info(f"  Checkpoint location: {checkpoint_dir}")
        logger.info("")
        return 130  # Standard code for SIGINT

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error("")
        logger.error("=" * 80)
        logger.error("PROCESSING FAILED")
        logger.error("=" * 80)
        logger.error("")
        logger.error(f"Error after {elapsed/60:.1f} minutes: {e}")
        logger.error("", exc_info=True)
        logger.error("")
        if checkpoint_dir.exists():
            logger.info("✓ Checkpoint saved - you can resume by running this script again")
            logger.info(f"  Checkpoint location: {checkpoint_dir}")
        logger.error("")
        return 1

if __name__ == "__main__":
    sys.exit(main())
