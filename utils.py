import re


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
