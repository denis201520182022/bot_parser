import os


URL_REF = "https://www.moigruz.ru/trucks/?from=&to=&rfrom=&rto=&date=&days=&body=3&cfrom=&cto=&vfrom=&vto=&load=&unload=&i=1"
URL_ISO = "https://www.moigruz.ru/trucks/?from=&to=&rfrom=&rto=&date=&days=&body=4&cfrom=&cto=&vfrom=&vto=&load=&unload="


DEFAULT_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/141.0.0.0 Safari/537.36"
)


def env(name: str, default: str | None = None) -> str | None:
    v = os.getenv(name)
    return v if v not in (None, "") else default


def env_required(name: str) -> str:
    v = env(name)
    if not v:
        raise RuntimeError(f"Missing required env var: {name}")
    return v


def get_poll_interval_sec() -> int:
    raw = env("POLL_INTERVAL_SEC", "10")
    try:
        return max(5, int(raw))  # защита от слишком частого поллинга
    except ValueError:
        return 60


def get_cookies_path() -> str:
    return env("MOIGRUZ_COOKIES_PATH", "state/cookies.pkl") or "state/cookies.pkl"


def get_state_dir() -> str:
    return env("STATE_DIR", "state") or "state"


def get_service_account_file() -> str:
    # gspread.service_account() ожидает json файла сервисного аккаунта
    return env_required("GOOGLE_SERVICE_ACCOUNT_FILE")


def get_ref_spreadsheet_id() -> str:
    return env_required("GSHEET_REF_SPREADSHEET_ID")


def get_iso_spreadsheet_id() -> str:
    return env_required("GSHEET_ISO_SPREADSHEET_ID")


def get_worksheet_name() -> str:
    return env("GSHEET_WORKSHEET_NAME", "Лист1") or "Лист1"


def get_moigruz_email() -> str:
    return env_required("MOIGRUZ_EMAIL")


def get_moigruz_password() -> str:
    return env_required("MOIGRUZ_PASSWORD")


def get_proxy_url() -> str | None:
    """
    Единая точка настройки прокси.
    Приоритет:
    1) MOIGRUZ_PROXY
    2) HTTPS_PROXY / HTTP_PROXY из окружения (если заданы).
    """
    proxy = env("MOIGRUZ_PROXY")
    if proxy:
        return proxy
    https = env("HTTPS_PROXY")
    if https:
        return https
    http = env("HTTP_PROXY")
    if http:
        return http
    return None


def get_proxies() -> dict[str, str] | None:
    proxy = get_proxy_url()
    if not proxy:
        return None
    return {"http": proxy, "https": proxy}


