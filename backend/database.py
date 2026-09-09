import pymysql
from unidecode import unidecode
from datetime import datetime
import re
from PyQt5.QtCore import pyqtSignal, QObject
import os
import sys
import configparser
import json

# Colors for patient statuses
STATUS_COLORS = {
    # For Triage, Admission Consult and Reassessment
    "Completed": "#69DD45",  # Green
    "Not completed": "#FF0000",  # Red
    "1": "#69DD45",  # Green
    "2": "#69DD45",  # Green
    "3": "#69DD45",  # Green
    "4": "#69DD45",  # Green
    "5": "#69DD45",  # Green

    # For Labs and Imaging
    "Not started": "#FF0000",  # Red
    "Awaiting results": "#FFD900",  # Yellow
    "Results complete": "#69DD45",  # Green

    # For Specialist Consult
    "Not opened": "#FF0000",  # Red
    "Open": "#FFD900",  # Yellow
}

# How long a patient may wait before the cell is flagged with an alarm.
# Triage levels 2 and 3 are flagged when the admission consult has not been
# completed within the department's own service window; patients under
# observation are flagged once they exceed the maximum observation stay.
# Triage 1 is not timed here: it must be seen immediately.
# Triage 4 and 5 are handled by the outpatient priority clinic, not this system.
TRIAGE_2_ALARM_SECONDS = 30 * 60
TRIAGE_3_ALARM_SECONDS = 120 * 60
OBSERVATION_ALARM_SECONDS = 12 * 60 * 60

# Invisible characters that survive a copy and paste from a document or a web
# page. They are never typed on purpose, and a credential carrying one fails to
# authenticate with no visible reason, so they are stripped from what the user
# enters before it is used.
INVISIBLE_CHARACTERS = "​‌‍⁠﻿ "


def clean_input(value):
    """Removes surrounding whitespace and invisible characters from typed input."""
    if not isinstance(value, str):
        return value
    for character in INVISIBLE_CHARACTERS:
        value = value.replace(character, "")
    return value.strip()

class ConfigurationModel:
    """Model for managing the application configuration"""

    @staticmethod
    def get_config_path():
        """Determines the path of the configuration file"""
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        config_path = os.path.join(base_path, 'config.ini')
        print(f"Config file path: {config_path}")
        return config_path

    @classmethod
    def load_configuration(cls):
        """Loads the configuration from the config.ini file"""
        try:
            config_path = cls.get_config_path()

            if not os.path.exists(config_path):
                cls.create_config_file(config_path)

            # Read the configuration
            config = configparser.ConfigParser()
            config.read(config_path)

            # Return the database host
            return config.get('DATABASE', 'host', fallback='localhost')

        except Exception as e:
            print(f"Error loading configuration: {str(e)}")
            return 'localhost'  # Default value in case of error

    @staticmethod
    def create_config_file(config_path):
        """Creates a configuration file with default values"""
        try:
            config = configparser.ConfigParser()
            config['DATABASE'] = {'host': 'localhost'}

            # Add ADMIN section with default credentials
            config['ADMIN'] = {
                'user': 'emergency_admin',
                'password': 'CHANGE_ME_BEFORE_DEPLOYMENT'
            }

            # Add DBA_USERS section for users with administration privileges
            config['DBA_USERS'] = {'users': 'emergency_admin'}

            with open(config_path, 'w') as config_file:
                config.write(config_file)

            return True
        except Exception as e:
            print(f"Error creating configuration file: {str(e)}")
            return False

    @classmethod
    def save_configuration(cls, new_host):
        """Saves the configuration to the config.ini file"""
        try:
            config_path = cls.get_config_path()
            config = configparser.ConfigParser()

            # If the file exists, load the current configuration
            if os.path.exists(config_path):
                config.read(config_path)

            # Make sure the DATABASE section exists
            if 'DATABASE' not in config:
                config['DATABASE'] = {}

            # Update the host
            config['DATABASE']['host'] = new_host

            # Save the configuration
            with open(config_path, 'w') as config_file:
                config.write(config_file)

            return True, ""
        except Exception as e:
            return False, str(e)


class AuthenticationModel:
    """Model for managing user authentication"""

    _credentials = {'user': None, 'password': None, 'workstation': None}

    @classmethod
    def get_credentials(cls):
        """Returns the current credentials"""
        return cls._credentials.copy()

    @classmethod
    def set_server(cls, server):
        """Sets the server in the credentials"""
        cls._credentials['workstation'] = server

    @classmethod
    def validate_credentials(cls, user, password):
        """Validates the user credentials by trying to connect to the database"""
        from backend.users.users_model import UsersModel

        user = clean_input(user)
        password = clean_input(password)

        if not user or not password:
            return False, "Please fill in all the fields before continuing."

        # Validate that the user and password meet the format requirements
        if not UsersModel.validate_username(user):
            return False, "The username is not valid."

        try:
            connection = pymysql.connect(
                host=cls._credentials['workstation'],
                user=user,
                password=password,
                database='urgentix',
                charset='utf8mb4'
            )
            connection.close()

            # Save valid credentials
            cls._credentials['user'] = user
            cls._credentials['password'] = password

            return True, "Valid credentials"

        except pymysql.Error as e:
            return False, f"Error trying to connect: {str(e)}\nPlease check the data you entered."

    @classmethod
    def clear_credentials(cls):
        """Clears the user and password credentials"""
        cls._credentials['user'] = None
        cls._credentials['password'] = None

    @classmethod
    def check_admin_role(cls, username=None):
        """
        Checks whether a user has the administrator role

        Args:
            username: Username to check (or the current user if None)

        Returns:
            bool: True if the user has the administrator role, False otherwise
        """
        from backend.users.users_model import UsersModel

        if username is None and cls._credentials['user'] is not None:
            username = cls._credentials['user']

        if not username:
            return False

        return UsersModel.get_user_role(username) == 'admin'


