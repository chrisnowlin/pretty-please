# Async Processing Guide

## Overview

The RAG pipeline supports asynchronous processing to prevent API blocking during heavy document processing operations. This guide covers three progressive approaches to handling document processing at scale:

1. **ThreadPool Offloading** - For single-machine deployments
2. **Distributed Workers (RQ)** - For multi-machine horizontal scaling
3. **Production Deployment** - For high-availability production environments

## Phase 1: ThreadPool Offloading

### Problem Statement

- Large PDFs (96+ pages, 21+ MB) caused uvicorn's single event loop to block
- Health check endpoint became unresponsive during heavy document processing
- API appeared "hung" to clients during Nanonets OCR extraction

### Solution Architecture

#### ThreadPool Executor

```python
_executor = ThreadPoolExecutor(max_workers=2)
```

- Module-level ThreadPoolExecutor with 2 worker threads
- Used for I/O-bound Nanonets processing (PDF rendering, image processing)
- ThreadPoolExecutor chosen over ProcessPoolExecutor because:
  - GIL doesn't affect I/O-bound operations significantly
  - PDF rendering is primarily I/O
  - Lower overhead than multiprocessing

#### Async Wrapper Method

Added `TaskManager._load_nanonets_document_async()` which:
- Uses `asyncio.run_in_executor()` to run blocking Nanonets load in thread pool
- Keeps event loop responsive - can process other API requests during loading
- Reports progress updates via WebSocket to connected clients
- Logs page/slide extraction counts

#### Updated Document Loading Pipeline

Modified `TaskManager.process_task()` to:
- Detect Nanonets-format files (PDFs, PPTX, images)
- Route to async offloader when `NANONETS_FIRST_ENABLED=true`
- Gracefully fall back to traditional loaders if Nanonets unavailable
- Handle both extracted regions and chunked processing

### Configuration

#### Environment Variables

```bash
# Enable Nanonets-first routing (default: true)
export NANONETS_FIRST_ENABLED=true

# Disable to use traditional loaders only
export NANONETS_FIRST_ENABLED=false
```

#### ThreadPool Settings

```python
max_workers=2  # 2 concurrent Nanonets processing tasks
```

**Rationale**:
- 2 workers allow 1-2 PDFs to process simultaneously
- Prevents overwhelming system with rendering threads
- Stays within typical uvicorn worker count
- Can be adjusted in production based on system resources

### Architecture Diagram

```
[API Request]
    ↓
[FastAPI Endpoint]
    ↓
[TaskManager.process_task() - async]
    ├─→ Detect format (PDF/PPTX/Image)
    ├─→ If Nanonets-enabled:
    │   ├─→ Call _load_nanonets_document_async()
    │   ├─→ run_in_executor(ThreadPool)
    │   ├─→ ThreadWorker1: PDF rendering + Nanonets OCR
    │   ├─→ ThreadWorker2: (Available for other work)
    │   └─→ Event Loop: FREE to handle other requests ✓
    ├─→ Process document (chunks/regions)
    └─→ Store embeddings

[Event Loop remains responsive]
    ├─→ Can accept new uploads ✓
    ├─→ Health checks respond ✓
    ├─→ Other API endpoints work ✓
```

### Test Results

#### 5-Page PDF Test (classroom_music_5pages.pdf, 998KB)

**Key Findings**:
1. ✓ **API Responsiveness**: Upload endpoint returned in 0.2s despite Nanonets processing
2. ✓ **No Blocking**: Health check endpoint remained accessible during processing
3. ✓ **Async Execution**: Nanonets OCR running in thread pool, not blocking event loop

### Benefits

**For Users**:
1. Faster API responses - Upload endpoints return immediately
2. Better UX - Can start multiple uploads without waiting
3. Real-time status - WebSocket progress updates while processing
4. No apparent hangs - API responsive even during heavy processing

**For Operations**:
1. No deadlocks - Async prevents event loop blocking
2. Scalable - Can handle multiple concurrent PDFs
3. Debuggable - Clear logging of progress
4. Graceful degradation - Falls back if Nanonets unavailable

---

## Phase 2: Distributed Processing (RQ)

### Overview

For horizontal scaling beyond a single server, the pipeline supports **RQ (Redis Queue)** for distributed processing across multiple worker machines.

### Architecture

