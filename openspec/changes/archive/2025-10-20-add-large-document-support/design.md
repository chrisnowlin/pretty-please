# Technical Design: Large Document Support

## System Constraints

### Hardware Profile
- **CPU**: Apple M4 Max (16 cores: 12 performance, 4 efficiency)
- **Memory**: 48GB unified memory
- **GPU**: Integrated with MPS (Metal Performance Shaders) support
- **Storage**: Fast SSD for temporary files

### Software Constraints
- Python 3.9+ (system Python)
- Nanonets-OCR2-3B model (~6-8GB VRAM/RAM)
- Jina Embeddings v4 (2048-dim, MPS acceleration)
- ChromaDB for vector storage

### Requirements
- **Quality > Speed**: Prioritize accurate extraction and chunking
- **Reliability > Performance**: Must complete 500+ page documents
- **Memory Target**: Keep peak usage below 32GB (leave 16GB for system)
- **Acceptable Time**: 1-2 hours for 500-page textbook

---

## Architecture Overview

### Current Processing Flow (Batch Mode)
```
PDF (500 pages)
    ↓
Render ALL pages → 500 PNG files (2.5GB)
    ↓
Load all into memory
    ↓
Process sequentially (1 page at a time)
    ↓
Embed sequentially
    ↓
Store in ChromaDB

Problems:
- High memory peak (10-12GB)
- No resume capability
- Slow (2-3 hours)
- Underutilizes CPU
```

### New Processing Flow (Progressive + Parallel)
```
PDF (500 pages)
    ↓
┌─────────────────────────────────────┐
│ Progressive Rendering               │
│ - Batch size: 10 pages              │
│ - Parallel workers: 4                │
│ - Memory: ~500MB per batch          │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ Checkpoint Manager                  │
│ - Save after each batch             │
│ - Resume from last checkpoint       │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ Parallel Analysis                   │
│ - Workers: 2-4 (GPU limited)        │
│ - Nanonets per page                 │
│ - Semantic region extraction        │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ Semantic Chunking                   │
│ - Preserve tables/equations         │
│ - Respect chapter boundaries        │
│ - Fallback to character-based       │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ Batch Embedding                     │
│ - 64 chunks per batch               │
│ - Jina v4 with MPS                  │
└─────────────────────────────────────┘
    ↓
Store in ChromaDB

Benefits:
- Low memory (6-8GB peak)
- Resume capability
- Fast (1-2 hours)
- Utilizes 8+ cores
```

---

## Component Designs

### 1. Progressive Document Processor

**Purpose**: Manage memory-efficient page-by-page processing with checkpointing.

```python
class ProgressiveDocumentProcessor:
    """
    Processes large PDFs progressively with checkpointing.
    
    Key Features:
    - Renders pages in batches to control memory
    - Saves checkpoint after each batch
    - Resumes from checkpoint on restart
    - Cleans up temp files aggressively
    """
    
    def __init__(
        self,
        checkpoint_dir: Path,
        batch_size: int = 10,
        max_memory_gb: int = 32
    ):
        self.checkpoint_dir = checkpoint_dir
        self.batch_size = batch_size
        self.max_memory_gb = max_memory_gb
        self.checkpoint_manager = CheckpointManager(checkpoint_dir)
        self.memory_monitor = MemoryMonitor(max_memory_gb)
    
    def process_pdf(
        self,
        file_path: Path,
        collection_name: str,
        analyzer: NanonetsLayoutAnalyzer,
        resume: bool = True
    ) -> Document:
        """
        Process PDF with checkpointing.
        
        Flow:
        1. Load checkpoint if resume=True
        2. Render pages in batches
        3. Process batch with Nanonets
        4. Save checkpoint
        5. Cleanup temp files
        6. Repeat until done
        """
        # Load existing checkpoint
        checkpoint = None
        if resume:
            checkpoint = self.checkpoint_manager.load(file_path, collection_name)
        
        start_page = 0 if not checkpoint else checkpoint.last_page_completed + 1
        
        # Get total pages
        import fitz
        doc = fitz.open(str(file_path))
        total_pages = doc.page_count
        doc.close()
        
        # Create checkpoint if new
        if not checkpoint:
            checkpoint = self.checkpoint_manager.create(
                file_path=file_path,
                collection_name=collection_name,
                total_pages=total_pages
            )
        
        all_results = checkpoint.page_results if checkpoint else []
        
        # Process batches
        for batch_start in range(start_page, total_pages, self.batch_size):
            batch_end = min(batch_start + self.batch_size, total_pages)
            
            # Check memory before batch
            if not self.memory_monitor.has_capacity(self.batch_size):
                # Reduce batch size adaptively
                safe_batch = self.memory_monitor.get_safe_batch_size()
                batch_end = batch_start + safe_batch
            
            # Render and process batch
            batch_results = self._process_batch(
                file_path,
                batch_start,
                batch_end,
                analyzer
            )
            
            all_results.extend(batch_results)
            
            # Save checkpoint
            checkpoint.last_page_completed = batch_end - 1
            checkpoint.page_results = all_results
            self.checkpoint_manager.save(checkpoint)
            
            # Log progress
            progress = (batch_end / total_pages) * 100
            logger.info(f"Progress: {progress:.1f}% ({batch_end}/{total_pages} pages)")
        
        # Cleanup checkpoint on success
        self.checkpoint_manager.delete(checkpoint)
        
        # Combine results into Document
        return self._combine_results(all_results, file_path)
```

