"""
Urgentix - Emergency Department Visualization System
First-run loader for the orderable exam catalogs.

The department's laboratory and imaging catalogs arrive as spreadsheet exports
from the hospital's own systems. The first time the application starts against
an empty database it imports them automatically, so the deployment is a single
step for whoever installs it. Once the catalogs hold rows the import is skipped,
which makes starting the application idempotent.

Spreadsheets are read with the standard library alone: an .xlsx file is a ZIP of
XML parts, so no third-party spreadsheet dependency is needed at runtime and the
packaged executable stays small.
"""
import os
import sys
import zipfile
import xml.etree.ElementTree as ElementTree

SPREADSHEET_NS = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
TEXT_TAG = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"
ROW_TAG = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row"

# Spreadsheet file name -> (target table, code column, name column)
CATALOG_SOURCES = [
    ("laboratory_test_catalog.xlsx", "lab_catalog", "lab_code", "lab_name"),
    ("imaging_procedure_catalog.xlsx", "imaging_catalog", "imaging_code", "imaging_name"),
    ("radiology_procedure_catalog.xlsx", "imaging_catalog", "imaging_code", "imaging_name"),
]

# Folders searched for the spreadsheets, relative to the application root
CANDIDATE_FOLDERS = ["inputs", "data", "catalogs", os.path.join("..", "inputs")]


def application_root():
    """Root folder of the application, whether running from source or frozen."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def find_catalog_folder():
    """Returns the first folder that holds at least one catalog spreadsheet."""
    root = application_root()
    for folder in CANDIDATE_FOLDERS:
        candidate = os.path.normpath(os.path.join(root, folder))
        if not os.path.isdir(candidate):
            continue
        for file_name, _, _, _ in CATALOG_SOURCES:
            if os.path.exists(os.path.join(candidate, file_name)):
                return candidate
    return None


def read_spreadsheet(path):
    """Reads an .xlsx file and returns its rows as lists of cell strings."""
    with zipfile.ZipFile(path) as workbook:
        shared_strings = []
        if "xl/sharedStrings.xml" in workbook.namelist():
            root = ElementTree.fromstring(workbook.read("xl/sharedStrings.xml"))
            for item in root.findall("main:si", SPREADSHEET_NS):
                shared_strings.append("".join(node.text or "" for node in item.iter(TEXT_TAG)))

        sheets = sorted(n for n in workbook.namelist() if n.startswith("xl/worksheets/sheet"))
        if not sheets:
            return []
        root = ElementTree.fromstring(workbook.read(sheets[0]))

        rows = []
        for row in root.iter(ROW_TAG):
            values = []
            for cell in row.findall("main:c", SPREADSHEET_NS):
                cell_type = cell.get("t")

                # Writers differ: some store text in a shared table, others
                # inline it in the cell. Both forms appear in real exports.
                if cell_type == "inlineStr":
                    inline = cell.find("main:is", SPREADSHEET_NS)
                    text = "".join(node.text or "" for node in inline.iter(TEXT_TAG)) if inline is not None else ""
                    values.append(text)
                    continue

                value = cell.find("main:v", SPREADSHEET_NS)
                if value is None or value.text is None:
                    values.append("")
                elif cell_type == "s":
                    values.append(shared_strings[int(value.text)])
                else:
                    values.append(value.text)
            rows.append(values)
        return rows


def read_catalog_entries(path):
    """Returns the (code, name) pairs from a catalog spreadsheet, skipping its header."""
    entries = []
    for row in read_spreadsheet(path)[1:]:
        if len(row) < 2:
            continue
        code, name = str(row[0]).strip(), str(row[1]).strip()
        if code and name:
            entries.append((code, name))
    return entries


def catalogs_are_empty(cursor):
    """True when neither exam catalog holds any row yet."""
    cursor.execute("SELECT COUNT(*) FROM lab_catalog")
    labs = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM imaging_catalog")
    imaging = cursor.fetchone()[0]
    return labs == 0 and imaging == 0


def ensure_catalogs_loaded(connection):
    """
    Imports the exam catalogs if they have not been loaded yet.

    Returns a (loaded, message) tuple. `loaded` is False both when the catalogs
    were already populated and when the spreadsheets could not be found, so the
    caller can surface the message without treating either case as a failure.
    """
    try:
        with connection.cursor() as cursor:
            if not catalogs_are_empty(cursor):
                return False, "Exam catalogs already loaded."

            folder = find_catalog_folder()
            if folder is None:
                return False, (
                    "Exam catalogs are empty and the source spreadsheets were not found. "
                    "Place them in an 'inputs' folder next to the application and restart."
                )

            inserted = 0
            for file_name, table, code_column, name_column in CATALOG_SOURCES:
                path = os.path.join(folder, file_name)
                if not os.path.exists(path):
                    continue
                for code, name in read_catalog_entries(path):
                    cursor.execute(
                        f"INSERT IGNORE INTO {table} ({code_column}, {name_column}) VALUES (%s, %s)",
                        (code, name),
                    )
                    inserted += cursor.rowcount

        connection.commit()
        if inserted == 0:
            return False, (
                f"Exam catalog spreadsheets were found in {folder} but no rows could be read "
                "from them. Check that each file has the exam code in the first column and "
                "the exam name in the second."
            )
        return True, f"Exam catalogs loaded: {inserted} entries imported."

    except Exception as error:
        return False, f"Could not load the exam catalogs: {error}"
