import logging
from datetime import datetime
import logging
from nurse import get_nurses_from_sheet, validate_pin
import gspread
from google.oauth2.service_account import Credentials
from colorama import Fore, Back, Style

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
def welcome():
    print(f"""
        *Welcome to the Medication Administration App*

Effortlessly manage patient medication schedules and records. 
This app is designed to enhance your workflow, ensuring safe
and accurate medication administration.

1. Patients
   - Manage patient information and medication schedules.

2. Add Medication
   - Record stock intake and track medication on hand.

3. Add Nurse Details
   - Input new nurse information and update existing records.

4. Guidelines
   - Access detailed information on medication usage, timing, and symptoms.

Log in to get started and provide the best care for your patients.

    """)

def get_non_empty_input(prompt):
    while True:
        user_input = input(prompt).strip()
        if user_input:
            return user_input
        print("Input cannot be empty. Please try again.")

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
            "System error: Unable to access nurse data.",
            "Please contact support."
        )
        return None

    attempts = 0
    while attempts < max_attempts:
        logging.info(f"Login attempt {attempts + 1} of {max_attempts}")
        print(f"\nAttempt {attempts + 1} of {max_attempts}")
        print("Please enter the 4 number pin to start the program.")
        print("Watch for spaces between numbers\n")
        entered_pin = get_non_empty_input("Enter your pin here:\n ").strip()
        nurse = validate_pin(entered_pin, nurses)
        if nurse:
            print(f"\nWelcome, {nurse.name}!")
            return nurse.name
        else:
            print(f"""
{Fore.RED}Invalid pin entry, please try again .. {Style.RESET_ALL}
            """)
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
    patient_surname = get_non_empty_input(
        "Enter patient surname (lowercase only): \n"
    ).strip().lower()
    found_patients = [
        p for p in patients if patient_surname in p.patient_surname.lower()
    ]
    
    if not found_patients:
        print("No patients found with that surname.")
        return None

    if len(found_patients) == 1:
        selected_patient = found_patients[0]
        print(f"Selected patient: {selected_patient.description()}")
        return selected_patient
    else:
        print("\nMultiple patients found with that surname. Please select:")
        for idx, p in enumerate(found_patients, start=1):
            print(f"{idx}. {p.description()}")
        
        while True:
            try:
                patient_choice = int(get_non_empty_input(
                    "Enter the number of the patient you want to select: \n"
                ).strip()) - 1
                if 0 <= patient_choice < len(found_patients):
                    selected_patient = found_patients[patient_choice]
                    print(f"""
                    Selected patient: {selected_patient.description()}
                    """
                    )
                    return selected_patient
                else:
                    print(f"""
                    Invalid selection.",
                    "Please enter a number between 1 and {
                        len(found_patients)
                    }.
                    """
                    )
            except ValueError:
                print("Please enter a valid number.")


def add_new_patient(worksheet):
    """To add new Patients to the list."""
    patient_id = get_non_empty_input("Enter patient ID: \n")
    patient_name = get_non_empty_input("Enter patient's name: \n")
    patient_surname = get_non_empty_input("Enter patient's surname: \n")
    patient_birthdate = get_non_empty_input("Enter patient's birthdate (DD-MM-YYYY): \n")
    patient_room_bed_number = get_non_empty_input("Enter the room number: \n")
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
        choice = get_non_empty_input("Enter your choice (1-4): \n")
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
    """Menu for the Medication Inventory, what's in stock."""
    medications = get_medication_information(WORKSHEETS["inventory"])
    while True:
        display_medication_menu()
        choice = get_non_empty_input("Enter your choice (1-4): \n").strip()
        if choice == '1':
            display_all_medications(medications)
        elif choice == '2':
            search_medication(medications)
        elif choice == '3':
            update_existing_medication(WORKSHEETS["inventory"], medications)
        elif choice == '4':
            break
        else:
            print("Invalid choice. Please try again.")


def display_all_medications(medications):
    """To show all present medication in stock"""
    print("\nAll Medications in Inventory:")
    for med in medications:
        print(f"{med.medication_name} - Stock: {med.quantity_in_stock}")


def display_medication_menu():
    """Medication Menu"""
    print("\nMedication Inventory Menu:")
    print("1. Display all medications")
    print("2. Search for a medication")
    print("3. Update medication stock")
    print("4. Exit")