---

### 2. Checkpoint Manager

**Purpose**: Persist processing progress for crash recovery.

```python
@dataclass
class Checkpoint:
    """Checkpoint data structure."""
    checkpoint_id: str
    file_path: str
    file_hash: str
    collection_name: str
    total_pages: int
    processed_pages: int
    last_page_completed: int
    page_results: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

class CheckpointManager:
    """
    Manages checkpoint persistence and recovery.
    
    Checkpoint Location:
    ./checkpoints/{collection}/{file_hash}/checkpoint.json
    
    Cleanup Strategy:
    - Auto-delete on successful completion
    - Expire after 7 days
    - Manual cleanup API endpoint
    """
    
    def __init__(self, base_dir: Path = Path("./checkpoints")):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def create(
        self,
        file_path: Path,
        collection_name: str,
        total_pages: int
    ) -> Checkpoint:
        """Create new checkpoint."""
        file_hash = self._hash_file(file_path)
        checkpoint_id = f"{collection_name}_{file_hash}"
        
        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            file_path=str(file_path),
            file_hash=file_hash,
            collection_name=collection_name,
            total_pages=total_pages,
            processed_pages=0,
            last_page_completed=-1,
            page_results=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.save(checkpoint)
        return checkpoint
    
    def load(
        self,
        file_path: Path,
        collection_name: str
    ) -> Optional[Checkpoint]:
        """Load existing checkpoint."""
        file_hash = self._hash_file(file_path)
        checkpoint_file = self._get_checkpoint_path(collection_name, file_hash)
        
        if not checkpoint_file.exists():
            return None
        
        try:
            with open(checkpoint_file, 'r') as f:
                data = json.load(f)
            
            # Validate checkpoint
            if self._is_expired(data['updated_at']):
                logger.warning(f"Checkpoint expired, deleting: {checkpoint_file}")
                checkpoint_file.unlink()
                return None
            
            return Checkpoint(**data)
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None
    
    def save(self, checkpoint: Checkpoint):
        """Persist checkpoint to disk."""
        checkpoint.updated_at = datetime.now()
        checkpoint_file = self._get_checkpoint_path(
            checkpoint.collection_name,
            checkpoint.file_hash
        )
        
        checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(checkpoint_file, 'w') as f:
            json.dump(asdict(checkpoint), f, indent=2, default=str)
    
    def delete(self, checkpoint: Checkpoint):
        """Delete checkpoint after successful completion."""
        checkpoint_file = self._get_checkpoint_path(
            checkpoint.collection_name,
            checkpoint.file_hash
        )
        
        if checkpoint_file.exists():
            checkpoint_file.unlink()
    
    def cleanup_expired(self, days: int = 7):
        """Remove checkpoints older than N days."""
        cutoff = datetime.now() - timedelta(days=days)
        
        for checkpoint_file in self.base_dir.rglob("checkpoint.json"):
            try:
                with open(checkpoint_file, 'r') as f:
                    data = json.load(f)
                
                updated = datetime.fromisoformat(data['updated_at'])
                if updated < cutoff:
                    checkpoint_file.unlink()
                    logger.info(f"Cleaned up expired checkpoint: {checkpoint_file}")
            except Exception as e:
                logger.error(f"Error cleaning checkpoint {checkpoint_file}: {e}")
```

