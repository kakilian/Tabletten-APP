import logging
from datetime import datetime
import logging
from nurse import get_nurses_from_sheet, validate_pin
import gspread
from google.oauth2.service_account import Credentials
from colorama import Fore, Back, Style
print(Fore.RED + 'some red text')
print(Back.GREEN + 'and with a green background')
print(Style.DIM + 'and in dim text')
print(Style.RESET_ALL)
print('back to normal now')

logging.basicConfig(
    filename='login_attempts.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%d-%m-%Y %H:%M:%S'
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
    "medication_administration_logs": SHEET.worksheet(
        "medication_administration_logs"
    ),
    "guidelines": SHEET.worksheet("guidelines")
}

current_nurse_name = ""

class Nurse:
    def __init__(self, name, pin):
        self.name = name
        self.pin = pin

def get_nurses_from_sheet():
    """Retrieve nurse data from the nurse_pin worksheet"""
    records = WORKSHEETS["nurse_pin"].get_all_records()
    nurses = []
    for record in records:
        name = record.get('nurse_name', 'Unknown')
        pin = str(record.get('nurse_pin', ''))  
        nurses.append(Nurse(name, pin))
    return nurses

def validate_pin(entered_pin, nurses):
    """
    Validation check of the pin to gain access into the system.
    Returns the nurse object if the PIN is valid, None otherwise.
    """
    for nurse in nurses:
        if nurse.pin == entered_pin:
            logging.info(f"PIN validation successful for nurse: {nurse.name}")
            return nurse
    logging.info("Pin validation failed")
    return None

def get_login(max_attempts=3):
    """
    Login required to enable system to start, and an added safety measure
    for the BTM safe. Allows up to 3 login attempts.
    """
    nurses = get_nurses_from_sheet()
    

    if not nurses:
        logging.error("Failed to retrieve nurse data from the sheet.")
        print(
            "System error: Unable to access nurse data. Please contact support."
        )
        return None

    attempts = 0
    while attempts < max_attempts:
        logging.info(f"Login attempt {attempts + 1} of {max_attempts}")
        print(f"\nAttempt {attempts + 1} of {max_attempts}")
        print("Please enter the 4 number pin to start the program.")
        print("Watch for spaces between numbers\n")
        entered_pin = input("Enter your pin here: ").strip()
        nurse = validate_pin(entered_pin, nurses)
        if nurse:
            print(f"\nWelcome, {nurse.name}!")
            return nurse.name
        else:
            print("Invalid pin entry, please try again .. \n")
        attempts += 1
    logging.error("Maximum login attempts reached. Access denied.")
    print("Maximum login attempts reached. Access denied.")
    return None


class PatientInformation:
    """Patient Information Class"""
    def __init__(
        self, 
        patient_id, 
        patient_name,
        patient_surname,
        patient_birthdate,
        room_bed_number
    ):
        self.patient_id = patient_id
        self.patient_name = patient_name
        self.patient_surname = patient_surname
        self.patient_birthdate = patient_birthdate
        self.room_bed_number = room_bed_number


    def description(self):
        return f"""
    Patient with ID {self.patient_id}, 
    Name {self.patient_name}
    Surname {self.patient_surname}, 
    Date of Birth {self.patient_birthdate},
    Room {self.room_bed_number}
        """


def get_patient_info(worksheet):
    """Retrieve Patient information from the worksheet"""
    patients = []
    data = worksheet.get_all_values()[1:]
    for row in data:
        patient = PatientInformation(
            row[0], row[1], row[2], row[3], row[4]
        )
        patients.append(patient)
    return patients


def display_patient_menu():
    print("\nPatient Information Menu:")
    print("1. View all Patients")
    print("2. Search for a Patient")
    print("3. Add a new Patient")
    print("4. Return to main Menu")


def search_patient(patients):
    search_term = input("Enter patient surname to search: ").lower()
    found_patients = [
        p for p in patients if search_term in p.patient_surname.lower()
    ]
    
    if not found_patients:
        print("No patients found with that surname.")
        return None
    """
    If multiple patients with same surname, and first name
    the unique Hospital ID would be enabled to get target Patient
    """
    if len(found_patients) == 1:
        selected_patient = found_patients[0]
        print(f"Selected patient: {selected_patient.description()}")
        return selected_patient
    else:
        print("\nMultiple patients found. Please select:")
        for patient in found_patients:
            print(f"ID: {patient.patient_id} - {patient.description()}")
        
        while True:
            patient_id = input(
                "Enter the Patient ID of the patient you want to select: "
            )
            selected_patient = next(
                (p for p in found_patients if p.patient_id == patient_id), None
            )
            if selected_patient:
                print(f"Selected patient: {selected_patient.description()}")
                return selected_patient
            else:
                print("Invalid Patient ID. Please try again.")

    return None


