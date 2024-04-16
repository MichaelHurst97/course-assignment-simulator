"""Import data from CSV files to be used in the simulator."""

import datetime
import os
import sqlite3
from contextlib import closing
from pathlib import Path

import pandas as pd

import utils.constants as consts
from utils import db_utils, file_utils
from utils.logger import logger

from . import (
    model_import_db_csv_custom_patches,
    model_import_db_csv_validation,
)


def read_csv_to_df(csv_folder, csv_filename, import_mapping):
    """Return a dataframe from a csv file using an import mapping.

    Arguments:
    ---------
    csv_folder: import folder
    csv_filename: filename of a csv file to return as dataframe
    import_mapping: loaded json structure of "import_mapping.json"

    The mapping defines what column names the dataframe should use instead of
    the original csv columns. It also defines the datatypes for each column.

    """
    # CSV encoding detection. Using "detect" as a setting can result in very
    # long import times and ram/swap issues
    try:
        if consts.DB_SETTING_READ_CSV_ENCODING == "detect":
            import chardet

            with Path.open(
                Path(csv_folder, csv_filename),
                "rb",
            ) as f:
                # Detect encoding of csv file
                # https://pypi.org/project/chardet/ (last accessed: 14.04.2024)
                detected_encoding = chardet.detect(f.read())
                encoding = detected_encoding["encoding"]
        else:
            encoding = consts.DB_SETTING_READ_CSV_ENCODING

        # Remove file extension
        table = Path(csv_filename).stem

        dtypes = import_mapping[table].pop("dtypes")
        import_structure = {table: dtypes}

        # Check which columns should be imported by looking at map_to_columns
        # and if entries are marked as NULL
        df_columns = []
        mapping_columns = import_mapping[table]["map_to_columns"]
        for from_column, to_column in mapping_columns.items():
            if to_column is not None:
                df_columns.append(from_column)

        # Get datatypes for dataframe from mapping file
        # where dtypes are manually defined.
        # Otherwise panda guesses and sometimes assigns wrong dtypes
        dtypes = {
            column: dtype
            for column, dtype in import_structure[table].items()
            if not column.startswith("_parse_dates_") and column in df_columns
        }

        # Get variables where parse_dates should be called.
        # Used if parsing / formatting of dates should be done
        parse_dates_columns = [
            column.replace("_parse_dates_", "")
            for column, _ in import_structure[table].items()
            if column.startswith("_parse_dates_")
        ]
        # Only use existing dates columns in final df
        parse_dates_columns = [
            column for column in parse_dates_columns if column in df_columns
        ]

        # Read csv into pandas dataframe using chunks
        # Chunks can prevent memory issues when reading huge datasets

        df = pd.read_csv(
            os.path.realpath(Path(csv_folder, csv_filename)),
            usecols=df_columns,
            delimiter=";",
            encoding=encoding,
            on_bad_lines="error",
            dtype=dtypes,
            parse_dates=parse_dates_columns if parse_dates_columns else False,
            index_col=False,
        )

        # Remove 'Unnamed' column
        # If present, "Unnamed" was created as an dataframe index.
        df = df.loc[:, ~df.columns.str.startswith("Unnamed")]

        # Apply the same datetime formatting to all datetime strings
        for date in parse_dates_columns:
            df[date] = pd.to_datetime(df[date], format="mixed")

        return df

    except Exception:
        logger.exception(
            f"Fehler beim Verarbeiten der Datei '{csv_filename}'.",
        )
        raise


def create_base_db(base_db_structure, conn):
    """Use base db structure structure to create an empty sqlite database.

    Arguments:
    ---------
    base_db_structure: loaded json structure of "base_db_structure.json"
    conn: open connection to a sqlite3 database

    SQLite queries are created from the json text.
    Only the table and column names, as well as primary and foreign keys are
    committed to db here.

    """
    # Translate pandas dtypes into sqlite datatypes
    # Keys are dtypes in pandas syntax, values in sqlite syntax
    type_mapping = {
        # Pandas doesn't null int and int32 dtypes, so sqlite also shouldn't
        "int": "INTEGER NOT NULL",
        "Int64": "INTEGER",
        "object": "TEXT",
        "category": "TEXT",
        "datetime64[ns]": "TEXT",
        # Note: float has currently no use in supplied base db
        "float": "REAL",
    }

    cursor = conn.cursor()

    # Overwrite tables on this connection
    # Overwriting checks, e.g. if a db files exists,
    # should be made outside of this scope
    cursor.execute("""SELECT name FROM sqlite_master WHERE type='table';""")
    tables = cursor.fetchall()
    for table in tables:
        try:
            cursor.execute(f"""DROP TABLE IF EXISTS {table[0]};""")
        except Exception:
            logger.exception(f"Fehler beim Löschen der Tabelle {table[0]}.")
            raise

    try:
        # Create columns and primary / foreign keys for each table and commit
        for table, table_info in base_db_structure.items():
            column_definitions = []
            primary_keys = table_info["primary_key"]
            foreign_keys = []

            # Column definitions
            for column, column_type in table_info["columns"].items():
                column_definitions.append(
                    f"{column} {type_mapping[column_type]}",
                )

            # Foreign key definitions
            for column, foreign_key_info in table_info["foreign_key"].items():
                for target in foreign_key_info["target_column"]:
                    for target_table, target_column in target.items():
                        constraint = " ".join(foreign_key_info["constraint"])
                        foreign_keys.append(
                            f"FOREIGN KEY({column}) REFERENCES {target_table}({target_column}) {constraint}",
                        )

            # SQL statement creation
            # Written this way and not more programmatically for better insight
            # on how statements are build.
            if primary_keys and primary_keys[0] != "" and foreign_keys:
                create_table_statement = f"CREATE TABLE {table} ({', '.join(column_definitions)}, PRIMARY KEY ({', '.join(primary_keys)}), {', '.join(foreign_keys)});"
            elif primary_keys and primary_keys[0] != "" and not foreign_keys:
                create_table_statement = f"CREATE TABLE {table} ({', '.join(column_definitions)}, PRIMARY KEY ({', '.join(primary_keys)}));"
            elif primary_keys and primary_keys[0] == "" and foreign_keys:
                create_table_statement = f"CREATE TABLE {table} ({', '.join(column_definitions)}, {', '.join(foreign_keys)});"
            else:
                create_table_statement = (
                    f"CREATE TABLE {table} ({', '.join(column_definitions)});"
                )

            cursor.executescript(create_table_statement)

        logger.info(
            f"{consts.CONSOLE_GREEN}Basis Datenbank Struktur angelegt."
            f"{consts.CONSOLE_ENDCMD}",
        )

    except (KeyError, Exception):
        logger.exception(
            "Die Basis Datenbank Struktur ist fehlerhaft oder Basis Datenbank"
            "Struktur konnte nicht vollständig angelegt werden.",
        )
        raise