---

### 3. Memory Monitor

**Purpose**: Prevent OOM by tracking memory and adjusting batch sizes.

```python
class MemoryMonitor:
    """
    Monitors system memory and adjusts processing batch sizes.
    
    Strategy:
    - Track available memory every N seconds
    - Warn at 80% usage
    - Reduce batch size at 85%
    - Error at 95%
    """
    
    def __init__(self, max_memory_gb: int = 32):
        self.max_memory_bytes = max_memory_gb * 1024 * 1024 * 1024
        self.page_memory_estimate = 100 * 1024 * 1024  # 100MB per page
    
    def get_current_usage(self) -> float:
        """Get current memory usage in GB."""
        import psutil
        return psutil.virtual_memory().used / (1024**3)
    
    def get_available(self) -> float:
        """Get available memory in GB."""
        import psutil
        return psutil.virtual_memory().available / (1024**3)
    
    def get_usage_percent(self) -> float:
        """Get memory usage percentage."""
        import psutil
        return psutil.virtual_memory().percent
    
    def has_capacity(self, batch_size: int) -> bool:
        """Check if memory can handle batch_size pages."""
        required = batch_size * self.page_memory_estimate
        available = self.get_available() * (1024**3)
        
        # Use only 50% of available to be safe
        return (available * 0.5) >= required
    
    def get_safe_batch_size(self) -> int:
        """Calculate safe batch size based on available memory."""
        available = self.get_available() * (1024**3)
        
        # Use 50% of available memory
        safe_bytes = available * 0.5
        safe_pages = int(safe_bytes / self.page_memory_estimate)
        
        return max(1, min(safe_pages, 10))
    
    def check_memory_pressure(self):
        """Check for memory pressure and log warnings."""
        usage_pct = self.get_usage_percent()
        
        if usage_pct >= 95:
            raise MemoryError(f"Critical memory pressure: {usage_pct:.1f}%")
        elif usage_pct >= 85:
            logger.warning(f"High memory usage: {usage_pct:.1f}%")
        elif usage_pct >= 80:
            logger.info(f"Memory usage approaching limit: {usage_pct:.1f}%")
```

---

### 4. Parallel Processing Strategy

**Purpose**: Leverage M4 Max cores for 3-4× speedup.

```python
class ParallelPageProcessor:
    """
    Process pages in parallel using ThreadPoolExecutor.
    
    Worker Pools:
    - Rendering: 4-8 workers (CPU bound, I/O overlap)
    - Analysis: 2-4 workers (GPU memory limited)
    - Embedding: 1 worker with batching (GPU bound)
    
    Ordering:
    - Track page numbers with futures
    - Sort results before returning
    - Maintain document order
    """
    
    def __init__(
        self,
        max_render_workers: int = 4,
        max_analysis_workers: int = 2
    ):
        self.max_render_workers = max_render_workers
        self.max_analysis_workers = max_analysis_workers
    
    def process_pages_parallel(
        self,
        file_path: Path,
        page_range: Tuple[int, int],
        analyzer: NanonetsLayoutAnalyzer
    ) -> List[Dict[str, Any]]:
        """
        Process a range of pages in parallel.
        
        Returns results in correct page order.
        """
        start_page, end_page = page_range
        
        # Phase 1: Parallel rendering
        with ThreadPoolExecutor(max_workers=self.max_render_workers) as executor:
            # Submit render jobs
            render_futures = {}
            for page_num in range(start_page, end_page):
                future = executor.submit(
                    self._render_page,
                    file_path,
                    page_num
                )
                render_futures[future] = page_num
            
            # Collect rendered pages
            rendered_pages = {}
            for future in as_completed(render_futures):
                page_num = render_futures[future]
                try:
                    img_path = future.result()
                    rendered_pages[page_num] = img_path
                except Exception as e:
                    logger.error(f"Failed to render page {page_num}: {e}")
                    raise
        
        # Phase 2: Parallel analysis (limited workers)
        with ThreadPoolExecutor(max_workers=self.max_analysis_workers) as executor:
            analysis_futures = {}
            for page_num in sorted(rendered_pages.keys()):
                img_path = rendered_pages[page_num]
                future = executor.submit(
                    analyzer.analyze_document,
                    img_path,
                    page_number=page_num
                )
                analysis_futures[future] = (page_num, img_path)
            
            # Collect analysis results
            results = {}
            for future in as_completed(analysis_futures):
                page_num, img_path = analysis_futures[future]
                try:
                    markdown = future.result()
                    results[page_num] = {
                        "page_num": page_num,
                        "content": markdown,
                        "img_path": img_path
                    }
                except Exception as e:
                    logger.error(f"Failed to analyze page {page_num}: {e}")
                    raise
                finally:
                    # Cleanup temp file
                    if img_path.exists():
                        img_path.unlink()
        
        # Return results in page order
        return [results[pnum] for pnum in sorted(results.keys())]
```

