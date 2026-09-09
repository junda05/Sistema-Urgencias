# Urgentix — Emergency Department Visualization System

A desktop application that shows every patient currently in a hospital emergency
department on one live board, flags patients who have waited past the department's
service window, and reports on how long each stage of care takes.

**There are two ways to run it:**

| Route | Needs | Go to |
|---|---|---|
| **A — the packaged executable** | MySQL only. No Python. | [Part 1](#part-1--database-setup-both-routes), then [Part 2](#part-2--route-a-run-the-executable) |
| **B — from source** | MySQL and Python 3.8+ | [Part 1](#part-1--database-setup-both-routes), then [Part 3](#part-3--route-b-run-from-source) |

Both routes share the same database setup, which is Part 1. Do that first either way.

---

# Part 1 — Database setup (both routes)

## 1.1 Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Windows | 10 or later | The interface is built for Windows workstations |
| MySQL Server | 8.0 or later | Must be running before you start the application |

You also need the MySQL command line client, installed with MySQL Server. On a default
Windows install it is at:

```
C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe
```

Every command below assumes you have put it in a variable first:

```powershell
$mysql = 'C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe'
```

Check the server is up:

```powershell
Get-Service -Name "*mysql*"
```

## 1.2 Create the database

Creates the `urgentix` database with all tables empty:

```powershell
Get-Content database\schema.sql | & $mysql -u root -p
```

> ⚠️ This script begins with `DROP DATABASE IF EXISTS urgentix`. That makes it safe to
> re-run while you are setting things up, but it destroys everything in that database —
> patients, users and loaded catalogs alike. Run it once, at the start. If you later want
> a clean slate, re-running it is the way to get one, and you will need to repeat steps
> 1.3 to 1.5 afterwards.

Run it as `root`. The script creates the database and a view, and the account that creates
that view owns it, so a later account with rights only on `urgentix` cannot replace it.

> PowerShell does not support the `<` redirection used on Linux shells, which is why
> this uses `Get-Content` and a pipe.

Verify — this should report **9** (eight tables plus one view):

```powershell
& $mysql -u root -p -e "SELECT COUNT(*) AS objects FROM information_schema.tables WHERE table_schema='urgentix';"
```

## 1.3 Create the administrator account

The application keeps no password list of its own. Every user is a **MySQL account**, and
what they may do is enforced by database privileges. Each account also needs a matching
row in the `users` table, which is what carries the role.

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

> ⚠️ These are documented defaults for a local evaluation instance. Change the password,
> in MySQL and in `config.ini`, before any real deployment.

## 1.4 Load the test data

The system ships with an empty database — no patient data is delivered with it. That is
the right default for clinical software, but it leaves you looking at a blank board, and
the reports need finished episodes before they can measure anything.

`database/seed_test_data.sql` fills it with 60 invented patients. It is plain SQL, so it
works for both routes and needs no Python:

```powershell
Get-Content database\seed_test_data.sql | & $mysql -u emergency_admin -p
```

It prints `Seeded patients loaded: 60` when it finishes.

Everything in it is fabricated — names, document numbers and timings are randomly
generated, and nothing real is included. The patients are spread across every care path
and every triage level, so each part of the system has something to show:

- **discharged patients** give the reports their turnaround times;
- **patients under observation** trigger the 12-hour alarm;
- **patients still in care** populate the board itself;
- triage times are drawn so most patients meet the target for their level and some miss
  it badly, which is what makes the SLA gauges show something other than a flat 100%.

Every timestamp in the file is written relative to the moment you load it, so the data is
always recent no matter when you run it, and the alarms behave as they would in a live
department.

To remove it again — every seeded record has a document number starting with `SEED`, so
this touches nothing else:

```powershell
& $mysql -u emergency_admin -p -e "DELETE FROM urgentix.patients WHERE document_id LIKE 'SEED%';"
```

Loading the file again replaces the previous batch rather than adding to it.

## 1.5 Create users for the other two roles

The seeded data covers patients, not accounts. The administrator account above only shows
you the administrator view. To see the doctor and waiting-room views you need a user in
each role:

```powershell
& $mysql -u emergency_admin -p -e @"
CREATE USER IF NOT EXISTS 'test_doctor'@'%' IDENTIFIED BY 'TestDoctor2026!';
GRANT SELECT, INSERT, UPDATE, DELETE ON urgentix.* TO 'test_doctor'@'%';
CREATE USER IF NOT EXISTS 'test_visitor'@'%' IDENTIFIED BY 'TestVisitor2026!';
GRANT SELECT ON urgentix.* TO 'test_visitor'@'%';

INSERT INTO urgentix.users (username, full_name, role_doctor)
VALUES ('test_doctor', 'Test Doctor', TRUE);
INSERT INTO urgentix.users (username, full_name, role_visitor)
VALUES ('test_visitor', 'Test Visitor', TRUE);
"@
```

This runs as `emergency_admin`, not root: step 1.3 granted it `CREATE USER ... WITH GRANT
OPTION` for exactly this. Note there is no `FLUSH PRIVILEGES` — `CREATE USER` and `GRANT`
apply immediately, and flushing needs the `RELOAD` privilege, which this account
deliberately does not have.

| User | Password | Sees |
|---|---|---|
| `emergency_admin` | `Urgentix2026!` | Everything: patients, users, reports, audit trail |
| `test_doctor` | `TestDoctor2026!` | Patients and area filtering; no user management, no reports |
| `test_visitor` | `TestVisitor2026!` | Waiting-room display: masked names, no disposition, auto-paging |

Log out and back in to switch between views.

Once you can log in, you can create further users from **Menu → Create user** inside the
application, which creates the MySQL account and the role row in one step.

---

# Part 2 — Route A: run the executable

No Python, no dependencies. You need Part 1 done and MySQL running.

## 2.1 Check the folder layout

```
deliverable/
  executable/
    Urgentix.exe      <- run this
    config.ini        <- must stay beside the executable
inputs/
  laboratory_test_catalog.xlsx
  imaging_procedure_catalog.xlsx
  radiology_procedure_catalog.xlsx
```

Two things matter here:

- **`config.ini` must sit in the same folder as `Urgentix.exe`.** The executable reads its
  server address from beside itself, not from the source folder.
- **The `inputs` folder must be reachable.** On first login the application imports the
  exam catalogs from those spreadsheets. It looks for a folder named `inputs`, `data` or
  `catalogs` beside the executable and up to two levels above it, which is why the layout
  delivered in this package works as-is. If you move the executable somewhere else, copy
  `inputs` next to it.

## 2.2 Point it at your server

`executable/config.ini`:

```ini
[DATABASE]
host = localhost
```

Leave `localhost` for a local MySQL. For a shared server put its hostname or IP here — or
change it at run time from **Settings**, at the bottom left of the login screen, with no
rebuild.

## 2.3 Run

Double-click `Urgentix.exe`, or:

```powershell
.\executable\Urgentix.exe
```

Log in with `emergency_admin` / `Urgentix2026!`.

The first login also imports the exam catalogs, which takes a few seconds. It happens once
— later starts skip it. Then go to [What to try](#what-to-try).

> The executable is built with `--windowed`, so it has no console. If it does not appear,
> the cause is almost always the database: check MySQL is running and that `config.ini`
> points at it.

---

# Part 3 — Route B: run from source

You need Part 1 done, MySQL running, and Python 3.8 or later (3.13 tested).

## 3.1 Install the dependencies

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

## 3.2 Point it at your server

`config.ini` in the project folder — same format and same options as in 2.2:

```ini
[DATABASE]
host = localhost
```

## 3.3 Provide the exam catalogs

The application imports the laboratory and imaging catalogs on first login, from the
spreadsheets delivered with this package. It searches for a folder named `inputs`, `data`
or `catalogs` in the project folder and up to two levels above it, so the delivered layout
works unchanged.

Each file needs the exam code in the first column and the exam name in the second, with
one header row. Expect this in the console on the first login:

```
Exam catalogs loaded: 1107 entries imported.
```

## 3.4 Run

```powershell
python main.py
```

Log in with `emergency_admin` / `Urgentix2026!`.

## 3.5 Regenerating the test data (optional)

Part 1.4 already loaded test data, and that is enough to evaluate the system. If you want
a different volume or a fresh random mix, the generator that produced that SQL file is
included and needs Python:

```powershell
python tools\seed_test_data.py 120      # insert 120 patients instead
python tools\seed_test_data.py --clear  # remove them
```

It asks for the `emergency_admin` password and connects to whatever server `config.ini`
points at, exactly as the application does. Unlike the SQL file it also computes the stage
metrics through the application's own code path, so the two are always consistent.

To freeze a new batch back into `database/seed_test_data.sql`:

```powershell
python tools\export_seed_sql.py
```

---

# What to try

1. **Look at the board** — every patient in the department on one screen, each care
   process shown as a coloured circle. Hover a pending cell to see the specific tests
   still outstanding.
2. **Add a patient** — name, document number, area and cubicle are required. The name must
   have at least three words. Set Triage to `2` and leave Admission Consult as
   `Not completed`.
3. **Try to break the sequence** — mark the admission consult complete before setting a
   triage level, or order labs before the admission consult is done. The system refuses
   and explains why; a board that can be put into an impossible state is worse than no
   board.
4. **Attach exams** — open a patient, set Labs to `Awaiting results`, then pick tests from
   the catalog.
5. **Watch for an alarm** — a triage 2 patient whose admission consult is still not
   completed 30 minutes after triage starts blinking. Triage 3 allows 120 minutes; a
   patient held in Observation is flagged after 12 hours. The seeded data includes
   patients in all three situations.
6. **Generate a report** — Menu → Generate reports. Group mode gives average, median and
   P90 per stage plus the SLA compliance gauges; individual mode compares one patient
   against their area. Both export to PDF.
7. **Check the audit trail** — Menu → Traceability lists every action with who did it and
   what changed.
8. **See the other views** — log out and back in as `test_doctor`, then as `test_visitor`,
   to see area filtering and the masked public display.

---

# Roles

| Role | Can do |
|---|---|
| **Administrator** | Everything: manage patients, create users, change roles, reports, audit trail |
| **Doctor** | Manage patients and filter by area. No user management, no reports |
| **Visitor** | Read only, for waiting-room screens. Names and document numbers masked, no disposition column, pages automatically |

The role comes from the row in the `users` table; what the account may actually do comes
from its MySQL privileges. Both halves matter.

---

# Project layout

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
  seed_test_data.sql        Synthetic patients for evaluation (Part 1.4)

tools/
  seed_test_data.py         Generates synthetic patients (Part 3.5)
  export_seed_sql.py        Freezes generated patients into seed_test_data.sql

executable/
  Urgentix.exe              Single-file build, runs without Python
  config.ini                Configuration for the packaged build
```

To rebuild the executable:

```powershell
python build_exe.py
```

The result is written to `dist/`. The build bundles the interface assets and explicitly
collects the QtWebEngine components the report view needs.

---

# Troubleshooting

**"Error trying to connect: Access denied"** — the username or password is not a valid
MySQL account, or it has no privileges on `urgentix`. Re-run step 1.3.

**"Can't connect to MySQL server"** — MySQL is not running, or the host in `config.ini` is
wrong:

```powershell
Get-Service -Name "*mysql*"
```

**The executable starts and nothing appears** — it is built windowed, so it has no console
to show the error. It is nearly always the database: confirm MySQL is running and that
`config.ini` sits beside the executable with the right host.

**The exam selector is empty** — the catalogs did not load, because the `inputs` folder was
not found. See 2.1 for the executable or 3.3 for source. To force a reload, empty both
catalog tables and log in again:

```sql
DELETE FROM lab_catalog;
DELETE FROM imaging_catalog;
```

**The board is empty** — no patient data ships with the system. Load the test data, step
1.4.

**The reports show `--` everywhere** — `--` means "no data in range", deliberately rather
than `0`, which would read as "instant". Either no patients finished the stage inside the
selected date range, or the test data was not loaded. Widen the date filter, or run step
1.4.

**The report window opens but stays blank** — QtWebEngine is missing. Reinstall with
`pip install PyQtWebEngine` (source route only; the executable bundles it).

**A patient will not save** — name, document number, area and cubicle are mandatory, and
the name must have at least three words. The system also refuses a document number that is
already on the board under a *different* name. If the name matches, it asks whether you
meant to open a second record for the same patient.