def add_new_patient(worksheet):
    """To add new Patients to the list."""
    patient_id = input("Enter patient ID: ")
    patient_name = input("Enter patient's name: ")
    patient_surname = input("Enter patient's surname: ")
    patient_birthdate = input("Enter patient's birthdate (DD-MM-YYYY): ")
    patient_room_bed_number = input("Enter the room number: ")
    new_patient = PatientInformation(
        patient_id, patient_name, patient_surname, patient_birthdate,
        patient_room_bed_number
    )
    worksheet.append_row(
        [
            new_patient.patient_id,
            new_patient.patient_name,
            new_patient.patient_surname,
            new_patient.patient_birthdate,
            new_patient.room_bed_number
        ]
    )
    print(f"New patient added: {new_patient.description()}")


def patient_information_system():
    """
    Management Section for Patients, to keep the Patients
    information up to Date.
    """
    patients = get_patient_info(WORKSHEETS["patient_information"])
    while True:
        display_patient_menu()
        choice = input("Enter your choice (1-4): ")
        if choice == '1':
            for patient in patients:
                print(patient.description())
        elif choice == '2':
            selected_patient = search_patient(patients)
            if selected_patient:
                print("Patient selected for further actions.")
        elif choice == '3':
            add_new_patient(WORKSHEETS["patient_information"])
            patients = get_patient_info(WORKSHEETS["patient_information"])
        elif choice == '4':
            break
        else:
            print("Invalid choice. Please try again.")


class MedicationInventory:
    """Creates medication Class"""
    def __init__(
        self, medication_name, strength, form, quantity_in_stock,
        reorder_level, last_ordered_date, in_stock
    ):
        self.medication_name = medication_name
        self.strength = strength
        self.form = form
        self.quantity_in_stock = int(quantity_in_stock)
        self.reorder_level = int(reorder_level)
        self.last_ordered_date = last_ordered_date
        self.in_stock = in_stock


    def description(self):
        """Returns description string including instance attributes."""
        return f"""
        {self.medication_name}
        {self.strength} 
        {self.form}
        In stock: {self.quantity_in_stock}"

        """


    def full_details(self):
        return f"""
    List of medication in inventory, as follows: {self.medication_name}

    Strength: {self.strength}

    Form: {self.form}

    Quantity in stock: {self.quantity_in_stock}

    Last ordered: {self.last_ordered_date}

    In stock: {'Yes' if self.in_stock else 'No'}"

        """


def get_medication_information(worksheet):
    """Medication List of Inventory, what's in stock."""
    medications = []
    data = worksheet.get_all_values()[1:]
    for row in data:
        medication = MedicationInventory(
            row[0], row[1], row[2], row[3], row[4],
            row[5], row[6].lower() == 'yes'
        )
        medications.append(medication)  
    return medications


def medication_inventory_system():
    """Menu for the Medication Inventory, whats in stock."""
    medications = get_medication_information(WORKSHEETS["inventory"])
    while True:
        display_medication_menu()
        choice = input("Enter your choice (1-5): ").strip()
        if choice == '1':
            display_all_medications(medications)
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


def display_all_medications(medications):
    print("\nAll Medications in Inventory:")
    for med in medications:
        print(med.description())
        print("-" * 40)


def display_medication_menu():
    """Medication Menu."""
    print("\nMedication Inventory Menu:")
    print("1. View all Medications")
    print("2. Search for a Medication")
    print("3. Add a new Medication")
    print("4. Update existing Medication")
    print("5. Return to the main menu")


def search_medication(medications):
    """Searching Menu to find the neccessary Medication."""
    search_term = input(
        "Enter medication name to search:"
    ).strip().lower()
    matching_medications = [
        med for med in medications if search_term in m.medication_name.lower()
    ]
    if matching_medications:
        print("\nMatching Medications:")
        for med in found_medications:
            print(med.description())
            print("-" * 40)
    else:
        print("No matching medications found.")


