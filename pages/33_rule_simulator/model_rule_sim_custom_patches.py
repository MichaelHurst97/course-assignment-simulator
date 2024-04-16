"""Use to resolve table join overflows conditionally."""

import pandas as pd

import utils.constants as consts


def run_custom_rule_patches(table2: str, dtypes: dict, conn):
    """Patch data overflows when joining database tables.

    This happens when a left join is made and the right side has more entries.
    As the script merges dataframes via foreign keys programmatically, this
    patch is needed to have a "WHERE" clause, limiting student entries from
    historical semesters other than the current one.
    """
    # Students have db entries for each semester, only use the current one
    if table2 == "studierende":
        return pd.read_sql_query(
            f"SELECT * FROM studierende"
            f" WHERE {consts.COLUMN_NAME_STUDENT_SEMESTER} ="
            f" {consts.RULE_SETTING_CURRENT_SEMESTER} LIMIT 1",
            conn,
            dtype=dtypes,
        )

    # Zuordnung can have multiple study programs.
    # They do not differ in data so limit to one.
    elif table2 == "zuordnung_stg_va_beleg":
        return pd.read_sql_query(
            """
            SELECT *
            FROM (
                SELECT *, ROW_NUMBER() OVER(PARTITION BY veranstaltungs_id ORDER BY veranstaltungs_id) AS rn
                FROM zuordnung_stg_va_beleg
            )
            WHERE rn = 1
            """,
            conn,
            dtype=dtypes,
        )

    # Studiengang can have multiple values for studienfach, depending on PO
    # version. Use the newest one because data between the versions does
    # not differ, except for standard period of study, which is sparingly
    # set anyways.
    elif table2 == "studiengang":
        return pd.read_sql_query(
            """
            SELECT *
            FROM (
                SELECT *
                FROM studiengang
                ORDER BY po_version DESC
            )
            GROUP BY studienfach
            """,
            conn,
            dtype=dtypes,
        )

    else:
        return pd.read_sql_query(f"SELECT * FROM {table2}", conn, dtype=dtypes)
