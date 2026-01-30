from __future__ import annotations

from typing import Iterable

import gspread


def make_gspread_client(service_account_file: str) -> gspread.Client:
    return gspread.service_account(filename=service_account_file)


def get_worksheet(
    *,
    client: gspread.Client,
    spreadsheet_id: str,
    worksheet_name: str,
) -> gspread.Worksheet:
    sh = client.open_by_key(spreadsheet_id)
    return sh.worksheet(worksheet_name)


def read_existing_ids(ws: gspread.Worksheet, *, id_col: int = 1) -> set[str]:
    """
    Читаем колонку с truck_id (обычно A).
    Возвращает set строковых id, без заголовка.
    """
    values = ws.col_values(id_col)
    out: set[str] = set()
    for v in values[1:]:  # пропускаем заголовок
        v = (v or "").strip()
        if v:
            out.add(v)
    return out


def ensure_header(ws: gspread.Worksheet, header: list[str]) -> None:
    # Если таблица пустая — пишем заголовок в первую строку
    if ws.row_count == 0:
        ws.append_row(header, value_input_option="RAW")
        return

    first_row = ws.row_values(1)
    if not first_row:
        ws.append_row(header, value_input_option="RAW")
        return

    # Если заголовок отличается — не ломаем существующую таблицу, просто оставляем как есть


def append_rows(ws: gspread.Worksheet, rows: Iterable[list[str]]) -> None:
    batch = list(rows)
    if not batch:
        return
    ws.append_rows(batch, value_input_option="RAW")


