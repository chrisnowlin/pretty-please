from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class Document:
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: Optional[str] = None
    
    def __post_init__(self) -> None:
        if self.source and "source" not in self.metadata:
            self.metadata["source"] = self.source


class DocumentLoader(ABC):
    @abstractmethod
    def load(self, file_path: Path) -> Document:
        pass
    
    @abstractmethod
    def supports(self, file_path: Path) -> bool:
        pass
