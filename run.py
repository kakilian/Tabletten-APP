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

WORKSHEETS = {
    "nurse_pin": SHEET.worksheet("nurse_pin"),
    "inventory": SHEET.worksheet("inventory"),
    "patient_information": SHEET.worksheet("patient_information"),
    "medication_administration_logs": SHEET.worksheet("medication_administration_logs"),
    "guidelines": SHEET.worksheet("guidelines")
}


def validate_pin(entered_pin, worksheet):
    """
    Validation check of the pin to gain access into the system.
    """
    pin_data = worksheet.col_values(2)[1:]  
    print(f"PIN data retrieved: {pin_data}")

    if entered_pin in pin_data:
        return True
    return False   

def get_login(max_attempts=3):
    """
    Login required to enable system to start, and an added safety measure for the BTM safe
    Allows up to 3 login attempts.
    """
    attempts = 0
    while attempts < max_attempts:
        print(f"\nAttempt {attempts + 1} of {max_attempts}")
        print("Please enter the pin to start the program.")
        print("Enter the 4 pin number now\n")
        print("Watch for spaces between numbers\n")

        data_str = input("Enter your pin here: ")

        if validate_pin(data_str, WORKSHEETS["nurse_pin"]):
            print("You are now logged in")
            return True
        else:
            print("Invalid pin entry, please try again .. \n")
            attempts += 1

    print("Maximum login attempts reached. Access denied.")
    return False        

def main():
    if get_login():
        print("Access granted. Proceeding with the application... \n")
    else:
        print("Login failed. Exiting the application.")    

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Handle the keyboard interrupt exception when the user presses Ctrl+C
        print("\nApplication terminated by user. Quitting the application...")
    