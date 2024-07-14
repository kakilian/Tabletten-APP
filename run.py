import gspread
from google.oauth2.service_account import Credentials
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(filename='login_attempts.log', level=logging.INFO,
                    format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

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
    logging.info(f"PIN validation attempt: {'Success' if entered_pin in pin_data else 'Failure'}")
    return entered_pin in pin_data

def get_login(max_attempts=3):
    """
    Login required to enable system to start, and an added safety measure for the BTM safe
    Allows up to 3 login attempts.
    """
    attempts = 0
    while attempts < max_attempts:
        logging.info(f"Login attempt {attempts + 1} of {max_attempts}")
        print(f"\nAttempt {attempts + 1} of {max_attempts}")
        print("Please enter the 4 number pin to start the program.")
        print("Watch for spaces between numbers\n")

        data_str = input("Enter your pin here: ")

        if validate_pin(data_str, WORKSHEETS["nurse_pin"]):
            logging.info("Login successful")
            return True
        else:
            logging.warning("Invalid PIN entry")
            print("Invalid pin entry, please try again .. \n")
            attempts += 1

    logging.error("Maximum login attempts reached. Access denied.")
    print("Maximum login attempts reached. Access denied.")
    return False        

def main():
    logging.info("Application started")
    if get_login():
        logging.info("Access granted. Proceeding with the application.")
        print("Access granted. Proceeding with the application... \n")
    else:
        logging.error("Login failed. Exiting the application.")
        print("Login failed. Exiting the application.")    

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.warning("Application terminated by user.")
        print("\nApplication terminated by user. Quitting the application...")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        print(f"An unexpected error occurred: {str(e)}")