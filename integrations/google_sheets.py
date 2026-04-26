from pathlib import Path

import gspread


DEFAULT_CREDENTIALS_PATH = Path(__file__).resolve().parent.parent / "credentials" / "google_service_account.json"
INPUT_COLUMNS = (
    "name",
    "email",
    "company",
    "property_address",
    "city",
    "state",
    "country",
)
OUTPUT_COLUMNS = (
    "status",
    "score",
    "priority",
    "top_insight",
    "draft_email",
    "processed_at",
    "error_message",
)


def _normalize_header(value: object) -> str:
    return "" if value is None else str(value).strip().lower()


def _pad_row(row: list[str], width: int) -> list[str]:
    return row + [""] * max(0, width - len(row))


def _update_full_row(worksheet, row_number: int, row_values: list[str]) -> None:
    end_cell = gspread.utils.rowcol_to_a1(row_number, len(row_values))
    worksheet.update(range_name=f"A{row_number}:{end_cell}", values=[row_values])


def _get_header_map(worksheet) -> tuple[list[str], dict[str, int]]:
    values = worksheet.get_all_values()
    if not values:
        raise ValueError("Worksheet is empty. Add a header row before processing leads.")

    headers = [_normalize_header(value) for value in values[0]]
    header_map = {
        header: index for index, header in enumerate(headers) if header
    }
    return headers, header_map


def ensure_sheet_columns(worksheet) -> tuple[list[str], dict[str, int]]:
    headers, header_map = _get_header_map(worksheet)
    expected_input_headers = list(INPUT_COLUMNS)
    actual_input_headers = headers[:len(INPUT_COLUMNS)]

    if actual_input_headers != expected_input_headers:
        expected_headers = ", ".join(INPUT_COLUMNS)
        raise ValueError(
            "Worksheet header row is not set up for lead automation. "
            f"The first columns should be: {expected_headers}."
        )

    missing_columns = [
        column for column in OUTPUT_COLUMNS
        if column not in header_map
    ]

    if missing_columns:
        updated_headers = headers + missing_columns
        worksheet.update(range_name="1:1", values=[updated_headers])
        headers = updated_headers
        header_map = {
            header: index for index, header in enumerate(headers) if header
        }

    return headers, header_map


def get_gspread_client(credentials_path: str | None = None) -> gspread.Client:
    credential_file = credentials_path or str(DEFAULT_CREDENTIALS_PATH)
    return gspread.service_account(filename=credential_file)


def open_sheet(sheet_name: str, credentials_path: str | None = None) -> gspread.Spreadsheet:
    client = get_gspread_client(credentials_path)
    return client.open(sheet_name)


def get_worksheet(sheet_name: str, worksheet_name: str | None = None, credentials_path: str | None = None):
    spreadsheet = open_sheet(sheet_name, credentials_path)

    if worksheet_name:
        return spreadsheet.worksheet(worksheet_name)

    return spreadsheet.sheet1


def read_sheet_records(sheet_name: str, worksheet_name: str | None = None, credentials_path: str | None = None) -> list[dict]:
    worksheet = get_worksheet(sheet_name, worksheet_name, credentials_path)
    return worksheet.get_all_records()


def read_sheet_values(sheet_name: str, worksheet_name: str | None = None, credentials_path: str | None = None) -> list[list[str]]:
    worksheet = get_worksheet(sheet_name, worksheet_name, credentials_path)
    return worksheet.get_all_values()


def read_lead_rows(sheet_name: str, worksheet_name: str | None = None, credentials_path: str | None = None, status_filter: str | None = "new") -> list[dict]:
    worksheet = get_worksheet(sheet_name, worksheet_name, credentials_path)
    headers, header_map = ensure_sheet_columns(worksheet)
    values = worksheet.get_all_values()

    rows = []
    status_filter_normalized = _normalize_header(status_filter)

    for row_number, raw_row in enumerate(values[1:], start=2):
        padded_row = _pad_row(raw_row, len(headers))
        row_data = {
            header: padded_row[index]
            for header, index in header_map.items()
        }

        if not any(row_data.get(column, "").strip() for column in INPUT_COLUMNS):
            continue

        row_status = _normalize_header(row_data.get("status", ""))
        if status_filter_normalized == "new":
            if row_status not in {"", "new"}:
                continue
        elif status_filter_normalized and row_status != status_filter_normalized:
            continue

        lead_input = {
            column: row_data.get(column, "")
            for column in INPUT_COLUMNS
        }

        rows.append(
            {
                "row_number": row_number,
                "sheet_row": row_data,
                "lead_input": lead_input,
            }
        )

    return rows


def update_row_status(worksheet, row_number: int, status: str, error_message: str = "") -> None:
    headers, header_map = ensure_sheet_columns(worksheet)
    row_values = _pad_row(worksheet.row_values(row_number), len(headers))

    row_values[header_map["status"]] = status
    row_values[header_map["error_message"]] = error_message

    _update_full_row(worksheet, row_number, row_values)


def write_processed_lead(worksheet, row_number: int, processed_lead: dict) -> None:
    headers, header_map = ensure_sheet_columns(worksheet)
    row_values = _pad_row(worksheet.row_values(row_number), len(headers))

    score = processed_lead.get("score", {})
    insights = processed_lead.get("sales_insights", [])
    meta = processed_lead.get("meta", {})
    error_message = "; ".join(meta.get("errors", []))

    updates = {
        "status": "done" if meta.get("status") == "success" else "error",
        "score": str(score.get("value", 0)),
        "priority": score.get("label", "Low"),
        "top_insight": insights[0] if insights else "",
        "draft_email": processed_lead.get("draft_email", ""),
        "processed_at": meta.get("processed_at", ""),
        "error_message": error_message,
    }

    for column, value in updates.items():
        row_values[header_map[column]] = value

    _update_full_row(worksheet, row_number, row_values)
