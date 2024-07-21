import gspread
from google.oauth2.service_account import Credentials
from gspread.exceptions import SpreadsheetNotFound, WorksheetNotFound

class Nurse:
    def __init__(self, name, pin):
        self.name = name
        self.pin = pin

def get_nurses_from_sheet(spreadsheet_name, worksheet_name):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds_path = '/workspace/animated-waffle/creds.json'

    try:
        creds = Credentials.from_service_account_file(creds_path, scopes=scope)
        client = gspread.authorize(creds)

        try:
            sheet = client.open(spreadsheet_name)
            worksheet = sheet.worksheet(worksheet_name)
            records = worksheet.get_all_records()

            nurses = [
                Nurse(record['name'], record['pin']) for record in records
            ]
            return nurses
        except SpreadsheetNotFound:
            print(f"""
            Error: Spreadsheet '{spreadsheet_name}' not found. Please check
            the spreadsheet name and permissions.
            """
            )
            return []
        except WorksheetNotFound:
            print(f"""
            Error: Worksheet '{worksheet_name}' not found in
            spreadsheet '{spreadsheet_name}'.
            """
            )
            return []
        except Exception as e:
            print(f"Error accessing worksheet: {str(e)}")
            return []

    except FileNotFoundError:
        print(f"Error: Credentials file not found at {creds_path}")
        return []
    except Exception as e:
        print(f"Error with credentials or authorization: {str(e)}")
        return []

def validate_pin(pin, nurses):
    for nurse in nurses:
        if nurse.pin == pin:
            return nurse
    return None