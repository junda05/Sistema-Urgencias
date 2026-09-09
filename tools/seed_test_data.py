"""
Generate synthetic patients for testing the Urgentix reports.

Everything here is invented: names, document numbers and timings are random, so
nothing real ever enters the database. Timestamps are spread over the past weeks
and cover every care path — discharged, under observation, admitted, and still
in care — so the metrics, the compliance gauges and the timeline chart all have
something to show.

    python seed_test_data.py            # insert 60 patients
    python seed_test_data.py 120        # insert a different number
    python seed_test_data.py --clear    # remove everything this script created

Seeded records are recognisable by their document numbers, which all start with
the prefix below, so the cleanup never touches anything else.
"""
import contextlib
import io
import os
import random
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import pymysql  # noqa: E402

PREFIX = "SEED"
USER = "emergency_admin"
DATABASE = "urgentix"

FIRST_NAMES = ["Ana", "Ben", "Clara", "David", "Elena", "Frank", "Grace", "Henry",
               "Iris", "Jonas", "Karen", "Liam", "Maya", "Noah", "Olive", "Peter",
               "Quinn", "Rosa", "Simon", "Tara", "Uma", "Victor", "Wendy", "Xavier"]
MIDDLE_NAMES = ["Aaron", "Blake", "Cole", "Drew", "Ellis", "Faye", "Gray", "Hope",
                "Ivy", "Jude", "Kai", "Lane", "Mercy", "Neal", "Opal", "Paige"]
LAST_NAMES = ["Adler", "Brooks", "Carver", "Dalton", "Ellery", "Fenwick", "Grant",
              "Hollis", "Irving", "Jarrett", "Keane", "Lowell", "Marsh", "Norton",
              "Oakley", "Prentice", "Quill", "Radcliffe", "Sterling", "Thorne"]

AREAS = {
    "Old wing": (1, 18),
    "Yellow": (19, 38),
    "Pediatrics": (39, 59),
    "Hallways": (60, 200),
    "Clinic": (1, 40),
    "Waiting room": (1, 2),
}

# how the population splits across care paths
PATHS = (["discharged"] * 11) + (["observation"] * 3) + (["hospitalized"] * 3) + (["in_care"] * 3)


def connect(host, password):
    return pymysql.connect(host=host, user=USER, password=password,
                           database=DATABASE, charset="utf8mb4")


def make_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(MIDDLE_NAMES)} {random.choice(LAST_NAMES)}"


def build_patient(index):
    """Returns the column values for one synthetic patient."""
    triage = random.choices(["1", "2", "3"], weights=[1, 4, 6])[0]
    path = random.choice(PATHS)
    area = random.choice(list(AREAS))
    low, high = AREAS[area]
    location = f"{area} - {random.randint(low, high)}"

    # spread arrivals over the past 45 days, weighted towards recent days
    admission = datetime.now() - timedelta(
        days=random.triangular(0, 45, 3),
        minutes=random.randint(0, 1439),
    )

    # triage: mostly inside the target for its level, sometimes badly late
    target = {"1": 3, "2": 30, "3": 120}[triage]
    if random.random() < 0.75:
        triage_minutes = random.randint(1, max(2, int(target * 0.8)))
    else:
        triage_minutes = random.randint(target, int(target * 2.5))
    t_triage = admission + timedelta(minutes=triage_minutes)

    row = {
        "name": make_name(),
        "document_id": f"{PREFIX}{index:05d}",
        "triage": triage,
        "triage_timestamp": t_triage,
        "admission": admission,
        "location": location,
        "admission_consult": "Not completed",
        "labs": "", "imaging": "", "specialist_consult": "", "reassessment": "",
        "pending_tasks": "", "disposition": "",
        "admission_consult_not_done_timestamp": t_triage,
        "admission_consult_done_timestamp": None,
        "labs_not_done_timestamp": None, "labs_requested_timestamp": None,
        "labs_complete_timestamp": None,
        "imaging_not_done_timestamp": None, "imaging_requested_timestamp": None,
        "imaging_complete_timestamp": None,
        "specialist_consult_not_opened_timestamp": None,
        "specialist_consult_opened_timestamp": None,
        "specialist_consult_done_timestamp": None,
        "reassessment_not_done_timestamp": None,
        "reassessment_done_timestamp": None,
        "discharge_timestamp": None,
        "observation_timestamp": None,
    }

    if path == "in_care" and random.random() < 0.4:
        # arrived recently, still waiting for the admission consult
        return row

    # admission consult
    ci_done = t_triage + timedelta(minutes=random.randint(5, 200))
    row["admission_consult"] = "Completed"
    row["admission_consult_done_timestamp"] = ci_done
    cursor_time = ci_done

    # laboratories
    if random.random() < 0.85:
        row["labs_not_done_timestamp"] = cursor_time
        requested = cursor_time + timedelta(minutes=random.randint(2, 40))
        row["labs_requested_timestamp"] = requested
        row["labs"] = "Awaiting results"
        if path != "in_care" or random.random() < 0.6:
            complete = requested + timedelta(minutes=random.randint(20, 400))
            row["labs_complete_timestamp"] = complete
            row["labs"] = "Results complete"
            cursor_time = complete
        else:
            cursor_time = requested

    # diagnostic imaging
    if random.random() < 0.6:
        row["imaging_not_done_timestamp"] = ci_done
        requested = ci_done + timedelta(minutes=random.randint(2, 60))
        row["imaging_requested_timestamp"] = requested
        row["imaging"] = "Awaiting results"
        if path != "in_care" or random.random() < 0.5:
            complete = requested + timedelta(minutes=random.randint(25, 420))
            row["imaging_complete_timestamp"] = complete
            row["imaging"] = "Results complete"
            cursor_time = max(cursor_time, complete)
        else:
            cursor_time = max(cursor_time, requested)

    if path == "in_care":
        return row

    # specialist consult
    if random.random() < 0.7:
        row["specialist_consult_not_opened_timestamp"] = cursor_time
        opened = cursor_time + timedelta(minutes=random.randint(3, 90))
        row["specialist_consult_opened_timestamp"] = opened
        row["specialist_consult"] = "Open"
        done = opened + timedelta(minutes=random.randint(10, 240))
        row["specialist_consult_done_timestamp"] = done
        row["specialist_consult"] = "Completed"
        cursor_time = done

    # reassessment
    row["reassessment_not_done_timestamp"] = cursor_time
    rv_done = cursor_time + timedelta(minutes=random.randint(5, 180))
    row["reassessment_done_timestamp"] = rv_done
    row["reassessment"] = "Completed"

    if path == "discharged":
        row["disposition"] = "Discharged"
        row["discharge_timestamp"] = rv_done + timedelta(minutes=random.randint(5, 90))
    elif path == "observation":
        row["disposition"] = "Observation"
        row["observation_timestamp"] = rv_done
    else:
        row["disposition"] = "Hospitalized"

    return row


