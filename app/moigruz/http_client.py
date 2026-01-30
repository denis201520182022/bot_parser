from curl_cffi import requests

from . import config
from .config import DEFAULT_UA


def make_public_session() -> requests.Session:
    s = requests.Session()
    proxies = config.get_proxies()
    if proxies:
        s.proxies.update(proxies)
    return s


def default_headers(referer: str | None = None) -> dict[str, str]:
    h = {"User-Agent": DEFAULT_UA}
    if referer:
        h["Referer"] = referer
    return h


def get_text(url: str, *, session: requests.Session | None = None, referer: str | None = None) -> str:
    s = session or make_public_session()
    r = s.get(url, headers=default_headers(referer), impersonate="chrome110")
    r.raise_for_status()
    return r.text


