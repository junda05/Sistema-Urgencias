from backend.database import PatientModel

class WaitingRoomModel(PatientModel):
    """Specific model for the waiting room with limited functionality"""

    def get_patient_data(self):
        """Gets patient data for the waiting room view"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, document_id, triage, admission_consult, labs, imaging, specialist_consult, reassessment, pending_tasks,
                location, admission, triage_timestamp, id, observation_timestamp
            FROM patients
            ORDER BY admission DESC
        """)
        data = cursor.fetchall()
        conn.close()
        return data

    def get_filtered_patient_data(self, selected_areas=None):
        """Gets patient data filtered by specific areas"""
        conn = self.connect()
        cursor = conn.cursor()

        if selected_areas and len(selected_areas) > 0:
            # Build a list of conditions for each selected area
            conditions = []
            for area in selected_areas:
                conditions.append(f"location LIKE '{area}%'")

            # Join the conditions with OR
            where_condition = " OR ".join(conditions)

            # Query with area filter
            query = f"""
                SELECT name, document_id, triage, admission_consult, labs, imaging, specialist_consult, reassessment, pending_tasks,
                    location, admission, triage_timestamp, id, observation_timestamp
                FROM patients
                WHERE {where_condition}
                ORDER BY admission DESC
            """
        else:
            # If there are no selected areas or the list is empty, fetch all the data
            query = """
                SELECT name, document_id, triage, admission_consult, labs, imaging, specialist_consult, reassessment, pending_tasks,
                    location, admission, triage_timestamp, id, observation_timestamp
                FROM patients
                ORDER BY admission DESC
            """

        cursor.execute(query)
        data = cursor.fetchall()
        conn.close()
        return data