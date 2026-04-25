from integrations.google_sheets import get_worksheet


SHEET_NAME = "leads"


worksheet = get_worksheet(SHEET_NAME)
all_values = worksheet.get_all_values()
records = worksheet.get_all_records()

print(f"Connected to spreadsheet: {SHEET_NAME}")
print(f"Worksheet title: {worksheet.title}")
print(f"Total rows with values: {len(all_values)}")

if not all_values:
    print("The worksheet is empty.")
elif len(all_values) == 1:
    print("The worksheet only has a header row, so get_all_records() returns an empty list.")
    print(f"Header row: {all_values[0]}")
else:
    print(f"Header row: {all_values[0]}")
    print(f"Loaded {len(records)} records from the worksheet.")
    print(records)