def search_medication(meds):
    """Searching through medication"""
    search_term = get_non_empty_input(
        "Enter medication name to search: \n"
    ).strip().lower()
    matching_medications = [
        med for med in meds if search_term in med.medication_name.lower()
    ]
    if matching_medications:
        print("\nMatching Medications:")
        for med in matching_medications:
            print(f"{med.medication_name} - Stock: {med.quantity_in_stock}")
    else:
        print("No matching medications found.")


def add_new_medication(worksheet):
    """To add new medication"""
    medication_name = get_non_empty_input("Enter medication name: \n").strip()
    strength = get_non_empty_input("Enter strength: \n").strip()
    form = get_non_empty_input("Enter form: \n").strip()
    quantity_in_stock = int(get_non_empty_input("Enter quantity in stock: \n").strip())
    reorder_level = int(get_non_empty_input("Enter reorder level: \n").strip())
    last_ordered_date = get_non_empty_input(
        "Enter last ordered date (DD-MM-YYYY): \n"
    ).strip()
    in_stock = get_non_empty_input("Is it in stock? (yes/no): \n").strip().lower() == 'yes'
    
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
    search_term = get_non_empty_input(
        "Enter medication name to update: \n"
    ).strip().lower()
    matching_medications = [
        med for med in medications 
        if search_term in med.medication_name.lower()
    ]
    if not matching_medications:
        print("No matching medications found.")
        return
    
    print("Matching medications:")
    for idx, med in enumerate(matching_medications, start=1):
        print(f"""
            {idx}. {med.medication_name}
            Current stock: {med.quantity_in_stock}"
        """
        )
    
    while True:
        try:
            med_choice = int(
                get_non_empty_input(
                    "Enter the number of the medication to update: \n"
                ).strip()
            ) - 1
            if 0 <= med_choice < len(matching_medications):
                selected_medication = matching_medications[med_choice]
                break
            else:
                print(f"""
                Invalid selection. Please enter a number between 1 and {
                    len(matching_medications)
                }."
                """    
                )
        except ValueError:
            print("Please enter a valid number.")
    
    while True:
        try:
            new_stock = int(get_non_empty_input(f"""
            Enter the quantity of new stock for,
            {selected_medication.medication_name}: \n
            """).strip())
            if new_stock < 0:
                print("Please enter a non-negative number.")
                continue
            break
        except ValueError:
            print("Please enter a valid number.")

    selected_medication.quantity_in_stock += new_stock
    selected_medication.last_ordered_date = datetime.now(
    ).strftime("%d-%m-%Y")
    
    """Worksheet Update"""
    inventory_data = worksheet.get_all_records()
    for idx, row in enumerate(inventory_data, start=2):  
        if row[
            'Medication name'
        ] == selected_medication.medication_name:
            worksheet.update(f"D{idx}",
            selected_medication.quantity_in_stock
            )
            worksheet.update(f"F{idx}",
            selected_medication.last_ordered_date
            )
            break
    
    print("Medication stock updated successfully:")
    print(f"""
    {selected_medication.medication_name}  
    New stock level: {selected_medication.quantity_in_stock}
    """
    )


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


def update_inventory(medication, quantity_administered):
    """Updating local Inventory on Google Sheets, after intake arrival"""
    inventory_worksheet = WORKSHEETS["inventory"]
    inventory_data =  inventory_worksheet.get_all_records()

    if row['Medication name'] == medication.medication_name:
            current_quantity = int(row['Quantity in stock'])
            new_quantity = current_quantity - quantity_administered

            if new_quantity < 0:
                print(
                    f"""
                    Error: Not enough {medication.medication_name} in stock.
                    Current stock: {current_quantity}
                """
                )
                return False

                medication.quantity_in_stock = new_quantity
            inventory_worksheet.update(
                f"D{idx}", new_quantity
            )

            print(
                f"Inventory updated. New quantity for "
                f"{medication.medication_name}: {new_quantity}"
            )
            return True
            

            print(f"""
            Error: {medication.medication_name} not found in inventory.
            """
            )
    return False

    if len(found_patients) == 1:
        selected_patient = found_patients[0]
        print(f"Selected patient: {selected_patient.description()}")
    else:
        print("\nMultiple patients found with that surname. Please select:")
        for idx, patient in enumerate(found_patients, start=1):
            print(f"{idx}. {patient.description()}")
        
        while True:
            try:
                patient_choice = int(get_non_empty_input(
                "Enter the number of the patient you want to select: \n"
                ).strip()) - 1
                if 0 <= patient_choice < len(found_patients):
                    selected_patient = found_patients[patient_choice]
                    print(f"""
                    Selected patient: {selected_patient.description()}
                    """
                    )
                    break
                else:
                    print(f"""
                    Invalid selection. Please enter a number between 1 and {
                        len(found_patients)
                    }.
                    """
                    )
            except ValueError:
                print("Please enter a valid number.")