---

### 5. Semantic Region Chunker

**Purpose**: Preserve document structure during chunking.

```python
class SemanticRegionChunker(ChunkingStrategy):
    """
    Chunk documents based on semantic regions from Nanonets.
    
    Strategy:
    - Tables: Single chunk (never split)
    - Equations: Single chunk with LaTeX
    - Figures: Single chunk with description
    - Text: Group until max_size, respect paragraphs
    - Headings: Start new chunk
    
    Fallback:
    - If no semantic regions, use character chunking
    """
    
    def __init__(
        self,
        max_chunk_size: int = 1000,
        preserve_tables: bool = True,
        preserve_equations: bool = True
    ):
        self.max_chunk_size = max_chunk_size
        self.preserve_tables = preserve_tables
        self.preserve_equations = preserve_equations
    
    def chunk(self, document: Document) -> List[Chunk]:
        """Create chunks from semantic regions."""
        regions = document.metadata.get("semantic_regions", [])
        
        if not regions:
            # Fallback to character chunking
            logger.info("No semantic regions, using character chunking")
            return FixedSizeChunker(self.max_chunk_size).chunk(document)
        
        chunks = []
        current_section = []
        current_size = 0
        
        for region in regions:
            region_type = region.get("region_type", "text")
            content = region.get("content", "")
            size = len(content)
            
            # Atomic regions (never split)
            if region_type in ["table", "equation", "figure"]:
                if self._should_preserve(region_type):
                    # Flush current section
                    if current_section:
                        chunks.append(self._merge_regions(current_section))
                        current_section = []
                        current_size = 0
                    
                    # Add as single chunk
                    chunks.append(self._create_atomic_chunk(region))
                    continue
            
            # Section boundaries
            if region_type in ["title", "heading"]:
                # Start new section
                if current_section:
                    chunks.append(self._merge_regions(current_section))
                current_section = [region]
                current_size = size
                continue
            
            # Regular text
            if current_size + size > self.max_chunk_size:
                # Section too large, flush and start new
                if current_section:
                    chunks.append(self._merge_regions(current_section))
                current_section = [region]
                current_size = size
            else:
                # Add to current section
                current_section.append(region)
                current_size += size
        
        # Flush remaining
        if current_section:
            chunks.append(self._merge_regions(current_section))
        
        return chunks
    
    def _should_preserve(self, region_type: str) -> bool:
        """Check if region type should be preserved."""
        if region_type == "table":
            return self.preserve_tables
        elif region_type == "equation":
            return self.preserve_equations
        return False
    
    def _create_atomic_chunk(self, region: Dict) -> Chunk:
        """Create chunk from single atomic region."""
        return Chunk(
            content=region["content"],
            metadata={
                "region_type": region["region_type"],
                "page_number": region.get("page_number"),
                "bbox": region.get("bbox"),
                "atomic": True  # Mark as indivisible
            },
            start_index=0,
            end_index=len(region["content"])
        )
    
    def _merge_regions(self, regions: List[Dict]) -> Chunk:
        """Merge multiple regions into single chunk."""
        content_parts = [r["content"] for r in regions]
        content = "\n\n".join(content_parts)
        
        metadata = {
            "region_types": [r.get("region_type") for r in regions],
            "page_numbers": list(set(r.get("page_number") for r in regions if r.get("page_number"))),
            "merged_regions": len(regions)
        }
        
        return Chunk(
            content=content,
            metadata=metadata,
            start_index=0,
            end_index=len(content)
        )
```

