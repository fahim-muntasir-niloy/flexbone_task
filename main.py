import time
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from google.cloud import vision
from utils import get_confidence_score
import logging
from rich import print

# Initialize FastAPI app
app = FastAPI(
    title="OCR Image Text Extraction API",
    description="An API to extract text from images using Google Cloud Vision.",
    version="1.0.0",
    author="Fahim Muntasir",
)

# Initialize Google Cloud Vision client
# This will use the application's default credentials.
# On Cloud Run, this is the attached service account.
# Locally, this is your gcloud auth application-default login.
try:
    vision_client = vision.ImageAnnotatorClient()
    logging.info("Successfully initialized Google Cloud Vision client.")
except Exception as e:
    logging.error(f"Failed to initialize Google Cloud Vision client: {e}")
    # If the client fails to initialize, the app can't function.
    # In a real-world scenario, you might have a fallback or more robust error handling.
    vision_client = None

    # will set up gemini here later

# Define constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
SUPPORTED_CONTENT_TYPES = ["image/jpeg", "image/jpg", "image/png"]


@app.get(
    "/",
    summary="Health Check",
)
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "ok", "message": "Service is up and running."}


@app.post(
    "/extract-text",
    summary="Extract Text from Image",
    description="Upload an image to extract text content using OCR.",
)
async def extract_text(image: UploadFile = File(...)):
    """
    This endpoint accepts a JPG image file and returns the extracted text.

    - **Input**: JPG image file (multipart/form-data).
    - **Output**: JSON response with extracted text, confidence, and processing time.
    """
    start_time = time.time()

    # Validate file type
    if image.content_type not in SUPPORTED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,  # Unsupported Media Type
            detail=f"Unsupported file format. Please upload a JPG/JPEG image. Found: {image.content_type}",
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
            status_code=503,  # Service Unavailable
            detail="Vision API client is not available. The service cannot process images.",
        )

    try:
        vision_image = vision.Image(content=contents)

        # text detection
        # response = vision_client.text_detection(image=vision_image)
        response = vision_client.document_text_detection(image=vision_image)
        # texts = response.text_annotations

        texts = response.full_text_annotation

        score = get_confidence_score(texts)

        # Check for errors from the Vision API response
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
                "text": "",
                "confidence": 0.0,
                "processing_time_ms": processing_time_ms,
                "message": "No text found in the image.",
            }
            return JSONResponse(content=json_response)

    except Exception as e:
        # Catch any other unexpected errors during processing
        logging.error(f"An unexpected error occurred: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occurred while processing the image: {str(e)}",
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=6969, log_level="info", reload=True)
