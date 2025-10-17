import os
import time
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from google.cloud import vision
from models.ocr_models import OCRRequest, OCRResponse
from utils import get_confidence_score
import logging
from rich import print


ocr_router = APIRouter()

# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "cloud_vision_credentials.json" -> as it's handled automatically in cloud run

try:
    vision_client = vision.ImageAnnotatorClient()
    logging.info("Successfully initialized Google Cloud Vision client.")
except Exception as e:
    vision_client = None
    logging.error(f"Failed to initialize Google Cloud Vision client: {e}")


MAX_FILE_SIZE = 10 * 1024 * 1024
SUPPORTED_CONTENT_TYPES = ["image/jpeg", "image/jpg", "image/png"]


@ocr_router.post(
    "/extract-text",
    summary="Extract Text from Image",
    description="Upload an image to extract text content using OCR.",
    response_model=OCRResponse,
)
async def extract_text(image: UploadFile = File(...)):
    """
    This endpoint accepts a JPG image file and returns the extracted text.
    Args:
        image (UploadFile): The image file uploaded by the user.
    Returns:
        JSONResponse: A JSON response containing the extracted text and confidence score.
    """

    start_time = time.time()

    # Validate file type
    if image.content_type not in SUPPORTED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,  # Unsupported Media Type
            detail=f"Unsupported file format. Please upload a JPG/JPEG/PNG image. Found: {image.content_type}",
        )

    contents = await image.read()

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
            print(f"Extracted Text: {texts.text}")
            json_response = {
                "success": True,
                "text": texts.text,
                "confidence": score,
                "processing_time_ms": processing_time_ms,
            }
            return JSONResponse(content=json_response)
        else:
            print("No text found in the image.")
            json_response = {
                "success": False,
                "text": "No text found in the image.",
                "confidence": 0.0,
                "processing_time_ms": processing_time_ms,
            }
            return JSONResponse(content=json_response)

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occurred while processing the image: {str(e)}",
        )
