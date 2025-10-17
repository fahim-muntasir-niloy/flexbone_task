# OCR Text Extraction API

A FastAPI-based OCR service that extracts text from images using `Google Cloud Vision API`. Features include rate limiting, image caching, and batch processing capabilities. The application is hosted on `Google Cloud Run`.

[ Live Swagger UI ](https://flexbone-task-961844822308.asia-south2.run.app/docs)


## 🚀 Features

- **Text Extraction**: Extract text from images
- **Multiple Formats**: Supports JPG, JPEG, PNG and GIFs
- **Confidence Score**: Average confidence score of the extraction is given.
- **Formatted Output**: Extracted texts are formatted and cleaned using regex.
- **Batch Processing**: Process multiple images in a single request
- **Rate Limiting**: Built-in rate limiting to prevent API abuse
- **Image Caching**: Automatic caching of identical images for improved performance
- **Health Monitoring**: Health check endpoint and cache statistics
- **Error Handling**: Comprehensive error handling with detailed responses
- **Metadata Extraction**: Detailed metadata and exif are extracted and sent with output


## 📁 Project Structure

```
flexbone_task/
├── apis/
│   ├── __init__.py
│   └── ocr.py                 # OCR endpoints and business logic
├── models/
│   ├── __init__.py
│   └── ocr_models.py          # Pydantic models for request/response
├── images/                    # Test images directory
│   ├── Google.png
│   ├── meme.jpeg
│   ├── programming-meme-29.jpg
│   └── programming-or-googling.jpg
├── flex/                      # Python virtual environment
├── main.py                    # FastAPI application entry point
├── utils.py                   # Utility functions (text cleanup, caching, etc.)
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker configuration
├── test.py                   # Basic API tests
└── README.md                 
```


## ⚡️ API Endpoints
[<- Deployed Swagger UI ->](https://flexbone-task-961844822308.asia-south2.run.app/docs)

#### 1. Health Check
```bash
GET /

# curl
curl -X GET "https://flexbone-task-961844822308.asia-south2.run.app"  
```
Returns server status and health information.

#### 2. Extract Text from Single Image
```bash
POST /extract-text
Content-Type: multipart/form-data

# curl
curl -X POST "https://flexbone-task-961844822308.asia-south2.run.app/extract-text" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "image=@path/to/your/image.jpg"
```

#### 3. Batch Text Extraction
```bash
POST /batch-extract-text
Content-Type: multipart/form-data

# curl
curl -X POST "https://flexbone-task-961844822308.asia-south2.run.app/batch-extract-text" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "images=@image1.jpg" \
     -F "images=@image2.jpg"
```

#### 4. Cache Statistics
```bash
GET /cache-stats

# curl
curl -X GET "https://flexbone-task-961844822308.asia-south2.run.app/cache-stats"  
```
Returns cache performance statistics.

## 📊 Rate Limits

- **Health Check**: 10 requests/minute per IP
- **Single OCR**: 5 requests/minute per IP
- **Batch OCR**: 5 requests/minute per IP

## 🎯 Response Format

### Successful OCR Response
```json
{
  "success": true,
  "text": "Extracted text content",
  "confidence": 0.95471,
  "processing_time_ms": 1250,
  "metadata": {
    "file_info": {
      "filename": "image.jpg",
      "content_type": "image/jpeg",
      "size_bytes": 245760
    },
    "image_info": {
      "format": "JPEG",
      "width": 1920,
      "height": 1080,
      "mode": "RGB"
    }
  }
}
```

### Cache Statistics Response
```json
{
  "cache_statistics": {
    "cache_size": 5,
    "max_size": 1000,
    "ttl_seconds": 3600
  },
  "message": "Cache statistics retrieved successfully"
}
```

## 🔧 Configuration


### Cache Settings
- **Cache Size**: 1000 items maximum
- **TTL**: 1 hour expiration
- **Cache Key**: SHA-256 hash of image content


## 🐳 Docker Deployment

Build and run with Docker:
```bash
docker build -t ocr-api .
docker run -p 6969:6969 ocr-api
```

## 📈 Performance Features

- **Image Caching**: Identical images are cached for 1 hour
- **Rate Limiting**: Prevents API abuse and ensures fair usage
- **Batch Processing**: Efficient processing of multiple images
- **Error Handling**: Graceful error handling with detailed messages

## 🔒 Security

- Rate limiting per IP address
- File type validation (JPG, PNG, GIF only)
- File size limits (10MB maximum)
- Input validation and sanitization

## 📞 Contact

- **Developer**: Fahim Muntasir
- **Email**: muntasirfahim.niloy@gmail.com