def add_new_medication(worksheet):
    """To add new medication"""
    medication_name = input("Enter medication name: ").strip()
    strength = input("Enter strength: ").strip()
    form = input("Enter form: ").strip()
    quantity_in_stock = int(input("Enter quantity in stock: ").strip())
    reorder_level = int(input("Enter reorder level: ").strip())
    last_ordered_date = input("Enter last ordered date (DD-MM-YYYY): ").strip()
    in_stock = input("Is it in stock? (yes/no): ").strip().lower() == 'yes'
    
    new_medication = MedicationInventory(
        medication_name, 
        strength, 
        form, 
        quantity_in_stock,
        reorder_level, 
        last_ordered_date, 
        in_stock
    )
    
    worksheet.append_row(
        [
            new_med.medication_name,
            new_med.strength,
            new_med.form,
            new_med.quantity_in_stock,
            new_med.reorder_level,
            new_med.last_ordered_date,
            'YES' if new_med.in_stock else 'no'
        ]
    )
    print("New medication added successfully:")
    print(new_medication.description())
    return new_medication


def update_existing_medication(worksheet, medications):
    """To update stock when new stock arrives after being ordered"""
    search_term = input("Enter medication name to update: ").strip().lower()
    matching_medications = [
        med for med in medications if search_term in med.medication_name.lower()
    ]
    if not matching_medications:
        print("No matching medications found.")
        return
    
    print("Matching medications:")
    for idx, med in enumerate(matching_medications, start=1):
        print(f"{idx}.")
        print(med.description())
        print("-" * 40) 
    
    while True:
        try:
            med_choice = int(input(
                "Enter the number of the medication to update: ").strip()
            ) - 1
            if 0 <= med_choice < len(matching_medications):
                selected_medication = matching_medications[med_choice]
                break
            else:
                print(f"""
                Invalid selection. Please enter a number between 1 and {
                    len(matching_medications)
                }
                """
                )

        except ValueError:
            print("Please enter a valid number.")
    
    """Update the selected medication"""
    selected_medication.quantity_in_stock = int(input(
        f"Enter new quantity in stock for {selected_medication.medication_name}: "
        ).strip()
    )
    selected_medication.reorder_level = int(input(
        f"Enter new reorder level for {selected_medication.medication_name}: "
        ).strip()
    )
    selected_medication.last_ordered_date = input(
    f"Enter new last ordered date (DD-MM-YYYY) for {
        selected_medication.medication_name
    }: "
    ).strip()
    selected_medication.in_stock = input(
        f"Is it in stock? (yes/no): "
    ).strip().lower() == 'yes'
    
    """Update the worksheet"""
    inventory_data = worksheet.get_all_records()
    for idx, row in enumerate(inventory_data, start=2):  
        if row['Medication name'] == selected_medication.medication_name
        and row['Strength'] == selected_medication.strength
        and row['form'] == selected_medication.form:
            worksheet.update(f"D{idx}", selected_medication.quantity_in_stock)
            worksheet.update(f"E{idx}", selected_medication.reorder_level)
            worksheet.update(f"F{idx}", selected_medication.last_ordered_date)
            worksheet.update(
                f"G{idx}", 'yes' if selected_medication.in_stock else 'no'
            )
            break
    
    print("Medication updated successfully:")
    print(selected_medication.description())


class MatchingPatientsWithMedication:
    """ Patient registration for medication """
    def __init__(
        self, patient_surname,
        patient_name,
        patient_birthdate, 
        patient_id,
        medication_name,
        medication_quantity,
        medication_strength,
        guidelines
    ):
        self.patient_surname = patient_surname
        self.patient_name = patient_name
        self.patient_birthdate = patient_birthdate
        self.patient_id = patient_id
        self.medication_name = medication_name
        self.medication_quantity = medication_quantity
        self.medication_strength = medication_strength
        self.guidelines = guidelines


        def full_details(self):
            return f"""
        Patient list, Surname:{self.patient_surname}
        First Name{self.patient_name}

        Birthdate:{self.self.patient_birthdate}

        ID: {self.patient_id}

        Medication: {self.medication_name}

        Quantity: {self.medication_quantity}

        Medication Dosage: {self.medication_strength}

        Guidelines: {self.guidelines}
            """


