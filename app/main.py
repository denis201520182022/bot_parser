import os
import time
from typing import Dict, List

from moigruz import config
from moigruz import auth
from moigruz import scrape_public
from moigruz import scrape_private
from moigruz import state
from moigruz import sheets


COLUMNS: List[str] = [
    "truck_id",
    "company_name",
    "contact_name",
    "phone",
    "skype",
    "has_viber",
    "has_whatsapp",
    "has_telegram",
    "rating",
    "pro_status",
    "post_time",
]


def build_row(record: Dict[str, str]) -> List[str]:
    return [str(record.get(col, "") or "") for col in COLUMNS]


def process_source(
    *,
    name: str,
    url: str,
    worksheet,
    state_file: str,
    seen_ids: set[str],
    auth_session,
) -> set[str]:
    print(f"\n=== Источник {name}: проверка новых заявок ===")
    public_items = scrape_public.fetch_truck_ids(url)
    if not public_items:
        print("  Нет заявок на странице")
        return seen_ids

    # карта id -> публичная инфа (время публикации)
    by_id: Dict[str, Dict[str, str]] = {str(i["truck_id"]): i for i in public_items if i.get("truck_id")}

    new_ids = [tid for tid in by_id.keys() if tid not in seen_ids]
    if not new_ids:
        print("  Новых заявок нет")
        return seen_ids

    print(f"  Найдено новых заявок: {len(new_ids)}")

    if auth_session is None:
        auth_session = auth.ensure_auth_session(
            cookies_path=config.get_cookies_path(),
            email=config.get_moigruz_email(),
            password=config.get_moigruz_password(),
        )

    rows_to_append: List[List[str]] = []
    try:
        contacts_by_id = scrape_private.fetch_contacts_for_ids(auth_session, url, new_ids)
    except Exception as e:
        print(f"  Ошибка при загрузке контактов: {e}")
        contacts_by_id = {}

    for tid in new_ids:
        contact_info = contacts_by_id.get(tid, {"truck_id": tid})
        record: Dict[str, str] = {}
        record.update(contact_info)
        record["post_time"] = by_id[tid].get("post_time", "")
        rows_to_append.append(build_row(record))
        seen_ids.add(tid)

    if rows_to_append:
        sheets.append_rows(worksheet, rows_to_append)
        state.save_seen_ids(state_file, seen_ids)
        print(f"  В Google Sheet добавлено строк: {len(rows_to_append)}")

    return seen_ids


def main() -> None:
    poll_interval = config.get_poll_interval_sec()
    cookies_path = config.get_cookies_path()
    state_dir = config.get_state_dir()
    os.makedirs(state_dir, exist_ok=True)

    ref_state_file = os.path.join(state_dir, "ref.json")
    iso_state_file = os.path.join(state_dir, "iso.json")

    client = sheets.make_gspread_client(config.get_service_account_file())
    ws_ref = sheets.get_worksheet(
        client=client,
        spreadsheet_id=config.get_ref_spreadsheet_id(),
        worksheet_name=config.get_worksheet_name(),
    )
    ws_iso = sheets.get_worksheet(
        client=client,
        spreadsheet_id=config.get_iso_spreadsheet_id(),
        worksheet_name=config.get_worksheet_name(),
    )

    sheets.ensure_header(ws_ref, COLUMNS)
    sheets.ensure_header(ws_iso, COLUMNS)

    seen_ref = state.load_seen_ids(ref_state_file)
    seen_iso = state.load_seen_ids(iso_state_file)

    # подхватываем уже существующие id из таблиц, чтобы не было дублей при рестарте
    try:
        seen_ref |= sheets.read_existing_ids(ws_ref)
    except Exception:
        pass
    try:
        seen_iso |= sheets.read_existing_ids(ws_iso)
    except Exception:
        pass

    print("Мониторинг запущен.")
    print(f"Интервал опроса: {poll_interval} сек.")
    print(f"Файл куки: {cookies_path}")

    auth_session = None

    while True:
        try:
            seen_ref = process_source(
                name="Рефрижератор",
                url=config.URL_REF,
                worksheet=ws_ref,
                state_file=ref_state_file,
                seen_ids=seen_ref,
                auth_session=auth_session,
            )

            seen_iso = process_source(
                name="Изотермический",
                url=config.URL_ISO,
                worksheet=ws_iso,
                state_file=iso_state_file,
                seen_ids=seen_iso,
                auth_session=auth_session,
            )
        except KeyboardInterrupt:
            print("\nОстановка по Ctrl+C")
            break
        except Exception as e:
            print(f"Глобальная ошибка цикла: {e}")

        time.sleep(poll_interval)


if __name__ == "__main__":
    main()
