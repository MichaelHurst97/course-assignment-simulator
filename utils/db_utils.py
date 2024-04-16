"""Utils for database related operations."""

import datetime
import os
import shutil
import sqlite3
from contextlib import closing
from pathlib import Path

import pandas as pd

from . import constants as consts
from . import file_utils
from .logger import logger


def get_db_path(name: str, check_file_presence=False):
    """Return the path to a database file in the apps db folder."""
    database_folder = file_utils.get_folder(consts.FOLDER_DB)
    database_path = Path(database_folder, name)

    if check_file_presence and not file_utils.check_file_presence(
        database_folder,
        name,
    ):
        logger.error(f"Datenbank-Datei '{database_path}' nicht gefunden.")
        raise FileNotFoundError

    return database_path


def get_db_filelist():
    """Return a list of db files present in the apps db folder."""
    database_folder = file_utils.get_folder(consts.FOLDER_DB)
    files = os.listdir(database_folder)
    return [file for file in files if file.endswith(".db")]


def delete_db(name: str):
    """Delete a db file by name. Must be in the apps db folder."""
    database_path = get_db_path(name)
    try:
        Path.unlink(database_path)
        logger.info(f"Die Datei '{name}' wurde gelöscht.")
    except FileNotFoundError:
        logger.exception(
            f"Die Datei '{name}' wurde nicht gefunden"
            " oder ist bereits gelöscht.",
        )


def rename_db(name: str, name_new: str):
    """Rename a db file. Must be in the apps db folder."""
    database_path = get_db_path(name, check_file_presence=True)
    database_path_new = get_db_path(name_new)

    Path.rename(database_path, database_path_new)
    logger.info(
        f"Die Datei '{name}' wurde in '{name_new}' umbenannt.",
    )


def duplicate_db(name: str, name_new: str):
    """Duplicate a db file. Must be in the apps db folder."""
    database_path = get_db_path(name, check_file_presence=True)
    database_path_new = get_db_path(name_new)

    shutil.copy2(database_path, database_path_new)
    logger.info(
        f"Die Datei '{name}' wurde als neue Datei '{name_new}' dupliziert.",
    )


def get_db_info(name: str):
    """Return various information about a database file.

    Output contains the given name, contents of the internal metainfo table,
    and file size.
    """
    database_path = get_db_path(name, check_file_presence=True)
    with closing(sqlite3.connect(database_path)) as conn:
        cursor = conn.cursor()

        # Select first row (there should only be one row in internal table)
        try:
            cursor.execute(
                f"""SELECT * FROM {consts.TABLE_NAME_INTERNAL} LIMIT 1""",
            )
            info = cursor.fetchone()
            columns = [description[0] for description in cursor.description]
            db_info = dict(zip(columns, info, strict=False))
            db_info["name"] = name
            db_info["filesize"] = file_utils.get_filesize(database_path)
            return db_info

        except sqlite3.OperationalError:
            logger.exception(
                f"Fehler beim Laden der Informationen für Tabelle '{name}'.",
            )
            raise


def get_df(
    name: str,
    table: str,
    condition: str = None,
    condition_value: str = None,
):
    """Return a dataframe for given db file and one of it's table names."""
    database_path = get_db_path(name, check_file_presence=True)

    base_db_structure = file_utils.read_json(
        consts.FOLDER_UTILS,
        consts.FILENAME_BASE_DB_STRUCTURE,
    )
    dtypes = get_dtypes(base_db_structure, table)
    if condition and condition_value:
        with closing(sqlite3.connect(database_path)) as conn:
            return pd.read_sql_query(
                f"SELECT * FROM {table} WHERE {condition} = {condition_value}",
                conn,
                dtype=dtypes,
            )

    with closing(sqlite3.connect(database_path)) as conn:
        return pd.read_sql_query(f"SELECT * FROM {table}", conn, dtype=dtypes)


def get_column_names(name: str, table: str):
    """Return the column names for a given db file and table."""
    database_path = get_db_path(name, check_file_presence=True)
    with closing(sqlite3.connect(database_path)) as conn:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        return [column[1] for column in cursor.fetchall()]


def get_dtypes(base_db_structure, selected_table: str):
    """Return a column and it's datatypes for a chosen table.

    Needs to be defined in the base db structure to guarantee consistency.
    """
    try:
        dtypes = {}
        for table, table_info in base_db_structure.items():
            if table == selected_table:
                for column, column_type in table_info["columns"].items():
                    dtypes[column] = column_type
                return dtypes

        logger.error(
            f"Tabelle '{selected_table}' stimmt mit keiner der Tabellen aus"
            " der Datenbank Struktur überein.",
        )
        return None

    except (KeyError, Exception):
        logger.exception("Dtypes konnten nicht ermittelt werden.")
        raise


