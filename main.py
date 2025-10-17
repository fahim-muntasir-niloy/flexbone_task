from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from apis.ocr import ocr_router

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="OCR Text Extraction API",
    description="API for extracting text from images using OCR.",
    version="1.0.0",
    contact={
        "name": "Muntasir Fahim", 
        "email": "muntasirfahim.niloy@gmail.com"
    },
)

# Add rate limiter to the app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(ocr_router, tags=["OCR"])


@app.get("/", summary="Health Check")
@limiter.limit("10/minute")
async def health_check(request: Request):
    return {"status": "ok", "message": "Service is up and running."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=6969)