---

### 6. Task Persistence with SQLite

**Purpose**: Survive server restarts and crashes.

```python
class PersistentTaskManager(TaskManager):
    """
    TaskManager with SQLite persistence.
    
    Schema:
    - tasks: Task metadata and status
    - task_files: Per-file status within task
    
    Features:
    - Auto-save on status change
    - Load active tasks on startup
    - Expire tasks after 7 days
    - Concurrent access via WAL mode
    """
    
    def __init__(
        self,
        embedder,
        vector_store,
        temp_dir: Path,
        db_path: Path = Path("./tasks.db")
    ):
        super().__init__(embedder, vector_store, temp_dir)
        self.db_path = db_path
        self._init_database()
        self._load_active_tasks()
    
    def _init_database(self):
        """Initialize SQLite database."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")  # Enable concurrent access
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                collection_name TEXT NOT NULL,
                status TEXT NOT NULL,
                progress REAL DEFAULT 0,
                total_files INTEGER,
                processed_files INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS task_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                status TEXT NOT NULL,
                size INTEGER,
                error TEXT,
                FOREIGN KEY (task_id) REFERENCES tasks(task_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_task(self, files, collection_name):
        """Create task and persist to database."""
        task = super().create_task(files, collection_name)
        
        # Save to database
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO tasks (task_id, collection_name, status, total_files, processed_files)
            VALUES (?, ?, ?, ?, ?)
        """, (task.task_id, collection_name, task.status, task.total_files, 0))
        
        for file_status in files:
            conn.execute("""
                INSERT INTO task_files (task_id, filename, status, size)
                VALUES (?, ?, ?, ?)
            """, (task.task_id, file_status.name, file_status.status, file_status.size))
        
        conn.commit()
        conn.close()
        
        return task
    
    def _update_task_db(self, task):
        """Update task in database."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            UPDATE tasks
            SET status = ?, progress = ?, processed_files = ?, updated_at = CURRENT_TIMESTAMP
            WHERE task_id = ?
        """, (task.status, task.progress, task.processed_files, task.task_id))
        conn.commit()
        conn.close()
    
    def _load_active_tasks(self):
        """Load active tasks from database on startup."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("""
            SELECT task_id, collection_name, status
            FROM tasks
            WHERE status IN ('pending', 'processing')
            AND updated_at > datetime('now', '-7 days')
        """)
        
        for row in cursor:
            task_id, collection_name, status = row
            logger.info(f"Resuming task {task_id} (status: {status})")
            # Reconstruct task from database and resume
            # Implementation depends on task state structure
        
        conn.close()
```

---

## Configuration

### Environment Variables

```bash
# Progressive Rendering
PROGRESSIVE_RENDERING=true          # Enable progressive mode (default: true)
RENDER_BATCH_SIZE=10               # Pages per batch (default: 10)

# Parallel Processing
MAX_RENDER_WORKERS=4               # Render worker threads (default: 4)
MAX_ANALYSIS_WORKERS=2             # Analysis workers (default: 2, GPU limited)
EMBEDDING_BATCH_SIZE=64            # Chunks per embedding batch (default: 64)

# Memory Management
MAX_MEMORY_GB=32                   # Memory limit (default: 32)
ENABLE_MEMORY_MONITORING=true     # Enable monitoring (default: true)
MEMORY_CHECK_INTERVAL=30          # Check interval in seconds (default: 30)

# Checkpointing
CHECKPOINT_DIR=./checkpoints       # Checkpoint directory (default: ./checkpoints)
CHECKPOINT_INTERVAL_PAGES=10      # Save after N pages (default: 10)
AUTO_RESUME=true                   # Auto-resume on restart (default: true)
CHECKPOINT_RETENTION_DAYS=7       # Delete after N days (default: 7)

# Task Persistence
TASK_DATABASE=./tasks.db          # SQLite database path (default: ./tasks.db)
TASK_RETENTION_DAYS=7             # Expire after N days (default: 7)

# Semantic Chunking
USE_SEMANTIC_CHUNKING=true        # Enable semantic chunking (default: true)
SEMANTIC_CHUNK_SIZE=1000          # Max chunk size (default: 1000)
PRESERVE_TABLES=true              # Keep tables intact (default: true)
PRESERVE_EQUATIONS=true           # Keep equations intact (default: true)
```

