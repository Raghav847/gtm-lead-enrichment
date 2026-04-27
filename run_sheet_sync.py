import argparse

from integrations.google_sheets import get_worksheet, read_lead_rows, update_row_status, write_processed_lead
from main import process_lead


def run_sheet_sync(sheet_name: str, worksheet_name: str | None = None) -> int:
    worksheet = get_worksheet(sheet_name, worksheet_name)
    pending_rows = read_lead_rows(sheet_name, worksheet_name, status_filter="new")

    if not pending_rows:
        print("No new sheet leads found.")
        return 0

    print(f"Found {len(pending_rows)} new lead(s) in {sheet_name}.")

    for idx, row in enumerate(pending_rows, start=1):
        row_number = row["row_number"]
        lead_input = row["lead_input"]
        print(f"Processing row {row_number} ({idx}/{len(pending_rows)})")

        update_row_status(worksheet, row_number, "processing")
        result = process_lead(lead_input)
        write_processed_lead(worksheet, row_number, result)

    print(f"Finished processing {len(pending_rows)} lead(s).")
    return len(pending_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Process new inbound leads from Google Sheets.")
    parser.add_argument("--sheet-name", default="gtm_lead_enrichment", help="Google Sheets spreadsheet name")
    parser.add_argument("--worksheet-name", default="", help="Optional worksheet/tab name")
    args = parser.parse_args()

    run_sheet_sync(args.sheet_name, args.worksheet_name or None)


if __name__ == "__main__":
    main()
