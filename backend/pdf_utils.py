"""
PDF Processing Utilities for DeepSeek OCR
Handles PDF to image conversion and batch processing
"""

import io
import re
from typing import List, Tuple, Dict, Any
import fitz  # PyMuPDF
import img2pdf
from PIL import Image
import numpy as np


def pdf_to_images_high_quality(pdf_bytes: bytes, dpi: int = 144) -> List[Image.Image]:
    """
    Convert PDF pages to high-quality PIL images

    Args:
        pdf_bytes: PDF file as bytes
        dpi: Resolution for rendering (default: 144)

    Returns:
        List of PIL Image objects, one per page
    """
    images = []

    # Open PDF from bytes
    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")

    # Calculate zoom factor from DPI
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)

    # Process each page
    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]

        # Render page to pixmap
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)

        # Allow large images
        Image.MAX_IMAGE_PIXELS = None

        # Convert to PIL Image
        img_data = pixmap.tobytes("png")
        img = Image.open(io.BytesIO(img_data))

        # Ensure RGB mode
        if img.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        images.append(img)

    pdf_document.close()
    return images


def images_to_pdf(pil_images: List[Image.Image]) -> bytes:
    """
    Convert list of PIL images to PDF bytes

    Args:
        pil_images: List of PIL Image objects

    Returns:
        PDF file as bytes
    """
    if not pil_images:
        return b''

    image_bytes_list = []

    for img in pil_images:
        # Ensure RGB mode
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Convert to JPEG bytes
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='JPEG', quality=95)
        img_bytes = img_buffer.getvalue()
        image_bytes_list.append(img_bytes)

    # Convert to PDF
    pdf_bytes = img2pdf.convert(image_bytes_list)
    return pdf_bytes


def extract_ref_patterns(text: str) -> Tuple[List[Tuple], List[str], List[str]]:
    """
    Extract reference patterns from OCR output

    Args:
        text: OCR output text with reference tags

    Returns:
        Tuple of (all_matches, image_matches, other_matches)
    """
    pattern = r'(<\|ref\|>(.*?)<\|/ref\|><\|det\|>(.*?)<\|/det\|>)'
    matches = re.findall(pattern, text, re.DOTALL)

    matches_image = []
    matches_other = []

    for match in matches:
        if '<|ref|>image<|/ref|>' in match[0]:
            matches_image.append(match[0])
        else:
            matches_other.append(match[0])

    return matches, matches_image, matches_other


def parse_coordinates(ref_text: Tuple, image_width: int, image_height: int) -> Dict[str, Any]:
    """
    Parse coordinates from reference text

    Args:
        ref_text: Tuple of (full_match, label, coordinates)
        image_width: Image width in pixels
        image_height: Image height in pixels

    Returns:
        Dictionary with label and scaled coordinates
    """
    try:
        label_type = ref_text[1]
        cor_list = eval(ref_text[2])

        # Scale coordinates from 0-999 to actual pixels
        scaled_boxes = []
        for points in cor_list:
            x1, y1, x2, y2 = points
            scaled_box = [
                int(x1 / 999 * image_width),
                int(y1 / 999 * image_height),
                int(x2 / 999 * image_width),
                int(y2 / 999 * image_height)
            ]
            scaled_boxes.append(scaled_box)

        return {
            'label': label_type,
            'boxes': scaled_boxes
        }
    except Exception as e:
        print(f"Error parsing coordinates: {e}")
        return None


def crop_images_from_refs(image: Image.Image, refs: List[Tuple]) -> List[Image.Image]:
    """
    Crop images based on reference bounding boxes

    Args:
        image: Source PIL Image
        refs: List of reference tuples

    Returns:
        List of cropped PIL Images
    """
    cropped_images = []
    image_width, image_height = image.size

    for ref in refs:
        coord_data = parse_coordinates(ref, image_width, image_height)
        if coord_data and coord_data['label'] == 'image':
            for box in coord_data['boxes']:
                x1, y1, x2, y2 = box
                try:
                    cropped = image.crop((x1, y1, x2, y2))
                    cropped_images.append(cropped)
                except Exception as e:
                    print(f"Error cropping image: {e}")
                    continue

    return cropped_images


def clean_markdown_content(content: str, image_refs: List[str], other_refs: List[str]) -> str:
    """
    Clean markdown content by removing reference tags

    Args:
        content: Raw OCR output with tags
        image_refs: List of image reference tags
        other_refs: List of other reference tags

    Returns:
        Cleaned markdown content
    """
    cleaned = content

    # Remove image reference tags (will be replaced with markdown images)
    for ref in image_refs:
        cleaned = cleaned.replace(ref, '')

    # Remove other reference tags and clean up formatting
    for ref in other_refs:
        cleaned = cleaned.replace(ref, '')

    # Clean up LaTeX and formatting
    cleaned = (cleaned
               .replace('\\coloneqq', ':=')
               .replace('\\eqqcolon', '=:')
               .replace('\n\n\n\n', '\n\n')
               .replace('\n\n\n', '\n\n'))

    return cleaned
