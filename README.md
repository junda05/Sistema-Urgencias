# Urgentix — Emergency Department Visualization System

A desktop application that shows every patient currently in a hospital emergency
department on one live board, flags patients who have waited past the
department's service window, and reports on how long each stage of care takes.

This file is the setup guide. Follow it top to bottom and the application will
run against a clean database with no manual data entry.

---

## 1. Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Windows | 10 or later | The interface is built for Windows workstations |
| Python | 3.8 or later (3.13 tested) | Only needed to run from source |
| MySQL Server | 8.0 or later | Must be running before you start the application |

You also need the MySQL command line client, installed with MySQL Server. On a
default Windows install it is at:

```
C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe
```

---

## 2. Install the Python dependencies

From the project folder:

```powershell
pip install -r requirements.txt
```

Or, for an isolated environment:

```powershell
pip install pipenv
$env:PIPENV_VENV_IN_PROJECT = "1"
pipenv install -r requirements.txt
```

---

## 3. Create the database

Creates the `urgentix` database with all tables empty. Run from the project
folder, in PowerShell:

```powershell
$mysql = 'C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe'
Get-Content database\schema.sql | & $mysql -u root -p
```

> PowerShell does not support the `<` redirection used on Linux shells, which is
> why this uses `Get-Content` and a pipe.

Verify — this should report **9** (eight tables plus one view):

```powershell
& $mysql -u root -p -e "SELECT COUNT(*) AS objects FROM information_schema.tables WHERE table_schema='urgentix';"
```

---

## 4. Create the application account

The application does not keep its own password list. Every user is a **MySQL
account**, and what they may do is enforced by database privileges. Each account
also needs a matching row in the `users` table, which is what carries the role.

Create the default administrator:

```powershell
& $mysql -u root -p -e @"
CREATE USER IF NOT EXISTS 'emergency_admin'@'%' IDENTIFIED BY 'Urgentix2026!';
GRANT ALL PRIVILEGES ON urgentix.* TO 'emergency_admin'@'%' WITH GRANT OPTION;
GRANT CREATE USER ON *.* TO 'emergency_admin'@'%' WITH GRANT OPTION;
FLUSH PRIVILEGES;
INSERT INTO urgentix.users (username, full_name, role_admin)
VALUES ('emergency_admin', 'System Administrator', TRUE);
"@
```

**Default credentials for evaluation:**

| Field | Value |
|---|---|
| Username | `emergency_admin` |
| Password | `Urgentix2026!` |
| Role | Administrator |

These same values are set in `config.ini`, which the application uses for
administrative operations such as creating further users.

> ⚠️ These are documented defaults for a local evaluation instance. Change the
> password, in MySQL and in `config.ini`, before any real deployment.

---

## 5. Point the application at the server

`config.ini` in the project folder:

```ini
[DATABASE]
host = localhost
```

Leave `localhost` for a local MySQL. For a shared server, put its hostname or IP
here — or change it at run time from **Settings**, at the bottom left of the
login screen, with no rebuild.

---

## 6. Provide the exam catalogs

The laboratory and imaging catalogs are department reference data, delivered as
spreadsheet exports. Put them in a folder named `inputs` next to the project
folder (this is where they already are in this package):

```
inputs/
├── laboratory_test_catalog.xlsx      1,052 laboratory tests
├── imaging_procedure_catalog.xlsx      398 imaging procedures
└── radiology_procedure_catalog.xlsx     64 radiology procedures
```

The application also looks for `inputs`, `data` or `catalogs` inside the project
folder itself. Each file needs the exam code in the first column and the exam
name in the second, with one header row.

**You do not import these by hand.** The first time anyone logs in against an
empty database the application reads the spreadsheets and loads them, then skips
the import on every later start. Expect this in the console on that first login:

```
Exam catalogs loaded: 1107 entries imported.
```

---

## 7. Run

```powershell
python main.py
```

Log in with `emergency_admin` / `Urgentix2026!`.

---

## 8. What to try

The board starts empty, which is expected: no patient data ships with the system.

1. **Add a patient** — name, document number, area and cubicle are required. Set
   Triage to `2` and leave Admission Consult as `Not completed`.
2. **Watch the pending column** — the system derives outstanding work by itself.
3. **Attach exams** — open the patient, set Labs to `Awaiting results`, then pick
   tests from the catalog. The system refuses exams while the stage status is
   unset, and refuses them before triage and the admission consult are complete.
4. **Watch for an alarm** — a triage 2 patient whose admission consult is still
   not completed 30 minutes after triage starts blinking. Triage 3 allows 120
   minutes; a patient held in Observation is flagged after 12 hours.
5. **Generate a report** — Menu → Generate reports. Group and individual modes,
   average / median / P90 per stage, exportable to PDF.
6. **Check the audit trail** — Menu → Traceability lists every action with who
   did it and what changed.
7. **See the public view** — create a visitor-role user and log in as them to see
   masked names and document numbers.

Reports need discharged patients to have something to measure, so add a patient,
move them through the stages and set the disposition to `Discharged`.

---

## 9. Roles

| Role | Can do |
|---|---|
| **Administrator** | Everything: manage patients, create users, change roles, reports, audit trail |
| **Doctor** | Manage patients and filter by area. No user management, no reports |
| **Visitor** | Read only, for waiting-room screens. Names and document numbers masked, no disposition column, pages automatically |

Create further users from **Menu → Create user**, which also creates the matching
MySQL account.

---

## 10. Packaged executable

`executable/Urgentix.exe` runs without Python installed. Keep `config.ini` beside
it and make sure the `inputs` folder is reachable, then run the executable and
follow steps 3, 4 and 5 above for the database.

To rebuild it:

```powershell
python build_exe.py
```

The result is written to `dist/`. The build bundles the interface assets and
explicitly collects the QtWebEngine components the report view needs.

---

## 11. Project layout

```
main.py                     Application entry point
config.ini                  Server address and bootstrap account
requirements.txt            Python dependencies
build_exe.py                PyInstaller build script

backend/
  database.py               Configuration, authentication, patients, audit trail
  metrics_model.py          Turnaround time metrics for reports
  catalog_loader.py         First-run import of the exam catalogs
  users/                    Users, preferences, waiting-room and auth models

frontend/
  login_interface.py        Login and server settings
  admin.py                  Administrator view
  doctors.py                Doctor view
  waiting_room.py           Public waiting-room display
  images/                   Interface assets
  styles/                   Reusable UI components, report generator, PDF export

database/
  schema.sql                Database schema, tables empty

executable/
  config.ini                Configuration for the packaged build
```

---

## 12. Troubleshooting

**"Error trying to connect: Access denied"** — the username or password is not a
valid MySQL account, or it has no privileges on `urgentix`. Re-run step 4.

**"Can't connect to MySQL server"** — MySQL is not running, or the host in
`config.ini` is wrong. Check with:

```powershell
Get-Service -Name "*mysql*"
```

**The exam selector is empty** — the catalogs did not load. The console prints
the reason on login. Usually the `inputs` folder is not where the application
looks; see step 6. To force a reload, empty both catalog tables and log in again:

```sql
DELETE FROM lab_catalog;
DELETE FROM imaging_catalog;
```

**The report window opens but stays blank** — QtWebEngine is missing. Reinstall
with `pip install PyQtWebEngine`.

**A patient will not save** — name, document number, area and cubicle are
mandatory. The system also refuses a second active record for a document number
that is already admitted.