def map_to_base_db(df, import_mapping, table):
    """Rename dataframe columns to ones specified in mapping file
    under 'map_to_columns'.
    """
    mapping_columns = import_mapping[table]["map_to_columns"]

    for from_column, to_column in mapping_columns.items():
        if to_column is not None:
            df.rename(columns={from_column: to_column}, inplace=True)
    return df


def import_csv_files(db_filename: None):
    """Write CSV tables to a database compatible with the simulator.

    A mapping file must be supplied to align CSV files with expected
    database structure.
    """
    # Validate to check if files are present and mapping is successful
    model_import_db_csv_validation.run_import_validation()

    base_db_structure = file_utils.read_json(
        consts.FOLDER_UTILS,
        consts.FILENAME_BASE_DB_STRUCTURE,
    )

    import_mapping = file_utils.read_json(
        consts.FOLDER_CSV_IMPORT,
        consts.FILENAME_IMPORT_MAPPING,
    )

    csv_files = [f"{key}.csv" for key in import_mapping]

    # DB Filename and path, if none is specified use datetime
    database_name = (
        db_filename
        or f"CSV_Import {datetime.datetime.now().strftime(
        consts.DB_SETTING_IMPORT_NAME_DATEFORMAT
    )}.db"
    )
    logger.info(f"Verwende '{database_name}' als Datenbank-Name")

    # Check for overwriting
    if (
        file_utils.check_file_presence(consts.FOLDER_DB, database_name)
        and not consts.DB_SETTING_OVERWRITE_IMPORT
    ):
        logger.error(
            f"Datenbank mit dem Namen '{database_name}'"
            " existiert bereits und wird nicht überschrieben."
            " Breche ab.",
        )
        raise FileExistsError
    database_path = db_utils.get_db_path(database_name)

    # Open DB Connection
    with closing(sqlite3.connect(database_path)) as conn:
        csv_tables = list(import_mapping)

        # Create base sqlite db without content, only tables,
        # columns and pks/fks
        create_base_db(base_db_structure, conn)

        # Add a table with metainformation to the db, containing id, stored
        # assignment round (0 as the db is just being imported) and the
        # creation date
        db_id = db_utils.create_db_id(consts.DB_SETTING_INTERNAL_ID_LENGTH)
        timestamp = datetime.datetime.now()
        db_utils.create_internal_information_table(db_id, 0, timestamp, conn)

        # Import each csv file
        # https://realpython.com/python-zip-function/ (last accessed: 14.04.2024)
        for csv_file, csv_table in zip(csv_files, csv_tables, strict=False):
            logger.info(
                f"Importiere '{csv_file}'...",
            )

            # Read CSV into dataframe, use specified dtypes so pandas doesn't
            # need to guess dtypes. It's guessed dtypes often do not match the
            # proper type exactly (e.g. float instead of Int64 values for
            # nullable values, resulting in decimal places)
            try:
                df = read_csv_to_df(
                    consts.FOLDER_CSV_IMPORT,
                    csv_file,
                    import_mapping,
                )
            except Exception:
                logger.error(
                    f"Konnte Dataframe für Tabelle '{csv_table}' nicht"
                    " erstellen.",
                )
                raise

            # Map the dataframe columns to new columns specified in mapping
            # file. This is done by renaming the df columns
            mapped_df = map_to_base_db(df, import_mapping, csv_table)

            # Finally write df to database with table name specified by
            # mapping file
            map_to_table = import_mapping[csv_table]["map_to"]
            if map_to_table is None:
                # This should be the case if user wants to explicitly
                # discard a table
                logger.warning(
                    f"Tabelle '{csv_table}' wird verworfen und nicht"
                    " importiert.",
                )

            else:
                try:
                    mapped_df.to_sql(
                        map_to_table,
                        conn,
                        if_exists="append",
                        index=False,
                    )
                except Exception:
                    logger.exception(
                        f"Fehler beim Schreiben der Tabelle '{map_to_table}'"
                        " in die Datenbank.",
                    )
                    raise

                logger.info(
                    f"Import von csv_file in interne Tabelle '{map_to_table}'"
                    " abgeschlossen.",
                )

        # If adjustments need to be made programmatically for import data
        # to adhere to base db structure, this is the place to define
        # custom functions
        model_import_db_csv_custom_patches.run_custom_import_patches(conn)

        logger.info(
            f"{consts.CONSOLE_GREEN}CSV Import abgeschlossen."
            f"{consts.CONSOLE_ENDCMD}",
        )

        return True
