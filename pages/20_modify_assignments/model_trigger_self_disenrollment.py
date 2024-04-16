"""Function to apply a self disenroll status on assignments by chance."""

import datetime
import random
import sqlite3
from contextlib import closing

import utils.constants as consts
from utils import db_utils
from utils.logger import logger


def trigger_self_disenrollment_chance(
    target_id,
    database_name,
    target_type="veranstaltungs_id",
    probability=consts.GENERATOR_SETTING_DEFAULT_DISENROLL_CHANCE,
):
    logger.info(
        f"Löse Selbstabmeldungen für {target_type} {target_id} aus...",
    )
    database_path = db_utils.get_db_path(database_name, True)
    with closing(sqlite3.connect(database_path)) as conn:
        cursor = conn.cursor()

        cursor.execute(
            f"SELECT * FROM {consts.TABLE_NAME_ASSIGNMENTS}"
            f" WHERE {target_type} = ?"
            " AND status IN (?, ?)",
            (
                target_id,
                consts.RULE_SETTING_STATUS_ACCEPTED,
                consts.RULE_SETTING_STATUS_ENROLLED,
            ),
        )
        rows = cursor.fetchall()
        count = 0

        for row in rows:
            # random.random() generates a floating point value between 0 and 1
            if random.random() < probability:
                cursor.execute(
                    f"UPDATE {consts.TABLE_NAME_ASSIGNMENTS}"
                    " SET status = ?, zeitstempel = ?"
                    " WHERE _pk_id = ?",
                    (
                        consts.RULE_SETTING_STATUS_SELF_DISENROLLED,
                        str(datetime.datetime.now()),
                        row[0],
                    ),
                )
                count += 1

        conn.commit()

        logger.info(
            f"Es wurden {count} Belegungen auf Status"
            f" {consts.RULE_SETTING_STATUS_SELF_DISENROLLED} gesetzt",
        )

        return count