```
┌──────────────────────────────────────────────────────────┐
│ FastAPI Server (stays responsive)                       │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ TaskManager                                          │ │
│ │ ├─ Small files → ThreadPool (2 workers)             │ │
│ │ └─ Large files → RQ (distributed workers)           │ │
│ └──────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
                    ↓
        ┌───────────────────────┐
        │ Redis (job queue)      │
        └───────────────────────┘
                    ↓
    ┌───────────────────────────────────┐
    │ RQ Workers (on separate machines) │
    │ ┌──────────┐  ┌──────────┐       │
    │ │ Worker 1 │  │ Worker 2 │  ...  │
    │ └──────────┘  └──────────┘       │
    └───────────────────────────────────┘
```

### Features

✅ **Automatic Routing**
- Files under 10MB: Processed via ThreadPool (fast, local)
- Files over 10MB: Routed to RQ workers (distributed)
- Configurable threshold via `LARGE_FILE_THRESHOLD_MB`

✅ **Graceful Fallback**
- RQ unavailable → Falls back to ThreadPool
- ThreadPool fails → Falls back to traditional loaders
- Ensures processing never fails completely

✅ **Real-Time Progress**
- Per-page updates via WebSocket
- Job status tracking
- Progress percentage reporting

✅ **Multiple Priority Queues**
- `high`: Large files (>50MB PDFs)
- `default`: Normal files (10-50MB)
- `low`: Background tasks (chunk processing)

### Setup

#### 1. Install Dependencies

```bash
uv pip install redis>=5.0.0 rq>=1.15.0
```

#### 2. Start Redis Server

**Using Docker**:
```bash
docker run -d -p 6379:6379 redis:latest
```

**Using Homebrew (macOS)**:
```bash
brew install redis
brew services start redis
```

**Using apt (Linux)**:
```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

#### 3. Configure Environment

```bash
export DISTRIBUTED_PROCESSING_ENABLED=true
export REDIS_URL="redis://localhost:6379/0"
export LARGE_FILE_THRESHOLD_MB=10.0
export RQ_WORKERS=2
```

#### 4. Start RQ Workers

```bash
# Start worker for all queues (recommended)
python -m jina_rag_pipeline.workers.worker

# Start worker for specific queues
python -m jina_rag_pipeline.workers.worker --queues high default

# Start multiple workers (in separate terminals)
python -m jina_rag_pipeline.workers.worker --name worker-01 &
python -m jina_rag_pipeline.workers.worker --name worker-02 &

# Start in burst mode (exits when queues empty - useful for testing)
python -m jina_rag_pipeline.workers.worker --burst
```

#### 5. Start API Server

```bash
uvicorn jina_rag_pipeline.api.app:app --host 0.0.0.0 --port 8000
```

### Configuration

#### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DISTRIBUTED_PROCESSING_ENABLED` | `false` | Enable RQ distributed processing |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection string |
| `REDIS_HOST` | `localhost` | Redis server hostname |
| `REDIS_PORT` | `6379` | Redis server port |
| `REDIS_DB` | `0` | Redis database number |
| `LARGE_FILE_THRESHOLD_MB` | `10.0` | File size threshold for RQ routing |
| `RQ_WORKERS` | `2` | Number of worker processes per machine |

#### Queue Settings

| Queue | Priority | Use Case |
|-------|----------|----------|
| `high` | Highest | PDFs >50MB, urgent processing |
| `default` | Medium | PDFs 10-50MB, PPTX files |
| `low` | Lowest | Background chunk processing |

### Monitoring

#### Check Redis Connection

```bash
redis-cli ping  # Should return: PONG
```

#### Monitor Queue Stats

```python
from jina_rag_pipeline.workers.queue import JobQueueManager

manager = JobQueueManager()
stats = manager.get_queue_stats()
print(stats)
```

#### RQ Dashboard (Optional)

```bash
uv pip install rq-dashboard
rq-dashboard --redis-url redis://localhost:6379/0
# Open browser to http://localhost:9181
```

### Performance Metrics

#### Expected Performance

| File Size | Processing Method | Typical Time |
|-----------|-------------------|--------------|
| <5MB PDF | ThreadPool | 10-30 seconds |
| 10-20MB PDF | RQ Worker | 30-60 seconds |
| 50-100MB PDF | RQ Worker | 2-5 minutes |
| >100MB PDF | RQ Worker (progressive) | 5-15 minutes |

