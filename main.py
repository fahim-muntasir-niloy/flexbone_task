from fastapi import FastAPI
from apis.ocr import ocr_router

app = FastAPI(
    title="OCR Text Extraction API",
    description="API for extracting text from images using OCR.",
    version="1.0.0",
    author="Muntasir Fahim",
)

# Include routes
app.include_router(ocr_router, tags=["OCR"])


@app.get("/", summary="Health Check")
async def health_check():
    return {"status": "ok", "message": "Service is up and running."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=6969)
