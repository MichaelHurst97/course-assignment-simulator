"""Use to apply custom functions after importing data.

Can alter imported databases, so their data adheres to the Base DB
Structure standard.

In this example, an assignment column that marks first assignments is filled
based on if the student booked already booked a course some semesters ago.
Also data marked as inactive is being removed.

All functions added to run_custom_import_patches() are run by importer,
as the last step when importing.
"""

from utils import db_utils
from utils.logger import logger

# Code in this module doesn't use global table and column names
# because the patching functionality is unique to the HTW dataset.


def patch_column_first_assignment(conn):
    """Add a yes or no value to the 'erstbelegung' column to mark if
    someone was already accepted for a lecture in a previous semester.
    """
    cursor = conn.cursor()

    # Find duplicates where matrikelnummer and lecture text are the same,
    # but semester differs. This means a student has already been accepted
    # for a course. It's import to check and group per semester, as a
    # semester + lecture can have multiple assignments for each student
    cursor.execute(
        """
        CREATE TABLE temp AS
        SELECT b.matrikelnummer, b.semester, v.text, b.veranstaltungs_id, v._pk_id,
                COUNT(*) OVER(PARTITION BY b.matrikelnummer, v.text) as count
        FROM belegungen b
        JOIN veranstaltung v ON b.veranstaltungs_id = v._pk_id
        GROUP BY matrikelnummer, text;
        """,
    )
    
    cursor.execute(
        """
        UPDATE belegungen
        SET erstbelegung = "N"
        """,
    )
    cursor.execute(
        """
        UPDATE belegungen
        SET erstbelegung = 'J'
        WHERE (matrikelnummer, veranstaltungs_id) IN (
            SELECT matrikelnummer, _pk_id
            FROM temp
        )
        """,
    )
    
    cursor.execute("""DROP TABLE IF EXISTS temp""")

    cursor.close()


def delete_inactive_lectures(conn):
    """Delete assignments with inactive lectures."""
    cursor = conn.cursor()
    cursor.execute(
        """
        DELETE FROM belegungen
        WHERE _pk_id IN (
            SELECT belegungen._pk_id
            FROM belegungen
            JOIN veranstaltung ON belegungen.veranstaltungs_id = veranstaltung._pk_id
            WHERE veranstaltung.status = 'I'
            )
        """,
    )
    cursor.close()


def delete_row_conditionally(
    table: str,
    column: str,
    operand: str,
    condition,
    conn,
):
    """Execute a sql delete statement with conditions."""
    cursor = conn.cursor()
    cursor.execute(
        f"DELETE FROM {table} WHERE {table}.{column} {operand} {condition}",
    )
    cursor.close()


def add_incomings_study_program(conn):
    """Add 'studiengang' with number 999.

    Incomings get registered to this study program number.
    Missing in original import files but present in imported assignment data.
    """
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO studiengang (_pk_id, status, kurztext, text, fachbereich, studiumstyp, abschluss, regelstudienzeit, po_version, studienfach) 
        VALUES (999, 'A', 'INCOMINGS', 'PLATZHALTER FÜR INCOMINGS', 99, 'V', 99, 1, 99999, 999)
        """,
    )
    cursor.close()


def fill_zuordnung_semester(conn):
    """Fill in missing NULL semester values for rule compatibility.

    This enables a semester_bis based rule to work properly.
    """
    cursor = conn.cursor()

    # Set empty semester_von and semester_bis to a large range
    cursor.execute(
        "UPDATE zuordnung_stg_va_beleg SET semester_von = 0 WHERE semester_von IS NULL",
    )
    cursor.execute(
        "UPDATE zuordnung_stg_va_beleg SET semester_bis = 999 WHERE semester_bis IS NULL",
    )

    # Set semester_bis to 999 if it is set to 0.
    # Lectures that have semester_von 0 and semester_0 mostly aren't present
    # in DB because they are inacative.
    cursor.execute(
        "UPDATE zuordnung_stg_va_beleg SET semester_bis = 999 WHERE semester_von = 0 AND semester_bis = 0",
    )

    # Add lectures that dont exist in zuordnung
    cursor.execute(
        """INSERT INTO zuordnung_stg_va_beleg (veranstaltungs_id, studiengangs_id, semester_von, semester_bis, fachart_id)
        SELECT v._pk_id, 0, 0, 99, 3
        FROM veranstaltung v
        LEFT JOIN zuordnung_stg_va_beleg z ON v._pk_id = z.veranstaltungs_id
        WHERE z.veranstaltungs_id IS NULL
        """,
    )

    cursor.close()


def run_custom_import_patches(conn):
    """Run import functions to manipulate imported data.

    Alterations should not modify the base db structure, only the data.
    """
    logger.info(
        "Löscht inaktive Veranstaltungen und Studiengänge aus Datenbank...",
    )
    delete_inactive_lectures(conn)
    delete_row_conditionally("veranstaltung", "status", "=", "'I'", conn)
    delete_row_conditionally("studiengang", "status", "=", "'I'", conn)

    logger.info(
        "Patched Datenbank mit Erstbelegungsdaten und weiteren"
        " fehlenden Daten...",
    )
    patch_column_first_assignment(conn)
    add_incomings_study_program(conn)
    fill_zuordnung_semester(conn)

    conn.commit()
    db_utils.vacuum_db(conn)
