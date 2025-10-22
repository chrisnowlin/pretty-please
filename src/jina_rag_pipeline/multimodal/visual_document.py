"""Visual document processing for layout-aware embeddings."""

import io
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import logging

from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)


class VisualDocumentProcessor:
    """Process visual documents with layout understanding."""
    
    def __init__(self, preserve_layout: bool = True):
        """Initialize visual document processor.
        
        Args:
            preserve_layout: Whether to preserve spatial relationships
        """
        self.preserve_layout = preserve_layout
        
    def pdf_to_images(
        self,
        pdf_path: str,
        dpi: int = 150,
        first_page: Optional[int] = None,
        last_page: Optional[int] = None
    ) -> List[Image.Image]:
        """Convert PDF pages to images.
        
        Args:
            pdf_path: Path to PDF file
            dpi: DPI for rendering
            first_page: First page to convert (1-indexed)
            last_page: Last page to convert (inclusive)
            
        Returns:
            List of PIL Images
        """
        try:
            import pypdf
            import pdf2image
            
            images = pdf2image.convert_from_path(
                pdf_path,
                dpi=dpi,
                first_page=first_page,
                last_page=last_page
            )
            return images
            
        except ImportError:
            logger.warning("pdf2image not installed. Using pypdf text extraction only.")
            # Fallback: extract text and create simple image
            reader = pypdf.PdfReader(pdf_path)
            images = []
            
            for page_num in range(len(reader.pages)):
                if first_page and page_num + 1 < first_page:
                    continue
                if last_page and page_num + 1 > last_page:
                    break
                    
                page = reader.pages[page_num]
                text = page.extract_text()
                
                # Create a simple text image (placeholder)
                img = Image.new('RGB', (800, 1000), color='white')
                images.append(img)
                
            return images
            
    def detect_regions(
        self,
        image: Image.Image,
        min_region_size: int = 50
    ) -> List[Dict[str, Any]]:
        """Detect text and visual regions in an image.
        
        Args:
            image: Input image
            min_region_size: Minimum region size in pixels
            
        Returns:
            List of detected regions with metadata
        """
        # Convert to numpy array
        img_array = np.array(image)
        height, width = img_array.shape[:2]
        
        # Simple region detection based on color variance
        # In production, use proper layout detection models
        regions = []
        
        # Divide image into grid
        grid_size = 100
        for y in range(0, height - grid_size, grid_size):
            for x in range(0, width - grid_size, grid_size):
                region = img_array[y:y+grid_size, x:x+grid_size]
                
                # Calculate variance to detect non-empty regions
                if region.shape[2] == 3:  # RGB
                    variance = np.var(region.reshape(-1, 3), axis=0).mean()
                else:
                    variance = np.var(region)
                    
                if variance > 10:  # Non-empty region
                    regions.append({
                        "bbox": [x, y, x+grid_size, y+grid_size],
                        "type": "text" if variance < 1000 else "image",
                        "confidence": min(1.0, variance / 1000),
                        "area": grid_size * grid_size
                    })
                    
        # Filter small regions
        regions = [r for r in regions if r["area"] >= min_region_size * min_region_size]
        
        return regions
        
    def extract_region_features(
        self,
        image: Image.Image,
        regions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract features from detected regions.
        
        Args:
            image: Source image
            regions: List of regions with bounding boxes
            
        Returns:
            Regions with extracted features
        """
        for region in regions:
            bbox = region["bbox"]
            x1, y1, x2, y2 = bbox
            
            # Crop region
            region_img = image.crop((x1, y1, x2, y2))
            
            # Extract basic features
            region["features"] = {
                "size": (x2 - x1, y2 - y1),
                "position": ((x1 + x2) / 2, (y1 + y2) / 2),
                "relative_position": (
                    (x1 + x2) / 2 / image.width,
                    (y1 + y2) / 2 / image.height
                ),
                "aspect_ratio": (x2 - x1) / (y2 - y1) if y2 > y1 else 1
            }
            
            # Store cropped image for embedding
            region["image"] = region_img
            
        return regions
        
    def generate_layout_description(
        self,
        regions: List[Dict[str, Any]],
        image_size: Tuple[int, int]
    ) -> str:
        """Generate text description of document layout.
        
        Args:
            regions: List of detected regions
            image_size: Size of original image (width, height)
            
        Returns:
            Text description of layout
        """
        if not regions:
            return "Empty document"
            
        width, height = image_size
        
        # Group regions by type
        text_regions = [r for r in regions if r["type"] == "text"]
        image_regions = [r for r in regions if r["type"] == "image"]
        
        description_parts = []
        
        # Overall layout
        description_parts.append(
            f"Document layout: {len(regions)} regions "
            f"({len(text_regions)} text, {len(image_regions)} visual)"
        )
        
        # Spatial distribution
        if self.preserve_layout:
            # Top, middle, bottom distribution
            top_regions = [r for r in regions if r["features"]["relative_position"][1] < 0.33]
            middle_regions = [r for r in regions if 0.33 <= r["features"]["relative_position"][1] < 0.67]
            bottom_regions = [r for r in regions if r["features"]["relative_position"][1] >= 0.67]
            
            description_parts.append(
                f"Spatial distribution: {len(top_regions)} top, "
                f"{len(middle_regions)} middle, {len(bottom_regions)} bottom"
            )
            
        return ". ".join(description_parts)
        
    def process_document(
        self,
        document_path: str,
        embedder = None
    ) -> Dict[str, Any]:
        """Process a visual document end-to-end.
        
        Args:
            document_path: Path to document (PDF or image)
            embedder: Optional embedder for generating embeddings
            
        Returns:
            Processed document with regions and embeddings
        """
        path = Path(document_path)
        
        # Load document
        if path.suffix.lower() == ".pdf":
            images = self.pdf_to_images(str(path))
        elif path.suffix.lower() in [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]:
            images = [Image.open(path)]
        else:
            raise ValueError(f"Unsupported document type: {path.suffix}")
            
        # Process each page
        pages = []
        for page_num, image in enumerate(images):
            # Detect regions
            regions = self.detect_regions(image)
            regions = self.extract_region_features(image, regions)
            
            # Generate layout description
            layout_desc = self.generate_layout_description(regions, image.size)
            
            page_data = {
                "page_number": page_num + 1,
                "size": image.size,
                "regions": regions,
                "layout_description": layout_desc
            }
            
            # Generate embeddings if embedder provided
            if embedder:
                # Page-level embedding
                if hasattr(embedder, 'encode_image'):
                    page_data["page_embedding"] = embedder.encode_image(image)
                    
                    # Region-level embeddings
                    region_images = [r["image"] for r in regions if "image" in r]
                    if region_images:
                        region_embeddings = embedder.encode_image(region_images)
                        for i, region in enumerate(regions):
                            if "image" in region:
                                region["embedding"] = region_embeddings[i] if len(region_embeddings) > i else None
                                
            pages.append(page_data)
            
        return {
            "path": str(path),
            "type": path.suffix.lower()[1:],
            "num_pages": len(pages),
            "pages": pages
        }