### Collection Configuration

```json
{
  "collection_name": "textbook_collection",
  "chunking_strategy": "semantic",
  "chunking_config": {
    "max_chunk_size": 1000,
    "preserve_tables": true,
    "preserve_equations": true,
    "fallback_to_character": true
  },
  "processing": {
    "progressive": true,
    "batch_size": 10,
    "parallel_workers": 4,
    "checkpoint_enabled": true
  }
}
```

---

## Performance Expectations

### M4 Max Benchmarks

#### 100-Page Document (~10MB)
- **Rendering**: 1-2 min (progressive)
- **Analysis**: 5-10 min (2 workers)
- **Embedding**: 1-2 min (batched)
- **Total**: ~10-15 minutes
- **Memory Peak**: ~6GB

#### 500-Page Document (~100MB)
- **Rendering**: 5-10 min (progressive)
- **Analysis**: 25-40 min (2 workers)
- **Embedding**: 5-10 min (batched)
- **Total**: ~40-60 minutes
- **Memory Peak**: ~8GB

#### 1000-Page Document (~200MB)
- **Rendering**: 10-20 min (progressive)
- **Analysis**: 50-80 min (2 workers)
- **Embedding**: 10-15 min (batched)
- **Total**: ~80-120 minutes (1.3-2 hours)
- **Memory Peak**: ~10GB

### Conservative Estimates (Quality Mode)
If we limit parallelization to ensure quality:
- Reduce analysis workers to 1-2
- Increase checkpoint frequency
- Add validation steps

**500-page**: ~1-2 hours  
**1000-page**: ~2-4 hours

Still acceptable given quality priority.

---

## Testing Strategy

### Unit Tests
- Checkpoint save/load/resume
- Memory monitor batch sizing
- Semantic chunking algorithm
- Parallel result ordering

### Integration Tests
- 100-page end-to-end
- Crash recovery at 50%
- Memory usage profiling
- Semantic vs character quality

### Stress Tests
- 1000-page synthetic document
- Multiple concurrent uploads
- Memory pressure simulation
- Checkpoint corruption recovery

---

## Deployment Considerations

### Hardware Requirements
- **Minimum**: 16GB RAM, 4 cores
- **Recommended**: 32GB+ RAM, 8+ cores (M4 Max ideal)
- **Storage**: 10GB free for checkpoints/temp files

### Configuration Tuning
For **48GB M4 Max**:
```bash
MAX_MEMORY_GB=32
MAX_RENDER_WORKERS=4
MAX_ANALYSIS_WORKERS=2
RENDER_BATCH_SIZE=10
```

For **16GB Mac**:
```bash
MAX_MEMORY_GB=12
MAX_RENDER_WORKERS=2
MAX_ANALYSIS_WORKERS=1
RENDER_BATCH_SIZE=5
```

### Monitoring
- Track memory usage per phase
- Log worker utilization
- Monitor checkpoint save time
- Alert on memory pressure

---

## Future Enhancements (Out of Scope)

1. **Distributed Processing**: Use Celery/RQ for multi-machine
2. **GPU Pool Management**: Share GPU across workers more efficiently
3. **Adaptive Worker Scaling**: Adjust workers based on load
4. **Incremental Reprocessing**: Update only changed pages
5. **Streaming Results**: Emit chunks as they're created

---

## UPDATED: High-Performance Configuration for M4 Max

### Aggressive Memory Utilization Strategy

With 48GB RAM available, we should maximize throughput by using more memory:

**Key Changes**:
1. **Larger batch sizes**: 30-50 pages instead of 10
2. **More parallel workers**: 8-12 workers for rendering, 4-6 for analysis
3. **Bigger embedding batches**: 128-256 chunks instead of 64
4. **Pre-render ahead**: Keep 2-3 batches rendered in memory
5. **Cache Nanonets model**: Keep model loaded between pages

### Revised Architecture