class PatientModel(QObject):
    data_updated = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.conn = None

    @staticmethod
    def connect():
        credentials = AuthenticationModel.get_credentials()
        return pymysql.connect(
            host=credentials['workstation'],
            user=credentials['user'],
            password=credentials['password'],
            database='urgentix',
            charset='utf8mb4'
        )

        # return pymysql.connect(
        #     host=credentials['workstation'],
        #     user=credentials['user'],
        #     password=credentials['password'],
        #     database='urgentix'
        # )

    def sort_by_admission(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, document_id, triage, admission_consult, labs, imaging, specialist_consult, reassessment, pending_tasks,
                disposition, location, admission, triage_timestamp, id, observation_timestamp
            FROM patients
            ORDER BY admission DESC
        """)
        data = cursor.fetchall()
        conn.close()
        return data

    def get_record_by_document(self, document_id):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM patients WHERE document_id = %s", (document_id,))
        patients = cursor.fetchall()
        conn.close()
        return patients

    def search_patients(self, search_term):
        """
        Searches for patients by name or document id containing the search term

        Args:
            search_term: Term to look for in the name or document id

        Returns:
            list: List of patients matching the criteria
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()

            # Search for patients containing the term in the name or document id
            query = """
                SELECT name, document_id, location, id, admission
                FROM patients
                WHERE LOWER(name) LIKE %s OR LOWER(document_id) LIKE %s
                ORDER BY admission DESC
                LIMIT 20
            """

            parameter = f"%{search_term.lower()}%"
            cursor.execute(query, (parameter, parameter))
            results = cursor.fetchall()
            conn.close()

            return results
        except Exception as e:
            print(f"Error searching for patients: {str(e)}")
            return []

    def check_patient_same_document(self, document_id):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM patients WHERE document_id = %s", (document_id,))
        existing_patient_doc = cursor.fetchone()
        return existing_patient_doc

    def insert_into_db(self, data, location):
        # Validate the name before inserting
        name_validation = self.validate_name(data['name'])
        if name_validation:
            return False, name_validation

        # Validate the document id if it is not an unidentified (NN) patient
        if not data['name'].startswith('NN -'):
            if not data.get('document_id'):
                return False, "The document id is mandatory for identified patients"

        conn = self.connect()
        cursor = conn.cursor()

        # Determine the timestamp based on triage
        triage = data.get('triage', '')
        triage_timestamp = datetime.now() if triage in ["1", "2", "3", "4", "5"] else None

        # Determine the observation timestamp
        observation_timestamp = data.get('observation_timestamp')

        sql = """INSERT INTO patients (name, document_id, triage, triage_timestamp, admission_consult, labs,
                    imaging, specialist_consult, reassessment, pending_tasks, disposition, location, admission, observation_timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)"""
        values = (
            data['name'], data.get('document_id', ''), triage,
            triage_timestamp,
            data.get('admission_consult', '') or "", data.get('labs', '') or "",
            data.get('imaging', '') or "", data.get('specialist_consult', '') or "",
            data.get('reassessment', '') or "", data.get('pending_tasks', ''),
            data.get('disposition', '') or "", location,
            observation_timestamp
        )
        cursor.execute(sql, values)
        # Get the ID of the newly inserted patient
        patient_id = cursor.lastrowid
        conn.commit()

        # Record it in the audit trail
        # Build the change details for the audit trail
        details = []
        if data.get('document_id'):
            details.append(f"Document ID: {data.get('document_id')}")
        if data.get('triage'):
            details.append(f"TRIAGE: {data.get('triage')}")
        if data.get('admission_consult'):
            details.append(f"ADMISSION CONSULT: {data.get('admission_consult')}")
        if data.get('labs'):
            details.append(f"LABS: {data.get('labs')}")
        if data.get('imaging'):
            details.append(f"IMAGING: {data.get('imaging')}")
        if data.get('specialist_consult'):
            details.append(f"SPECIALIST CONSULT: {data.get('specialist_consult')}")
        if data.get('reassessment'):
            details.append(f"REASSESSMENT: {data.get('reassessment')}")
        if data.get('disposition'):
            details.append(f"DISPOSITION: {data.get('disposition')}")
        if data.get('pending_tasks'):
            details.append(f"PENDING TASKS: {data.get('pending_tasks')}")

        # Add the location to the details
        details.append(f"LOCATION: {location}")

        # Log the action in the audit trail
        AuditTrailModel.log_action(
            action="Add patient",
            affected_patient=data['name'],
            change_details=" | ".join(details)
        )

        self.data_updated.emit()
        return True, "Patient saved successfully", patient_id

    def check_patient_same_name_different_document(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT document_id, name FROM patients")
        all_patients = cursor.fetchall()
        return all_patients

    def update_patient_data(self, data, location, record):
        # Validate the name before updating
        name_validation = self.validate_name(data['name'])
        if name_validation:
            return False, name_validation

        # Validate the document id if it is not an unidentified (NN) patient
        if not data['name'].startswith('NN -'):
            if not data.get('document_id'):
                return False, "The document id is mandatory for identified patients"

        conn = self.connect()
        cursor = conn.cursor()

        # Get the current patient information for the console log
        cursor.execute("""
            SELECT name, document_id, triage, admission_consult, labs, imaging, specialist_consult, reassessment, pending_tasks, disposition, triage_timestamp
            FROM patients WHERE id=%s
        """, (record[13],))
        current_data = cursor.fetchone()

        if current_data:
            patient_name = current_data[0]
            patient_document = current_data[1]
            previous_status = {
                'triage': current_data[2],
                'admission_consult': current_data[3],
                'labs': current_data[4],
                'imaging': current_data[5],
                'specialist_consult': current_data[6],
                'reassessment': current_data[7],
                'pending_tasks': current_data[8],
                'disposition': current_data[9]
            }
            previous_triage_timestamp = current_data[10]

            # Print tracking information
            print(f"\n[UPDATING PATIENT] - {patient_name} ({patient_document})")
            print(f"ID: {record[13]}")

            # Show changes in the main statuses
            print("Status changes:")

            # Build the change details for the audit trail
            change_details = []
            for field in ['triage', 'admission_consult', 'labs', 'imaging', 'specialist_consult', 'reassessment', 'disposition']:
                previous_value = previous_status[field]
                new_value = data.get(field, '')
                if previous_value != new_value:
                    print(f"- {field.upper()}: {previous_value or 'empty'}  {new_value or 'empty'}")
                    change_details.append(f"{field.upper()}: {previous_value or 'empty'} → {new_value or 'empty'}")

            # Check whether there are changes in the pending tasks
            previous_pending_tasks = previous_status['pending_tasks'] or ''
            new_pending_tasks = data.get('pending_tasks', '') or ''
            if previous_pending_tasks != new_pending_tasks:
                change_details.append(f"PENDING TASKS: '{previous_pending_tasks}' → '{new_pending_tasks}'")

            # Show changes in the pending tasks if there are any
            print(f"Previous pending tasks: {previous_status['pending_tasks'] or 'None'}")
            print(f"Updated pending tasks: {data.get('pending_tasks', '') or 'None'}")

            # If there are changes, record them in the audit trail
            if change_details:
                details_text = " | ".join(change_details)
                AuditTrailModel.log_action(
                    action="Edit patient",
                    affected_patient=patient_name,
                    change_details=details_text
                )

        # Determine the timestamp based on triage
        current_triage = previous_status.get('triage', '')
        new_triage = data.get('triage', '')

        # Improved logic for the triage timestamp
        triage_timestamp = None

        # Case 1: If the new triage is valid (1-5)
        if new_triage in ["1", "2", "3", "4", "5"]:
            # If it changes from one valid triage to a different valid triage, update the timestamp
            if current_triage in ["1", "2", "3", "4", "5"] and current_triage != new_triage:
                print(f"Updating triage timestamp: change from {current_triage} to {new_triage}")
                triage_timestamp = datetime.now()
            # If it comes from an invalid status to a valid triage, set the timestamp
            elif current_triage not in ["1", "2", "3", "4", "5"]:
                print(f"Setting the initial triage timestamp for value {new_triage}")
                triage_timestamp = datetime.now()
            # If it does not change, keep the existing timestamp
            else:
                triage_timestamp = previous_triage_timestamp
        # Case 2: If it changes to "Not completed" or an invalid value, clear the timestamp
        else:
            triage_timestamp = None
            print("Clearing the triage timestamp because it changed to an invalid value")

        # Check whether the disposition status changed to Observation
        observation_timestamp = None
        if data.get('disposition') == 'Observation':
            # Check whether the previous record was already in Observation
            cursor.execute("SELECT disposition, observation_timestamp FROM patients WHERE id=%s", (record[13],))
            result = cursor.fetchone()
            if result:
                previous_disposition, previous_timestamp = result
                # If it was already in Observation, keep the original timestamp
                if previous_disposition == 'Observation' and previous_timestamp:
                    observation_timestamp = previous_timestamp
                else:
                    # If it is new in Observation, create the timestamp now
                    observation_timestamp = datetime.now()

        sql = """UPDATE patients SET name=%s, triage=%s, triage_timestamp=%s, admission_consult=%s, labs=%s,
                    imaging=%s, specialist_consult=%s, reassessment=%s, pending_tasks=%s, disposition=%s, location=%s, observation_timestamp=%s
                    WHERE id=%s"""
        values = (
            data['name'], new_triage, triage_timestamp,
            data.get('admission_consult', '') or "", data.get('labs', '') or "",
            data.get('imaging', '') or "", data.get('specialist_consult', '') or "",
            data.get('reassessment', '') or "", data.get('pending_tasks', ''),
            data.get('disposition', '') or "", location, observation_timestamp,
            record[13]  # ID is now at index 13
        )
        cursor.execute(sql, values)
        conn.commit()

        # Calculate and store metrics for the updated patient
        patient_id = record[13]
        try:
            # Calculate and store metrics only for this updated patient
            AuditTrailModel.calculate_and_store_metrics(patient_id)
            print(f"Metrics updated for patient ID {patient_id}")
        except Exception as e:
            print(f"Error updating metrics for patient ID {patient_id}: {str(e)}")

        self.data_updated.emit()
        print("Patient updated successfully")
        return True, "Patient updated successfully"

    def update_timestamp(self, patient_id, timestamp_field):
        """
        Updates a specific timestamp for a patient

        Args:
            patient_id (int): Patient ID
            timestamp_field (str): Name of the timestamp field to update

        Returns:
            bool: True if it was updated successfully, False otherwise
        """
        try:
            conn = self.connect()
            if not conn:
                return False

            cursor = conn.cursor()
            current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Validate that the timestamp field exists
            valid_fields = [
                'triage_timestamp',
                'admission_consult_not_done_timestamp', 'admission_consult_done_timestamp',
                'labs_not_done_timestamp', 'labs_requested_timestamp', 'labs_complete_timestamp',
                'imaging_not_done_timestamp', 'imaging_requested_timestamp', 'imaging_complete_timestamp',
                'specialist_consult_not_opened_timestamp', 'specialist_consult_opened_timestamp', 'specialist_consult_done_timestamp',
                'reassessment_not_done_timestamp', 'reassessment_done_timestamp',
                'observation_timestamp', 'discharge_timestamp'
            ]

            if timestamp_field not in valid_fields:
                print(f"Invalid timestamp field: {timestamp_field}")
                return False

            query = f"""
                UPDATE patients
                SET {timestamp_field} = %s
                WHERE id = %s
            """

            cursor.execute(query, (current_timestamp, patient_id))
            conn.commit()
            return True

        except Exception as e:
            print(f"Error updating timestamp: {str(e)}")
            return False
        finally:
            if conn and hasattr(conn, 'close'):
                cursor.close()
                conn.close()

    def update_status_with_timestamp(self, patient_id, status_field, new_status, timestamp_field=None):
        """
        Updates a status and its associated timestamp

        Args:
            patient_id (int): Patient ID
            status_field (str): Name of the status field to update
            new_status (str): New value for the status
            timestamp_field (str, optional): Name of the timestamp field to update.
                If it is not specified, it is inferred from status_field

        Returns:
            bool: True if it was updated successfully, False otherwise
        """
        try:
            conn = self.connect()
            if not conn:
                return False

            cursor = conn.cursor()
            current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # If this is a triage update, check the current value and the new value
            if status_field == 'triage':
                # Only for valid triage values (1-5)
                if new_status in ["1", "2", "3", "4", "5"]:
                    # Get the current triage value
                    cursor.execute("SELECT triage FROM patients WHERE id = %s", (patient_id,))
                    current_triage_result = cursor.fetchone()
                    current_triage = current_triage_result[0] if current_triage_result else None

                    # If it is changing from one valid triage to another, update the timestamp
                    if current_triage in ["1", "2", "3", "4", "5"] and current_triage != new_status:
                        print(f"Updating triage timestamp for patient {patient_id}: change from {current_triage} to {new_status}")
                        query = f"""
                            UPDATE patients
                            SET {status_field} = %s, triage_timestamp = %s
                            WHERE id = %s
                        """
                        cursor.execute(query, (new_status, current_timestamp, patient_id))
                        conn.commit()

                        # Calculate and store metrics immediately
                        AuditTrailModel.calculate_and_store_metrics(patient_id)
                        return True

                    # If this is the first time or it comes from "Not completed", set the timestamp
                    if not current_triage or current_triage not in ["1", "2", "3", "4", "5"]:
                        print(f"Setting a new triage timestamp for patient {patient_id}")
                        query = f"""
                            UPDATE patients
                            SET {status_field} = %s, triage_timestamp = %s
                            WHERE id = %s
                        """
                        cursor.execute(query, (new_status, current_timestamp, patient_id))
                        conn.commit()

                        # Calculate and store metrics immediately
                        AuditTrailModel.calculate_and_store_metrics(patient_id)
                        return True

                    # If the value did not change, only update the triage without changing the timestamp
                    query = f"""
                        UPDATE patients
                        SET {status_field} = %s
                        WHERE id = %s
                    """
                    cursor.execute(query, (new_status, patient_id))
                    conn.commit()

                    # Calculate and store metrics immediately
                    AuditTrailModel.calculate_and_store_metrics(patient_id)
                    return True
                else:
                    # If it is "Not completed" or another invalid value, only update the status without a timestamp
                    query = f"""
                        UPDATE patients
                        SET {status_field} = %s, triage_timestamp = NULL
                        WHERE id = %s
                    """
                    cursor.execute(query, (new_status, patient_id))
                    conn.commit()

                    # Calculate and store metrics immediately
                    AuditTrailModel.calculate_and_store_metrics(patient_id)
                    return True

            # Infer the timestamp field if it is not provided
            if not timestamp_field:
                # Mapping of statuses to their corresponding timestamp fields
                status_timestamp_map = {
                    'triage': {
                        '1': 'triage_timestamp',
                        '2': 'triage_timestamp',
                        '3': 'triage_timestamp',
                        '4': 'triage_timestamp',
                        '5': 'triage_timestamp'
                    },
                    'admission_consult': {
                        'Not completed': 'admission_consult_not_done_timestamp',
                        'Completed': 'admission_consult_done_timestamp'
                    },
                    'labs': {
                        'Not started': 'labs_not_done_timestamp',
                        'Awaiting results': 'labs_requested_timestamp',
                        'Results complete': 'labs_complete_timestamp'
                    },
                    'imaging': {
                        'Not started': 'imaging_not_done_timestamp',
                        'Awaiting results': 'imaging_requested_timestamp',
                        'Results complete': 'imaging_complete_timestamp'
                    },
                    'specialist_consult': {
                        'Not opened': 'specialist_consult_not_opened_timestamp',
                        'Open': 'specialist_consult_opened_timestamp',
                        'Completed': 'specialist_consult_done_timestamp'
                    },
                    'reassessment': {
                        'Not completed': 'reassessment_not_done_timestamp',
                        'Completed': 'reassessment_done_timestamp'
                    },
                    'disposition': {
                        'Observation': 'observation_timestamp',
                        'Discharged': 'discharge_timestamp'
                    }
                }

                # Determine the timestamp field based on the status field and the new value
                if status_field in status_timestamp_map:
                    if isinstance(status_timestamp_map[status_field], dict):
                        # If it is a dictionary, look for the specific field for the new status
                        if new_status in status_timestamp_map[status_field]:
                            timestamp_field = status_timestamp_map[status_field][new_status]
                        else:
                            print(f"No timestamp field was found for status '{status_field}' with value '{new_status}'")
                            # Instead of failing, only update the status without a timestamp
                            query = f"""
                                UPDATE patients
                                SET {status_field} = %s
                                WHERE id = %s
                            """
                            cursor.execute(query, (new_status, patient_id))
                            conn.commit()
                            return True
                    else:
                        # If it is a direct value, use it
                        timestamp_field = status_timestamp_map[status_field]

            if not timestamp_field:
                print(f"The timestamp field could not be inferred for the status: {status_field} = {new_status}")
                # Instead of failing, update only the status
                query = f"""
                    UPDATE patients
                    SET {status_field} = %s
                    WHERE id = %s
                """
                cursor.execute(query, (new_status, patient_id))
                conn.commit()
                return True

            # Update the status and the timestamp
            query = f"""
                UPDATE patients
                SET {status_field} = %s, {timestamp_field} = %s
                WHERE id = %s
            """

            cursor.execute(query, (new_status, current_timestamp, patient_id))
            conn.commit()

            # Calculate and store metrics immediately
            AuditTrailModel.calculate_and_store_metrics(patient_id)

            return True

        except Exception as e:
            print(f"Error updating status with timestamp: {str(e)}")
            return False
        finally:
            if conn and hasattr(conn, 'close'):
                cursor.close()
                conn.close()

    # Position of each status field inside a patient record, in the column order
    # the patient queries select.
    STATUS_RECORD_INDEX = {
        'triage': 2,
        'admission_consult': 4,
        'labs': 5,
        'imaging': 6,
        'specialist_consult': 7,
        'reassessment': 8,
        'disposition': 10,
    }

    def record_status_timestamps(self, patient_id, data, previous_record=None):
        """
        Stamps the transition time of every status this save actually moved.

        The reports measure the gaps between these timestamps, so a view that
        writes the statuses without them leaves its patients out of every metric.
        Keeping the walk over the fields here means a view cannot forget it, and
        the clinical views cannot drift apart on which fields count.

        Args:
            patient_id (int): Patient the statuses belong to
            data (dict): The values being saved
            previous_record (tuple, optional): The record as it was before the
                edit. Omit it when creating a patient, where every status set is
                new. When given, only the fields that actually changed are
                stamped, including those cleared back to an empty value, which
                is what removes a timestamp that no longer applies.
        """
        for field, index in self.STATUS_RECORD_INDEX.items():
            value = data.get(field, '') or ''

            if previous_record is None:
                # Creating: nothing to compare against, and an unset status has
                # no transition to record.
                if not value:
                    continue
            elif value == (previous_record[index] or ''):
                continue

            self.update_status_with_timestamp(patient_id, field, value)

    def validate_name(self, name):
        """
        Validates that the name complies with the established rules:
        - It cannot be empty
        - If it is not an unidentified (NN) patient, it must have at least 3 words

        Returns:
            None if it is valid, an error message if it is not
        """
        if not name.strip():
            return "The patient name is mandatory"

        # Check whether it is an unidentified (NN) patient
        if name.startswith('NN -'):
            return None  # Unidentified (NN) patients are a special case and are allowed

        # Count the words in the name
        words = name.strip().split()

        if len(words) < 3:
            return "The name must have at least three words (given names and surnames)"

        return None  # Valid name

    def process_name(self, name):
        """
        Processes the name to standardize it:
        - Removes extra spaces
        - Removes accents
        - Capitalizes each word
        - If it is empty or has a single word, suggests registering it as unidentified (NN)

        Returns:
            tuple: (processed_name, is_anonymous, message)
                - processed_name: the already processed name
                - is_anonymous: True if it must be registered as unidentified (NN)
                - message: informational message or None
        """
        name = name.strip() if name else ""

        # If it is empty, suggest registering it as anonymous
        if not name:
            return name, True, "The name is empty. It will be registered as anonymous (NN)"

        words = re.split(r'\s+', name)  # Split by any whitespace

        if len(words) == 1:
            # If there is only one word, suggest registering it as anonymous
            return name, True, "The name has only one word. It is suggested to register it as anonymous (NN)"

        # Remove accents and capitalize each word correctly
        normalized_name = ' '.join(word.capitalize() for word in [unidecode(w) for w in words])

        return normalized_name, False, None

    def create_unidentified_name(self):
        """Creates a name for an anonymous patient with the current date and time"""
        current_datetime = datetime.now().strftime("%Y-%m-%d - %H:%M:%S")
        return f"NN - {current_datetime}"

    @staticmethod
    def normalize_text(text):
        """Normalizes a text to a standard format"""
        from unidecode import unidecode
        if not text:
            return text

        normalized_text = unidecode(text.lower())
        return ' '.join(word.capitalize() for word in normalized_text.split())

    @staticmethod
    def compare_names(name1, name2):
        """Compares two names by removing spaces and accents and converting to lowercase"""
        if not name1 or not name2:
            return False

        name1 = unidecode(name1.lower().replace(" ", ""))
        name2 = unidecode(name2.lower().replace(" ", ""))
        return name1 == name2

    def delete(self, record_id):
        conn = self.connect()
        cursor = conn.cursor()

        # Get the patient information before deleting it for the audit trail
        cursor.execute("SELECT name, document_id FROM patients WHERE id = %s", (record_id,))
        patient_info = cursor.fetchone()

        if patient_info:
            patient_name = patient_info[0]
            patient_document = patient_info[1]

            # Delete the patient
            sql = "DELETE FROM patients WHERE id = %s"
            cursor.execute(sql, (record_id,))
            conn.commit()

            # Record it in the audit trail
            details = f"Document ID: {patient_document}"
            AuditTrailModel.log_action(
                action="Delete patient",
                affected_patient=patient_name,
                change_details=details
            )

            print(f"Patient deleted: {patient_name} ({patient_document})")
        else:
            # If the patient was not found, only run the deletion
            sql = "DELETE FROM patients WHERE id = %s"
            cursor.execute(sql, (record_id,))
            conn.commit()
            print(f"Record with ID {record_id} deleted (no patient information was found)")

        cursor.close()
        conn.close()
        self.data_updated.emit()

    def close_db(self):
        """Closes the database connection if it is open"""
        try:
            if hasattr(self, 'conn') and self.conn:
                self.conn.close()
                self.conn = None
        except Exception as e:
            print(f"Error closing the connection: {e}")

    def validate_patient_status(self, data):
        """
        Validates that the statuses of a patient are consistent according to the business rules.

        Rules:
        1. Admission consult cannot be 'Completed' if there is no triage level
        2. Specialist consult cannot be 'Open'/'Completed' if admission consult/triage/labs/imaging are not completed
        3. Reassessment cannot be 'Completed' if specialist consult/labs/imaging/admission consult/triage are not completed
        4. A patient cannot be discharged if not all the processes are completed

        Args:
            data: Dictionary with the patient data

        Returns:
            str: Error message if there are inconsistencies, None if everything is valid
        """
        statuses = {
            'triage': data.get('triage', ''),
            'admission_consult': data.get('admission_consult', ''),
            'labs': data.get('labs', ''),
            'imaging': data.get('imaging', ''),
            'specialist_consult': data.get('specialist_consult', ''),
            'reassessment': data.get('reassessment', ''),
            'disposition': data.get('disposition', '')
        }

        # 1. Checks based on Triage
        if statuses['triage'] not in ["1", "2", "3", "4", "5"]:
            # Admission consult cannot be 'Completed' if there is no triage level
            if statuses['admission_consult'] == 'Completed':
                return "Admission consult cannot be 'Completed' if the triage level has not been set."

            # No other process can move forward if there is no triage
            restricted_fields = ['labs', 'imaging', 'specialist_consult', 'reassessment']
            for field in restricted_fields:
                if statuses[field] in ['Results complete', 'Open', 'Completed', 'Completed', 'Awaiting results']:
                    return f"The other processes cannot have statuses if the triage is not completed. Error in {field.upper()}."

        # 2. Checks based on Admission Consult
        if statuses['admission_consult'] != 'Completed':
            restricted_fields = ['labs', 'imaging', 'specialist_consult', 'reassessment']
            for field in restricted_fields:
                if statuses[field] in ['Results complete', 'Open', 'Completed', 'Completed', 'Awaiting results']:
                    return f"The procedure cannot be in progress or completed because the admission consult is not finished. Error in {field.upper()}."

        # 3. Checks based on Specialist Consult
        if statuses['specialist_consult'] in ['Open', 'Completed']:
            # Check that admission consult and triage are completed
            if statuses['triage'] not in ["1", "2", "3", "4", "5"]:
                return "Specialist consult cannot be 'Open' or 'Completed' if the triage level has not been set."
            if statuses['admission_consult'] != 'Completed':
                return "Specialist consult cannot be 'Open' or 'Completed' if the admission consult is not completed."
            # Check that at least one exam (labs or imaging) is in progress or completed
            if (statuses['labs'] != 'Results complete' and
                statuses['imaging'] != 'Results complete'):
                # statuses['imaging'] not in ['Awaiting results', 'Results complete'])
                return "Specialist consult cannot be 'Open' or 'Completed' if at least one exam (Labs or Imaging) has not been completed."

        # 4. Checks based on Reassessment
        if statuses['reassessment'] == 'Completed':
            # For reassessment, check that all the previous processes are completed
            if statuses['triage'] not in ["1", "2", "3", "4", "5"]:
                return "Reassessment cannot be 'Completed' if the triage level has not been set."
            if statuses['admission_consult'] != 'Completed':
                return "Reassessment cannot be 'Completed' if the admission consult is not completed."
            if statuses['specialist_consult'] != 'Completed':
                return "Reassessment cannot be 'Completed' if the specialist consult is not completed."
            # Check that at least one exam is complete
            if (statuses['labs'] != 'Results complete' and
                statuses['imaging'] != 'Results complete'):
                return "Reassessment cannot be 'Completed' if at least one exam (Labs or Imaging) has not been completed."

        # 5. Check for the "Discharged" status
        if statuses['disposition'] == 'Discharged':
            # Check triage and admission consult
            if statuses['triage'] not in ["1", "2", "3", "4", "5"]:
                return "The patient cannot be discharged if the triage level has not been set."
            if statuses['admission_consult'] != 'Completed':
                return "The patient cannot be discharged if the admission consult is not completed."

            # Check that the specialist consult is completed
            if statuses['specialist_consult'] == 'Not opened':
                return "The patient cannot be discharged if a specialist consult has not been opened."
            elif statuses['specialist_consult'] == 'Open':
                return "The patient cannot be discharged if the specialist consult is open but not completed."

            # Check that the reassessment is completed
            if statuses['reassessment'] != 'Completed':
                return "The patient cannot be discharged if the reassessment is not completed."

            # Check that at least one type of exam has complete results
            if statuses['labs'] != 'Results complete' and statuses['imaging'] != 'Results complete':
                return "The patient cannot be discharged without at least one complete result (Labs or Imaging)."

            # Check that neither labs nor imaging are in intermediate statuses
            if statuses['labs'] == 'Awaiting results':
                return "The patient cannot be discharged while Labs is awaiting results."
            if statuses['imaging'] == 'Awaiting results':
                return "The patient cannot be discharged while Imaging is awaiting results."

        # If all the validations pass
        return None

    def check_alarms(self, data):
        """
        Checks the alarm conditions for the patients.
        Returns a set of tuples (row_idx, col_idx) representing the cells with an alarm.

        Args:
            data: List of patient records

        Returns:
            set: Set of tuples (row_idx, col_idx) with the cells that must have an alarm
        """
        alarm_cells = set()

        for row_idx, row in enumerate(data):
            triage = row[2]  # Triage index
            admission_consult = row[3]      # Admission consult index
            triage_timestamp = row[12]  # Triage timestamp index

            # Check the alarm conditions
            if triage in ['2', '3'] and admission_consult == 'Not completed' and triage_timestamp:
                now = datetime.now()
                if isinstance(triage_timestamp, datetime):
                    elapsed_time = (now - triage_timestamp).total_seconds()

                    # Alarm for triage 2: more than 30 minutes without admission consult
                    # Alarm for triage 3: more than 120 minutes without admission consult
                    if (triage == '2' and elapsed_time >= TRIAGE_2_ALARM_SECONDS) or \
                       (triage == '3' and elapsed_time >= TRIAGE_3_ALARM_SECONDS):
                        admission_consult_col = 3  # Index of the Admission Consult column
                        alarm_cells.add((row_idx, admission_consult_col))

        return alarm_cells

    def check_disposition_alarm(self, data):
        """
        Checks the alarm conditions for patients in Observation status.
        Returns a set of tuples (row_idx, col_idx) representing the cells with an alarm.

        Args:
            data: List of patient records

        Returns:
            set: Set of tuples (row_idx, col_idx) with the cells that must have an alarm
        """
        disposition_alarm_cells = set()

        for row_idx, row in enumerate(data):
            disposition = row[9]       # Disposition index
            observation_timestamp = None   # Timestamp specific to observation

            # Check whether we have the observation_timestamp field in the data
            if len(row) > 14:
                observation_timestamp = row[14]

            # Check the alarm conditions for disposition
            if disposition == "Observation" and observation_timestamp:
                now = datetime.now()
                if isinstance(observation_timestamp, datetime):
                    elapsed_time = (now - observation_timestamp).total_seconds()

                    if elapsed_time >= OBSERVATION_ALARM_SECONDS:
                        disposition_col = 9  # Index of the Disposition column
                        disposition_alarm_cells.add((row_idx, disposition_col))

        return disposition_alarm_cells

    def get_colors(self):
        """Get the colors for the different statuses, including the triage levels."""
        colors = {
            # Triage keeps its own scale, agreed with the department's clinicians,
            # so a level is read by hue as well as by the digit drawn on the circle.
            "1": "#663300",                    # Brown, triage 1
            "2": "#660066",                    # Purple, triage 2
            "3": "#3b82f6",                    # Light blue, triage 3
            "4": "#8b5cf6",                    # Violet, triage 4
            "5": "#ec4899",                    # Pink, triage 5
            # The remaining stages share one traffic light: red not started,
            # yellow in progress, green resolved.
            "Not completed": "#CC0000",        # Red, stage not done
            "Completed": "#00D000",            # Green, stage done
            "Not started": "#CC0000",          # Red, labs/imaging not started
            "Awaiting results": "#FFCC00",     # Yellow, results pending
            "Results complete": "#00D000",     # Green, every result in
            "Not opened": "#CC0000",           # Red, specialist consult not opened
            "Open": "#FFCC00",                 # Yellow, specialist consult open
        }
        return colors

    def get_filtered_patient_data(self, selected_areas=None, start_date=None, end_date=None):
        """
        Gets patient data filtered by specific areas and/or a date range.

        Args:
            selected_areas: List of selected areas
            start_date: Start date of the range (format: 'YYYY-MM-DD HH:MM:SS')
            end_date: End date of the range (format: 'YYYY-MM-DD HH:MM:SS')

        Returns:
            list: List of filtered patient records
        """
        conn = self.connect()
        cursor = conn.cursor()

        # Build the WHERE conditions based on the filters
        conditions = []

        # Filter by areas
        if selected_areas and len(selected_areas) > 0:
            area_conditions = []
            for area in selected_areas:
                area_conditions.append(f"location LIKE '{area}%'")

            if area_conditions:
                conditions.append("(" + " OR ".join(area_conditions) + ")")

        # Filter by date
        if start_date and end_date:
            conditions.append(f"admission BETWEEN '{start_date}' AND '{end_date}'")

        query = """
            SELECT name, document_id, triage, admission_consult, labs, imaging, specialist_consult, reassessment, pending_tasks,
                disposition, location, admission, triage_timestamp, id, observation_timestamp
            FROM patients
        """

        # Add the WHERE conditions if they exist
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        # Sort by admission date descending
        query += " ORDER BY admission DESC"

        # Run the query
        cursor.execute(query)
        data = cursor.fetchall()
        conn.close()

        return data

    def save_patient_data(self, data, location):
        """
        Main method to save a new patient in the database.
        This function validates the data and delegates the insertion to the insert_into_db method.

        Args:
            data: Dictionary with the patient data
            location: String with the patient location (area - cubicle)

        Returns:
            tuple: (success, message) where success is a boolean and message is a string
        """
        try:
            # Validate the name before inserting
            name_validation = self.validate_name(data['name'])
            if name_validation:
                return False, name_validation

            # Validate the patient status
            status_validation = self.validate_patient_status(data)
            if status_validation:
                return False, status_validation

            # Record the observation timestamp if applicable
            if data.get('disposition') == 'Observation':
                data['observation_timestamp'] = datetime.now()
            else:
                data['observation_timestamp'] = None

            # Insert into the database
            return self.insert_into_db(data, location)
        except Exception as e:
            return False, f"Error saving patient: {str(e)}", None

    def get_patient_labs(self, patient_id):
        """Gets the labs associated with a patient"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT l.lab_code, l.lab_name, pl.status
            FROM patient_labs pl
            JOIN lab_catalog l ON pl.lab_code = l.lab_code
            WHERE pl.patient_id = %s
        """, (patient_id,))
        labs = cursor.fetchall()
        conn.close()
        return labs

    def save_patient_labs(self, patient_id, labs):
        """
        Saves the labs associated with a patient and updates the pending tasks.
        Validates that there is consistency between the Labs status and the selected labs.

        Args:
            patient_id: Patient ID
            labs: List with the lab codes to save

        Returns:
            tuple: (success, message) where success is a boolean and message is a string
        """
        # First check whether triage and admission consult are completed
        conn = self.connect()
        cursor = conn.cursor()

        # Get the patient information for the console log
        cursor.execute("SELECT name, document_id, triage, admission_consult, labs FROM patients WHERE id = %s", (patient_id,))
        result = cursor.fetchone()

        if not result:
            conn.close()
            return False, "The patient was not found"

        patient_name = result[0]
        patient_document = result[1]
        triage, admission_consult, labs_status = result[2], result[3], result[4]

        # Print tracking information
        print(f"\n[SAVING LABS] - {patient_name} ({patient_document})")
        print(f"ID: {patient_id}")
        print(f"Current status: Triage={triage}, Admission Consult={admission_consult}, Labs={labs_status}")
        print(f"Labs to save: {len(labs)}")

        # Validate that triage and admission consult are completed
        if triage not in ["1", "2", "3", "4", "5"] or admission_consult != "Completed":
            print(f"Error: Triage and admission consult must be completed before associating labs")
            conn.close()
            return False, "Triage and admission consult must be completed before associating labs"

        # Consistency validation between the Labs status and the selected labs
        valid_statuses = ["Not started", "Awaiting results", "Results complete"]

        # ✅ If there are labs but a valid status has not been set
        if labs and (not labs_status or labs_status not in valid_statuses):
            print(f"Error: You must set a valid status in Labs when you select labs")
            conn.close()
            return False, "You must set a valid status in Labs when you select labs"

        # ✅ If there is a valid status but no labs have been selected
        if not labs and labs_status in valid_statuses:
            print(f"Error: You selected a status for Labs but you did not add any lab")
            conn.close()
            return False, "You selected a status for Labs but you did not add any lab"

        # If there are no labs and there is no status, simply delete the old associations
        if not labs and (not labs_status or labs_status not in valid_statuses):
            cursor.execute("DELETE FROM patient_labs WHERE patient_id = %s", (patient_id,))
            # Update the status in the patients table to empty if it has any value
            if labs_status:
                cursor.execute("UPDATE patients SET labs = '' WHERE id = %s", (patient_id,))
            conn.commit()
            conn.close()
            AuditTrailModel.log_action(
                action="Update labs",
                affected_patient=patient_name,
                change_details="Laboratory orders cleared and the stage status reset"
            )
            print("No labs were associated (existing associations were deleted)")
            return True, "No labs were associated"

        # Continue with the normal lab insertion procedure
        cursor.execute("DELETE FROM patient_labs WHERE patient_id = %s", (patient_id,))

        # Get the lab details to show in the console
        lab_details = []

        # Insert the new labs
        for lab_code in labs:
            # Get the lab name to show in the console
            cursor.execute("SELECT lab_name FROM lab_catalog WHERE lab_code = %s", (lab_code,))
            lab_info = cursor.fetchone()
            lab_name = lab_info[0] if lab_info else lab_code

            cursor.execute("""
                INSERT INTO patient_labs (patient_id, lab_code)
                VALUES (%s, %s)
            """, (patient_id, lab_code))

            lab_details.append(f"{lab_code} - {lab_name}")

        conn.commit()

        # Print the details of the saved labs
        print(f"Saved labs:")
        for detail in lab_details:
            print(f"  - {detail}")

        # Get the current Labs status
        cursor.execute("SELECT labs FROM patients WHERE id = %s", (patient_id,))
        result = cursor.fetchone()
        labs_current_status = result[0] if result else ""

        conn.close()

        # Ordering an exam is a clinical decision, so the log names the exams
        # themselves rather than only recording that the list changed.
        AuditTrailModel.log_action(
            action="Update labs",
            affected_patient=patient_name,
            change_details=f"LABS: {labs_current_status or 'no status'} | "
                           f"{len(lab_details)} ordered: {', '.join(lab_details)}"
        )

        # Update the pending tasks automatically according to the Labs status
        print(f"Updating pending tasks for Labs with status: {labs_current_status}")
        self.update_pending_tasks_for_labs(patient_id, labs_current_status)

        self.data_updated.emit()
        print("Labs saved successfully")
        return True, "Labs saved successfully"

    def get_patient_imaging(self, patient_id):
        """Gets the imaging exams associated with a patient"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT i.imaging_code, i.imaging_name, pi.status
            FROM patient_imaging pi
            JOIN imaging_catalog i ON pi.imaging_code = i.imaging_code
            WHERE pi.patient_id = %s
        """, (patient_id,))
        imaging = cursor.fetchall()
        conn.close()
        return imaging

    def update_pending_tasks_column(self, patient_id, pending_tasks_text):
        """
        Updates the pending tasks column for a specific patient.

        Args:
            patient_id: ID of the patient to update
            pending_tasks_text: Text with the updated pending tasks

        Returns:
            bool: True if the update was successful, False otherwise
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()

            # Get the patient name for the console log
            cursor.execute("SELECT name, document_id FROM patients WHERE id = %s", (patient_id,))
            patient_info = cursor.fetchone()
            patient_name = patient_info[0] if patient_info else f"Patient ID: {patient_id}"
            patient_document = patient_info[1] if patient_info else "Unknown"

            # Update the pending tasks field in the main table
            cursor.execute("""
                UPDATE patients
                SET pending_tasks = %s
                WHERE id = %s
            """, (pending_tasks_text, patient_id))

            conn.commit()

            # Check whether any changes were made
            if cursor.rowcount > 0:
                print(f"\n[PENDING TASKS UPDATED] - {patient_name} ({patient_document})")
                print(f"ID: {patient_id}")
                print(f"Pending tasks: {pending_tasks_text}")
                # Emit the data updated signal to refresh the interface
                self.data_updated.emit()
                return True
            else:
                print(f"No patient was found with ID: {patient_id}")
                return False

        except Exception as e:
            print(f"Error updating pending tasks: {str(e)}")
            return False
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    def calculate_pending_tasks_auto(self, patient_id):
        """
        Automatically calculates the pending tasks based on the status of other fields
        and the labs and imaging exams assigned to the patient.

        Args:
            patient_id: Patient ID

        Returns:
            str: Calculated pending tasks text
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()

            # Get the relevant patient data
            cursor.execute("""
                SELECT triage, admission_consult, labs, imaging, specialist_consult, reassessment, pending_tasks
                FROM patients
                WHERE id = %s
            """, (patient_id,))

            result = cursor.fetchone()

            if not result:
                return ""

            triage, admission_consult, labs_status, imaging_status, specialist_consult, reassessment, current_pending_tasks = result
            pending_tasks = []

            if current_pending_tasks:
                # List of specific automatic pending tasks that will be regenerated
                automatic_pending_tasks = [
                    "Pending admission consult", "Open specialist consult", "Specialist consult response",
                    "Perform reassessment", "Perform triage"
                ]

                # Filter the pending tasks removing all the automatic ones and those related to labs/imaging
                custom_pending_tasks = []
                for pending_task in current_pending_tasks.split(", "):
                    # Remove any pending task containing the word "Labs"
                    if not pending_task.startswith("Labs pending:") and "Labs" not in pending_task:
                        # Remove any pending task containing the word "Imaging"
                        if not pending_task.startswith("Imaging pending:") and "Imaging" not in pending_task and "Imaging results" not in pending_task:
                            # Check whether it is a specific automatic pending task
                            is_automatic = any(auto_task in pending_task for auto_task in automatic_pending_tasks)

                            # Check whether it is related to labs/imaging
                            is_lab_img = pending_task.startswith("Labs pending:") or pending_task.startswith("Imaging pending:")

                            if not is_automatic and not is_lab_img:
                                cursor.execute("""
                                    SELECT COUNT(*) FROM (
                                        SELECT lab_name AS name FROM lab_catalog
                                        WHERE lab_name = %s
                                        UNION
                                        SELECT imaging_name AS name FROM imaging_catalog
                                        WHERE imaging_name = %s
                                    ) AS combined
                                """, (pending_task, pending_task))

                                check_result = cursor.fetchone()
                                is_lab_img_item = check_result[0] > 0 if check_result else False

                                # Only add it if it is not a lab or imaging item
                                if not is_lab_img_item:
                                    custom_pending_tasks.append(pending_task)

                # Update the pending tasks list with only the custom non-automatic ones
                pending_tasks = custom_pending_tasks

            # 1. Triage pending
            if triage in ["", "Not completed"] and "Perform triage" not in pending_tasks:
                pending_tasks.append("Perform triage")

            # 2. Admission consult pending (only if there is triage)
            if triage not in ["", "Not completed"] and admission_consult == "Not completed" and "Pending admission consult" not in pending_tasks:
                pending_tasks.append("Pending admission consult")

            # 3. If the admission consult is completed, check the other pending tasks
            if admission_consult == "Completed":
                # 4. Check the specialist consult pending tasks
                if specialist_consult in ["Not opened", "Open"]:
                    pending_task_text = "Open specialist consult" if specialist_consult == "Not opened" else "Specialist consult response"
                    if pending_task_text not in pending_tasks:
                        pending_tasks.append(pending_task_text)

                # 5. Check the reassessment pending tasks
                if reassessment == "Not completed" and "Perform reassessment" not in pending_tasks:
                    pending_tasks.append("Perform reassessment")

            # 7. Process the pending labs - Unique and sorted list
            pending_labs_list = []
            if admission_consult == "Completed" and labs_status in ["Not started", "Awaiting results"]:
                cursor.execute("""
                    SELECT DISTINCT l.lab_name
                    FROM patient_labs pl
                    JOIN lab_catalog l ON pl.lab_code = l.lab_code
                    WHERE pl.patient_id = %s
                    ORDER BY l.lab_name
                """, (patient_id,))

                pending_labs = cursor.fetchall()

                if pending_labs:
                    # Extract the lab names and create a unique list
                    pending_labs_list = sorted(set(lab[0] for lab in pending_labs))

            # 8. Process the pending imaging exams - Unique and sorted list
            pending_imaging_list = []
            if admission_consult == "Completed" and imaging_status in ["Not started", "Awaiting results"]:
                cursor.execute("""
                    SELECT DISTINCT i.imaging_name
                    FROM patient_imaging pi
                    JOIN imaging_catalog i ON pi.imaging_code = i.imaging_code
                    WHERE pi.patient_id = %s
                    ORDER BY i.imaging_name
                """, (patient_id,))

                pending_imaging = cursor.fetchall()

                if pending_imaging:
                    # Extract the imaging names and create a unique list
                    pending_imaging_list = sorted(set(img[0] for img in pending_imaging))

            # Add the pending labs and imaging exams if they exist
            if pending_labs_list:
                pending_tasks.append(f"Labs pending: {', '.join(pending_labs_list)}")

            if pending_imaging_list:
                pending_tasks.append(f"Imaging pending: {', '.join(pending_imaging_list)}")

            return ", ".join(pending_tasks)

        except Exception as e:
            print(f"Error calculating the automatic pending tasks: {str(e)}")
            return ""
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    def save_patient_imaging(self, patient_id, imaging):
        """
        Saves the imaging exams associated with a patient and updates the pending tasks.
        Validates that there is consistency between the Imaging status and the selected imaging exams.

        Args:
            patient_id: Patient ID
            imaging: List with the imaging codes to save

        Returns:
            tuple: (success, message) where success is a boolean and message is a string
        """
        # First check whether triage and admission consult are completed
        conn = self.connect()
        cursor = conn.cursor()

        # Get the patient information for the console log
        cursor.execute("SELECT name, document_id, triage, admission_consult, imaging FROM patients WHERE id = %s", (patient_id,))
        result = cursor.fetchone()

        if not result:
            conn.close()
            return False, "The patient was not found"

        patient_name = result[0]
        patient_document = result[1]
        triage, admission_consult, imaging_status = result[2], result[3], result[4]

        # Print tracking information
        print(f"\n[SAVING IMAGING] - {patient_name} ({patient_document})")
        print(f"ID: {patient_id}")
        print(f"Current status: Triage={triage}, Admission Consult={admission_consult}, Imaging={imaging_status}")
        print(f"Imaging exams to save: {len(imaging)}")

        # Validate that triage and admission consult are completed
        if triage not in ["1", "2", "3", "4", "5"] or admission_consult != "Completed":
            print(f"Error: Triage and admission consult must be completed before associating imaging exams")
            conn.close()
            return False, "Triage and admission consult must be completed before associating imaging exams"

        # Consistency validation between the Imaging status and the selected imaging exams
        valid_statuses = ["Not started", "Awaiting results", "Results complete"]

        # ✅ If there are imaging exams but a valid status has not been set
        if imaging and (not imaging_status or imaging_status not in valid_statuses):
            print(f"Error: You must set a valid status in Imaging when you select imaging exams")
            conn.close()
            return False, "You must set a valid status in Imaging when you select imaging exams"

        # ✅ If there is a valid status but no imaging exams have been selected
        if not imaging and imaging_status in valid_statuses:
            print(f"Error: You selected a status for Imaging but you did not add any imaging exam")
            conn.close()
            return False, "You selected a status for Imaging but you did not add any imaging exam"

        # If there are no imaging exams and there is no status, simply delete the old associations
        if not imaging and (not imaging_status or imaging_status not in valid_statuses):
            cursor.execute("DELETE FROM patient_imaging WHERE patient_id = %s", (patient_id,))
            # Update the status in the patients table to empty if it has any value
            if imaging_status:
                cursor.execute("UPDATE patients SET imaging = '' WHERE id = %s", (patient_id,))
            conn.commit()
            conn.close()
            AuditTrailModel.log_action(
                action="Update imaging",
                affected_patient=patient_name,
                change_details="Imaging orders cleared and the stage status reset"
            )
            print("No imaging exams were associated (existing associations were deleted)")
            return True, "No imaging exams were associated"

        # Continue with the normal imaging insertion procedure
        cursor.execute("DELETE FROM patient_imaging WHERE patient_id = %s", (patient_id,))

        # Get the imaging details to show in the console
        imaging_details = []

        # Insert the new imaging exams
        for imaging_code in imaging:
            # Get the imaging name to show in the console
            cursor.execute("SELECT imaging_name FROM imaging_catalog WHERE imaging_code = %s", (imaging_code,))
            imaging_info = cursor.fetchone()
            imaging_name = imaging_info[0] if imaging_info else imaging_code

            cursor.execute("""
                INSERT INTO patient_imaging (patient_id, imaging_code)
                VALUES (%s, %s)
            """, (patient_id, imaging_code))

            imaging_details.append(f"{imaging_code} - {imaging_name}")

        conn.commit()

        # Print the details of the saved imaging exams
        print(f"Saved imaging exams:")
        for detail in imaging_details:
            print(f"  - {detail}")

        # Get the current Imaging status
        cursor.execute("SELECT imaging FROM patients WHERE id = %s", (patient_id,))
        result = cursor.fetchone()
        imaging_current_status = result[0] if result else ""

        conn.close()

        AuditTrailModel.log_action(
            action="Update imaging",
            affected_patient=patient_name,
            change_details=f"IMAGING: {imaging_current_status or 'no status'} | "
                           f"{len(imaging_details)} ordered: {', '.join(imaging_details)}"
        )

        # Update the pending tasks automatically according to the Imaging status
        print(f"Updating pending tasks for Imaging with status: {imaging_current_status}")
        self.update_pending_tasks_for_imaging(patient_id, imaging_current_status)

        self.data_updated.emit()
        print("Imaging exams saved successfully")
        return True, "Imaging exams saved successfully"

    def update_pending_tasks_for_labs(self, patient_id, labs_status):
        """
        Updates the pending tasks based on the Labs status

        Args:
            patient_id: Patient ID
            labs_status: Current status of the Labs field

        Returns:
            bool: True if the update was successful, False otherwise
        """
        try:
            # If Labs is complete, remove the pending tasks related to labs
            if labs_status == "Results complete":
                conn = self.connect()
                cursor = conn.cursor()

                # Get the current pending tasks
                cursor.execute("SELECT pending_tasks FROM patients WHERE id = %s", (patient_id,))
                result = cursor.fetchone()
                current_pending_tasks = result[0] if result and result[0] else ""

                # Filter the pending tasks to remove those related to labs
                filtered_pending_tasks = []
                for pending_task in current_pending_tasks.split(", "):
                    # Remove any pending task containing the word "Labs"
                    if not pending_task.startswith("Labs pending:") and "Labs" not in pending_task:
                        filtered_pending_tasks.append(pending_task)

                new_pending_tasks = ", ".join(filtered_pending_tasks)

                # Update the pending tasks
                cursor.execute("UPDATE patients SET pending_tasks = %s WHERE id = %s",
                              (new_pending_tasks, patient_id))
                conn.commit()
                conn.close()
                self.data_updated.emit()
                return True
            else:
                # If Labs is not complete, recalculate the pending tasks
                new_pending_tasks = self.calculate_pending_tasks_auto(patient_id)
                return self.update_pending_tasks_column(patient_id, new_pending_tasks)

        except Exception as e:
            print(f"Error updating the pending tasks according to the Labs status: {str(e)}")
            return False

    def update_pending_tasks_for_imaging(self, patient_id, imaging_status):
        """
        Updates the pending tasks based on the Imaging status

        Args:
            patient_id: Patient ID
            imaging_status: Current status of the Imaging field

        Returns:
            bool: True if the update was successful, False otherwise
        """
        try:
            # If Imaging is complete, remove the pending tasks related to imaging exams
            if imaging_status == "Results complete":
                conn = self.connect()
                cursor = conn.cursor()

                # Get the current pending tasks
                cursor.execute("SELECT pending_tasks FROM patients WHERE id = %s", (patient_id,))
                result = cursor.fetchone()
                current_pending_tasks = result[0] if result and result[0] else ""

                # Filter the pending tasks to remove those related to imaging exams
                filtered_pending_tasks = []
                for pending_task in current_pending_tasks.split(", "):
                    # Remove any pending task containing the word "Imaging"
                    if not pending_task.startswith("Imaging pending:") and "Imaging" not in pending_task and "Imaging results" not in pending_task:
                        filtered_pending_tasks.append(pending_task)

                new_pending_tasks = ", ".join(filtered_pending_tasks)

                # Update the pending tasks
                cursor.execute("UPDATE patients SET pending_tasks = %s WHERE id = %s",
                              (new_pending_tasks, patient_id))
                conn.commit()
                conn.close()
                self.data_updated.emit()
                return True
            else:
                # If Imaging is not complete, recalculate the pending tasks
                new_pending_tasks = self.calculate_pending_tasks_auto(patient_id)
                return self.update_pending_tasks_column(patient_id, new_pending_tasks)

        except Exception as e:
            print(f"Error updating the pending tasks according to the Imaging status: {str(e)}")
            return False

    def update_pending_tasks_for_admission_consult(self, patient_id, admission_consult_status):
        """
        Updates the pending tasks based on the Admission Consult status

        Args:
            patient_id: Patient ID
            admission_consult_status: Current status of the Admission Consult field

        Returns:
            bool: True if the update was successful, False otherwise
        """
        try:
            # If the admission consult is Completed, remove the related pending task
            if admission_consult_status == "Completed":
                conn = self.connect()
                cursor = conn.cursor()

                # Get the current pending tasks
                cursor.execute("SELECT pending_tasks FROM patients WHERE id = %s", (patient_id,))
                result = cursor.fetchone()
                current_pending_tasks = result[0] if result and result[0] else ""

                # Filter the pending tasks to remove those related to the admission consult
                filtered_pending_tasks = []
                for pending_task in current_pending_tasks.split(", "):
                    if pending_task and pending_task != "Pending admission consult":
                        filtered_pending_tasks.append(pending_task)

                new_pending_tasks = ", ".join(filtered_pending_tasks)

                # Update the pending tasks
                cursor.execute("UPDATE patients SET pending_tasks = %s WHERE id = %s",
                              (new_pending_tasks, patient_id))
                conn.commit()
                conn.close()
                self.data_updated.emit()
                return True
            else:
                # If the admission consult is not completed, update the pending tasks accordingly
                new_pending_tasks = self.calculate_pending_tasks_auto(patient_id)
                return self.update_pending_tasks_column(patient_id, new_pending_tasks)

        except Exception as e:
            print(f"Error updating the pending tasks according to the Admission Consult status: {str(e)}")
            return False

    def update_pending_tasks_for_triage(self, patient_id, triage_status):
        """
        Updates the pending tasks based on the triage status

        Args:
            patient_id: Patient ID
            triage_status: Current status of the triage field

        Returns:
            bool: True if the update was successful, False otherwise
        """
        try:
            # If the triage is set (it has a level), remove the related pending task
            if triage_status in ["1", "2", "3", "4", "5"]:
                conn = self.connect()
                cursor = conn.cursor()

                # Get the current pending tasks
                cursor.execute("SELECT pending_tasks FROM patients WHERE id = %s", (patient_id,))
                result = cursor.fetchone()
                current_pending_tasks = result[0] if result and result[0] else ""

                # Filter the pending tasks to remove those related to triage
                filtered_pending_tasks = []
                for pending_task in current_pending_tasks.split(", "):
                    if pending_task and pending_task != "Perform triage":
                        filtered_pending_tasks.append(pending_task)

                new_pending_tasks = ", ".join(filtered_pending_tasks)

                # Update the pending tasks
                cursor.execute("UPDATE patients SET pending_tasks = %s WHERE id = %s",
                              (new_pending_tasks, patient_id))
                conn.commit()
                conn.close()
                self.data_updated.emit()
                return True
            else:
                # If the triage is not set, add the corresponding pending task
                new_pending_tasks = self.calculate_pending_tasks_auto(patient_id)
                return self.update_pending_tasks_column(patient_id, new_pending_tasks)

        except Exception as e:
            print(f"Error updating the pending tasks according to the triage status: {str(e)}")
            return False

    def update_pending_tasks_for_specialist_consult(self, patient_id, specialist_consult_status):
        """
        Updates the pending tasks based on the specialist consult status

        Args:
            patient_id: Patient ID
            specialist_consult_status: Current status of the specialist consult field

        Returns:
            bool: True if the update was successful, False otherwise
        """
        try:
            # If the specialist consult is completed, remove the related pending task
            if specialist_consult_status == "Completed":
                conn = self.connect()
                cursor = conn.cursor()

                # Get the current pending tasks
                cursor.execute("SELECT pending_tasks FROM patients WHERE id = %s", (patient_id,))
                result = cursor.fetchone()
                current_pending_tasks = result[0] if result and result[0] else ""

                # Filter the pending tasks to remove those related to the specialist consult
                filtered_pending_tasks = []
                for pending_task in current_pending_tasks.split(", "):
                    if pending_task and pending_task != "Open specialist consult" and pending_task != "Specialist consult response":
                        filtered_pending_tasks.append(pending_task)

                new_pending_tasks = ", ".join(filtered_pending_tasks)

                # Update the pending tasks
                cursor.execute("UPDATE patients SET pending_tasks = %s WHERE id = %s",
                              (new_pending_tasks, patient_id))
                conn.commit()
                conn.close()
                self.data_updated.emit()
                return True
            else:
                # If the specialist consult is not completed, recalculate the pending tasks
                new_pending_tasks = self.calculate_pending_tasks_auto(patient_id)
                return self.update_pending_tasks_column(patient_id, new_pending_tasks)

        except Exception as e:
            print(f"Error updating the pending tasks according to the specialist consult status: {str(e)}")
            return False

    def update_pending_tasks_for_reassessment(self, patient_id, reassessment_status):
        """
        Updates the pending tasks based on the Reassessment status

        Args:
            patient_id: Patient ID
            reassessment_status: Current status of the Reassessment field

        Returns:
            bool: True if the update was successful, False otherwise
        """
        try:
            # If the reassessment is completed, remove the related pending task
            if reassessment_status == "Completed":
                conn = self.connect()
                cursor = conn.cursor()

                # Get the current pending tasks
                cursor.execute("SELECT pending_tasks FROM patients WHERE id = %s", (patient_id,))
                result = cursor.fetchone()
                current_pending_tasks = result[0] if result and result[0] else ""

                # Filter the pending tasks to remove those related to the reassessment
                filtered_pending_tasks = []
                for pending_task in current_pending_tasks.split(", "):
                    if pending_task and pending_task != "Perform reassessment":
                        filtered_pending_tasks.append(pending_task)

                new_pending_tasks = ", ".join(filtered_pending_tasks)

                # Update the pending tasks
                cursor.execute("UPDATE patients SET pending_tasks = %s WHERE id = %s",
                              (new_pending_tasks, patient_id))
                conn.commit()
                conn.close()
                self.data_updated.emit()
                return True
            else:
                # If the reassessment is not completed, recalculate the pending tasks
                new_pending_tasks = self.calculate_pending_tasks_auto(patient_id)
                return self.update_pending_tasks_column(patient_id, new_pending_tasks)

        except Exception as e:
            print(f"Error updating the pending tasks according to the Reassessment status: {str(e)}")
            return False

    def get_username(self, username):
        """Gets the full name of the user from the database"""
        try:
            from backend.users.users_model import UsersModel

            # Connect to the database
            conn = UsersModel.connect_db()
            if not conn:
                return username  # If it cannot connect, return the username as a fallback

            cursor = conn.cursor()

            # Query the user name
            cursor.execute("""
                SELECT full_name FROM users
                WHERE username = %s
            """, (username,))

            result = cursor.fetchone()
            conn.close()

            if result and result[0]:
                return result[0]
            else:
                return "System User"  # Generic name if there is no registered name

        except Exception as e:
            print(f"Error getting the user name: {str(e)}")
            return username