def administer_medication(patients, medications, nurse_name):
    """
    Entering the Patients surname, medication name, authorising nurse
    and amount here required.
    """
    while True:
        patient_surname = input(
            "Enter patient surname (lowercase only): "
        ).strip().lower()
        found_patients = [
            p for p in patients if patient_surname in p.patient_surname.lower()
        ]
        
        if not found_patients:
            print("No patients found with that surname.")
            continue_search = input(
                "Do you want to search again? (y/n): "
            ).strip().lower()
            if continue_search != 'y':
                return
        else:
            break

    if len(found_patients) == 1:
        selected_patient = found_patients[0]
        print(f"Selected patient: {selected_patient.description()}")
    else:
        print("\nMultiple patients found with that surname. Please select:")
        for idx, patient in enumerate(found_patients, start=1):
            print(f"{idx}. {patient.description()}")
        
        while True:
            patient_choice = input(
                "Enter the number of the patient you want to select: "
                ).strip()
            try:
                patient_choice = int(patient_choice)
                if 1 <= patient_choice <= len(found_patients):
                    selected_patient = found_patients[patient_choice - 1]
                    print(f"Selected patient: {selected_patient.description()}")
                    break
                else:
                    print(f"""
                    Invalid selection. Please enter a number between 1 and {
                        len(found_patients)
                    }
                    """
                    )
            except ValueError:
                print("Please enter a valid number.")

    while True:
        medication_name = input(
            "Enter the name of the medication required: "
        ).strip()
        matching_medications = [
            m for m in medications if medication_name.lower()
            in m.medication_name.lower()
        ]

        if not matching_medications:
            print("No matching medications found.")
            continue_search = input(
                "Do you want to search for another medication? (y/n): "
                ).strip().lower()
            if continue_search != 'y':
                return
        else:
            break

    if len(matching_medications) == 1:
        selected_medication = matching_medications[0]
        print(f"Selected medication: {selected_medication.description()}")
    else:
        print("\nMultiple medications found. Please select:")
        for idx, med in enumerate(matching_medications, start=1):
            print(f"{idx}. {med.description()}")
        
        while True:
            try:
                med_choice = int(
                    input("Enter the medication number: ").strip()
                ) - 1
                if 0 <= med_choice < len(matching_medications):
                    selected_medication = matching_medications[med_choice]
                    print(f""""
                    Selected medication: {
                        selected_medication.description()
                    }
                    """
                    )
                    break
                else:
                    print("Invalid selection. Please try again.")
            except ValueError:
                print("Please enter a valid number.")

    while True:
        try:
            quantity = int(input("Enter the quantity to administer: ").strip())
            break
        except ValueError:
            print("Please enter a valid number.")

    print(f"""
    Summary:
    Patient: {selected_patient.patient_name} {selected_patient.patient_surname}
    Medication: {selected_medication.medication_name}
    Quantity: {quantity}
    Administering Nurse: {nurse_name}
    """)

    confirm = input("Confirm administration? (y/n): ").strip().lower()
    if confirm == 'y':
        log_administration(
            selected_patient, 
            selected_medication, 
            quantity, 
            nurse_name
        )
    else:
        print("Administration cancelled.")

def log_administration(patient, medication, quantity, nurse_name):
    log_entry = [
        datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
        patient.patient_surname,
        patient.patient_name,
        medication.medication_name,
        str(quantity),
        medication.strength,
        nurse_name
    ]
    WORKSHEETS["medication_administration_logs"].append_row(log_entry)
    print("Administration logged successfully.\n")



def main():
    global current_nurse_name

    current_nurse_name = get_login()
    if not current_nurse_name:
        logging.error("Login failed. Exiting the application.")
        print("Login failed. Exiting the application.")
        return

    logging.info("Application started")
    logging.info
    f"""
    Access granted for nurse: {current_nurse_name}.
    Proceeding with the application.
    """
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
            administer_medication(patients, medications, current_nurse_name)
        elif choice == '4':
            guidelines_system()
        elif choice == '5':
            print("Exiting the application.")
            break
        else:
            print("Invalid choice. Please try again.")


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
    """Menu for Opitate Medicine guidelines"""
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
    """Glossary index for Guidelines when working with BTM"""
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
    print(
        f"Administration Guidelines: {guideline['administration_guidelines']}"
    )
    print(f"Dosage Guidelines: {guideline['dosage_guidelines']}")
    print(f"Intervals: {guideline['intervals']}")
    print(f"Potential Side Effects: {guideline['potential_side_effects']}")
    print(f"Emergency Procedures: {guideline['emergency_procedures']}")
    print(f"Additional Notes: {guideline['additional_notes']}")
    print("-" * 50)


def search_guidelines(guidelines):
    search_term = input(
        "Enter medication name or guideline to search: "
        ).lower()
    found_guidelines = [
        g for g in guidelines if search_term in g['medication_name'].lower()
    ]
    if found_guidelines:
        for guideline in found_guidelines:
            display_guideline(guideline)
    else:
        print("No matching guidelines found.")