```
PDF (1000 pages)
    ↓
┌─────────────────────────────────────────────────┐
│ Aggressive Parallel Rendering                   │
│ - Batch size: 50 pages (5GB per batch)          │
│ - Parallel workers: 12 (all P-cores)            │
│ - Pre-render 2 batches ahead (10GB buffered)    │
│ - Memory: ~15GB for rendering pipeline          │
└─────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────┐
│ Parallel Nanonets Analysis                      │
│ - Workers: 4-6 (GPU memory permits)             │
│ - Keep model loaded (8GB persistent)            │
│ - Process batches as they arrive                │
│ - Memory: ~8-10GB for model + inference         │
└─────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────┐
│ High-Throughput Embedding                       │
│ - Batch size: 256 chunks at once                │
│ - Keep embedder loaded                          │
│ - MPS acceleration                              │
│ - Memory: ~4-6GB                                │
└─────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────┐
│ Batch Vector Store Writes                       │
│ - Write 500-1000 embeddings at once             │
│ - Memory: ~2-4GB                                │
└─────────────────────────────────────────────────┘

Total Memory Usage: ~30-35GB (sweet spot)
```

### Configuration for Maximum Speed

```bash
# Aggressive Configuration for 48GB M4 Max
PROGRESSIVE_RENDERING=true
RENDER_BATCH_SIZE=50              # 5× larger batches
PRE_RENDER_BATCHES=2              # Keep 2 batches ahead

# Maximize parallelism
MAX_RENDER_WORKERS=12             # Use all P-cores
MAX_ANALYSIS_WORKERS=6            # Push GPU harder
EMBEDDING_BATCH_SIZE=256          # 4× larger batches

# Use more memory
MAX_MEMORY_GB=40                  # Use 83% of available RAM
AGGRESSIVE_MODE=true              # Enable all optimizations

# Still checkpoint frequently for safety
CHECKPOINT_INTERVAL_PAGES=50      # After each batch
```

### Performance Re-estimation

#### With Aggressive Configuration (48GB M4 Max)

**100-Page Document** (~10MB):
- Rendering: 30-45 seconds (parallel, full cores)
- Analysis: 3-5 minutes (6 workers)
- Embedding: 30-60 seconds (256-chunk batches)
- **Total: ~5-7 minutes** (was 10-15 min)
- **Memory: ~20GB peak**

**500-Page Document** (~100MB):
- Rendering: 3-5 minutes (batch size 50)
- Analysis: 15-25 minutes (6 workers, overlapped with rendering)
- Embedding: 3-5 minutes (batched)
- **Total: ~20-35 minutes** (was 40-60 min)
- **Memory: ~30GB peak**

**1000-Page Document** (~200MB):
- Rendering: 6-10 minutes
- Analysis: 30-50 minutes (overlapped)
- Embedding: 6-10 minutes
- **Total: ~40-70 minutes** (was 80-120 min)
- **Memory: ~35GB peak**

### Speed Improvements

| Document | Conservative | Aggressive | Speedup |
|----------|-------------|------------|---------|
| 100 pages | 10-15 min | 5-7 min | **2-3×** |
| 500 pages | 40-60 min | 20-35 min | **2-3×** |
| 1000 pages | 80-120 min | 40-70 min | **2-3×** |

**Key Insight**: With 48GB RAM, 1000-page textbook processes in under 1 hour!

### Pipeline Overlapping

The real speedup comes from overlapping stages:

```
Timeline for 1000-page document:

Minute 0-5:   Render batch 1 (50 pages)
Minute 3-8:   Analyze batch 1 | Render batch 2
Minute 6-11:  Embed batch 1   | Analyze batch 2 | Render batch 3
Minute 9-14:  Store batch 1   | Embed batch 2   | Analyze batch 3 | Render batch 4
...

Result: All stages run in parallel after initial ramp-up
```

### Implementation Changes

#### Update ProgressiveDocumentProcessor

