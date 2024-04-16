"""Function to set the status of assignments back to 'enrolled'."""

import datetime
import sqlite3
from contextlib import closing

import utils.constants as consts
from utils import db_utils
from utils.logger import logger


def reset_assignment_status(
    database_name: str,
    target_id=None,
    target_type=None,
    semester=None,
):
    logger.info(
            f"Setze Belegungsstatus von Einträgen in {database_name} zurück...",
        )
    database_path = db_utils.get_db_path(database_name, True)
    with closing(sqlite3.connect(database_path)) as conn:
        cursor = conn.cursor()

        assignment_status_values = (
            consts.RULE_SETTING_STATUS_ACCEPTED,
            consts.RULE_SETTING_STATUS_DENIED,
            "HP",
            "NP",
            "ST",
        )

        # Set the condition based on the provided parameters
        query_condition = None
        if target_id is not None and target_type is not None:
            query_condition = f"{target_type} = {target_id}"
        elif semester is not None and isinstance(semester, (int, float)):
            query_condition = f"semester = {semester}"

        # Build sql query string with conditions
        query = f"SELECT * FROM {consts.TABLE_NAME_ASSIGNMENTS} WHERE status IN (?, ?, ?, ?, ?)"
        if query_condition is not None:
            query += f" AND {query_condition}"

        # Execute query and fetch all rows
        cursor.execute(query, assignment_status_values)
        rows = cursor.fetchall()

        # Get kombotrigger rows
        query += " AND systemnachricht = 'Kombotrigger'"
        cursor.execute(query, assignment_status_values)
        rows_combo = cursor.fetchall()

        # Set new status
        for row in rows:
            cursor.execute(
                f"UPDATE {consts.TABLE_NAME_ASSIGNMENTS} SET status = ?, zeitstempel = ? WHERE _pk_id = ?",
                (
                    consts.RULE_SETTING_STATUS_ENROLLED,
                    str(datetime.datetime.now()),
                    row[0],
                ),
            )

        # Remove kombotrigger rows from db
        for row in rows_combo:
            cursor.execute(
                f"DELETE FROM {consts.TABLE_NAME_ASSIGNMENTS} WHERE _pk_id = ?",
                (row[0],),
            )

        conn.commit()
        db_utils.vacuum_db(conn)

        logger.info(
            f"Der Status von {len(rows)} Belegungen wurde auf '{consts.RULE_SETTING_STATUS_ENROLLED}' gesetzt und {len(rows_combo)} Kombotrigger wurden gelöscht.",
        )

        return len(rows), len(rows_combo)
