#!/bin/bash
cd /Users/cnowlin/Developer/pretty_please
export PYTHONPATH=/Users/cnowlin/Developer/pretty_please:$PYTHONPATH
source .venv/bin/activate
# Use port 8000 as default
PORT=${PORT:-8000}
python -m uvicorn src.jina_rag_pipeline.api.app:app --port $PORT --host 127.0.0.1
