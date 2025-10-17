import os
import time
from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from google.cloud import vision
from models.ocr_models import OCRRequest, OCRResponse, BatchOCRResponse
from utils import (
    text_cleanup, 
    get_confidence_score, 
    get_image_metadata,
    generate_image_hash,
    get_cached_result,
    cache_result,
    get_cache_stats
)
import logging
from rich import print


ocr_router = APIRouter()

# Initialize rate limiter for OCR endpoints
limiter = Limiter(key_func=get_remote_address)

# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "cloud_vision_credentials.json" -> it's handled automatically in google cloud run

try:
    vision_client = vision.ImageAnnotatorClient()
    logging.info("Successfully initialized Google Cloud Vision client.")
except Exception as e:
    vision_client = None
    logging.error(f"Failed to initialize Google Cloud Vision client: {e}")


MAX_FILE_SIZE = 10 * 1024 * 1024
SUPPORTED_CONTENT_TYPES = ["image/jpeg", "image/jpg", "image/png", "image/gif"]


async def extract_text(image: UploadFile = File(...)):
    """
    This endpoint accepts a JPG image file and returns the extracted text.
    Args:
        image (UploadFile): The image file uploaded by the user.
    Returns:
        JSONResponse: A JSON response containing the extracted text and confidence score.
    """
    filename = image.filename
    content_type = image.content_type

    start_time = time.time()

    # Validate file type
    if content_type not in SUPPORTED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,  # Unsupported Media Type
            detail=f"Unsupported file format. Please upload a JPG/JPEG/PNG image. Found: {content_type}",
        )

    contents = await image.read()
    
    # Generate hash for caching
    image_hash = generate_image_hash(contents)
    
    # Check cache first
    cached_result = get_cached_result(image_hash)
    if cached_result:
        print(f"Cache hit for image: {filename}")
        # Remove cache_hit flag from response to client
        cached_result.pop('cache_hit', None)
        return cached_result
    
    print(f"Cache miss for image: {filename}, processing...")
    
    image_metadata = get_image_metadata(filename, content_type, contents)

    # Validate file size
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,  # Payload Too Large
            detail="File size exceeds the limit of 10MB.",
        )

    if not vision_client:
        raise HTTPException(
            status_code=503,
            detail="Vision API client is not available. The service cannot process images.",
        )

    try:
        vision_image = vision.Image(content=contents)

        # response = vision_client.text_detection(image=vision_image) -> doesnt give word-level confidence
        # texts = response.text_annotations

        response = vision_client.document_text_detection(image=vision_image)
        texts = response.full_text_annotation

        score = get_confidence_score(texts)

        if response.error.message:
            raise HTTPException(
                status_code=500,
                detail=f"Error from Vision API: {response.error.message}",
            )

        end_time = time.time()
        processing_time_ms = round((end_time - start_time) * 1000)

        if texts.text:
            clean_text = text_cleanup(texts.text)
            print(f"Extracted Text: {clean_text}")
            json_response = {
                "success": True,
                "text": clean_text,
                "confidence": score,
                "processing_time_ms": processing_time_ms,
                "metadata": image_metadata,
            }
        else:
            print("No text found in the image.")
            json_response = {
                "success": False,
                "text": "No text found in the image.",
                "confidence": 0.0,
                "processing_time_ms": processing_time_ms,
                "metadata": image_metadata,
            }
        
        # Cache the result
        cache_result(image_hash, json_response)
        print(f"Cached result for image: {filename}")
        
        return json_response

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occurred while processing the image: {str(e)}",
        )


@ocr_router.post(
    "/extract-text",
    summary="Extract Text from Image",
    description="Upload an image to extract text content using OCR.",
    response_model=OCRResponse,
)
@limiter.limit("5/minute")  # Allow 5 requests per minute per IP
async def extract_text_endpoint(request: Request, image: UploadFile = File(...)):
    """
    This endpoint accepts a JPG image file and returns the extracted text.
    Args:
        image (UploadFile): The image file uploaded by the user.
    Returns:
        JSONResponse: A JSON response containing the extracted text and confidence score.
    """
    result = await extract_text(image)
    return JSONResponse(content=result)


# batch extract endpoint
@ocr_router.post(
    "/batch-extract-text",
    summary="Batch Extract Text from Images",
    description="Upload multiple images to extract text content using OCR.",
    response_model=BatchOCRResponse,
)
@limiter.limit("5/minute")
async def batch_extract_text(request: Request, images: list[UploadFile] = File(...)):
    """
    This endpoint accepts multiple JPG image files and returns the extracted text for each.
    Args:
        images (list[UploadFile]): The list of image files uploaded by the user.
    Returns:
        JSONResponse: A JSON response containing the extracted text and confidence score for each image.
    """
    results = []
    for image in images:
        try:
            response = await extract_text(image)
            results.append(response)
        except HTTPException as http_exc:
            results.append(
                {
                    "success": False,
                    "text": f"Error processing image {image.filename}: {http_exc.detail}",
                    "confidence": 0.0,
                    "processing_time_ms": 0,
                    "metadata": {},
                }
            )
    return JSONResponse(content={"results": results})


@ocr_router.get(
    "/cache-stats",
    summary="Get Cache Statistics",
    description="Get cache statistics including size, hits, misses, and TTL information.",
)
async def get_cache_statistics():
    """
    Get cache statistics for monitoring cache performance.
    Returns:
        JSONResponse: Cache statistics including size, TTL, and performance metrics.
    """
    stats = get_cache_stats()
    return JSONResponse(content={
        "cache_statistics": stats,
        "message": "Cache statistics retrieved successfully"
    })
