"""Functions to generate new assignments based on existing ones."""

import datetime
import random
import sqlite3
from collections import Counter
from contextlib import closing

import utils.constants as consts
from utils import db_utils
from utils.logger import logger


def get_students_data(target_type, target_id, cursor):
    """Return student rows from database.

    Arguments:
    ---------
    target_type: veranstaltungs_id or studiengangs_id
    target_id: corresponding id in database
    cursor: sqlite3 cursor object

    """

    cursor.execute(
        f"""
        SELECT *
        FROM studierende s
        JOIN {consts.TABLE_NAME_ASSIGNMENTS} b
        ON s._pk_matrikelnummer = b.matrikelnummer
        WHERE b.{target_type} = ?
        """,
        (target_id,),
    )
    return cursor.fetchall()


def delete_assignments(target_type, target_id, cursor):
    """Delete assignments from database.

    Arguments:
    ---------
    target_type: veranstaltungs_id or studiengangs_id
    target_id: corresponding id in database
    cursor: sqlite3 cursor object

    """
    cursor.execute(
        f"""DELETE FROM {consts.TABLE_NAME_ASSIGNMENTS}
        WHERE {target_type} = ?""",
        (target_id,),
    )


def get_probability_distribution(rows: list):
    """Return distribution of probablities across all given rows."""
    distribution = {}
    table_column_count = len(rows[0])
    for i in range(table_column_count):
        column_values = [row[i] for row in rows]
        counter = Counter(column_values)
        total = len(column_values)
        distribution[i] = {
            value: count / total for value, count in counter.items()
        }
    return distribution


def pick_row_values_by_chance(rows: list, distribution: dict, column: list):
    """Return a random column value based on probability distribution."""
    for i in range(len(rows[0])):
        if distribution[i]:
            column[i] = random.choices(
                list(distribution[i].keys()),
                weights = distribution[i].values(),
            )[0]
    return column