#### Benchmarks

With distributed processing enabled (3 worker machines):
- **Throughput**: 10-15 large PDFs/minute
- **Concurrent jobs**: 6-9 (3 machines × 2-3 workers each)
- **Memory per worker**: 500MB-2GB (depends on PDF size)

---

## Phase 3: Production Deployment

### Multi-Worker Architecture

```
┌──────────────────────────────────────────────────┐
│ Nginx / Load Balancer                            │
│ ├─ HTTP: Round-robin                             │
│ └─ WebSocket: Sticky sessions (IP hash)          │
└──────────────────────────────────────────────────┘
         ↓                    ↓                ↓
┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│ Uvicorn Worker │  │ Uvicorn Worker │  │ Uvicorn Worker │
│ (Process 1)    │  │ (Process 2)    │  │ (Process 3)    │
└────────────────┘  └────────────────┘  └────────────────┘
         ↓                    ↓                ↓
    ┌─────────────────────────────────────────────┐
    │ Shared State Layer (Redis / PostgreSQL)    │
    │ ├─ Task status and progress                │
    │ ├─ WebSocket room subscriptions            │
    │ └─ Session data                             │
    └─────────────────────────────────────────────┘
         ↓
    ┌─────────────────────────────────────────────┐
    │ Persistent Storage                          │
    │ ├─ ChromaDB (shared volume / network)      │
    │ ├─ File uploads (shared volume / S3)       │
    │ └─ Metrics database                         │
    └─────────────────────────────────────────────┘
```

### Deployment Options

#### Option 1: Gunicorn + Uvicorn Workers (Recommended)

**Installation**:
```bash
uv pip install gunicorn
```

**Configuration** (`gunicorn.conf.py`):
```python
import multiprocessing
import os

bind = "0.0.0.0:8000"
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 10000
max_requests_jitter = 1000
timeout = 120
keepalive = 5

accesslog = "-"
errorlog = "-"
loglevel = "info"

graceful_timeout = 30
preload_app = False
```

**Start**:
```bash
gunicorn jina_rag_pipeline.api.app:app --config gunicorn.conf.py
```

#### Option 2: Supervisor + Multiple Uvicorn Instances

**Supervisor Configuration**:
```ini
[program:jina-rag-worker]
command=/path/to/venv/bin/uvicorn jina_rag_pipeline.api.app:app --host 127.0.0.1 --port 800%(process_num)s
process_name=worker-%(process_num)s
numprocs=4
autostart=true
autorestart=true
```

### Handling Shared State

#### Redis-backed State Manager

```python
# src/jina_rag_pipeline/api/state.py
import json
import redis
from typing import Any, Dict, Optional

class SharedStateManager:
    def __init__(self, redis_url: str = "redis://localhost:6379/1"):
        self.redis = redis.from_url(redis_url, decode_responses=True)

    def set_task_status(self, task_id: str, status: Dict[str, Any], ttl: int = 3600):
        key = f"task:{task_id}"
        self.redis.setex(key, ttl, json.dumps(status))

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        key = f"task:{task_id}"
        data = self.redis.get(key)
        return json.loads(data) if data else None

    def publish_progress(self, task_id: str, progress: Dict[str, Any]):
        channel = f"progress:{task_id}"
        self.redis.publish(channel, json.dumps(progress))
```

### WebSocket Handling

#### Nginx Configuration (Sticky Sessions)

```nginx
upstream jina_rag_backend {
    ip_hash;  # Enable sticky sessions based on client IP
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}

server {
    listen 80;
    server_name api.example.com;

    location /api/ {
        proxy_pass http://jina_rag_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws/ {
        proxy_pass http://jina_rag_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }
}
```

### File Storage

#### Option 1: Shared Volume (NFS, EFS)

```bash
mount -t nfs server:/exports/uploads /var/jina-rag/uploads
```

#### Option 2: Object Storage (S3, MinIO)

```bash
uv pip install boto3
```

```python
import boto3

s3_client = boto3.client('s3',
    endpoint_url='https://s3.amazonaws.com',
    aws_access_key_id='...',
    aws_secret_access_key='...'
)

s3_client.upload_file('local_file.pdf', 'my-bucket', 'uploads/file.pdf')
```

### Vector Database (ChromaDB)

#### Option 1: Network-mounted ChromaDB

