"""
Export the seeded patients as a portable SQL script.

`seed_test_data.py` needs Python and the application package. Someone evaluating
the packaged executable has neither, so this turns whatever that script produced
into plain SQL that the MySQL client can load on its own.

Absolute datetimes would rot: a patient admitted at a fixed date stops being
"recent", the alarms stop firing and the reports drift out of their default date
range. So every timestamp is written relative to a single `@now` captured when
the script runs, which keeps the data fresh whenever it is loaded. The metrics
table needs no such treatment, as it stores elapsed minutes rather than instants.

    python tools\\seed_test_data.py 60        # produce the data
    python tools\\export_seed_sql.py          # freeze it into SQL

Writes database/seed_test_data.sql.
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import pymysql  # noqa: E402

PREFIX = "SEED"
USER = "emergency_admin"
DATABASE = "urgentix"

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(PROJECT_ROOT, "database", "seed_test_data.sql")

PATIENT_COLUMNS = [
    "name", "document_id", "triage", "triage_timestamp", "admission", "location",
    "admission_consult", "labs", "imaging", "specialist_consult", "reassessment",
    "pending_tasks", "disposition",
    "admission_consult_not_done_timestamp", "admission_consult_done_timestamp",
    "labs_not_done_timestamp", "labs_requested_timestamp", "labs_complete_timestamp",
    "imaging_not_done_timestamp", "imaging_requested_timestamp", "imaging_complete_timestamp",
    "specialist_consult_not_opened_timestamp", "specialist_consult_opened_timestamp",
    "specialist_consult_done_timestamp",
    "reassessment_not_done_timestamp", "reassessment_done_timestamp",
    "discharge_timestamp", "observation_timestamp",
]

METRIC_COLUMNS = [
    "triage_time", "triage_level", "admission_consult_time",
    "labs_request_time", "labs_results_time", "labs_total_time",
    "imaging_request_time", "imaging_results_time", "imaging_total_time",
    "specialist_consult_opening_time", "specialist_consult_completion_time",
    "specialist_consult_total_time", "reassessment_time", "total_care_time", "area",
]


def literal(value, reference):
    """Renders one column value as SQL.

    Datetimes become an offset from @now so the data ages with the clock instead
    of against it; everything else is escaped as a normal literal.
    """
    if value is None:
        return "NULL"
    if isinstance(value, datetime):
        seconds = int((reference - value).total_seconds())
        return f"DATE_SUB(@now, INTERVAL {seconds} SECOND)"
    if isinstance(value, (int, float)):
        return str(value)
    escaped = str(value).replace("\\", "\\\\").replace("'", "''")
    return f"'{escaped}'"


def main():
    password = os.environ.get("MYSQL_PWD")
    if not password:
        import getpass
        password = getpass.getpass(f"Password for MySQL user {USER}: ")

    from backend.database import ConfigurationModel
    host = ConfigurationModel.load_configuration()
    connection = pymysql.connect(host=host, user=USER, password=password,
                                 database=DATABASE, charset="utf8mb4")

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT NOW()")
            reference = cursor.fetchone()[0]

            cursor.execute(
                f"SELECT id, {', '.join(PATIENT_COLUMNS)} FROM patients "
                "WHERE document_id LIKE %s ORDER BY id", (PREFIX + "%",))
            patients = cursor.fetchall()

            cursor.execute(
                f"SELECT p.document_id, {', '.join('m.' + c for c in METRIC_COLUMNS)} "
                "FROM patient_metrics m JOIN patients p ON p.id = m.patient_id "
                "WHERE p.document_id LIKE %s ORDER BY p.id", (PREFIX + "%",))
            metrics = cursor.fetchall()
    finally:
        connection.close()

    if not patients:
        print("No seeded patients found. Run tools\\seed_test_data.py first.")
        return 1

    lines = [
        "-- ---------------------------------------------------------------------------",
        "-- Urgentix — synthetic test data",
        "--",
        "-- Loads invented patients so the board, the alarms and the reports can be",
        "-- evaluated against a system that ships with an empty database. Names,",
        "-- document numbers and timings are randomly generated; nothing here is real.",
        "--",
        "-- Every timestamp is relative to the moment this script runs, so the data is",
        "-- always recent no matter when it is loaded.",
        "--",
        "-- Load with:",
        "--   Get-Content database\\seed_test_data.sql | & $mysql -u emergency_admin -p",
        "--",
        "-- Every row inserted here has a document number starting with 'SEED'. To",
        "-- remove them:  DELETE FROM patients WHERE document_id LIKE 'SEED%';",
        "-- (patient_metrics rows are removed automatically by the foreign key.)",
        "-- ---------------------------------------------------------------------------",
        "",
        "USE urgentix;",
        "",
        "SET @now = NOW();",
        "",
        "-- Replace any previous batch rather than piling up on it.",
        "DELETE FROM patients WHERE document_id LIKE 'SEED%';",
        "",
        f"-- {len(patients)} patients",
    ]

    for row in patients:
        values = ", ".join(literal(v, reference) for v in row[1:])
        lines.append(f"INSERT INTO patients ({', '.join(PATIENT_COLUMNS)})")
        lines.append(f"VALUES ({values});")

    lines += [
        "",
        f"-- Precomputed stage durations for the {len(metrics)} patients above.",
        "-- These are elapsed minutes, so they need no adjustment for the clock.",
        "-- Linked by document number so the script never depends on auto-increment ids.",
    ]

    for row in metrics:
        document_id = row[0]
        values = ", ".join(literal(v, reference) for v in row[1:])
        lines.append(
            f"INSERT INTO patient_metrics (patient_id, {', '.join(METRIC_COLUMNS)})")
        lines.append(
            f"SELECT id, {values} FROM patients WHERE document_id = '{document_id}';")

    lines += [
        "",
        "SELECT CONCAT('Seeded patients loaded: ', COUNT(*)) AS result",
        "FROM patients WHERE document_id LIKE 'SEED%';",
        "",
    ]

    with open(OUTPUT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines))

    print(f"wrote {OUTPUT}")
    print(f"  {len(patients)} patients, {len(metrics)} metric rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
