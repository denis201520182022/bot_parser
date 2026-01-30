from bs4 import BeautifulSoup

from .http_client import get_text


def fetch_truck_ids(url: str) -> list[dict]:
    """
    Публичный парсер списка транспорта (без авторизации).
    Возвращает список объектов:
      {truck_id: str, post_time: str}
    """
    html = get_text(url, referer=url)
    soup = BeautifulSoup(html, "html.parser")

    rows = soup.find_all("tr", attrs={"data-id": True})
    out: list[dict] = []
    for row in rows:
        truck_id = row.get("data-id")
        if not truck_id:
            continue

        post_time = ""
        time_elem = row.find("td", class_="emptynop")
        if time_elem and "right" in (time_elem.get("class") or []):
            post_time = time_elem.get_text(strip=True)

        out.append({"truck_id": str(truck_id), "post_time": post_time})

    return out


