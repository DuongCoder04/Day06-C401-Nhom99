import re
import unicodedata


def normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text.lower())
    normalized = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    return normalized.replace("đ", "d")


def extract_budget(text: str) -> int | None:
    value = normalize(text)
    match = re.search(r"(?:duoi|toi da|khong qua|ngan sach)?\s*(\d{2,3})(?:\s?k|\.000|000)", value)
    if not match:
        return None
    amount = int(match.group(1))
    return amount * 1000 if amount < 1000 else amount


def extract_group_size(text: str) -> int | None:
    value = normalize(text)
    match = re.search(r"(?:cho\s*nhom|cho|dat cho|nhom|an cung|cho\s*may|may)\s*(\d+)", value)
    if not match:
        return None
    return int(match.group(1))
