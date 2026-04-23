import re
import logging
import aiohttp
from io import BytesIO
from difflib import SequenceMatcher
from config import OCR_API_KEY

OCR_URL = "https://api.ocr.space/parse/image"
SCORE_RE = re.compile(r"(\d{1,2})\s*[-:\u2013]\s*(\d{1,2})")
MATCH_THRESHOLD = 0.6  # минимальная схожесть для fuzzy match


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


def _normalize(s: str) -> str:
    """Нижний регистр, убираем не-буквенные символы для сравнения."""
    return re.sub(r"[^a-zа-я0-9]", "", (s or "").lower())


def _similarity(a: str, b: str) -> float:
    a2, b2 = _normalize(a), _normalize(b)
    if not a2 or not b2:
        return 0.0
    return SequenceMatcher(None, a2, b2).ratio()


def find_participants(text: str, participants):
    """
    Ищет двух участников из списка в OCR тексте.
    participants: список объектов с атрибутом .game_nickname и .id
    Возвращает: (p1, p2, score_tuple) — порядок (p1,p2) слева-направо, как на скрине.
    Если не смог уверенно определить — возвращает (None, None, None).
    """
    if not text:
        return None, None, None
    # собираем все "кандидаты" в тексте — строки и отдельные слова
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    tokens = []
    for ln in lines:
        tokens.append(ln)
        # плюс отдельные "слова" из строки (на случай, когда в строке имя+цифры)
        for w in re.split(r"[\s,:\-|()]+", ln):
            if len(w) >= 3:
                tokens.append(w)
    if not tokens:
        return None, None, None
    # для каждого участника ищем лучший токен
    best = {}  # participant_id -> (score, token_index_in_text)
    for p in participants:
        nick = p.game_nickname
        best_score, best_pos = 0.0, -1
        for i, tok in enumerate(tokens):
            s = _similarity(nick, tok)
            if s > best_score:
                best_score, best_pos = s, i
        if best_score >= MATCH_THRESHOLD:
            best[p.id] = (best_score, best_pos, p)
    if len(best) < 2:
        return None, None, None
    # берём двух с наибольшей уверенностью
    top = sorted(best.values(), key=lambda x: -x[0])[:2]
    # сортируем по позиции в тексте — это "лево-право"
    top_sorted = sorted(top, key=lambda x: x[1])
    p1 = top_sorted[0][2]
    p2 = top_sorted[1][2]
    # ищем счёт
    score = parse_score(text)
    return p1, p2, score