def get_foreign_key_relations(conn):
    """Return foreign key relations of a database as tuple."""
    cursor = conn.cursor()
    cursor.execute("""SELECT name FROM sqlite_master WHERE type='table';""")
    tables = cursor.fetchall()

    return [
        # Items: table[0] = origin table, fk[3] = origin column
        # fk[2] = target table, fk[4] = target column
        (table[0], fk[3], fk[2], fk[4])
        for table in tables
        for fk in (
            cursor.execute(f"PRAGMA foreign_key_list({table[0]})").fetchall()
        )
    ]


def vacuum_db(conn):
    """Rebuild db file tu use less disk space."""
    logger.info("Räume Datenbank auf...")
    cursor = conn.cursor()
    cursor.execute("vacuum")


def create_internal_information_table(
    db_id: str,
    assignment_round: int,
    timestamp_now: datetime,
    conn,
):
    """Create a db table, containing metainformation and db descriptors."""
    cursor = conn.cursor()

    cursor.execute(f"""DROP TABLE IF EXISTS {consts.TABLE_NAME_INTERNAL}""")

    cursor.execute(
        f"""CREATE TABLE {consts.TABLE_NAME_INTERNAL} (
        {consts.COLUMN_NAME_INTERNAL_ID} TEXT NOT NULL PRIMARY KEY,
        {consts.COLUMN_NAME_INTERNAL_ROUND} INTEGER NOT NULL,
        {consts.COLUMN_NAME_INTERNAL_EDIT_DATE} TEXT NOT NULL,
        {consts.COLUMN_NAME_INTERNAL_CREATION_DATE} TEXT NOT NULL);
        """,
    )

    cursor.execute(
        f"""INSERT INTO {consts.TABLE_NAME_INTERNAL} VALUES (?, ?, ?, ?)""",
        (db_id, assignment_round, timestamp_now, timestamp_now),
    )

    conn.commit()


def write_new_round_counter_and_timestamp(current_round, conn):
    """Update assignment round counter and timestamp of internal db table."""
    cursor = conn.cursor()
    timestamp = datetime.datetime.now()

    cursor.execute(
        f"""UPDATE {consts.TABLE_NAME_INTERNAL}
        SET {consts.COLUMN_NAME_INTERNAL_ROUND} = ?,
        {consts.COLUMN_NAME_INTERNAL_EDIT_DATE} = ?
        """,
        (
            current_round,
            timestamp,
        ),
    )

    conn.commit()


def create_db_id(length):
    """Generate a random id number to identify a database."""
    import random
    import string

    chars = string.ascii_letters + string.digits

    return "".join(random.choice(chars) for _ in range(length))


def get_db_id(conn):
    """Return the id of a database."""
    cursor = conn.cursor()
    cursor.execute(
        f"""SELECT {consts.COLUMN_NAME_INTERNAL_ID}
        FROM {consts.TABLE_NAME_INTERNAL}
        """,
    )
    row = cursor.fetchone()
    (db_id,) = row
    return db_id


def get_assignment_round(conn):
    """Return the current assignment round value of a database."""
    cursor = conn.cursor()

    cursor.execute(
        f"""SELECT {consts.COLUMN_NAME_INTERNAL_ROUND}
        FROM {consts.TABLE_NAME_INTERNAL}
        """,
    )

    row = cursor.fetchone()
    (current_round,) = row
    return current_round


def get_unique_column_values(database_name: str, table: str, column: str):
    """Return the unique values found in a database column per table.

    Use to find what the possible values in a column are.
    Function limits the max amount to only return sets of column values
    with few unique values. Can be used in the UI as a base for tooltip info.
    """
    descriptors = file_utils.read_json(
        consts.FOLDER_UTILS, "base_db_value_descriptors.json"
    )
    database_path = get_db_path(database_name, check_file_presence=True)

    with closing(sqlite3.connect(database_path)) as conn:
        cursor = conn.cursor()

        # Get unique values
        try:
            unique_values = cursor.execute(
                f"SELECT DISTINCT {column} FROM {table};",
            ).fetchall()
            unique_values = [value[0] for value in unique_values]

            # Convert unique values to their descriptors if available
            if column in descriptors:
                unique_values = [
                    f"{value}" + f" ({descriptors[column].get(value, value)})"
                    for value in unique_values
                ]

            # Limit to 10 unique values
            if len(unique_values) > 10:
                unique_values = None

        # If table / column is not found, just return none
        except sqlite3.OperationalError:
            unique_values = None

    return unique_values


# Replacements for sqlite3's deprecated default datetime adapter.
# https://docs.python.org/3/library/sqlite3.html#sqlite3-adapter-converter-recipes (last accessed 01.04.2024)
def adapt_datetime(val):
    """Adapt datetime.datetime to only show year, month, day, hours, mins
    and secs.
    """
    return val.strftime("%Y-%m-%d %H:%M:%S.%f")


sqlite3.register_adapter(datetime.datetime, adapt_datetime)
