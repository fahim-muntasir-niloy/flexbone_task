import re
import io
from PIL import Image, ExifTags


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
