import os
import pickle

from curl_cffi import requests
from bs4 import BeautifulSoup

from . import config
from .config import DEFAULT_UA


def _save_cookies(session: requests.Session, cookies_path: str) -> None:
    """
    Сохраняем только простые данные о куках, без lock-объектов,
    чтобы избежать ошибки `cannot pickle '_thread.RLock' object`.
    В curl_cffi `session.cookies` итерируется по именам куки (str),
    поэтому берём реальный CookieJar из атрибута `.jar`.
    """
    os.makedirs(os.path.dirname(cookies_path) or ".", exist_ok=True)
    simple_cookies: list[dict] = []

    jar = getattr(session.cookies, "jar", session.cookies)
    for c in jar:
        # ожидаем объекты Cookie
        name = getattr(c, "name", None)
        value = getattr(c, "value", None)
        if not name:
            continue
        simple_cookies.append(
            {
                "name": name,
                "value": value,
                "domain": getattr(c, "domain", None),
                "path": getattr(c, "path", None),
            }
        )
    with open(cookies_path, "wb") as f:
        pickle.dump(simple_cookies, f)


def _load_cookies(session: requests.Session, cookies_path: str) -> bool:
    if not os.path.exists(cookies_path):
        return False
    try:
        with open(cookies_path, "rb") as f:
            simple_cookies = pickle.load(f)
        for c in simple_cookies:
            session.cookies.set(
                c.get("name"),
                c.get("value"),
                domain=c.get("domain"),
                path=c.get("path"),
            )
        return True
    except Exception:
        return False


def _is_logged_in(html: str) -> bool:
    # Грубая эвристика: в залогиненном состоянии обычно доступен выход
    soup = BeautifulSoup(html, "html.parser")
    return bool(soup.find("a", href=lambda x: x and "/auth/exit" in x))


def ensure_auth_session(*, cookies_path: str, email: str, password: str) -> requests.Session:
    """
    Возвращает сессию с куками.
    - Публичный мониторинг делаем без неё.
    - Эту сессию используем только когда появились новые truck_id (для контактов).
    """
    s = requests.Session()
    proxies = config.get_proxies()
    if proxies:
        s.proxies.update(proxies)
    _load_cookies(s, cookies_path)

    # Пробуем понять, живые ли куки
    try:
        r = s.get(
            "https://www.moigruz.ru/trucks/",
            headers={"User-Agent": DEFAULT_UA},
            impersonate="chrome110",
        )
        if r.ok and _is_logged_in(r.text):
            return s
    except Exception:
        pass

    # Инициализация куки
    s.get(
        "https://www.moigruz.ru/trucks/",
        headers={"User-Agent": DEFAULT_UA},
        impersonate="chrome110",
    )

    auth_data = {
        "r": "/trucks/",
        "ac_email": email,
        "ac_password": password,
        "ac_code": "",
        "ac_remember": "on",
        "REQUEST_URI": "/trucks/",
    }

    resp = s.post(
        "https://www.moigruz.ru/auth/enter/",
        data=auth_data,
        headers={
            "Accept": "*/*",
            "Accept-Language": "ru",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://www.moigruz.ru",
            "Pragma": "no-cache",
            "Referer": "https://www.moigruz.ru/trucks/",
            "User-Agent": DEFAULT_UA,
        },
        impersonate="chrome110",
    )
    resp.raise_for_status()

    # Сохраняем куки сразу после логина
    _save_cookies(s, cookies_path)
    return s


