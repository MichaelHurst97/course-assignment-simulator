"""Functions to create new assignments for lecture combinations."""

import sqlite3
from contextlib import closing

import pandas as pd

import utils.constants as consts
from utils import db_utils
from utils.logger import logger


def get_lecture_combination(lecture_id, group_id, conn):
    """Get the lecture id that belongs to the same lecture.

    Lecture combinations are lectures that e.g. consist of a seminar and
    exercise part.
    """
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM veranstaltung_kombo
        WHERE quell_veranstaltungs_id = ?
            AND quell_gruppen_id = ?
    """,
        (
            lecture_id,
            group_id,
        ),
    )

    result = cursor.fetchall()

    if result:
        # HTW lecture combinations are always 1:1
        row = result[0]
        return {
            "_pk_kombo_id": row[0],
            "quell_veranstaltungs_id": row[1],
            "quell_gruppen_id": row[2],
            "ziel_veranstaltungs_id": row[3],
            "ziel_gruppen_id": row[4],
        }

    else:
        return None


def apply_lecture_combinations(
    df_all_assignments,
    df_rule_applied,
    database_name,
):
    """Check if combination assignment should be made via kombo db table.

    New combination assignments are added on top of the assignment table so
    ids do not clash.
    """
    rows_lecture_combination = []

    database_path = db_utils.get_db_path(database_name, True)
    with closing(sqlite3.connect(database_path)) as conn:
        for _, row in df_rule_applied.iterrows():
            # Copy row to not modify original dataframe
            row = row.copy()

            # If a group id is missing, use the standard group
            if pd.isna(row[consts.COLUMN_NAME_ASSIGNMENTS_GROUP_ID]):
                row[consts.COLUMN_NAME_ASSIGNMENTS_GROUP_ID] = None

            # Get lecture combination for current lecture id and
            # current group id
            lecture_combination = get_lecture_combination(
                row[consts.COLUMN_NAME_ASSIGNMENTS_LECTURE_ID],
                row[consts.COLUMN_NAME_ASSIGNMENTS_GROUP_ID],
                conn,
            )
            if lecture_combination is None:
                continue

            # Change row values to new lecture combination values
            row[consts.COLUMN_NAME_ASSIGNMENTS_STATUS] = (
                consts.RULE_SETTING_STATUS_ACCEPTED
            )
            row[consts.COLUMN_NAME_ASSIGNMENTS_LECTURE_ID] = (
                lecture_combination["ziel_veranstaltungs_id"]
            )
            row[consts.COLUMN_NAME_ASSIGNMENTS_SYSTEM_MESSAGE] = "Kombotrigger"
            row[consts.COLUMN_NAME_ASSIGNMENTS_GROUP_ID] = lecture_combination[
                "ziel_gruppen_id"
            ]
            row["kombo_id"] = lecture_combination["_pk_kombo_id"]

            rows_lecture_combination.append(row)

    df_lecture_combination = pd.DataFrame(rows_lecture_combination)

    if not df_lecture_combination.empty:
        # Get highest index number from complete assignment table and use that
        # as starting point for the combo lecture indices
        highest_index_all_assignments = df_all_assignments.index.max()
        df_lecture_combination.index = range(
            highest_index_all_assignments + 1,
            highest_index_all_assignments + 1 + len(df_lecture_combination),
        )

        # Add lecture combinations to end of assignment table
        df_all_assignments = pd.concat(
            [df_all_assignments, df_lecture_combination],
            ignore_index=False,
            verify_integrity=True,
        )

        logger.info(
            f"Es wurden {len(df_lecture_combination.index)} neue"
            " Kombo-Einschreibungen getätigt",
        )

    else:
        logger.info("Keine Kombo-Einschreibungen gefunden")

    return df_all_assignments, df_lecture_combination
