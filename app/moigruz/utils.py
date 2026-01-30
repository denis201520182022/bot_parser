import re


def clean_phone(phone_text: str | None) -> str:
    """Очистка номера телефона от лишних символов."""
    if not phone_text:
        return ""

    # Убираем все нецифровые символы
    digits = re.sub(r"\D", "", phone_text)

    # Если номер начинается с 7 или 8 (российский)
    if digits.startswith(("7", "8")):
        if len(digits) > 11:
            digits = digits[:11]
    elif digits.startswith("9") and len(digits) == 10:
        digits = "7" + digits

    return digits


def uniq_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