def insert(connection, rows):
    columns = list(rows[0].keys())
    placeholders = ", ".join(["%s"] * len(columns))
    sql = f"INSERT INTO patients ({', '.join(columns)}) VALUES ({placeholders})"
    ids = []
    with connection.cursor() as cursor:
        for row in rows:
            cursor.execute(sql, [row[c] for c in columns])
            ids.append(cursor.lastrowid)
    connection.commit()
    return ids


def store_metrics(ids):
    """Computes the turnaround metrics the reports read from.

    The model prints a line per patient, which buries the summary under
    hundreds of rows, so its output is swallowed and only failures surface.
    """
    from backend.database import AuditTrailModel
    stored = 0
    failures = []
    quiet = io.StringIO()
    for pid in ids:
        try:
            with contextlib.redirect_stdout(quiet):
                AuditTrailModel.calculate_and_store_metrics(pid)
            stored += 1
        except Exception as error:
            failures.append(f"  metrics failed for {pid}: {error}")
    for failure in failures:
        print(failure)
    return stored


def clear(connection):
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM patients WHERE document_id LIKE %s", (PREFIX + "%",))
        removed = cursor.rowcount
    connection.commit()
    return removed


def main():
    password = os.environ.get("MYSQL_PWD")
    if not password:
        import getpass
        password = getpass.getpass(f"Password for MySQL user {USER}: ")

    # Use the server the application is configured against, not a hardcoded one,
    # so this works unchanged when config.ini points somewhere other than localhost.
    from backend.database import AuthenticationModel, ConfigurationModel
    host = ConfigurationModel.load_configuration()
    AuthenticationModel.set_server(host)
    ok, message = AuthenticationModel.validate_credentials(USER, password)
    if not ok:
        print("Could not authenticate:", message)
        return 1

    connection = connect(host, password)
    try:
        if "--clear" in sys.argv:
            print(f"removed {clear(connection)} seeded patients")
            return 0

        count = 60
        for arg in sys.argv[1:]:
            if arg.isdigit():
                count = int(arg)

        existing = clear(connection)
        if existing:
            print(f"removed {existing} previously seeded patients")

        rows = [build_patient(i + 1) for i in range(count)]
        ids = insert(connection, rows)
        print(f"inserted {len(ids)} synthetic patients")
        print(f"stored metrics for {store_metrics(ids)} of them")

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT disposition, COUNT(*) FROM patients WHERE document_id LIKE %s "
                "GROUP BY disposition", (PREFIX + "%",))
            print("\nby disposition:")
            for disposition, total in cursor.fetchall():
                print(f"  {disposition or '(still in care)':18} {total}")
            cursor.execute(
                "SELECT triage, COUNT(*) FROM patients WHERE document_id LIKE %s "
                "GROUP BY triage ORDER BY triage", (PREFIX + "%",))
            print("by triage level:")
            for level, total in cursor.fetchall():
                print(f"  level {level:14} {total}")
    finally:
        connection.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