class AuditTrailModel:
    """Model for managing the audit trail of actions in the system"""

    @staticmethod
    def connect():
        """Establishes a connection with the database using the current credentials"""
        credentials = AuthenticationModel.get_credentials()
        return pymysql.connect(
            host=credentials['workstation'],
            user=credentials['user'],
            password=credentials['password'],
            database='urgentix',
            charset='utf8mb4'
        )

    @classmethod
    def log_action(cls, username=None, role=None, action=None, affected_patient=None, change_details=None):
        """
        Logs an action in the audit trail table

        Args:
            username: User who performed the action (if it is None, the current user is used)
            role: Role of the user (if it is None, it is inferred from the user)
            action: Description of the action performed
            affected_patient: Name of the patient affected by the action
            change_details: Specific details of the change performed

        Returns:
            bool: True if it was logged successfully, False otherwise
        """
        try:
            # If a user is not provided, use the currently authenticated user
            if not username:
                credentials = AuthenticationModel.get_credentials()
                username = credentials.get('user')

            # If there is no authenticated user, the action cannot be logged
            if not username:
                print("The audit trail entry could not be logged: There is no authenticated user")
                return False

            # Get the role of the user if it was not provided
            if not role:
                role = cls.get_user_role(username)
            # Connect to the database to look up the user ID
            conn = cls.connect()
            cursor = conn.cursor()

            # Query the user ID
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            result = cursor.fetchone()
            user_id = result[0] if result else None

            # Log the action in the audit trail table
            sql = """
                INSERT INTO audit_trail
                (username, role, action, timestamp, affected_patient, change_details, user_id)
                VALUES (%s, %s, %s, NOW(), %s, %s, %s)
            """
            cursor.execute(sql, (username, role, action, affected_patient, change_details, user_id))
            conn.commit()
            conn.close()

            print(f"Action logged in the audit trail: {username} ({role}) - {action}")
            return True
        except Exception as e:
            print(f"Error logging the action in the audit trail: {str(e)}")
            return False

    @classmethod
    def get_actions(cls, search_terms=None, user_role_filter=None, limit=200, page=1):
        """
        Gets the audit trail actions filtered according to the parameters

        Args:
            search_terms: List of search terms (they are applied with AND)
            user_role_filter: Filter by user role (Administrator, Doctor, etc.)
            limit: Limit of results to return
            page: Page number for pagination

        Returns:
            list: List of actions that meet the criteria
        """
        try:
            conn = cls.connect()
            cursor = conn.cursor()

            # Build the base query
            sql = """
                SELECT t.username, t.role, t.action, t.timestamp,
                       t.affected_patient, t.change_details, t.user_id, u.full_name
                FROM audit_trail t
                LEFT JOIN users u ON t.username = u.username
                WHERE 1=1
            """

            params = []

            # Add the search conditions by term
            if search_terms and len(search_terms) > 0:
                # Create conditions for each search term
                term_conditions = []

                for term in search_terms:
                    term_condition = """
                        (LOWER(t.username) LIKE %s
                        OR LOWER(u.full_name) LIKE %s
                        OR LOWER(t.affected_patient) LIKE %s
                        OR LOWER(t.change_details) LIKE %s)
                    """
                    term_conditions.append(term_condition)
                    search_text = f"%{term.lower()}%"
                    params.extend([search_text, search_text, search_text, search_text])

                # Combine all the conditions with AND so that all the terms are met
                if term_conditions:
                    sql += " AND " + " AND ".join(term_conditions)

            # Add the filter by role if it is present
            if user_role_filter:
                sql += """
                    AND t.username IN (
                        SELECT username FROM users
                        WHERE CASE
                            WHEN %s = 'Administrator' THEN role_admin = 1
                            WHEN %s = 'Doctor' THEN role_doctor = 1
                            ELSE 0 END
                    )
                """
                params.extend([user_role_filter, user_role_filter])

            # Calculate the offset for pagination
            offset = (page - 1) * limit

            # Sort by date descending and set the limit with pagination
            sql += " ORDER BY t.timestamp DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            # Run the query
            cursor.execute(sql, params)
            results = cursor.fetchall()

            conn.close()

            # Convert the results to a list of lists to keep consistency
            results_list = [list(row) for row in results]

            return results_list

        except Exception as e:
            print(f"Error getting the audit trail actions: {str(e)}")
            return []

    @classmethod
    def get_user_role(cls, username):
        """Gets the role of a user from the database"""
        try:
            from backend.users.users_model import UsersModel
            return UsersModel.get_user_role(username)
        except Exception as e:
            print(f"Error getting the user role: {str(e)}")
            return 'No role'

    @classmethod
    def calculate_and_store_metrics(cls, patient_id):
        """
        Calculates and stores metrics for a patient based on their timestamps.
        If metrics already exist for this patient, it updates them instead of creating new rows.

        Args:
            patient_id: ID of the patient to calculate metrics for

        Returns:
            bool: True if they were calculated and saved successfully, False otherwise
        """
        conn = None
        try:
            conn = cls.connect()
            cursor = conn.cursor()

            # Get all the relevant timestamps for the patient
            cursor.execute("""
                SELECT
                    admission, triage_timestamp,
                    admission_consult_not_done_timestamp, admission_consult_done_timestamp,
                    labs_not_done_timestamp, labs_requested_timestamp, labs_complete_timestamp,
                    imaging_not_done_timestamp, imaging_requested_timestamp, imaging_complete_timestamp,
                    specialist_consult_not_opened_timestamp, specialist_consult_opened_timestamp, specialist_consult_done_timestamp,
                    reassessment_not_done_timestamp, reassessment_done_timestamp,
                    discharge_timestamp, triage, location
                FROM patients
                WHERE id = %s
            """, (patient_id,))

            result = cursor.fetchone()
            if not result:
                print(f"The patient {patient_id} was not found")
                return False

            # Unpack the results
            (admission, triage_timestamp,
             admission_consult_not_done, admission_consult_done,
             labs_not_done, labs_requested, labs_complete,
             imaging_not_done, imaging_requested, imaging_complete,
             specialist_consult_not_opened, specialist_consult_opened, specialist_consult_done,
             reassessment_not_done, reassessment_done,
             discharge_timestamp, triage, location) = result

            # Initialize the dictionary to store the metrics
            metrics = {
                'patient_id': patient_id,
                'area': location
            }

            # Extract the triage level (digit 1-5)
            if triage in ["1", "2", "3", "4", "5"]:
                metrics['triage_level'] = triage

            # Triage time
            if admission and triage_timestamp:
                triage_time = int((triage_timestamp - admission).total_seconds() / 60)
                metrics['triage_time'] = triage_time

            # Admission consult time - FIX: Calculate it if the done timestamp exists, regardless of the other steps
            if admission_consult_not_done and admission_consult_done:
                admission_consult_time = int((admission_consult_done - admission_consult_not_done).total_seconds() / 60)
                metrics['admission_consult_time'] = admission_consult_time

            # Labs times - FIX: Calculate each part separately if the required timestamps exist
            if labs_not_done and labs_requested:
                labs_request_time = int((labs_requested - labs_not_done).total_seconds() / 60)
                metrics['labs_request_time'] = labs_request_time

            if labs_requested and labs_complete:
                labs_results_time = int((labs_complete - labs_requested).total_seconds() / 60)
                metrics['labs_results_time'] = labs_results_time

            if labs_not_done and labs_complete:
                labs_total_time = int((labs_complete - labs_not_done).total_seconds() / 60)
                metrics['labs_total_time'] = labs_total_time

            # Imaging times - FIX: Calculate each part separately if the required timestamps exist
            if imaging_not_done and imaging_requested:
                imaging_request_time = int((imaging_requested - imaging_not_done).total_seconds() / 60)
                metrics['imaging_request_time'] = imaging_request_time

            if imaging_requested and imaging_complete:
                imaging_results_time = int((imaging_complete - imaging_requested).total_seconds() / 60)
                metrics['imaging_results_time'] = imaging_results_time

            if imaging_not_done and imaging_complete:
                imaging_total_time = int((imaging_complete - imaging_not_done).total_seconds() / 60)
                metrics['imaging_total_time'] = imaging_total_time

            # Specialist consult times - FIX: Calculate each part separately if the required timestamps exist
            if specialist_consult_not_opened and specialist_consult_opened:
                specialist_consult_opening_time = int((specialist_consult_opened - specialist_consult_not_opened).total_seconds() / 60)
                metrics['specialist_consult_opening_time'] = specialist_consult_opening_time

            if specialist_consult_opened and specialist_consult_done:
                specialist_consult_completion_time = int((specialist_consult_done - specialist_consult_opened).total_seconds() / 60)
                metrics['specialist_consult_completion_time'] = specialist_consult_completion_time

            if specialist_consult_not_opened and specialist_consult_done:
                specialist_consult_total_time = int((specialist_consult_done - specialist_consult_not_opened).total_seconds() / 60)
                metrics['specialist_consult_total_time'] = specialist_consult_total_time

            # Reassessment time - FIX: Calculate it if the required timestamps exist
            if reassessment_not_done and reassessment_done:
                reassessment_time = int((reassessment_done - reassessment_not_done).total_seconds() / 60)
                metrics['reassessment_time'] = reassessment_time

            last_timestamp = None
            if discharge_timestamp:
                last_timestamp = discharge_timestamp
            else:
                # Try to use the latest available timestamp of any finished process
                final_timestamps = [
                    triage_timestamp, admission_consult_not_done, admission_consult_done, labs_not_done, labs_requested, labs_complete,
                    imaging_not_done, imaging_requested, imaging_complete, specialist_consult_not_opened, specialist_consult_opened, specialist_consult_done, reassessment_not_done, reassessment_done
                ]
                valid_timestamps = [ts for ts in final_timestamps if ts is not None]
                if valid_timestamps:
                    last_timestamp = max(valid_timestamps)

            # Now calculate the total time with the last timestamp if it is available
            if admission and last_timestamp:
                total_care_time = int((last_timestamp - admission).total_seconds() / 60)
                metrics['total_care_time'] = total_care_time

            # Check whether metrics already exist for this patient
            cursor.execute("SELECT id FROM patient_metrics WHERE patient_id = %s", (patient_id,))
            existing_metric = cursor.fetchone()

            if metrics:
                if existing_metric:
                    # If it exists, update the existing record
                    update_fields = []
                    update_values = []

                    for field, value in metrics.items():
                        if field != 'patient_id':  # Do not update the patient_id
                            update_fields.append(f"{field} = %s")
                            update_values.append(value)

                    # Add the update date
                    update_fields.append("calculation_date = NOW()")

                    # Add the ID at the end for the WHERE clause
                    update_values.append(patient_id)

                    # Build the update query
                    update_query = f"""
                        UPDATE patient_metrics
                        SET {", ".join(update_fields)}
                        WHERE patient_id = %s
                    """

                    cursor.execute(update_query, update_values)
                else:
                    # If it does not exist, insert a new record
                    fields = []
                    values = []
                    placeholders = []

                    for field, value in metrics.items():
                        fields.append(field)
                        values.append(value)
                        placeholders.append("%s")

                    # Build the insert query
                    insert_query = f"""
                        INSERT INTO patient_metrics
                        ({", ".join(fields)}, calculation_date)
                        VALUES ({", ".join(placeholders)}, NOW())
                    """

                    cursor.execute(insert_query, values)

                conn.commit()
                print(f"Metrics updated/saved for patient {patient_id}")
                return True
            else:
                print(f"There are no metrics to save for patient {patient_id}")
                return False

        except Exception as e:
            print(f"Error calculating or saving metrics for patient {patient_id}: {str(e)}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
