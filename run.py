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

class PatientInformation:
    """
    Patient Information Class
    """
    def __init__(self, patient_id, patient_name, patient_birthdate):
        self.patient_id = patient_id
        self.patient_name = patient_name
        self.patient_birthdate = patient_birthdate

    def description(self):
        return f"Patient with ID {self.patient_id} is {self.patient_name} "

def get_patient_info(worksheet):
    """
    Retrieve Patient information from the worksheet
    """
    patients = []
    data = worksheet.get_all_values()[1:]
    for row in data:
        patient = PatientInformation(row[0], row[1], row[2])
        patients.append(patient)
    return patients

def display_patient_menu():
    print("\nPatient Information Menu: ")
    print("1. View all Patients")
    print("2. Search for a Patient")
    print("3. Add a new Patient")    
    print("4. Return to main Menu")

def search_patient(patients):
    search_term = input("Enter patient ID or name to search: ").lower()
    found_patients = [p for p in patients if search_term in p.patient_id.lower() or search_term in p.patient_name.lower()]
    if found_patients:
        for patient in found_patients:
            print(patient.description())
    else:
        print("No matching patients found.")

def add_new_patient(worksheet):
    patient_id = input("Enter patient ID: ")
    patient_name = input("Enter patient name: ")
    patient_birthdate = input("Enter patient birthdate (YYYY-MM-DD): ")
    
    new_patient = PatientInformation(patient_id, patient_name, patient_birthdate)
    worksheet.append_row([new_patient.patient_id, new_patient.patient_name, new_patient.patient_birthdate])
    print(f"New patient added: {new_patient.description()}")

def patient_information_system():
    patients = get_patient_info(WORKSHEETS["patient_information"])
    while True:
        display_patient_menu()
        choice = input("Enter your choice (1-4): ")
        if choice == '1':
            for patient in patients:
                print(patient.description())
        elif choice == '2':
            search_patient(patients)
        elif choice == '3':
            add_new_patient(WORKSHEETS["patient_information"])
            patients = get_patient_info(WORKSHEETS["patient_information"])  # Refresh patient list
        elif choice == '4':
            break
        else:
            print("Invalid choice. Please try again.")

def main():
    logging.info("Application started")
    if get_login():
        logging.info("Access granted. Proceeding with the application.")
        print("Access granted. Proceeding with the application... \n")

        #Retreive Patient Information
        patients = get_patient_info(WORKSHEETS["patient_information"])

        for patient in patients:
            print(patient.description())

        patient_information_system()
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