```python
class ProgressiveDocumentProcessor:
    def __init__(
        self,
        batch_size: int = 50,          # 5× larger
        max_memory_gb: int = 40,       # Use more RAM
        max_render_workers: int = 12,  # All P-cores
        max_analysis_workers: int = 6, # Push GPU
        pre_render_batches: int = 2,   # Buffer ahead
        aggressive_mode: bool = True    # Enable optimizations
    ):
        self.batch_size = batch_size
        self.pre_render_batches = pre_render_batches
        self.aggressive_mode = aggressive_mode
        
        # Create larger worker pools
        self.render_pool = ThreadPoolExecutor(max_workers=max_render_workers)
        self.analysis_pool = ThreadPoolExecutor(max_workers=max_analysis_workers)
        
        # Enable model caching
        if aggressive_mode:
            self._preload_models()
    
    def _preload_models(self):
        """Pre-load models to avoid reload overhead."""
        logger.info("Pre-loading models for aggressive mode")
        # Load and cache Nanonets model
        # Load and cache Jina embeddings
        # Keep in memory throughout processing
    
    def process_with_overlapping(self, file_path: Path):
        """
        Process with overlapped pipeline stages.
        
        Uses queues to feed each stage:
        Render Queue → Analysis Queue → Embedding Queue → Storage
        
        All stages run concurrently after ramp-up.
        """
        render_queue = Queue(maxsize=self.pre_render_batches)
        analysis_queue = Queue(maxsize=2)
        embedding_queue = Queue(maxsize=2)
        
        # Start all pipeline stages
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pipeline:
            render_future = pipeline.submit(
                self._render_stage, file_path, render_queue
            )
            analysis_future = pipeline.submit(
                self._analysis_stage, render_queue, analysis_queue
            )
            embedding_future = pipeline.submit(
                self._embedding_stage, analysis_queue, embedding_queue
            )
            storage_future = pipeline.submit(
                self._storage_stage, embedding_queue
            )
            
            # Wait for completion
            concurrent.futures.wait([
                render_future, analysis_future, 
                embedding_future, storage_future
            ])
```

### Memory Safety with Aggressive Config

Even with aggressive config, maintain safety:

```python
class AggressiveMemoryMonitor(MemoryMonitor):
    def __init__(self, max_memory_gb: int = 40):
        super().__init__(max_memory_gb)
        self.aggressive_threshold = 0.85  # Use up to 85%
    
    def can_allocate_batch(self, batch_size: int) -> bool:
        """Check if we can safely allocate a large batch."""
        current_usage = self.get_usage_percent() / 100
        
        if current_usage > self.aggressive_threshold:
            # Scale back if approaching limit
            return False
        
        # Estimate required memory
        required_gb = (batch_size * 100) / 1024  # 100MB per page
        available_gb = self.get_available()
        
        return available_gb > (required_gb * 1.5)  # 50% safety margin
```

### Checkpoint Strategy for Large Batches

With 50-page batches, checkpoint after each batch:

```python
# Save checkpoint every 50 pages (one batch)
# This balances:
# - Progress preservation (lose at most 50 pages)
# - Checkpoint overhead (minimal at ~1% of processing time)
# - Disk space (one checkpoint per batch)

checkpoint_interval = self.batch_size  # 50 pages
```

### Configuration Profiles

Provide preset profiles for different scenarios:

```python
PROFILES = {
    "aggressive": {
        "batch_size": 50,
        "max_memory_gb": 40,
        "max_render_workers": 12,
        "max_analysis_workers": 6,
        "embedding_batch_size": 256,
        "pre_render_batches": 2,
        "description": "Maximum speed for 48GB+ systems"
    },
    "balanced": {
        "batch_size": 20,
        "max_memory_gb": 32,
        "max_render_workers": 6,
        "max_analysis_workers": 3,
        "embedding_batch_size": 128,
        "pre_render_batches": 1,
        "description": "Good speed with safety margin"
    },
    "conservative": {
        "batch_size": 10,
        "max_memory_gb": 24,
        "max_render_workers": 4,
        "max_analysis_workers": 2,
        "embedding_batch_size": 64,
        "pre_render_batches": 0,
        "description": "Safest for 32GB systems"
    }
}
```

### Final Performance Target

**With Aggressive Configuration on M4 Max**:
- ✅ 500-page textbook: **~25 minutes** (was 2-3 hours)
- ✅ 1000-page textbook: **~50 minutes** (was 2-4 hours)
- ✅ Memory usage: **30-35GB** (utilizing 48GB capacity)
- ✅ Quality: **No compromise** (still uses Nanonets + semantic chunking)

This makes large document processing practical for interactive use!
