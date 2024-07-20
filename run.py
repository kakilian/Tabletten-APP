import gspread
from google.oauth2.service_account import Credentials
import logging
from datetime import datetime

logging.basicConfig(
    filename='login_attempts.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

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
    """Validation check of the pin to gain access into the system."""
    pin_data = worksheet.col_values(2)[1:]
    logging.info(f"PIN validation attempt: {'Success' if entered_pin in pin_data else 'Failure'}")
    return entered_pin in pin_data

def get_login(max_attempts=3):
    """
    Login required to enable system to start, and an added safety measure for the BTM safe. Allows up to 3 login attempts.
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
    def __init__(self, patient_id, patient_name, patient_surname, patient_birthdate, room_bed_number):
        self.patient_id = patient_id
        self.patient_name = patient_name
        self.patient_surname = patient_surname
        self.patient_birthdate = patient_birthdate
        self.room_bed_number = room_bed_number

    def description(self):
        return f"Patient with ID {self.patient_id}, {self.patient_name}, {self.patient_surname}, Room {self.room_bed_number}"

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
    print("\nPatient Information Menu:")
    print("1. View all Patients")
    print("2. Search for a Patient")
    print("3. Add a new Patient")
    print("4. Return to main Menu")

def search_patient(patients):
    """
    To be able to search for patients through - Patient ID, Patient Name, Paitent Birthdate.
    """
    search_term = input("Enter patient ID or name to search: ").lower()
    found_patients = [p for p in patients if search_term in p.patient_id.lower() or search_term in p.patient_name.lower()]
    if found_patients:
        for patient in found_patients:
            print(patient.description())
    else:
        print("No matching patients found.")

def add_new_patient(worksheet):
    """
    To add new Patients to the list.
    """
    patient_id = input("Enter patient ID: ")
    patient_name = input("Enter patient's name: ")
    patient_surname = input("Enter patient's surname: ")
    patient_birthdate = input("Enter patient's birthdate (DD-MM-YYYY): ")
    patient_room_bed_number = input("Enter the room number (XXX): ")
    new_patient = PatientInformation(patient_id, patient_name, patient_surname, patient_birthdate, patient_room_bed_number)
    worksheet.append_row([new_patient.patient_id, new_patient.patient_name, new_patient.patient_surname, new_patient.patient_birthdate, new_patient.room_bed_number])
    print(f"New patient added: {new_patient.description()}")

def patient_information_system():
    """
    Management Section for Patients, to keep the Patients information up to Date.
    """
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
            patients = get_patient_info(WORKSHEETS["patient_information"]) 
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
        return f"{self.medication_name} - {self.strength} {self.form}, In stock: {self.quantity_in_stock}"

    def full_details(self):
        return f"list of medication in inventory, as follows: {self.medication_name}\nStrength: {self.strength}\nForm: {self.form}\nQuantity in stock: {self.quantity_in_stock}\nLast ordered: {self.last_ordered_date}\nIn stock: {'Yes' if self.in_stock else 'No'}"

def get_medication_information(worksheet):
    """
    Medication List of Inventory, what's in stock.
    """
    medications = []
    data = worksheet.get_all_values()[1:]
    for row in data:
        medication = MedicationInventory(row[0], row[1], row[2], row[3], row[4], row[5], row[6].lower() == 'yes')
        medications.append(medication)  
    return medications


def medication_inventory_system():
    """
    Menu for the Medication Inventory, whats in stock
    """
    medications = get_medication_information(WORKSHEETS["inventory"])
    while True:
        display_medication_menu()
        choice = input("Enter your choice (1-5): ")
        if choice == '1':
            for med in medications:
                print(med.description())
        elif choice == '2':
            search_medication(medications)
        elif choice == '3':
            new_med = add_new_medication(WORKSHEETS["inventory"])
            medications.append(new_med)
        elif choice == '4':
            update_existing_medication(WORKSHEETS["inventory"], medications)
        elif choice == '5':
            break
        else:
            print("Invalid choice. Please try again.")

def display_medication_menu():
    """
    Medication Menu
    
    """
    print("\nMedication Inventory Menu:")
    print("1. View all Medications")
    print("2. Search for a Medication")
    print("3. Add a new Medication")
    print("4. Update existing Medication")
    print("5. Return to the main menu")

def search_medication(medications):
    """
    Searching Menu to find the neccessary Medication
    
    """
    search_term = input("Enter medication name or strength to search: ").lower()
    found_medications = [m for m in medications if search_term in m.medication_name.lower() or search_term in m.strength.lower()]
    if found_medications:
        for med in found_medications:
            print(med.description())
    else:
        print("No matching medications found.")

def add_new_medication(worksheet):
    """
    To add new medication, Name, strength, form, quantity, reorder level, last ordered, in stock.
    """
    name = input("Enter medication name: ")
    strength = input("Enter strength: ")
    form = input("Enter form: ")
    quantity = int(input("Enter quantity in stock: "))
    reorder_level = int(input("Enter reorder level: "))
    last_ordered_date = input("Enter last ordered date (DD-MM-YYYY): ")
    in_stock = input("Is it in stock? (yes/no): ").lower() == 'yes'
    new_med = MedicationInventory(name, strength, form, quantity, reorder_level, last_ordered_date, in_stock)
    worksheet.append_row([new_med.medication_name, new_med.strength, new_med.form, new_med.quantity_in_stock, new_med.reorder_level, new_med.last_ordered_date, 'YES' if new_med.in_stock else 'NO'])
    print(f"New medication added: {new_med.description()}")
    return new_med

class MatchingPatientsWithMedication:
    """
    Patient registration for medication
    """
    def __init__(self, patient_surname, patient_name, patient_birthdate, patient_id, medication_name, medication_quantity, medication_strength, guidelines):
        self.patient_surname = patient_surname
        self.patient_name = patient_name
        self.patient_birthdate = patient_birthdate
        self.patient_id = patient_id
        self.medication_name = medication_name
        self.medication_quantity = medication_quantity
        self.medication_strength = medication_strength
        self.guidelines = guidelines

        def full_details(self):
            return f"Patient list, Surname:{self.patient_surname}First Name{self.patient_name}\nBirthdate:{self.self.patient_birthdate}\nID: {self.patient_id}\nMedication: {self.medication_name}\nQuantity: {self.medication_quantity}\nMedication Dosage: {self.medication_strength}\nGuidelines: {self.guidelines}\n"

def administer_medication(patients, medications):
    """
    Entering the Patients surname, medication name, and amount here required.
    """
    patient_surname = input("Enter patient surname(lowercase only): ")
    found_patients = [p for p in patients if patient_surname.lower() in p.patient_surname.lower()]
    
    if not found_patients:
        print("No patients found with that surname.")
        return

    if len(found_patients) == 1:
        selected_patient = found_patients[0]
    else:
        print("\nMultiple patients found. Please select:")
        for idx, patient in enumerate(found_patients, start=1):
            print(f"{idx}. {patient.description()}")
        
        while True:
            try:
                patient_choice = int(input("Enter the patient number: ")) - 1
                if 0 <= patient_choice < len(found_patients):
                    selected_patient = found_patients[patient_choice]
                    break
                else:
                    print("Invalid selection. Please try again.")
            except ValueError:
                print("Please enter a valid number.")

    print(f"\nSelected patient: {selected_patient.description()}")

    medication_name = input("Enter the name of the medication required: ")
    matching_medications = [m for m in medications if medication_name.lower() in m.medication_name.lower()]

    if not matching_medications:
        print("No matching medications found.")
        return

    if len(matching_medications) == 1:
        selected_medication = matching_medications[0]
    else:
        print("\nMultiple medications found. Please select:")
        for idx, med in enumerate(matching_medications, start=1):
            print(f"{idx}. {med.description()}")
        
        while True:
            try:
                med_choice = int(input("Enter the medication number: ")) - 1
                if 0 <= med_choice < len(matching_medications):
                    selected_medication = matching_medications[med_choice]
                    break
                else:
                    print("Invalid selection. Please try again.")
            except ValueError:
                print("Please enter a valid number.")

    quantity = int(input("Enter the quantity to administer: "))
    
    print(f"\nAdministering amount of: {quantity} of: {selected_medication.medication_name} to: {selected_patient.patient_name} {selected_patient.patient_surname}")
    
    log_administration(selected_patient, selected_medication, quantity)

def log_administration(patient, medication, quantity):
    log_entry = [
        datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
        patient.patient_id,
        patient.patient_surname,
        patient.patient_name,
        medication.medication_name,
        str(quantity),
        medication.strength
    ]
    WORKSHEETS["medication_administration_logs"].append_row(log_entry)
    print("Administration logged successfully.\n")



def main():
    logging.info("Application started")
    if get_login():
        logging.info("Access granted. Proceeding with the application.")
        print("Access granted. Proceeding with the application... \n")
        while True:
            print("\nMain Menu:")
            print("1. Patient Information System")
            print("2. Medication Inventory System")
            print("3. Administer Medication")
            print("4. Guidelines")
            print("5. Exit")
            choice = input("Enter your choice (1-5): ")
            if choice == '1':
                patient_information_system()
            elif choice == '2':
                medication_inventory_system()
            elif choice == '3':
                patients = get_patient_info(WORKSHEETS["patient_information"])
                medications = get_medication_information(WORKSHEETS["inventory"])
                administer_medication(patients, medications)
            elif choice == '4':
                guidelines_system()
            elif choice == '5':
                print("Exiting the application.")
                break
            else:
                print("Invalid choice. Please try again.")
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

def guidelines_system():
    guidelines = get_guidelines(WORKSHEETS["guidelines"])
    while True:
        print("\nGuidelines Menu:")
        print("1. View all Guidelines")
        print("2. Search Guidelines")
        print("3. Return to Main Menu")
        choice = input("Enter your choice (1-3): ")
        if choice == '1':
            display_all_guidelines(guidelines)
        elif choice == '2':
            search_guidelines(guidelines)
        elif choice == '3':
            break
        else:
            print("Invalid choice. Please try again.")

def get_guidelines(worksheet):
    guidelines = []
    data = worksheet.get_all_values()[1:]
    for row in data:
        guideline = {
            'medication_name': row[0],
            'administration_guidelines': row[1],
            'dosage_guidelines': row[2],
            'intervals': row[3],
            'potential_side_effects': row[4],
            'emergency_procedures': row[5],
            'additional_notes': row[6]
        }
        guidelines.append(guideline)
    return guidelines

def display_all_guidelines(guidelines):
    for guideline in guidelines:
        display_guideline(guideline)

def display_guideline(guideline):
    print(f"\nMedication Name: {guideline['medication_name']}")
    print(f"Administration Guidelines: {guideline['administration_guidelines']}")
    print(f"Dosage Guidelines: {guideline['dosage_guidelines']}")
    print(f"Intervals: {guideline['intervals']}")
    print(f"Potential Side Effects: {guideline['potential_side_effects']}")
    print(f"Emergency Procedures: {guideline['emergency_procedures']}")
    print(f"Additional Notes: {guideline['additional_notes']}")
    print("-" * 50)

def search_guidelines(guidelines):
    search_term = input("Enter medication name or guideline to search: ").lower()
    found_guidelines = [g for g in guidelines if search_term in g['medication_name'].lower()]
    if found_guidelines:
        for guideline in found_guidelines:
            display_guideline(guideline)
    else:
        print("No matching guidelines found.")