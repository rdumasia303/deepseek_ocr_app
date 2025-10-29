import os
import re
import tempfile
import shutil
import io
import logging
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import torch
from transformers import AutoModel, AutoTokenizer
from PIL import Image
import uvicorn
from decouple import config as env_config
import fitz  # PyMuPDF

# Set up logging
logger = logging.getLogger(__name__)

# Set reasonable limit for large images (500 megapixels)
# This protects against decompression bombs while allowing large PDFs
# Set once globally at module level to avoid threading issues
Image.MAX_IMAGE_PIXELS = 500_000_000

# -----------------------------
# PDF to Images conversion
# -----------------------------
def _convert_pdf_page(args):
    """
    Helper function to convert a single PDF page to PIL Image
    This is used by ThreadPoolExecutor for parallel processing
    
    Args:
        args: tuple of (pdf_path, page_num, dpi)
    
    Returns:
        tuple of (page_num, PIL Image object)
    """
    pdf_path, page_num, dpi = args
    
    # Open the PDF document for this thread
    pdf_document = fitz.open(pdf_path)
    
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    
    page = pdf_document[page_num]
    pixmap = page.get_pixmap(matrix=matrix, alpha=False)
    
    # Convert pixmap to PIL Image
    img_data = pixmap.tobytes("png")
    img = Image.open(io.BytesIO(img_data))
    
    # Convert RGBA to RGB if needed
    if img.mode in ('RGBA', 'LA'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background
    
    pdf_document.close()
    return (page_num, img)


def pdf_to_images(pdf_path: str, dpi: int = 144) -> List[Image.Image]:
    """
    Convert PDF pages to PIL Images using parallel processing
    
    Args:
        pdf_path: Path to the PDF file
        dpi: DPI for rendering (default: 144)
    
    Returns:
        List of PIL Image objects, one per page (in correct order)
    """
    # Get max workers from environment, default to 4
    max_workers = env_config("MAX_PDF_WORKERS", default=4, cast=int)
    
    # Open PDF to get page count
    pdf_document = fitz.open(pdf_path)
    page_count = pdf_document.page_count
    pdf_document.close()
    
    # If only 1 page, use the helper function directly
    if page_count == 1:
        _, img = _convert_pdf_page((pdf_path, 0, dpi))
        return [img]
    
    # Use ThreadPoolExecutor for parallel page conversion
    # Limit workers to min(max_workers, page_count) for efficiency
    num_workers = min(max_workers, page_count)
    
    logger.info(f"Converting {page_count} PDF page(s) using {num_workers} worker(s)")
    
    # Prepare arguments for each page
    page_args = [(pdf_path, page_num, dpi) for page_num in range(page_count)]
    
    # Process pages in parallel
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        results = list(executor.map(_convert_pdf_page, page_args))
    
    # Sort by page number to maintain correct order
    results.sort(key=lambda x: x[0])
    
    # Extract images in correct order
    images = [img for _, img in results]
    
    return images

# -----------------------------
# Lifespan context for model loading
# -----------------------------
model = None
tokenizer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model on startup, cleanup on shutdown"""
    global model, tokenizer
    
    # Environment setup
    os.environ.pop("TRANSFORMERS_CACHE", None)
    MODEL_NAME = env_config("MODEL_NAME", default="deepseek-ai/DeepSeek-OCR")
    HF_HOME = env_config("HF_HOME", default="/models")
    os.makedirs(HF_HOME, exist_ok=True)
    
    # Load model
    print(f"🚀 Loading {MODEL_NAME}...")
    torch_dtype = torch.bfloat16
    
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
    )
    
    model = AutoModel.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
        use_safetensors=True,
        attn_implementation="eager",
        torch_dtype=torch_dtype,
    ).eval().to("cuda")
    
    # Pad token setup
    try:
        if getattr(tokenizer, "pad_token_id", None) is None and getattr(tokenizer, "eos_token_id", None) is not None:
            tokenizer.pad_token = tokenizer.eos_token
        if getattr(model.config, "pad_token_id", None) is None and getattr(tokenizer, "pad_token_id", None) is not None:
            model.config.pad_token_id = tokenizer.pad_token_id
    except Exception:
        pass
    
    print("✅ Model loaded and ready!")
    
    yield
    
    # Cleanup
    print("🛑 Shutting down...")

# -----------------------------
# FastAPI app
# -----------------------------
app = FastAPI(
    title="DeepSeek-OCR API",
    description="Blazing fast OCR with DeepSeek-OCR model 🔥",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Prompt builder
# -----------------------------
def build_prompt(
    mode: str,
    user_prompt: str,
    grounding: bool,
    find_term: Optional[str],
    schema: Optional[str],
    include_caption: bool,
) -> str:
    """Build the prompt based on mode"""
    parts: List[str] = ["<image>"]
    mode_requires_grounding = mode in {"find_ref", "layout_map", "pii_redact"}
    if grounding or mode_requires_grounding:
        parts.append("<|grounding|>")

    instruction = ""
    if mode == "plain_ocr":
        instruction = "Free OCR."
    elif mode == "markdown":
        instruction = "Convert the document to markdown."
    elif mode == "tables_csv":
        instruction = (
            "Extract every table and output CSV only. "
            "Use commas, minimal quoting. If multiple tables, separate with a line containing '---'."
        )
    elif mode == "tables_md":
        instruction = "Extract every table as GitHub-flavored Markdown tables. Output only the tables."
    elif mode == "kv_json":
        schema_text = schema.strip() if schema else "{}"
        instruction = (
            "Extract key fields and return strict JSON only. "
            f"Use this schema (fill the values): {schema_text}"
        )
    elif mode == "figure_chart":
        instruction = (
            "Parse the figure. First extract any numeric series as a two-column table (x,y). "
            "Then summarize the chart in 2 sentences. Output the table, then a line '---', then the summary."
        )
    elif mode == "find_ref":
        key = (find_term or "").strip() or "Total"
        instruction = f"Locate <|ref|>{key}<|/ref|> in the image."
    elif mode == "layout_map":
        instruction = (
            'Return a JSON array of blocks with fields {"type":["title","paragraph","table","figure"],'
            '"box":[x1,y1,x2,y2]}. Do not include any text content.'
        )
    elif mode == "pii_redact":
        instruction = (
            'Find all occurrences of emails, phone numbers, postal addresses, and IBANs. '
            'Return a JSON array of objects {label, text, box:[x1,y1,x2,y2]}.'
        )
    elif mode == "multilingual":
        instruction = "Free OCR. Detect the language automatically and output in the same script."
    elif mode == "describe":
        instruction = "Describe this image. Focus on visible key elements."
    elif mode == "freeform":
        instruction = user_prompt.strip() if user_prompt else "OCR this image."
    else:
        instruction = "OCR this image."

    if include_caption and mode not in {"describe"}:
        instruction = instruction + "\nThen add a one-paragraph description of the image."

    parts.append(instruction)
    return "\n".join(parts)

# -----------------------------
# Grounding parser
# -----------------------------
# Match a full detection block and capture the coordinates as the entire list expression
# Examples of captured coords (including outer brackets):
#  - [[312, 339, 480, 681]]
#  - [[504, 700, 625, 910], [771, 570, 996, 996]]
#  - [[110, 310, 255, 800], [312, 343, 479, 680], ...]
# Using a greedy bracket capture ensures we include all inner lists up to the last ']' before </|det|>
DET_BLOCK = re.compile(
    r"<\|ref\|>(?P<label>.*?)<\|/ref\|>\s*<\|det\|>\s*(?P<coords>\[.*\])\s*<\|/det\|>",
    re.DOTALL,
)

def clean_grounding_text(text: str) -> str:
    """Remove grounding tags from text for display, keeping labels"""
    # Replace <|ref|>label<|/ref|><|det|>[...any nested lists...]<|/det|> with just the label
    cleaned = re.sub(
        r"<\|ref\|>(.*?)<\|/ref\|>\s*<\|det\|>\s*\[.*\]\s*<\|/det\|>",
        r"\1",
        text,
        flags=re.DOTALL,
    )
    # Also remove any standalone grounding tags
    cleaned = re.sub(r"<\|grounding\|>", "", cleaned)
    return cleaned.strip()

def parse_detections(text: str, image_width: int, image_height: int) -> List[Dict[str, Any]]:
    """Parse grounding boxes from text and scale from 0-999 normalized coords to actual image dimensions
    
    Handles both single and multiple bounding boxes:
    - Single: <|ref|>label<|/ref|><|det|>[[x1,y1,x2,y2]]<|/det|>
    - Multiple: <|ref|>label<|/ref|><|det|>[[x1,y1,x2,y2], [x1,y1,x2,y2], ...]<|/det|>
    """
    boxes: List[Dict[str, Any]] = []
    for m in DET_BLOCK.finditer(text or ""):
        label = m.group("label").strip()
        coords_str = m.group("coords").strip()

        print(f"🔍 DEBUG: Found detection for '{label}'")
        print(f"📦 Raw coords string (with brackets): {coords_str}")

        try:
            import ast

            # Parse the full bracket expression directly (handles single and multiple)
            parsed = ast.literal_eval(coords_str)

            # Normalize to a list of lists
            if (
                isinstance(parsed, list)
                and len(parsed) == 4
                and all(isinstance(n, (int, float)) for n in parsed)
            ):
                # Single box provided as [x1,y1,x2,y2]
                box_coords = [parsed]
                print("📦 Single box (flat list) detected")
            elif isinstance(parsed, list):
                box_coords = parsed
                print(f"📦 Boxes detected: {len(box_coords)}")
            else:
                raise ValueError("Unsupported coords structure")

            # Process each box
            for idx, box in enumerate(box_coords):
                if isinstance(box, (list, tuple)) and len(box) >= 4:
                    x1 = int(float(box[0]) / 999 * image_width)
                    y1 = int(float(box[1]) / 999 * image_height)
                    x2 = int(float(box[2]) / 999 * image_width)
                    y2 = int(float(box[3]) / 999 * image_height)
                    print(f"  Box {idx+1}: {box} → [{x1}, {y1}, {x2}, {y2}]")
                    boxes.append({"label": label, "box": [x1, y1, x2, y2]})
                else:
                    print(f"  ⚠️ Skipping invalid box: {box}")
        except Exception as e:
            print(f"❌ Parsing failed: {e}")
            continue
    
    print(f"🎯 Total boxes parsed: {len(boxes)}")
    return boxes

# -----------------------------
# Routes
# -----------------------------
@app.get("/")
async def root():
    return {"message": "DeepSeek-OCR API is running! 🚀", "docs": "/docs"}

@app.get("/health")
async def health():
    return {"status": "healthy", "model_loaded": model is not None}

@app.post("/api/ocr")
async def ocr_inference(
    image: UploadFile = File(...),
    mode: str = Form("plain_ocr"),
    prompt: str = Form(""),
    grounding: bool = Form(False),
    include_caption: bool = Form(False),
    find_term: Optional[str] = Form(None),
    schema: Optional[str] = Form(None),
    base_size: int = Form(1024),
    image_size: int = Form(640),
    crop_mode: bool = Form(True),
    test_compress: bool = Form(False),
):
    """
    Perform OCR inference on uploaded image or PDF
    
    - **image**: Image or PDF file to process
    - **mode**: OCR mode (plain_ocr, markdown, tables_csv, etc.)
    - **prompt**: Custom prompt for freeform mode
    - **grounding**: Enable grounding boxes
    - **include_caption**: Add image description
    - **find_term**: Term to find (for find_ref mode)
    - **schema**: JSON schema (for kv_json mode)
    - **base_size**: Base processing size
    - **image_size**: Image size parameter
    - **crop_mode**: Enable crop mode
    - **test_compress**: Test compression
    """
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet")
    
    # Build prompt
    prompt_text = build_prompt(
        mode=mode,
        user_prompt=prompt,
        grounding=grounding,
        find_term=find_term,
        schema=schema,
        include_caption=include_caption,
    )
    
    tmp_file = None
    tmp_images = []
    out_dir = None
    try:
        # Determine file type and save uploaded file
        filename = image.filename.lower()
        is_pdf = filename.endswith('.pdf')
        
        suffix = ".pdf" if is_pdf else ".png"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await image.read()
            tmp.write(content)
            tmp_file = tmp.name
        
        # Convert PDF to images if necessary
        if is_pdf:
            print(f"📄 Processing PDF file: {image.filename}")
            images_list = pdf_to_images(tmp_file)
            print(f"📄 Converted PDF to {len(images_list)} page(s)")
        else:
            # For regular images, load as single-item list
            try:
                img = Image.open(tmp_file)
                images_list = [img]
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")
        
        # Create single output directory for all pages
        out_dir = tempfile.mkdtemp(prefix="dsocr_")
        
        # Process each page/image
        all_results = []
        for idx, img in enumerate(images_list):
            # Save image to temp file for model processing
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img_file:
                img.save(tmp_img_file.name, format='PNG')
                tmp_img_path = tmp_img_file.name
                tmp_images.append(tmp_img_path)
            
            # Get image dimensions
            orig_w, orig_h = img.size
            
            # Run inference
            res = model.infer(
                tokenizer,
                prompt=prompt_text,
                image_file=tmp_img_path,
                output_path=out_dir,
                base_size=base_size,
                image_size=image_size,
                crop_mode=crop_mode,
                save_results=False,
                test_compress=test_compress,
                eval_mode=True,
            )
            
            # Normalize response
            if isinstance(res, str):
                text = res.strip()
            elif isinstance(res, dict) and "text" in res:
                text = str(res["text"]).strip()
            elif isinstance(res, (list, tuple)):
                text = "\n".join(map(str, res)).strip()
            else:
                text = ""
            
            # Fallback: check output file
            if not text:
                mmd = os.path.join(out_dir, "result.mmd")
                if os.path.exists(mmd):
                    with open(mmd, "r", encoding="utf-8") as fh:
                        text = fh.read().strip()
            if not text:
                text = "No text returned by model."
            
            # Parse grounding boxes with proper coordinate scaling
            boxes = parse_detections(text, orig_w or 1, orig_h or 1) if ("<|det|>" in text or "<|ref|>" in text) else []
            
            # Clean grounding tags from display text, but keep the labels
            display_text = clean_grounding_text(text) if ("<|ref|>" in text or "<|grounding|>" in text) else text
            
            # If display text is empty after cleaning but we have boxes, show the labels
            if not display_text and boxes:
                display_text = ", ".join([b["label"] for b in boxes])
            
            page_result = {
                "page": idx + 1 if is_pdf else None,
                "text": display_text,
                "raw_text": text,
                "boxes": boxes,
                "image_dims": {"w": orig_w, "h": orig_h}
            }
            all_results.append(page_result)
        
        # Combine results for PDF or return single result for image
        if is_pdf and len(all_results) > 1:
            # For multi-page PDFs, combine all text with page separators
            combined_text = []
            combined_raw_text = []
            
            for page_result in all_results:
                page_num = page_result["page"]
                combined_text.append(f"\n--- Page {page_num} ---\n{page_result['text']}")
                combined_raw_text.append(f"\n--- Page {page_num} ---\n{page_result['raw_text']}")
                # Note: boxes are per-page, so we'd need more complex handling to visualize multi-page
            
            return JSONResponse({
                "success": True,
                "text": "\n".join(combined_text),
                "raw_text": "\n".join(combined_raw_text),
                "boxes": [],  # Boxes are per-page, not combined for multi-page PDFs
                "image_dims": {"w": all_results[0]["image_dims"]["w"], "h": all_results[0]["image_dims"]["h"]},
                "is_pdf": True,
                "pages": all_results,
                "metadata": {
                    "mode": mode,
                    "grounding": grounding or (mode in {"find_ref","layout_map","pii_redact"}),
                    "base_size": base_size,
                    "image_size": image_size,
                    "crop_mode": crop_mode,
                    "total_pages": len(all_results)
                }
            })
        else:
            # Single page/image result
            page_result = all_results[0]
            return JSONResponse({
                "success": True,
                "text": page_result["text"],
                "raw_text": page_result["raw_text"],
                "boxes": page_result["boxes"],
                "image_dims": page_result["image_dims"],
                "is_pdf": is_pdf,
                "metadata": {
                    "mode": mode,
                    "grounding": grounding or (mode in {"find_ref","layout_map","pii_redact"}),
                    "base_size": base_size,
                    "image_size": image_size,
                    "crop_mode": crop_mode
                }
            })
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}")
    
    finally:
        # Cleanup temp files
        if tmp_file:
            try:
                os.remove(tmp_file)
            except Exception:
                pass
        for tmp_img in tmp_images:
            try:
                os.remove(tmp_img)
            except Exception:
                pass
        if out_dir:
            shutil.rmtree(out_dir, ignore_errors=True)

if __name__ == "__main__":
    host = env_config("API_HOST", default="0.0.0.0")
    port = env_config("API_PORT", default=8000, cast=int)
    uvicorn.run(app, host=host, port=port)
