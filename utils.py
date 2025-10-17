import re
import io
import hashlib
from typing import Dict, Optional, Any
from PIL import Image, ExifTags
from cachetools import TTLCache
from datetime import datetime


def text_cleanup(text: str) -> str:
    """
    Clean up the extracted text by removing unwanted characters and extra spaces.

    Args:
        text (str): The raw extracted text.
    Returns:
        str: The cleaned-up text.
    """
    # Remove non-printable characters
    cleaned_text = re.sub(r"[^\x20-\x7E]", " ", text)

    # Replace multiple spaces/newlines with a single space
    cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()

    return cleaned_text


def get_confidence_score(document) -> float:
    """
    Calculate a confidence score based on the length of extracted text.

    Args:
        documents: List of text annotations from OCR.

    Returns:
        float: A confidence score between 0 and 1.
    """
    extracted_text = document.text.strip() if document.text else ""
    word_confidences = [
        word.confidence
        for page in document.pages
        for block in page.blocks
        for paragraph in block.paragraphs
        for word in paragraph.words
        if word.confidence
    ]

    if word_confidences:
        confidence = sum(word_confidences) / len(word_confidences)
    else:
        confidence = 0.0

    # optional heuristic adjustment
    if len(extracted_text) < 10:
        confidence *= 0.5
    non_alpha_ratio = len(re.findall(r"[^a-zA-Z0-9\s.,!?-]", extracted_text)) / max(
        1, len(extracted_text)
    )
    confidence *= 1 - non_alpha_ratio
    confidence = round(max(0.0, min(1.0, confidence)), 5)

    return confidence


def get_image_metadata(filename: str, content_type: str, contents: str) -> dict:
    """
    Extract metadata from the image file path.

    Args:
        image_path (str): The path to the image file.
    Returns:
        dict: A dictionary containing metadata such as filename and extension.
    """

    file_size = len(contents)
    basic_metadata = {
        "filename": filename,
        "content_type": content_type,
        "size_bytes": file_size,
    }

    try:
        pil_image = Image.open(io.BytesIO(contents))
        image_metadata = {
            "format": pil_image.format,
            "width": pil_image.width,
            "height": pil_image.height,
            "mode": pil_image.mode,
        }

        # EXIF Data (if it exists)
        exif_data_raw = pil_image._getexif()
        exif_data_readable = {}

        if exif_data_raw:
            for tag_id, value in exif_data_raw.items():
                # Get the human-readable tag name
                tag_name = ExifTags.TAGS.get(tag_id, tag_id)

                # Some EXIF values are bytes and need decoding
                if isinstance(value, bytes):
                    try:
                        value = value.decode("utf-8", errors="ignore")
                    except:
                        value = repr(value)  # Represent as string if decoding fails

                exif_data_readable[tag_name] = value

    except Exception as e:
        return f"Invalid image file. Could not process with Pillow. Error: {e}"

    return {
        "file_info": {**basic_metadata, "size_bytes": file_size},
        "image_info": image_metadata,
        "exif_info": exif_data_readable or "No EXIF data found",
    }


# Global cache for OCR results - TTL cache with 1 hour expiration
ocr_cache: TTLCache = TTLCache(maxsize=1000, ttl=3600)  # 1000 items, 1 hour TTL


def generate_image_hash(image_content: bytes) -> str:
    """
    Generate a SHA-256 hash of the image content for caching purposes.
    
    Args:
        image_content (bytes): The binary content of the image.
    
    Returns:
        str: SHA-256 hash of the image content.
    """
    return hashlib.sha256(image_content).hexdigest()


def get_cached_result(image_hash: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve cached OCR result for a given image hash.
    
    Args:
        image_hash (str): SHA-256 hash of the image content.
    
    Returns:
        Optional[Dict[str, Any]]: Cached result if exists, None otherwise.
    """
    return ocr_cache.get(image_hash)


def cache_result(image_hash: str, result: Dict[str, Any]) -> None:
    """
    Cache OCR result for a given image hash.
    
    Args:
        image_hash (str): SHA-256 hash of the image content.
        result (Dict[str, Any]): OCR result to cache.
    """
    # Add timestamp to the cached result
    cached_data = {
        **result,
        "cached_at": datetime.now().isoformat(),
        "cache_hit": True
    }
    ocr_cache[image_hash] = cached_data


def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics for monitoring purposes.
    
    Returns:
        Dict[str, Any]: Cache statistics including size, hits, misses, etc.
    """
    return {
        "cache_size": len(ocr_cache),
        "max_size": ocr_cache.maxsize,
        "ttl_seconds": ocr_cache.ttl,
        "cache_info": ocr_cache.currsize if hasattr(ocr_cache, 'currsize') else len(ocr_cache)
    }
