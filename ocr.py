import re
import logging
import aiohttp
from io import BytesIO
from config import OCR_API_KEY

OCR_URL = "https://api.ocr.space/parse/image"
SCORE_RE = re.compile(r"(\d{1,2})\s*[-:\u2013]\s*(\d{1,2})")


async def recognize_image(file_bytes: BytesIO) -> str:
    """Отправить картинку в OCR.space и вернуть распознанный текст."""
    try:
        form = aiohttp.FormData()
        form.add_field("apikey", OCR_API_KEY)
        form.add_field("language", "eng")
        form.add_field("scale", "true")
        form.add_field("OCREngine", "2")
        form.add_field("file", file_bytes.getvalue(), filename="s.jpg", content_type="image/jpeg")
        async with aiohttp.ClientSession() as session:
            async with session.post(OCR_URL, data=form, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                data = await resp.json()
        if data.get("IsErroredOnProcessing"):
            logging.warning(f"OCR error: {data.get('ErrorMessage')}")
            return ""
        results = data.get("ParsedResults") or []
        if not results:
            return ""
        return results[0].get("ParsedText", "") or ""
    except Exception as e:
        logging.warning(f"OCR exception: {e}")
        return ""


def parse_score(text: str):
    """Найти счёт X-Y в тексте. Возвращает (s1, s2) или None."""
    if not text:
        return None
    candidates = SCORE_RE.findall(text)
    for s1, s2 in candidates:
        a, b = int(s1), int(s2)
        if 0 <= a <= 30 and 0 <= b <= 30:
            return a, b
    return None