```python
from chromadb.config import Settings

chroma_client = chromadb.Client(Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="/mnt/shared/chroma_storage"
))
```

#### Option 2: ChromaDB Client/Server Mode

```bash
docker run -d -p 8100:8100 chromadb/chroma
```

```python
import chromadb

chroma_client = chromadb.HttpClient(
    host="chroma-server",
    port=8100
)
```

### Docker Compose Example

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  chroma:
    image: chromadb/chroma:latest
    ports:
      - "8100:8100"
    volumes:
      - chroma_data:/chroma/chroma

  app:
    build: .
    command: gunicorn jina_rag_pipeline.api.app:app --config gunicorn.conf.py
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379/0
      - CHROMA_SERVER_HOST=chroma
      - DISTRIBUTED_PROCESSING_ENABLED=true
      - GUNICORN_WORKERS=4
    volumes:
      - shared_uploads:/var/jina-rag/uploads
    depends_on:
      - redis
      - chroma

  rq-worker:
    build: .
    command: python -m jina_rag_pipeline.workers.worker
    environment:
      - REDIS_URL=redis://redis:6379/0
      - CHROMA_SERVER_HOST=chroma
    volumes:
      - shared_uploads:/var/jina-rag/uploads
    depends_on:
      - redis
      - chroma
    deploy:
      replicas: 3

volumes:
  redis_data:
  chroma_data:
  shared_uploads:
```

### Environment Configuration

```bash
# Server
GUNICORN_WORKERS=4
WORKER_TIMEOUT=120

# Redis (shared state + RQ)
REDIS_URL=redis://redis-server:6379/0
DISTRIBUTED_PROCESSING_ENABLED=true

# Storage
UPLOAD_DIR=/mnt/shared/uploads
CHROMA_PERSIST_DIR=/mnt/shared/chroma_storage

# RQ Workers
LARGE_FILE_THRESHOLD_MB=10.0
RQ_WORKERS=2

# Logging
LOG_LEVEL=info
```

### Performance Tuning

#### Worker Count

```python
# Recommended: 2-4 workers per CPU core for I/O-bound workloads
import multiprocessing
workers = multiprocessing.cpu_count() * 2 + 1
```

#### Connection Limits

```python
worker_connections = 1000  # Max concurrent connections per worker
max_requests = 10000       # Restart worker after N requests (prevent memory leaks)
max_requests_jitter = 1000 # Add randomness to restarts
```

### Monitoring

#### Health Check

```bash
curl http://localhost:8000/api/health
```

#### Metrics Dashboard

```bash
curl http://localhost:8000/api/metrics/summary
curl http://localhost:8000/api/metrics/queues
curl http://localhost:8000/api/metrics/system
```

---

## Troubleshooting

### ThreadPool Issues

**Jobs not processing**:
- Check `NANONETS_FIRST_ENABLED=true`
- Check backend logs for errors
- Verify ThreadPool initialization

### RQ Issues

**Jobs not processing**:
1. Check Redis: `redis-cli ping`
2. Check workers: `ps aux | grep worker`
3. Check `DISTRIBUTED_PROCESSING_ENABLED=true`

**Workers can't connect to Redis**:
1. Verify `REDIS_URL` is correct
2. Check firewall allows port 6379
3. For remote Redis, ensure `bind 0.0.0.0` in redis.conf

**Jobs timing out**:
- Increase timeout in config
- Check worker has enough memory
- Monitor worker CPU/memory usage

### Production Issues

**WebSocket connections dropping**:
```nginx
proxy_read_timeout 3600s;
proxy_send_timeout 3600s;
```

**Task state not synchronized**:
```bash
redis-cli -h redis-server ping
```

**High memory usage**:
1. Reduce worker count
2. Enable `max_requests` to restart workers periodically
3. Use progressive PDF rendering

---

## Security Best Practices

1. **Use HTTPS in production**
2. **Enable authentication** (API keys, OAuth)
3. **Rate limiting** (use Redis-based rate limiter)
4. **Input validation** (file size limits, type checking)
5. **Network isolation** (Redis, ChromaDB on private network)
6. **Secret management** (use env vars or secret managers, never commit)

---

## Related Documentation

- [Nanonets Migration Guide](nanonets-migration.md)
- [Citations Feature](../features/citations.md)
- [System Architecture](../architecture/system-overview.md)
