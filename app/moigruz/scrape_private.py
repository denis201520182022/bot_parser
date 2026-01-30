from curl_cffi import requests
from bs4 import BeautifulSoup

from .config import DEFAULT_UA
from .utils import clean_phone, uniq_preserve_order


def _parse_contacts_from_row(row, next_row) -> dict:
    info: dict[str, str] = {}

    rarely_div = next_row.find("div", class_="rarely") if next_row else None
    if not rarely_div:
        return info

    company_link = rarely_div.find("a", href=lambda x: x and "/company-info/" in x)
    if company_link:
        info["company_name"] = company_link.get_text(strip=True)

    contact_link = rarely_div.find("a", href=lambda x: x and "/account/" in x)
    if contact_link:
        info["contact_name"] = contact_link.get_text(strip=True)

    phones: list[str] = []
    for a in rarely_div.find_all("a", href=lambda x: x and "tel:" in x):
        txt = a.get_text(strip=True)
        if not txt:
            continue
        p = clean_phone(txt)
        if p:
            phones.append(p)
    phones = uniq_preserve_order(phones)
    info["phone"] = ", ".join(phones) if phones else ""

    skype_link = rarely_div.find("a", href=lambda x: x and "skype:" in x)
    info["skype"] = skype_link.get_text(strip=True) if skype_link else ""

    info["has_viber"] = "Да" if rarely_div.find("a", class_="wicon_viber") else "Нет"
    info["has_whatsapp"] = "Да" if rarely_div.find("a", class_="wicon_whatsapp") else "Нет"
    info["has_telegram"] = "Да" if rarely_div.find("span", class_="wicon_telegram") else "Нет"

    rating_span = rarely_div.find("span", class_="rating")
    if rating_span:
        info["rating"] = rating_span.get_text(strip=True)
    else:
        info["rating"] = ""

    info["pro_status"] = "Да" if rarely_div.find("span", class_="pro") else "Нет"

    return info


def fetch_contacts_for_ids(session: requests.Session, url: str, truck_ids: list[str]) -> dict[str, dict]:
    """
    Приватный парсер той же страницы списка /trucks/ под авторизованной сессией.
    Находим строки с нужными truck_id и достаем контакты.
    """
    wanted = {str(tid) for tid in truck_ids}
    if not wanted:
        return {}

    r = session.get(
        url,
        headers={"User-Agent": DEFAULT_UA, "Referer": url},
        impersonate="chrome110",
    )
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    rows = soup.find_all("tr", attrs={"data-id": True})

    result: dict[str, dict] = {}
    for row in rows:
        tid = str(row.get("data-id"))
        if tid not in wanted:
            continue
        next_row = row.find_next_sibling("tr")
        data = _parse_contacts_from_row(row, next_row)
        data["truck_id"] = tid
        result[tid] = data

    return result