def administer_medication(patients, medications, nurse_name):
    """
    Entering the Patients surname, medication name, authorising nurse
    and amount here required.
    """
    print("Starting administer_medication function")
    
    # Patient selection
    while True:
        patient_surname = get_non_empty_input(
            "Enter patient surname (lowercase only): \n"
        ).strip().lower()
        found_patients = [
            p for p in patients if patient_surname 
            in p.patient_surname.lower()
        ]
        
        if not found_patients:
            print("No patients found with that surname.")
            continue_search = get_non_empty_input(
                "Do you want to search again? (y/n): \n"
            ).strip().lower()
            if continue_search != 'y':
                return
        else:
            break

    print(f"Found {len(found_patients)} patients")

    if len(found_patients) == 1:
        selected_patient = found_patients[0]
        print(f"Selected patient: {selected_patient.description()}")
    else:
        print("\nMultiple patients found with that surname.",
        "Please select:"
        )
        for idx, p in enumerate(found_patients, start=1):
            print(f"{idx}. {p.description()}")
        
        while True:
            try:
                patient_choice = int(get_non_empty_input(
                    "Enter the number of the patient you want to select: \n"
                ).strip()) - 1
                if 0 <= patient_choice < len(found_patients):
                    selected_patient = found_patients[patient_choice]
                    print(f"""
                    Selected patient: {selected_patient.description()}
                    """
                    )
                    break
                else:
                    print(
                        f"Invalid selection. Please enter a number between "
                        f"1 and {len(found_patients)}."
                    )
            except ValueError:
                print("Please enter a valid number.")

    print("Patient selection complete")

    # Medication selection
    while True:
        medication_name = get_non_empty_input(
            "Enter the name of the medication required: \n"
        ).strip()
        matching_medications = [
            m for m in medications 
            if medication_name.lower() in m.medication_name.lower()
        ]

        if not matching_medications:
            print("No matching medications found.")
            continue_search = get_non_empty_input(
                "Do you want to search for another medication? (y/n): \n"
            ).strip().lower()
            if continue_search != 'y':
                return
        else:
            break

    print(f"Found {len(matching_medications)} matching medications")

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
                    get_non_empty_input("Enter the medication number: ").strip()
                ) - 1
                if 0 <= med_choice < len(matching_medications):
                    selected_medication = matching_medications[med_choice]
                    print(
                        f"Selected medication: "
                        f"{selected_medication.description()}"
                    )
                    break
                else:
                    print("Invalid selection. Please try again.")
            except ValueError:
                print("Please enter a valid number.")
    
    print("Medication selection complete")

    # Quantity input
    while True:
        try:
            quantity = int(
                get_non_empty_input("Enter the quantity to administer: \n").strip()
            )
            if quantity <= 0:
                print("Please enter a positive number.")
                continue
            if quantity > selected_medication.quantity_in_stock:
                print(
                    f"Error: Not enough {selected_medication.medication_name}"
                    f"in stock. Current stock: "
                    f"{selected_medication.quantity_in_stock}"
                )
                continue
            break
        except ValueError:
            print("Please enter a valid number.")

    print("Quantity input complete")

    # Confirmation and administration
    print(f"""
    Summary:
    Patient: {selected_patient.patient_name} 
    {selected_patient.patient_surname}
    Medication: {selected_medication.medication_name}
    Quantity: {quantity}
    Administering Nurse: {nurse_name}
    """)

    confirm = get_non_empty_input("Confirm administration? (y/n): \n").strip().lower()
    if confirm == 'y':
        if update_inventory(selected_medication, quantity):
            log_administration(
                selected_patient, 
                selected_medication, 
                quantity, 
                nurse_name
            )
            check_low_stock(selected_medication)
        else:
            print("Administration cancelled due to inventory issues.")
    else:
        print("Administration cancelled.")

    print("Administer_medication function completed")


