import tempfile
from pathlib import Path

from PIL import Image
import pytest

from src.jina_rag_pipeline.ingestion.loaders import NanonetsFirstLoader


class FakeAnalyzer:
    def __init__(self):
        self.calls = []

    def analyze_document(self, file_path, page_number=1):
        # Record calls for verification
        self.calls.append((str(file_path), page_number))
        return f"FAKE_MARKDOWN_PAGE_{page_number}"


def create_temp_image(size=(64, 64), color=(200, 200, 200)) -> Path:
    img = Image.new("RGB", size, color)
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    img.save(tmp.name, format="PNG")
    return Path(tmp.name)


def test_nanonets_first_loader_on_image_uses_analyzer_and_returns_document():
    fake = FakeAnalyzer()
    loader = NanonetsFirstLoader(analyzer=fake)

    img_path = create_temp_image()
    try:
        doc = loader.load(img_path)
        assert "FAKE_MARKDOWN_PAGE_1" in doc.content
        assert doc.metadata.get("extraction_method") == "nanonets-ocr2-3b"
        assert doc.metadata.get("format") == "image"
        # Analyzer called once for image
        assert fake.calls == [(str(img_path), 1)]
    finally:
        try:
            img_path.unlink(missing_ok=True)
        except Exception:
            pass


def test_nanonets_first_loader_supports_images_and_pdfs():
    loader = NanonetsFirstLoader(analyzer=FakeAnalyzer())
    assert loader.supports(Path("foo.pdf"))
    assert loader.supports(Path("foo.png"))
    assert loader.supports(Path("foo.jpg"))
    assert not loader.supports(Path("foo.txt"))

