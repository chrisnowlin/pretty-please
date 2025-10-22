import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import Document
from .chunking import Chunk, ChunkingStrategy, FixedSizeChunker
from .loaders import LoaderFactory


class DocumentProcessor:
    def __init__(
        self,
        chunking_strategy: Optional[ChunkingStrategy] = None,
        loader_factory: Optional[LoaderFactory] = None,
    ) -> None:
        self.chunking_strategy = chunking_strategy or FixedSizeChunker(chunk_size=512, overlap=50)
        self.loader_factory = loader_factory or LoaderFactory()
        self._processed_docs: Dict[str, str] = {}
    
    def compute_fingerprint(self, file_path: Path) -> str:
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def is_processed(self, file_path: Path) -> bool:
        fingerprint = self.compute_fingerprint(file_path)
        cached_fingerprint = self._processed_docs.get(str(file_path))
        return cached_fingerprint == fingerprint
    
    def mark_processed(self, file_path: Path) -> None:
        fingerprint = self.compute_fingerprint(file_path)
        self._processed_docs[str(file_path)] = fingerprint
    
    def load_document(self, file_path: Path) -> Document:
        print(f"[DEBUG PIPELINE] load_document called with: {file_path}", flush=True)
        print(f"[DEBUG PIPELINE] File exists check: {file_path.exists()}", flush=True)
        if not file_path.exists():
            print(f"[ERROR PIPELINE] File not found in pipeline.load_document: {file_path}", flush=True)
            print(f"[ERROR PIPELINE] Parent dir exists: {file_path.parent.exists()}", flush=True)
            if file_path.parent.exists():
                print(f"[ERROR PIPELINE] Parent dir contents: {list(file_path.parent.iterdir())}", flush=True)
            raise FileNotFoundError(f"File not found: {file_path}")
        return self.loader_factory.load(file_path)
    
    def chunk_document(self, document: Document) -> List[Chunk]:
        return self.chunking_strategy.chunk(document)
    
    def process(
        self,
        file_path: Path,
        skip_if_processed: bool = True,
        force_reprocess: bool = False,
    ) -> List[Chunk]:
        if not force_reprocess and skip_if_processed and self.is_processed(file_path):
            return []
        
        document = self.load_document(file_path)
        chunks = self.chunk_document(document)
        
        self.mark_processed(file_path)
        
        return chunks
    
    def process_batch(
        self,
        file_paths: List[Path],
        skip_if_processed: bool = True,
        force_reprocess: bool = False,
    ) -> Dict[str, List[Chunk]]:
        results = {}
        
        for file_path in file_paths:
            try:
                chunks = self.process(
                    file_path,
                    skip_if_processed=skip_if_processed,
                    force_reprocess=force_reprocess,
                )
                results[str(file_path)] = chunks
            except Exception as e:
                results[str(file_path)] = []
                print(f"Error processing {file_path}: {e}")
        
        return results
    
    def get_processed_files(self) -> Dict[str, str]:
        return self._processed_docs.copy()
    
    def clear_processed_cache(self) -> None:
        self._processed_docs.clear()
