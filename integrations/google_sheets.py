from pathlib import Path

import gspread


DEFAULT_CREDENTIALS_PATH = Path(__file__).resolve().parent.parent / "credentials" / "google_service_account.json"


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
