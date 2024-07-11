import gspread
from google.oauth2.service_account import Credentials

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
    ]

CREDS = Credentials.from_service_account_file('creds.json')
SCOPED_CREDS = CREDS.with_scopes(SCOPE)
GSPREAD_CLIENT = gspread.authorize(SCOPED_CREDS)
SHEET = GSPREAD_CLIENT.open('medication_inventory')


def get_login():
    """
    Login required to enable system to start, and an added saftey measure for the BTM safe"
    """
    print("Please enter the pin to start the program.")
    print("Enter the 4 pin number now\n")
    print("Watch for spaces between numbers\n")

    data_str = input("Enter your pin here: ")

    print("You are now logged in")

get_login()