def generate_new_assignments(
    target_id,
    amount: int,
    database_name: str,
    target_type="veranstaltungs_id",
    database_name_output=None,
    start_matricule_number=None,
    semester_to_generate_for=None,
    delete_lecture_assignments=False,
    assignment_status_to_use=consts.RULE_SETTING_STATUS_ENROLLED,
):
    """Generate new assignment data with corresponding student data based on
    probability distribution of already given assignment data in db.
    """
    logger.info(
        "Starte Generierung von neuen Belegungsdaten...",
    )
    if database_name_output is not None:
        db_utils.duplicate_db(database_name, database_name_output)
        database_name = database_name_output

    database_path = db_utils.get_db_path(
        database_name,
        check_file_presence=True,
    )
    with closing(sqlite3.connect(database_path)) as conn:
        cursor = conn.cursor()

        # Select lecture / study program assignment data to use
        cursor.execute(
            f"""SELECT * FROM {consts.TABLE_NAME_ASSIGNMENTS} 
            WHERE {target_type} = ?""",
            (target_id,),
        )
        rows_assignments = cursor.fetchall()
        if not rows_assignments:
            logger.warning(
                f"{target_type} '{target_id}' hat keine Belegungen."
                " Breche generierung ab",
            )
            return False, None

        # Select other data for lecture
        if target_type == "veranstaltungs_id":
            # Get semester of given lecture
            cursor.execute(
                f"""SELECT semester FROM {consts.TABLE_NAME_ASSIGNMENTS}
                WHERE veranstaltungs_id = ?""",
                (target_id,),
            )
            lecture_semester = cursor.fetchone()[0]
            # Use lecture semester if not specified
            if semester_to_generate_for is None:
                semester_to_generate_for = lecture_semester

            # Get students from lecture
            rows_students = get_students_data(target_type, target_id, cursor)
            if not rows_students:
                logger.warning(
                    f"Keine Studierenden in Veranstaltung '{target_id}'."
                    " Breche generierung ab",
                )
                return False, None

            # Delete all assignments of lecture
            if delete_lecture_assignments:
                delete_assignments(target_type, target_id, cursor)

        # Select other data for study program
        elif target_type == "studiengangs_id":
            # Use current semester if not specified
            if semester_to_generate_for is None:
                semester_to_generate_for = consts.RULE_SETTING_CURRENT_SEMESTER

            # Get all students that made assignments for a given study program
            rows_students = get_students_data(target_type, target_id, cursor)
            if not rows_students:
                logger.warning(
                    f"Keine Studierenden in Studiengang '{target_id}'."
                    " Breche generierung ab",
                )
                return False, None

            if delete_lecture_assignments:
                delete_assignments(target_type, target_id, cursor)

        else:
            logger.error(
                f"Für das angegebene Ziel '{target_type}' können keine"
                " Belegungen generiert werden, bitte veranstaltungs_id oder"
                " studiengangs_id wählen.",
            )
            return False, None

        # Get highest matricule number and put all generated students after
        if not start_matricule_number:
            cursor.execute("SELECT MAX(_pk_matrikelnummer) FROM studierende")
            start_matricule_number = cursor.fetchone()[0] + 1

        # Get highest assignment id and put all generated assignments after
        cursor.execute(
            f"""SELECT MAX(_pk_id) 
                        FROM {consts.TABLE_NAME_ASSIGNMENTS}""",
        )
        start_assignment_number = cursor.fetchone()[0] + 1

        # Get distributions of probabilities
        distribution_assignments = get_probability_distribution(
            rows_assignments,
        )
        distribution_students = get_probability_distribution(
            rows_students,
        )

        logger.info(
            f"Generiere {amount} Belegungen und zugehörige Studierende Person"
            f" für {target_type} {target_id} im Semester"
            f" {semester_to_generate_for}...",
        )

        # Generate new assignment and corresponding student
        for _ in range(amount):
            # Initialize clean list with column count of
            # assignment / student table
            column_assignment = [None] * len(rows_assignments[0])
            column_student = [None] * len(rows_students[0])

            # Add values to new row depending on probabilities
            column_assignment = pick_row_values_by_chance(
                rows_assignments,
                distribution_assignments,
                column_assignment,
            )
            column_student = pick_row_values_by_chance(
                rows_students,
                distribution_students,
                column_student,
            )

            # Create list with probability values and new hard values
            # Assignment
            assignment = [
                start_assignment_number,  # _pk_id
                target_id
                if target_type == "veranstaltungs_id"
                else column_assignment[1],  # veranstaltungs_id
                assignment_status_to_use,  # status
                column_assignment[3],  # wunsch_prio
                column_assignment[4],  # fachsemester
                start_matricule_number,  # matrikelnummer
                target_id
                if target_type == "studiengangs_id"
                else column_assignment[6],  # studiengangs_id
                None,  # sortierwert
                None,  # systemnachricht
                "Sim Init Generierung",  # belegungs_verfahren
                None,  # ex_zwischenspeicher
                column_assignment[11],  # gruppen_id
                semester_to_generate_for,  # semester
                datetime.datetime.now(),  # zeitstempel
                None,  # kombo_id
                random.randint(0, 10000000000000000),  # los_nummer
                column_assignment[16],  # erstbelegung
            ]
            # Add generated rows to assignment table
            cursor.execute(
                f"""INSERT INTO {consts.TABLE_NAME_ASSIGNMENTS}
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                assignment,
            )

            # Student
            # Check if subject semester (fachsemester) is bigger than
            # university semester, if so use the bigger subject semester
            # for consistency
            if column_student[3] > column_student[9]:
                column_student[9] = column_student[3]

            student = [
                start_matricule_number,  # _pk_matrikelnummer
                semester_to_generate_for,  # _pk_semester
                column_student[2],  # _pk_studienfach
                column_student[3],  # fachsemester
                column_student[4],  # einschreibestatus
                column_student[5],  # hoererstatus
                column_student[6],  # studiumsart
                column_student[7],  # studiumstyp
                None,  # ende_grund
                column_student[9],  # hochschulsemester
                column_student[9],  # hochschulsemester_gewichtet
            ]

            cursor.execute(
                f"""INSERT INTO {consts.TABLE_NAME_STUDENT}
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                student,
            )

            start_assignment_number += 1
            start_matricule_number += 1

        conn.commit()
        db_utils.vacuum_db(conn)

        logger.info(
            f"{consts.CONSOLE_GREEN}Generierung von {amount} neuen Belegungen"
            f" und zugehörigen Studierenden für {target_type} {target_id} im"
            f" Semester {semester_to_generate_for} abgeschlossen."
            f"{consts.CONSOLE_ENDCMD}",
        )

        return True, semester_to_generate_for
