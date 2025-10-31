"""
PDF processing utilities for converting PDF pages to images
"""
import io
import fitz  # PyMuPDF
from PIL import Image
from typing import List


def pdf_to_images(pdf_content: bytes, dpi: int = 144) -> List[Image.Image]:
    """
    Convert PDF pages to PIL Images
    
    Args:
        pdf_content: PDF file content as bytes
        dpi: Resolution for rendering (default: 144)
        
    Returns:
        List of PIL Image objects, one per page
    """
    images = []
    
    # Open PDF from bytes
    pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
    
    # Calculate zoom factor from DPI
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    
    # Convert each page to image
    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        
        # Render page to pixmap
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        
        # Allow large images
        Image.MAX_IMAGE_PIXELS = None
        
        # Convert to PIL Image
        img_data = pixmap.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        
        # Convert RGBA to RGB if needed
        if img.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        images.append(img)
    
    pdf_document.close()
    return images