def update_inventory(medication, quantity_administered):
    """
    Update the inventory after medication administration.
    """
    inventory_worksheet = WORKSHEETS["inventory"]
    inventory_data = inventory_worksheet.get_all_records()
    
    for idx, row in enumerate(inventory_data, start=2):
        if row['Medication name'] == medication.medication_name:
            try:
                current_quantity = int(row['Quantity in stock'])
            except ValueError:
                print(f"""
                Error: Invalid quantity in stock for
                {medication.medication_name}.
                """
                )
                return False

            new_quantity = current_quantity - quantity_administered
            
            if new_quantity < 0:
                print(
                    f"""
                    Error: Not enough {medication.medication_name} in stock. 
                    """
                    f"Current stock: {current_quantity}"
                )
                return False
            
            medication.quantity_in_stock = new_quantity
            inventory_worksheet.update(
                f"D{idx}", new_quantity
            )
            
            print(
                f"Inventory updated. New quantity for "
                f"{medication.medication_name}: {new_quantity}"
            )
            return True
    
    print(f"Error: {medication.medication_name} not found in inventory.")
    return False


def check_low_stock(medication):
    """
    Checking stock on hand against reorder level,
    added warning to replenish
    """
    if medication.quantity_in_stock <= medication.reorder_level:
        print(f"""
        WARNING: Low stock for {medication.medication_name}. 
        Current stock: {medication.quantity_in_stock}.
        Reorder level: {medication.reorder_level}.
        """)
        print("Please reorder today.")


def log_administration(patient, medication, quantity, nurse_name):
    """
    Administration Log in, to keep all outgoing medication on patients, and
    through which nurse was the opiate given. Here it will be logged under
    'Medication Administration Logs'
    """
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
    logging.info(f"""
    Access granted for nurse: {current_nurse_name}.
    Proceeding with the application.
    """
    )
    print("Access granted. Proceeding with the application... \n")
    
    while True:
        print("\nMain Menu:")
        print("1. Patient Information System")
        print("2. Medication Inventory System")
        print("3. Administer Medication")
        print("4. Guidelines")
        print("5. Exit")
        choice = get_non_empty_input("Enter your choice (1-5): \n").strip()
        
        if choice == '1':
            patient_information_system()
        elif choice == '2':
            medication_inventory_system()
        elif choice == '3':
            patients = get_patient_info(
                WORKSHEETS["patient_information"]
            )
            medications = get_medication_information(
                WORKSHEETS["inventory"]
            )
            administer_medication(
                patients, medications, current_nurse_name
            )
        elif choice == '4':
            guidelines_system()
        elif choice == '5':
            print("Exiting the application.")
            break
        else:
            print("Invalid choice. Please try again.")


def guidelines_system():
    """Menu for Opitate Medicine guidelines"""
    guidelines = get_guidelines(WORKSHEETS["guidelines"])
    while True:
        print("\nGuidelines Menu:")
        print("1. View all Guidelines")
        print("2. Search Guidelines")
        print("3. Return to Main Menu")
        choice = get_non_empty_input("Enter your choice (1-3): \n")
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
        print(f"\nMedication: {guideline['medication']}")
        print(f"Frequency: {guideline['frequency']}")
        print(f"Special instructions: {guideline['special_instructions']}")


def display_guideline(guideline):
    print(f"\nMedication Name: {guideline['medication_name']}")
    print(
        f"""
        Administration Guidelines: {guideline['administration_guidelines']}
        """
    )
    print(f"Dosage Guidelines: {guideline['dosage_guidelines']}")
    print(f"Intervals: {guideline['intervals']}")
    print(f"Potential Side Effects: {guideline['potential_side_effects']}")
    print(f"Emergency Procedures: {guideline['emergency_procedures']}")
    print(f"Additional Notes: {guideline['additional_notes']}")


def search_guidelines(guidelines):
    search_term = get_non_empty_input(
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

if __name__ == "__main__":
    try:
        welcome()
        main()
    except KeyboardInterrupt:
        logging.warning("Application terminated by user.")
        print(
            "\nApplication terminated by user. Quitting the application..."
        )
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        print(f"An unexpected error occurred: {str(e)}")