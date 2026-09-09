import pymysql
from datetime import datetime, timedelta
import numpy as np
from backend.database import PatientModel, AuthenticationModel

class MetricsModel:
    """
    Model that computes and retrieves waiting time metrics between
    status transitions in patient care.
    """

    @classmethod
    def connect(cls):
        """Opens a connection to the database using direct credentials"""
        try:
            from backend.database import AuthenticationModel
            from backend.database import ConfigurationModel

            host_config = ConfigurationModel.load_configuration()
            credentials = AuthenticationModel.get_credentials()
            return pymysql.connect(
                    host=host_config,
                    user=credentials['user'],
                    password=credentials['password'],
                    database='urgentix',
                    charset='utf8mb4'
                )
        except Exception as e:
            print(f"Database connection error: {str(e)}")
            return None

    @classmethod
    def calculate_statistics(cls, values):
        """
        Computes descriptive statistics for a list of values.

        Args:
            values (list): List of numeric values

        Returns:
            dict: Dictionary with the average, median and 90th percentile
        """
        if not values or len(values) == 0:
            return {
                'average': None,
                'median': None,
                'p90': None
            }

        try:
            # Use numpy to compute the statistics
            values_np = np.array(values)
            return {
                'average': round(float(np.mean(values_np)), 2),
                'median': round(float(np.median(values_np)), 2),
                'p90': round(float(np.percentile(values_np, 90)), 2)
            }
        except Exception as e:
            print(f"Error computing the statistics: {str(e)}")
            return {
                'average': None,
                'median': None,
                'p90': None
            }

    @classmethod
    def get_triage_metrics(cls, area=None, start_date=None, end_date=None, triage_level=None):
        """
        Computes the time metrics from admission to triage.

        Args:
            area (str, optional): Area used to filter the data
            start_date (str, optional): Start date of the range (format: 'YYYY-MM-DD HH:MM:SS')
            end_date (str, optional): End date of the range (format: 'YYYY-MM-DD HH:MM:SS')
            triage_level (str, optional): Triage level used to filter (1-5)

        Returns:
            dict: Dictionary with the triage time statistics
        """
        try:
            conn = cls.connect()
            cursor = conn.cursor()

            # Build the WHERE conditions
            conditions = []
            params = []

            # Only consider patients with triage completed and a triage timestamp
            conditions.append("triage IN ('1', '2', '3', '4', '5') AND triage_timestamp IS NOT NULL")

            if area:
                conditions.append("location LIKE %s")
                params.append(f"%{area}%")

            if triage_level:
                conditions.append("triage = %s")
                params.append(triage_level)

            if start_date:
                conditions.append("admission >= %s")
                params.append(start_date)

            if end_date:
                conditions.append("admission < DATE_ADD(DATE(%s), INTERVAL 1 DAY)")
                params.append(end_date)

            # Build the query
            query = """
                SELECT
                    TIMESTAMPDIFF(MINUTE, admission, triage_timestamp) as triage_time
                FROM
                    patients
                WHERE
                    """ + " AND ".join(conditions)

            # Run the query
            cursor.execute(query, params)
            results = cursor.fetchall()

            # Extract the times
            times = [result[0] for result in results if result[0] is not None]

            # Compute the statistics
            statistics = cls.calculate_statistics(times)

            conn.close()
            return {
                'total_patients': len(times),
                'statistics': statistics
            }

        except Exception as e:
            print(f"Error getting the triage metrics: {str(e)}")
            return {
                'total_patients': 0,
                'statistics': {
                    'average': None,
                    'median': None,
                    'p90': None
                }
            }

    @classmethod
    def get_admission_consult_metrics(cls, area=None, start_date=None, end_date=None, triage_level=None):
        """
        Computes the time metrics from admission consult not completed to completed.

        Args:
            area (str, optional): Area used to filter the data
            start_date (str, optional): Start date of the range
            end_date (str, optional): End date of the range
            triage_level (str, optional): Triage level used to filter (1-5)

        Returns:
            dict: Dictionary with the admission consult time statistics
        """
        try:
            conn = cls.connect()
            cursor = conn.cursor()

            # Build the WHERE conditions
            conditions = []
            params = []

            # Only consider patients with the admission consult completed and matching timestamps
            conditions.append("admission_consult = 'Completed' AND admission_consult_not_done_timestamp IS NOT NULL AND admission_consult_done_timestamp IS NOT NULL")

            if area:
                conditions.append("location LIKE %s")
                params.append(f"%{area}%")

            if triage_level:
                conditions.append("triage = %s")
                params.append(triage_level)

            if start_date:
                conditions.append("admission >= %s")
                params.append(start_date)

            if end_date:
                conditions.append("admission < DATE_ADD(DATE(%s), INTERVAL 1 DAY)")
                params.append(end_date)

            # Build the query
            query = """
                SELECT
                    TIMESTAMPDIFF(MINUTE, admission_consult_not_done_timestamp, admission_consult_done_timestamp) as admission_consult_time
                FROM
                    patients
                WHERE
                    """ + " AND ".join(conditions)

            # Run the query
            cursor.execute(query, params)
            results = cursor.fetchall()

            # Extract the times
            times = [result[0] for result in results if result[0] is not None]

            # Compute the statistics
            statistics = cls.calculate_statistics(times)

            conn.close()
            return {
                'total_patients': len(times),
                'statistics': statistics
            }

        except Exception as e:
            print(f"Error getting the admission consult metrics: {str(e)}")
            return {
                'total_patients': 0,
                'statistics': {
                    'average': None,
                    'median': None,
                    'p90': None
                }
            }


    @classmethod
    def get_labs_metrics(cls, area=None, start_date=None, end_date=None, triage_level=None):
        """
        Computes the time metrics for labs, including:
        - Time from "Not started" to "Awaiting results"
        - Time from "Awaiting results" to "Results complete"
        - Total time from "Not started" to "Results complete"

        Args:
            area (str, optional): Area used to filter the data
            start_date (str, optional): Start date of the range
            end_date (str, optional): End date of the range
            triage_level (str, optional): Triage level used to filter (1-5)

        Returns:
            dict: Dictionary with the lab processing time statistics
        """
        try:
            conn = cls.connect()
            cursor = conn.cursor()

            # Base conditions for filtering
            base_conditions = []
            base_params = []

            if area:
                base_conditions.append("location LIKE %s")
                base_params.append(f"%{area}%")

            if triage_level:
                base_conditions.append("triage = %s")
                base_params.append(triage_level)

            if start_date:
                base_conditions.append("admission >= %s")
                base_params.append(start_date)

            if end_date:
                base_conditions.append("admission < DATE_ADD(DATE(%s), INTERVAL 1 DAY)")
                base_params.append(end_date)

            # Results for the different transitions
            results = {}

            # 1. Metrics for "Not started" to "Awaiting results"
            request_conditions = base_conditions.copy()
            request_params = base_params.copy()
            request_conditions.append(
                "labs IN ('Awaiting results', 'Results complete') AND labs_not_done_timestamp IS NOT NULL AND labs_requested_timestamp IS NOT NULL"
            )

            request_query = """
                SELECT
                    TIMESTAMPDIFF(MINUTE, labs_not_done_timestamp, labs_requested_timestamp) as request_time
                FROM
                    patients
                WHERE
                    """ + " AND ".join(request_conditions)

            cursor.execute(request_query, request_params)
            request_results = cursor.fetchall()
            request_times = [r[0] for r in request_results if r[0] is not None]

            # 2. Metrics for "Awaiting results" to "Results complete"
            results_conditions = base_conditions.copy()
            results_params = base_params.copy()
            results_conditions.append(
                "labs = 'Results complete' AND labs_requested_timestamp IS NOT NULL AND labs_complete_timestamp IS NOT NULL"
            )

            results_query = """
                SELECT
                    TIMESTAMPDIFF(MINUTE, labs_requested_timestamp, labs_complete_timestamp) as results_time
                FROM
                    patients
                WHERE
                    """ + " AND ".join(results_conditions)

            cursor.execute(results_query, results_params)
            results_results = cursor.fetchall()
            results_times = [r[0] for r in results_results if r[0] is not None]

            # 3. Metrics for the total time
            total_conditions = base_conditions.copy()
            total_params = base_params.copy()
            total_conditions.append(
                "labs = 'Results complete' AND labs_not_done_timestamp IS NOT NULL AND labs_complete_timestamp IS NOT NULL"
            )

            total_query = """
                SELECT
                    TIMESTAMPDIFF(MINUTE, labs_not_done_timestamp, labs_complete_timestamp) as total_time
                FROM
                    patients
                WHERE
                    """ + " AND ".join(total_conditions)

            cursor.execute(total_query, total_params)
            total_results = cursor.fetchall()
            total_times = [r[0] for r in total_results if r[0] is not None]

            # Compute the statistics for each set
            request_statistics = cls.calculate_statistics(request_times)
            results_statistics = cls.calculate_statistics(results_times)
            total_statistics = cls.calculate_statistics(total_times)

            conn.close()
            return {
                'total_patients_request': len(request_times),
                'request_statistics': request_statistics,
                'total_patients_results': len(results_times),
                'results_statistics': results_statistics,
                'total_patients_total': len(total_times),
                'total_statistics': total_statistics
            }

        except Exception as e:
            print(f"Error getting the lab metrics: {str(e)}")
            return {
                'total_patients_request': 0,
                'request_statistics': {'average': None, 'median': None, 'p90': None},
                'total_patients_results': 0,
                'results_statistics': {'average': None, 'median': None, 'p90': None},
                'total_patients_total': 0,
                'total_statistics': {'average': None, 'median': None, 'p90': None}
            }

    @classmethod
    def get_imaging_metrics(cls, area=None, start_date=None, end_date=None, triage_level=None):
        """
        Computes the time metrics for diagnostic imaging, including:
        - Time from "Not started" to "Awaiting results"
        - Time from "Awaiting results" to "Results complete"
        - Total time from "Not started" to "Results complete"

        Args:
            area (str, optional): Area used to filter the data
            start_date (str, optional): Start date of the range
            end_date (str, optional): End date of the range
            triage_level (str, optional): Triage level used to filter (1-5)

        Returns:
            dict: Dictionary with the imaging processing time statistics
        """
        try:
            conn = cls.connect()
            cursor = conn.cursor()

            # Base conditions for filtering
            base_conditions = []
            base_params = []

            if area:
                base_conditions.append("location LIKE %s")
                base_params.append(f"%{area}%")

            if triage_level:
                base_conditions.append("triage = %s")
                base_params.append(triage_level)

            if start_date:
                base_conditions.append("admission >= %s")
                base_params.append(start_date)

            if end_date:
                base_conditions.append("admission < DATE_ADD(DATE(%s), INTERVAL 1 DAY)")
                base_params.append(end_date)

            # Results for the different transitions
            results = {}

            # 1. Metrics for "Not started" to "Awaiting results"
            request_conditions = base_conditions.copy()
            request_params = base_params.copy()
            request_conditions.append(
                "imaging IN ('Awaiting results', 'Results complete') AND imaging_not_done_timestamp IS NOT NULL AND imaging_requested_timestamp IS NOT NULL"
            )

            request_query = """
                SELECT
                    TIMESTAMPDIFF(MINUTE, imaging_not_done_timestamp, imaging_requested_timestamp) as request_time
                FROM
                    patients
                WHERE
                    """ + " AND ".join(request_conditions)

            cursor.execute(request_query, request_params)
            request_results = cursor.fetchall()
            request_times = [r[0] for r in request_results if r[0] is not None]

            # 2. Metrics for "Awaiting results" to "Results complete"
            results_conditions = base_conditions.copy()
            results_params = base_params.copy()
            results_conditions.append(
                "imaging = 'Results complete' AND imaging_requested_timestamp IS NOT NULL AND imaging_complete_timestamp IS NOT NULL"
            )

            results_query = """
                SELECT
                    TIMESTAMPDIFF(MINUTE, imaging_requested_timestamp, imaging_complete_timestamp) as results_time
                FROM
                    patients
                WHERE
                    """ + " AND ".join(results_conditions)

            cursor.execute(results_query, results_params)
            results_results = cursor.fetchall()
            results_times = [r[0] for r in results_results if r[0] is not None]

            # 3. Metrics for the total time
            total_conditions = base_conditions.copy()
            total_params = base_params.copy()
            total_conditions.append(
                "imaging = 'Results complete' AND imaging_not_done_timestamp IS NOT NULL AND imaging_complete_timestamp IS NOT NULL"
            )

            total_query = """
                SELECT
                    TIMESTAMPDIFF(MINUTE, imaging_not_done_timestamp, imaging_complete_timestamp) as total_time
                FROM
                    patients
                WHERE
                    """ + " AND ".join(total_conditions)

            cursor.execute(total_query, total_params)
            total_results = cursor.fetchall()
            total_times = [r[0] for r in total_results if r[0] is not None]

            # Compute the statistics for each set
            request_statistics = cls.calculate_statistics(request_times)
            results_statistics = cls.calculate_statistics(results_times)
            total_statistics = cls.calculate_statistics(total_times)

            conn.close()
            return {
                'total_patients_request': len(request_times),
                'request_statistics': request_statistics,
                'total_patients_results': len(results_times),
                'results_statistics': results_statistics,
                'total_patients_total': len(total_times),
                'total_statistics': total_statistics
            }

        except Exception as e:
            print(f"Error getting the diagnostic imaging metrics: {str(e)}")
            return {
                'total_patients_request': 0,
                'request_statistics': {'average': None, 'median': None, 'p90': None},
                'total_patients_results': 0,
                'results_statistics': {'average': None, 'median': None, 'p90': None},
                'total_patients_total': 0,
                'total_statistics': {'average': None, 'median': None, 'p90': None}
            }

    @classmethod
    def get_specialist_consult_metrics(cls, area=None, start_date=None, end_date=None, triage_level=None):
        """
        Computes the time metrics for specialist consults, both for opening and for completion.

        Args:
            area (str, optional): Area used to filter the data
            start_date (str, optional): Start date of the range
            end_date (str, optional): End date of the range
            triage_level (str, optional): Triage level used to filter (1-5)

        Returns:
            dict: Dictionary with the specialist consult time statistics
        """
        try:
            conn = cls.connect()
            cursor = conn.cursor()

            # Build the WHERE conditions
            conditions = []
            params = []

            # Only consider patients with the specialist consult completed and matching timestamps
            conditions.append("specialist_consult = 'Completed' AND specialist_consult_not_opened_timestamp IS NOT NULL AND specialist_consult_opened_timestamp IS NOT NULL AND specialist_consult_done_timestamp IS NOT NULL")

            if area:
                conditions.append("location LIKE %s")
                params.append(f"%{area}%")

            if triage_level:
                conditions.append("triage = %s")
                params.append(triage_level)

            if start_date:
                conditions.append("admission >= %s")
                params.append(start_date)

            if end_date:
                conditions.append("admission < DATE_ADD(DATE(%s), INTERVAL 1 DAY)")
                params.append(end_date)

            # Build the query for the opening time (not opened -> open)
            opening_query = """
                SELECT
                    TIMESTAMPDIFF(MINUTE, specialist_consult_not_opened_timestamp, specialist_consult_opened_timestamp) as opening_time
                FROM
                    patients
                WHERE
                    """ + " AND ".join(conditions)

            # Run the opening time query
            cursor.execute(opening_query, params)
            opening_results = cursor.fetchall()

            # Extract the opening times
            opening_times = [result[0] for result in opening_results if result[0] is not None]

            # Build the query for the completion time (open -> completed)
            completion_query = """
                SELECT
                    TIMESTAMPDIFF(MINUTE, specialist_consult_opened_timestamp, specialist_consult_done_timestamp) as completion_time
                FROM
                    patients
                WHERE
                    """ + " AND ".join(conditions)

            # Run the completion time query
            cursor.execute(completion_query, params)
            completion_results = cursor.fetchall()

            # Extract the completion times
            completion_times = [result[0] for result in completion_results if result[0] is not None]

            # Build the query for the total time (not opened -> completed)
            total_query = """
                SELECT
                    TIMESTAMPDIFF(MINUTE, specialist_consult_not_opened_timestamp, specialist_consult_done_timestamp) as total_time
                FROM
                    patients
                WHERE
                    """ + " AND ".join(conditions)

            # Run the total time query
            cursor.execute(total_query, params)
            total_results = cursor.fetchall()

            # Extract the total times
            total_times = [result[0] for result in total_results if result[0] is not None]

            # Compute the statistics for each set of times
            opening_statistics = cls.calculate_statistics(opening_times)
            completion_statistics = cls.calculate_statistics(completion_times)
            total_statistics = cls.calculate_statistics(total_times)

            conn.close()
            return {
                'total_patients': len(total_times),
                'opening_statistics': opening_statistics,
                'completion_statistics': completion_statistics,
                'total_statistics': total_statistics
            }

        except Exception as e:
            print(f"Error getting the specialist consult metrics: {str(e)}")
            return {
                'total_patients': 0,
                'opening_statistics': {
                    'average': None,
                    'median': None,
                    'p90': None
                },
                'completion_statistics': {
                    'average': None,
                    'median': None,
                    'p90': None
                },
                'total_statistics': {
                    'average': None,
                    'median': None,
                    'p90': None
                }
            }

    @classmethod
    def get_reassessment_metrics(cls, area=None, start_date=None, end_date=None, triage_level=None):
        """
        Computes the time metrics from reassessment not completed to completed.

        Args:
            area (str, optional): Area used to filter the data
            start_date (str, optional): Start date of the range
            end_date (str, optional): End date of the range
            triage_level (str, optional): Triage level used to filter (1-5)

        Returns:
            dict: Dictionary with the reassessment time statistics
        """
        try:
            conn = cls.connect()
            cursor = conn.cursor()

            # Build the WHERE conditions
            conditions = []
            params = []

            # Only consider patients with the reassessment completed and matching timestamps
            conditions.append("reassessment = 'Completed' AND reassessment_not_done_timestamp IS NOT NULL AND reassessment_done_timestamp IS NOT NULL")

            if area:
                conditions.append("location LIKE %s")
                params.append(f"%{area}%")

            if triage_level:
                conditions.append("triage = %s")
                params.append(triage_level)

            if start_date:
                conditions.append("admission >= %s")
                params.append(start_date)

            if end_date:
                conditions.append("admission < DATE_ADD(DATE(%s), INTERVAL 1 DAY)")
                params.append(end_date)

            # Build the query
            query = """
                SELECT
                    TIMESTAMPDIFF(MINUTE, reassessment_not_done_timestamp, reassessment_done_timestamp) as reassessment_time
                FROM
                    patients
                WHERE
                    """ + " AND ".join(conditions)

            # Run the query
            cursor.execute(query, params)
            results = cursor.fetchall()

            # Extract the times
            times = [result[0] for result in results if result[0] is not None]

            # Compute the statistics
            statistics = cls.calculate_statistics(times)

            conn.close()
            return {
                'total_patients': len(times),
                'statistics': statistics
            }

        except Exception as e:
            print(f"Error getting the reassessment metrics: {str(e)}")
            return {
                'total_patients': 0,
                'statistics': {
                    'average': None,
                    'median': None,
                    'p90': None
                }
            }

    @classmethod
    def get_total_time_metrics(cls, area=None, start_date=None, end_date=None, triage_level=None):
        """
        Computes the total care time metrics from admission to discharge or the latest available timestamp.

        Args:
            area (str, optional): Area used to filter the data
            start_date (str, optional): Start date of the range
            end_date (str, optional): End date of the range
            triage_level (str, optional): Triage level used to filter (1-5)

        Returns:
            dict: Dictionary with the total care time statistics
        """
        try:
            conn = cls.connect()
            cursor = conn.cursor()

            # Build the WHERE conditions
            conditions = []
            params = []

            # Only consider patients that were discharged or have some final timestamp
            conditions.append("""
                (
                    (disposition = 'Discharged' AND discharge_timestamp IS NOT NULL) OR
                    admission_consult_done_timestamp IS NOT NULL OR
                    labs_complete_timestamp IS NOT NULL OR
                    imaging_complete_timestamp IS NOT NULL OR
                    specialist_consult_done_timestamp IS NOT NULL OR
                    reassessment_done_timestamp IS NOT NULL
                )
            """)

            if area:
                conditions.append("location LIKE %s")
                params.append(f"%{area}%")

            if triage_level:
                conditions.append("triage = %s")
                params.append(triage_level)

            if start_date:
                conditions.append("admission >= %s")
                params.append(start_date)

            if end_date:
                conditions.append("admission < DATE_ADD(DATE(%s), INTERVAL 1 DAY)")
                params.append(end_date)

            # Run the query using GREATEST() to select the most recent timestamp
            query = """
                SELECT
                    TIMESTAMPDIFF(MINUTE, admission,
                        GREATEST(
                            COALESCE(discharge_timestamp, '1000-01-01'),
                            COALESCE(observation_timestamp, '1000-01-01'),
                            COALESCE(reassessment_done_timestamp, '1000-01-01')
                        )
                    ) as total_time
                FROM
                    patients
                WHERE
                    """ + " AND ".join(conditions)

            # Run the query
            cursor.execute(query, params)
            results = cursor.fetchall()

            # Extract the valid times (greater than 0)
            times = [result[0] for result in results if result[0] is not None and result[0] > 0]

            # Compute the statistics
            statistics = cls.calculate_statistics(times)

            # Compute additional metrics broken down by disposition
            metrics_by_disposition = {}

            # Compute the times for discharged patients
            discharge_query = query.replace(
                " AND ".join(conditions),
                " AND ".join(conditions + ["disposition = 'Discharged'"])
            )
            cursor.execute(discharge_query, params)
            discharge_results = cursor.fetchall()
            discharge_times = [r[0] for r in discharge_results if r[0] is not None and r[0] > 0]
            metrics_by_disposition['discharge'] = {
                'total': len(discharge_times),
                'statistics': cls.calculate_statistics(discharge_times)
            }

            # Compute the times for patients under observation
            observation_query = query.replace(
                " AND ".join(conditions),
                " AND ".join(conditions + ["disposition = 'Observation'"])
            )
            cursor.execute(observation_query, params)
            observation_results = cursor.fetchall()
            observation_times = [r[0] for r in observation_results if r[0] is not None and r[0] > 0]
            metrics_by_disposition['observation'] = {
                'total': len(observation_times),
                'statistics': cls.calculate_statistics(observation_times)
            }

            # Compute the times for hospitalized patients
            hospitalization_query = query.replace(
                " AND ".join(conditions),
                " AND ".join(conditions + ["disposition = 'Hospitalized'"])
            )
            cursor.execute(hospitalization_query, params)
            hospitalization_results = cursor.fetchall()
            hospitalization_times = [r[0] for r in hospitalization_results if r[0] is not None and r[0] > 0]
            metrics_by_disposition['hospitalization'] = {
                'total': len(hospitalization_times),
                'statistics': cls.calculate_statistics(hospitalization_times)
            }

            conn.close()
            return {
                'total_patients': len(times),
                'statistics': statistics,
                'by_disposition': metrics_by_disposition
            }

        except Exception as e:
            print(f"Error getting the total care time metrics: {str(e)}")
            return {
                'total_patients': 0,
                'statistics': {
                    'average': None,
                    'median': None,
                    'p90': None
                },
                'by_disposition': {
                    'discharge': {'total': 0, 'statistics': {'average': None, 'median': None, 'p90': None}},
                    'observation': {'total': 0, 'statistics': {'average': None, 'median': None, 'p90': None}},
                    'hospitalization': {'total': 0, 'statistics': {'average': None, 'median': None, 'p90': None}}
                }
            }

    @classmethod
    def get_all_metrics(cls, area=None, start_date=None, end_date=None, triage_level=None):
        """
        Gets every available metric in a single dictionary.

        Args:
            area (str, optional): Area used to filter the data
            start_date (str, optional): Start date of the range
            end_date (str, optional): End date of the range
            triage_level (str, optional): Triage level used to filter (1-5)

        Returns:
            dict: Dictionary with every collected metric
        """
        # Collect all the individual metrics
        triage_metrics = cls.get_triage_metrics(area, start_date, end_date, triage_level)
        admission_consult_metrics = cls.get_admission_consult_metrics(area, start_date, end_date, triage_level)
        labs_metrics = cls.get_labs_metrics(area, start_date, end_date, triage_level)
        imaging_metrics = cls.get_imaging_metrics(area, start_date, end_date, triage_level)
        specialist_consult_metrics = cls.get_specialist_consult_metrics(area, start_date, end_date, triage_level)
        reassessment_metrics = cls.get_reassessment_metrics(area, start_date, end_date, triage_level)
        total_time_metrics = cls.get_total_time_metrics(area, start_date, end_date, triage_level)

        # Build the consolidated dictionary
        return {
            'triage': triage_metrics,
            'admission_consult': admission_consult_metrics,
            'labs': labs_metrics,
            'imaging': imaging_metrics,
            'specialist_consult': specialist_consult_metrics,
            'reassessment': reassessment_metrics,
            'total_time': total_time_metrics,
            'configuration': {
                'area': area or 'all',
                'start_date': start_date,
                'end_date': end_date,
                'triage_level': triage_level
            }
        }

    @classmethod
    def generate_timeline_data(cls, area=None, start_date=None, end_date=None):
        """Generates the data for the timeline chart with smart grouping"""
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d") if isinstance(start_date, str) else start_date
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d") if isinstance(end_date, str) else end_date

            days_difference = (end_date_obj - start_date_obj).days

            if days_difference <= 2:
                grouping = "hourly"
                format_str = "%H:%M"
                sql_format = "%H"
                # Grouped by day and hour, not by hour alone: bucketing on HOUR()
                # merges the same clock hour from different days into one point,
                # so a two-day range came out as a single scrambled 24-hour cycle.
                group_by = "DATE_FORMAT(admission, '%%Y-%%m-%%d %%H')"
            elif days_difference > 2 and days_difference <= 31:  # Up to a month: show daily
                grouping = "daily"
                format_str = "%d %b"
                sql_format = "%Y-%m-%d"
                group_by = "DATE(admission)"
            elif days_difference > 31 and days_difference <= 92:  # Up to 3 months: show weekly
                grouping = "weekly"
                format_str = "Week %U"
                sql_format = "%Y%U"
                group_by = "YEARWEEK(admission, 1)"
            elif days_difference > 92 and days_difference <= 365:  # Up to a year: show monthly
                grouping = "monthly"
                format_str = "%b %Y"
                sql_format = "%Y-%m"
                group_by = "DATE_FORMAT(admission, '%%Y-%%m')"
            else:  # More than a year: show quarterly
                grouping = "quarterly"
                format_str = "Q%q %Y"
                sql_format = "%Y-%q"
                group_by = "CONCAT(YEAR(admission), '-', QUARTER(admission))"

            # Create SQL query with dynamic grouping
            query = f"""
                    SELECT
                        {group_by} AS date_group,
                        AVG(TIMESTAMPDIFF(MINUTE, admission, discharge_timestamp)) AS avg_time
                    FROM
                        patients
                    WHERE
                        admission >= %s AND admission < DATE_ADD(DATE(%s), INTERVAL 1 DAY)
                        AND discharge_timestamp IS NOT NULL
                        {" AND location LIKE %s" if area else ""}
                    GROUP BY
                        date_group
                    ORDER BY
                        date_group
                """

            params = [start_date, end_date]
            if area:
                params.append(f"%{area}%")

            # Execute query
            with cls.connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, params)
                    results = cursor.fetchall()

            # Debugging
            print(f"Query results: {results}")
            print(f"SQL used: {query}")
            print(f"Parameters: {params}")
            print(f"Grouping: {grouping}")

            # Process results based on grouping
            labels = []
            data = []

            for row in results:
                date_str = str(row[0])  # Make sure it is a string
                avg_time = row[1]

                # Format date string based on grouping
                if grouping == "hourly":
                    # date_str is "YYYY-MM-DD HH". A single day needs only the clock
                    # time; a range spanning more than one needs the day as well, or
                    # two different afternoons read as the same point.
                    try:
                        date_obj = datetime.strptime(date_str, "%Y-%m-%d %H")
                        if days_difference == 0:
                            labels.append(date_obj.strftime("%H:00"))
                        else:
                            labels.append(date_obj.strftime("%d %b %H:00"))
                    except ValueError:
                        labels.append(f"Hour {date_str}")
                elif grouping == "daily":
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    labels.append(date_obj.strftime(format_str))
                elif grouping == "weekly":
                    # YEARWEEK returns the YYYYWW format without a dash, or it may be an integer
                    try:
                        # If the result looks like "202329" (year 2023, week 29)
                        if len(date_str) >= 6:
                            year = date_str[:4]
                            week = date_str[4:6]
                            # Build a date for the week using the first day of the week
                            date_obj = datetime.strptime(f"{year}-W{week}-1", "%Y-W%W-%w")
                            labels.append(f"Week {week}/{year}")
                        else:
                            # Alternative format or fallback
                            labels.append(f"Week {date_str}")
                    except ValueError as e:
                        print(f"Error processing the weekly date: {e}, value: {date_str}")
                        labels.append(f"Week {date_str}")
                elif grouping == "monthly":
                    date_obj = datetime.strptime(date_str, "%Y-%m")
                    labels.append(date_obj.strftime(format_str))
                elif grouping == "quarterly":
                    year, quarter = date_str.split('-')
                    labels.append(f"Q{quarter} {year}")

                data.append(round(avg_time) if avg_time else 0)

            if not results:
                print(f"There is no data for the timeline chart: start_date={start_date}, end_date={end_date}, area={area}")
                return {
                    "labels": [],
                    "data": [],
                    "grouping": grouping  # Keep the grouping for consistency
                }

            # Return the correct data
            return {
                "labels": labels,
                "data": data,
                "grouping": grouping
            }

        except Exception as e:
            print(f"Error generating the timeline data: {str(e)}")
            # Return empty data structure on error
            return {
                "labels": [],
                "data": [],
                "grouping": "daily"
            }

    @classmethod
    def generate_comparative_bar_data(cls, area=None, start_date=None, end_date=None, triage_level=None):
        """
        Generates the data for the bar chart of average times per stage.

        Args:
            area (str, optional): Area used to filter the data
            start_date (str, optional): Start date of the range
            end_date (str, optional): End date of the range
            triage_level (str, optional): Triage level used to filter (1-5)

        Returns:
            dict: Dictionary with the labels and data for the chart
        """
        try:
            # Get the metrics for every stage
            metrics = cls.get_all_metrics(area, start_date, end_date, triage_level)

            # Extract the data relevant for the chart
            labels = ['Triage', 'Admission Consult', 'Labs', 'Imaging', 'Specialist Consult', 'Reassessment']
            data = [
                metrics['triage'].get('statistics', {}).get('average', 0) or 0,
                metrics['admission_consult'].get('statistics', {}).get('average', 0) or 0,
                metrics['labs'].get('total_statistics', {}).get('average', 0) or 0,
                metrics['imaging'].get('total_statistics', {}).get('average', 0) or 0,
                metrics['specialist_consult'].get('total_statistics', {}).get('average', 0) or 0,
                metrics['reassessment'].get('statistics', {}).get('average', 0) or 0
            ]

            return {
                'labels': labels,
                'data': data
            }

        except Exception as e:
            print(f"Error generating the comparative bar data: {str(e)}")
            return {
                'labels': [],
                'data': []
            }

    @classmethod
    def get_sla_compliance_metrics(cls, area=None, start_date=None, end_date=None, triage_level=None):
        """
        Computes the SLA compliance metrics for each stage.

        Args:
            area (str, optional): Area used to filter the data
            start_date (str, optional): Start date of the range
            end_date (str, optional): End date of the range
            triage_level (str, optional): Triage level used to filter (1-5)

        Returns:
            dict: Dictionary with the compliance percentages for each stage
        """
        try:
            conn = cls.connect()
            cursor = conn.cursor()

            # Define the target SLAs (in minutes) for each stage and triage level
            slas = {
                # Format: {triage_level: target_time_in_minutes}
                'triage': {'1': 0, '2': 30, '3': 120, '4': 30, '5': 60},
                'admission_consult': {'1': 210, '2': 210, '3': 360, '4': 420, '5': 420},
                'labs': {'1': 360, '2': 360, '3': 360, '4': 360, '5': 360},
                'imaging': {'1': 360, '2': 360, '3': 360, '4': 360, '5': 360},
                'specialist_consult': {'1': 30, '2': 45, '3': 60, '4': 120, '5': 180},
                'reassessment': {'1': 30, '2': 60, '3': 120, '4': 240, '5': 360}
            }

            # Build the common filter conditions
            base_conditions = []
            base_params = []

            if area:
                base_conditions.append("location LIKE %s")
                base_params.append(f"%{area}%")

            if triage_level:
                base_conditions.append("triage = %s")
                base_params.append(triage_level)

            if start_date:
                base_conditions.append("admission >= %s")
                base_params.append(start_date)

            if end_date:
                base_conditions.append("admission < DATE_ADD(DATE(%s), INTERVAL 1 DAY)")
                base_params.append(end_date)

            # Compute the compliance for each stage
            results = {}

            # Triage
            conditions = base_conditions.copy() + ["triage IN ('1', '2', '3', '4', '5') AND triage_timestamp IS NOT NULL"]
            params = base_params.copy()

            query = """
                SELECT
                    triage,
                    TIMESTAMPDIFF(MINUTE, admission, triage_timestamp) as triage_time
                FROM
                    patients
                WHERE
                    """ + " AND ".join(conditions)

            cursor.execute(query, params)
            triage_data = cursor.fetchall()

            # Compute the compliance
            total_triage = len(triage_data)
            if total_triage > 0:
                compliant_triage = sum(1 for t, time in triage_data if time <= slas['triage'].get(t, 30))
                results['triage'] = round((compliant_triage / total_triage) * 100)
            else:
                # No qualifying patients in range: absence of data is not a breach.
                results['triage'] = None

            # Admission Consult
            conditions = base_conditions.copy() + ["admission_consult = 'Completed' AND admission_consult_not_done_timestamp IS NOT NULL AND admission_consult_done_timestamp IS NOT NULL"]
            params = base_params.copy()

            query = """
                SELECT
                    triage,
                    TIMESTAMPDIFF(MINUTE, admission_consult_not_done_timestamp, admission_consult_done_timestamp) as admission_consult_time
                FROM
                    patients
                WHERE
                    """ + " AND ".join(conditions)

            cursor.execute(query, params)
            admission_consult_data = cursor.fetchall()

            total_admission_consult = len(admission_consult_data)
            if total_admission_consult > 0:
                compliant_admission_consult = sum(1 for t, time in admission_consult_data if time <= slas['admission_consult'].get(t, 60))
                results['admission_consult'] = round((compliant_admission_consult / total_admission_consult) * 100)
            else:
                # No qualifying patients in range: absence of data is not a breach.
                results['admission_consult'] = None

            # Labs
            conditions = base_conditions.copy() + ["labs = 'Results complete' AND labs_requested_timestamp IS NOT NULL AND labs_complete_timestamp IS NOT NULL"]
            params = base_params.copy()

            query = """
                SELECT
                    triage,
                    TIMESTAMPDIFF(MINUTE, labs_requested_timestamp, labs_complete_timestamp) as labs_time
                FROM
                    patients
                WHERE
                    """ + " AND ".join(conditions)

            cursor.execute(query, params)
            labs_data = cursor.fetchall()

            total_labs = len(labs_data)
            if total_labs > 0:
                compliant_labs = sum(1 for t, time in labs_data if time <= slas['labs'].get(t, 90))
                results['labs'] = round((compliant_labs / total_labs) * 100)
            else:
                # No qualifying patients in range: absence of data is not a breach.
                results['labs'] = None

            # Imaging
            conditions = base_conditions.copy() + ["imaging = 'Results complete' AND imaging_requested_timestamp IS NOT NULL AND imaging_complete_timestamp IS NOT NULL"]
            params = base_params.copy()

            query = """
                SELECT
                    triage,
                    TIMESTAMPDIFF(MINUTE, imaging_requested_timestamp, imaging_complete_timestamp) as imaging_time
                FROM
                    patients
                WHERE
                    """ + " AND ".join(conditions)

            cursor.execute(query, params)
            imaging_data = cursor.fetchall()

            total_imaging = len(imaging_data)
            if total_imaging > 0:
                compliant_imaging = sum(1 for t, time in imaging_data if time <= slas['imaging'].get(t, 90))
                results['imaging'] = round((compliant_imaging / total_imaging) * 100)
            else:
                # No qualifying patients in range: absence of data is not a breach.
                results['imaging'] = None

            # Specialist Consult
            conditions = base_conditions.copy() + ["specialist_consult = 'Completed' AND specialist_consult_opened_timestamp IS NOT NULL AND specialist_consult_done_timestamp IS NOT NULL"]
            params = base_params.copy()

            query = """
                SELECT
                    triage,
                    TIMESTAMPDIFF(MINUTE, specialist_consult_opened_timestamp, specialist_consult_done_timestamp) as specialist_consult_time
                FROM
                    patients
                WHERE
                    """ + " AND ".join(conditions)

            cursor.execute(query, params)
            specialist_consult_data = cursor.fetchall()

            total_specialist_consult = len(specialist_consult_data)
            if total_specialist_consult > 0:
                compliant_specialist_consult = sum(1 for t, time in specialist_consult_data if time <= slas['specialist_consult'].get(t, 60))
                results['specialist_consult'] = round((compliant_specialist_consult / total_specialist_consult) * 100)
            else:
                # No qualifying patients in range: absence of data is not a breach.
                results['specialist_consult'] = None

            # Reassessment
            conditions = base_conditions.copy() + ["reassessment = 'Completed' AND reassessment_not_done_timestamp IS NOT NULL AND reassessment_done_timestamp IS NOT NULL"]
            params = base_params.copy()

            query = """
                SELECT
                    triage,
                    TIMESTAMPDIFF(MINUTE, reassessment_not_done_timestamp, reassessment_done_timestamp) as reassessment_time
                FROM
                    patients
                WHERE
                    """ + " AND ".join(conditions)

            cursor.execute(query, params)
            reassessment_data = cursor.fetchall()

            total_reassessment = len(reassessment_data)
            if total_reassessment > 0:
                compliant_reassessment = sum(1 for t, time in reassessment_data if time <= slas['reassessment'].get(t, 120))
                results['reassessment'] = round((compliant_reassessment / total_reassessment) * 100)
            else:
                # No qualifying patients in range: absence of data is not a breach.
                results['reassessment'] = None

            conn.close()
            return results

        except Exception as e:
            print(f"Error computing the SLA compliance metrics: {str(e)}")
            # Nothing could be measured, which is not the same as nothing complying.
            # Zero here would paint every stage red and read as a department in crisis.
            return {
                'triage': None,
                'admission_consult': None,
                'labs': None,
                'imaging': None,
                'specialist_consult': None,
                'reassessment': None
            }

    @classmethod
    def get_patient_metrics(cls, patient_id):
        """
        Gets the specific metrics for a patient and compares them against their area
        in order to generate an individual report.
        """
        conn = None
        try:
            conn = cls.connect()
            cursor = conn.cursor()

            # First we get the basic patient data including their current status and times
            cursor.execute("""
                SELECT p.name, p.document_id, p.location, p.triage, p.admission_consult, p.labs, p.imaging,
                    p.specialist_consult, p.reassessment, p.disposition, p.admission
                FROM patients p
                WHERE p.id = %s
            """, (patient_id,))

            basic_patient_data = cursor.fetchone()

            if not basic_patient_data:
                print(f"The patient with ID {patient_id} was not found")
                return None

            name = basic_patient_data[0]
            document_id = basic_patient_data[1]
            location = basic_patient_data[2]

            # Extract the area (first part of the location)
            area = location.split(' - ')[0] if ' - ' in location else location

            # Get the admission date to filter the comparative metrics over the same period
            admission_date = basic_patient_data[10]
            # Build a date range: 30 days before and after the admission
            from datetime import datetime, timedelta
            if isinstance(admission_date, str):
                admission_date = datetime.strptime(admission_date, "%Y-%m-%d %H:%M:%S")

            start_date = (admission_date - timedelta(days=30)).strftime("%Y-%m-%d")
            end_date = (admission_date + timedelta(days=30)).strftime("%Y-%m-%d")

            # Get the area metrics for comparison using the same date range
            area_metrics = {
                'triage': cls.get_triage_metrics(area=area, start_date=start_date, end_date=end_date),
                'admission_consult': cls.get_admission_consult_metrics(area=area, start_date=start_date, end_date=end_date),
                'labs': cls.get_labs_metrics(area=area, start_date=start_date, end_date=end_date),
                'imaging': cls.get_imaging_metrics(area=area, start_date=start_date, end_date=end_date),
                'specialist_consult': cls.get_specialist_consult_metrics(area=area, start_date=start_date, end_date=end_date),
                'reassessment': cls.get_reassessment_metrics(area=area, start_date=start_date, end_date=end_date),
                'total_time': cls.get_total_time_metrics(area=area, start_date=start_date, end_date=end_date)
            }

            # Get the patient metrics from the patient_metrics table
            cursor.execute("""
                SELECT *
                FROM patient_metrics
                WHERE patient_id = %s
            """, (patient_id,))

            metrics = cursor.fetchone()

            if not metrics:
                print(f"There are no metrics available for the patient with ID {patient_id}")
                # If there are no metrics, build an empty structure but do not return None
                metrics_dict = {}
            else:
                # Get the columns in order to map the indexes
                cursor.execute("DESCRIBE patient_metrics")
                columns = [col[0] for col in cursor.fetchall()]

                # Build a dictionary with the patient's metrics
                metrics_dict = {columns[i]: metrics[i] for i in range(len(columns))}

            # Build a structured dictionary with the metrics for the report
            statistics = {
                "patient": {
                    "id": patient_id,
                    "name": name,
                    "document_id": document_id,
                    "location": location,
                    "area": area,
                    "current_status": {
                        "triage": basic_patient_data[3],
                        "admission_consult": basic_patient_data[4],
                        "labs": basic_patient_data[5],
                        "imaging": basic_patient_data[6],
                        "specialist_consult": basic_patient_data[7],
                        "reassessment": basic_patient_data[8],
                        "disposition": basic_patient_data[9]
                    },
                    "admission": str(admission_date)
                },
                "metrics": {
                    "triage": {
                        "time": metrics_dict.get('triage_time', 0),
                        "level": metrics_dict.get('triage_level', "")
                    },
                    "admission_consult": {
                        "time": metrics_dict.get('admission_consult_time', 0)
                    },
                    "labs": {
                        "time": metrics_dict.get('labs_total_time', 0),
                        "request_time": metrics_dict.get('labs_request_time', 0),
                        "results_time": metrics_dict.get('labs_results_time', 0)
                    },
                    "imaging": {
                        "time": metrics_dict.get('imaging_total_time', 0),
                        "request_time": metrics_dict.get('imaging_request_time', 0),
                        "results_time": metrics_dict.get('imaging_results_time', 0)
                    },
                    "specialist_consult": {
                        "time": metrics_dict.get('specialist_consult_total_time', 0),
                        "opening_time": metrics_dict.get('specialist_consult_opening_time', 0),
                        "completion_time": metrics_dict.get('specialist_consult_completion_time', 0)
                    },
                    "reassessment": {
                        "time": metrics_dict.get('reassessment_time', 0)
                    }
                },
                "total_time": metrics_dict.get('total_care_time', 0),
                "area_averages": area_metrics,
                "area": area
            }

            if conn:
                conn.close()
            return statistics

        except Exception as e:
            print(f"Error getting the patient metrics: {str(e)}")
            import traceback
            traceback.print_exc()
            if conn:
                conn.close()
            return None
