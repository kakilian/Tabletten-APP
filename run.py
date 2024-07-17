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
    def __init__(self, patient_id, patient_name, patient_surname, patient_birthdate, room_bett_number):
        self.patient_id = patient_id
        self.patient_name = patient_name
        self.patient_surname = patient_surname
        self.patient_birthdate = patient_birthdate
        self.room_bett_number = room_bett_number

    def description(self):
        return f"Patient with ID {self.patient_id}, {self.patient_name}, {self.patient_surname} {self.room_bett_number} "

def get_patient_info(worksheet):
    """
    Retrieve Patient information from the worksheet
    """
    patients = []
    data = worksheet.get_all_values()[1:]
    for row in data:
        patient = PatientInformation(row[0], row[1], row[2], row[3], row[4])
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
    patient_name = input("Enter patients name: ")
    patient_surname = input("Enter patients surname: ")
    patient_birthdate = input("Enter patients birthdate (DD-MM-YYYY): ")
    patient_room_bed_number = input("Enter the room number(XXX): ")
    
    new_patient = PatientInformation(patient_id, patient_name, patient_birthdate, patient_room_bed_number)
    worksheet.append_row([new_patient.patient_id, new_patient.patient_name, new_patient.patient_birthdate, new_patient.room_bett_number])
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

class MedicationInventory:
    """
    Creates medication Class
    """
    def __init__(self, medication_name, strength, form, quantity_in_stock, reorder_level, last_ordered_date, in_stock):
        self.medication_name = medication_name
        self.strength = strength
        self.form = form
        self.quantity_in_stock = int(quantity_in_stock)
        self.reorder_level = int(reorder_level)
        self.last_ordered_date = last_ordered_date
        self.in_stock = in_stock

    def description(self):
        """
        Returns description string including instance attributes
        
        """  
        def description(self):
        return f"{self.medication_name} - {self.strength} {self.form}, In stock: {self.quantity_in_stock}"
        
        def full_details(self):
            return f"list of medication in inventory, as follows: {self.medication}\nStrength: {self.strength}\nForm: {self.form}\nQuantity in stock: {self.quantity_in_stock}\nLast ordered: {self.last_ordered_date}\nIn stock: {'Yes' if self.in_stock else 'No'}"
        print("Please type which medication and amount is required ...\n")

def get_medication_information(worksheet):
    medications = []
    data = worksheet.get_all_values()[1:]
    for row in data:
        medication = MedicationInventory(row[0], row[1], row[2], row[3], row[4], row[5], row[6] == True)
        medication.append(medication)
    return medications  

def medication_inventory_system():
    medications = get_medication_information(WORKSHEETS["inventory"])
    while True:
        display_medication_menu()
        choice = input("Enter your choice (1-4): ")
        if choice == '1':
            for med in medications:
                print(med.description())
            elif choice == '2':
                search_medication(medications)
            elif choice == '3':

add_new_medication(WORKSHEETS["inventory"])
                medications = get_medication_information(WORKSHEETS["inventory"]) 
                elif choice == '4':
                    break
                else:
                    print("Invalid choice. Please tra again.")

def display_medication_menu():
    print("\nMedication Inventory Menu: ")
    print("1. View all Medications ")
    print("2. Search for a Medication ")
    print("3. Add a new Medication ")
    print("4. Return to the main menu ")

def search_medication(medications):
    search_term = input("Enter medication namd or strength to searc: ").lower()
    found_medications = [m for m in medications if search_term in m-medication_name.lower() or search_term in m.strength.lower()]
        if found_medications:
            for med in found_medications:
                print(med.description())
            else:
                print("No matching medications found.")

def add_new_medication(worksheet):
    name = input("Enter medication name: ")
    strength = input("Enter strength: ")
    form = input("Enter form: ")
    quantity = int(input("Enter quantity in stock: "))
    reorder_level = int(input("Enter reoder level: "))
    last_ordered_date = input("Enter last ordered date (DD-MM-YYY): ")
    in_stock = input("Is it in stock? (yes/no):").lower()== 'yes'

    new_med = MedicationInventory(name, strength, form, quantity, reorder_level, last_ordered_date, in_stock)

worksheet.append_row([new_med.medication_name, new_med.strength, new_med.form, new_med.quantity_in_stock, new_med.reorder_level, new_med.last_ordered_date, str(new_med.in_stock).upper()])
    print(f"New medication added: {new_med.description()}")



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

        #Retrieve Medication Information
        medication = get_medication_information(WORKSHEETS["inventory"])

        for inventory in inventorys:
            print(inventory.description)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.warning("Application terminated by user.")
        print("\nApplication terminated by user. Quitting the application...")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        print(f"An unexpected error occurred: {str(e)}")