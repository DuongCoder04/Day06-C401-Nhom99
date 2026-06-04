import re
import unicodedata


def normalize(text: str) -> str:
    """Lowercase + strip Vietnamese diacritics + replace 'đ' → 'd'."""
    normalized = unicodedata.normalize("NFD", text.lower())
    normalized = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    return normalized.replace("đ", "d")


def extract_budget(text: str) -> int | None:
    """
    Extract a budget amount (VND) from natural-language Vietnamese text.

    Supported formats:
    - "80k", "80 k", "80K"
    - "80.000", "80000", "80,000"
    - "80 nghìn", "80 nghin", "80 ngàn"
    - "1 triệu", "1tr", "1 trieu"
    - Optional leading keyword: "dưới / tối đa / không quá / ngân sách / khoảng / tầm"
    """
    value = normalize(text)

    # Millions: "1 trieu", "1tr", "2.5tr"
    m = re.search(
        r"(?:duoi|toi da|khong qua|ngan sach|khoang|tam)?\s*"
        r"(\d+(?:[.,]\d+)?)\s*(?:tr(?:ieu)?|trieu)",
        value,
    )
    if m:
        amount_str = m.group(1).replace(",", ".")
        try:
            return int(float(amount_str) * 1_000_000)
        except ValueError:
            pass

    # Thousands with explicit unit: "80k", "80 k", "80 nghìn", "80 ngàn"
    m = re.search(
        r"(?:duoi|toi da|khong qua|ngan sach|khoang|tam)?\s*"
        r"(\d{2,3})\s*(?:k|\.000|,000|nghìn|nghin|ngan)",
        value,
    )
    if m:
        return int(m.group(1)) * 1_000

    # Plain thousands without unit: "80000", "80.000", "80,000"
    m = re.search(
        r"(?:duoi|toi da|khong qua|ngan sach|khoang|tam)\s*"
        r"(\d{2,3})\.?(\d{3})\b",
        value,
    )
    if m:
        return int(m.group(1)) * 1_000 + int(m.group(2))

    return None


def extract_group_size(text: str) -> int | None:
    """Extract number of people from text like 'đặt cho 4 người', 'nhóm 3 người'."""
    value = normalize(text)
    m = re.search(
        r"(?:cho\s*nhom|cho|dat\s*cho|nhom|an\s*cung|cho\s*may|may)\s*(\d+)",
        value,
    )
    if not m:
        return None
    n = int(m.group(1))
    # Sanity check: ignore implausibly large numbers
    return n if 2 <= n <= 100 else None
