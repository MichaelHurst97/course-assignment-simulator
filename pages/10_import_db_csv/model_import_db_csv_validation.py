"""Functions to validate mappings for correct CSV import."""
from collections import OrderedDict
from pathlib import Path

import utils.constants as consts
from utils import file_utils
from utils.logger import logger


def check_csv_presence(csv_folder: Path, import_mapping: dict):
    """Read in import_mapping data to check which CSV files are
    expected to be imported.

    Returns a dict containing each CSV file and it's presence.
    """
    csv_files = [f"{key}.csv" for key in import_mapping]
    import_files_checked = {}

    for csv_file in csv_files:
        csv_file_present = file_utils.check_file_presence(csv_folder, csv_file)
        import_files_checked[csv_file] = csv_file_present

    return import_files_checked


def verify_mapping_structure(import_mapping: dict):
    """Verify the integrity of import_mapping data.

    In specific, checks if typos between 'dtypes' and 'map_to_columns' exist.
    Returns a dict with all checked entries.
    """
    dtypes_checked = {}
    map_to_columns_checked = {}

    for table, table_info in import_mapping.items():
        dtypes = table_info["dtypes"]
        map_to_columns = table_info["map_to_columns"]

        dtypes_buffer = OrderedDict()
        map_to_columns_buffer = OrderedDict()

        # Remove identifier for date parsing at the beginning of some
        # column names
        for column, dtype in dtypes.items():
            column = (
                column[len("_parse_dates_") :]
                if column.startswith("_parse_dates_")
                else column
            )
            dtypes_buffer[column] = dtype
        for column, map_to_column in map_to_columns.items():
            column = (
                column[len("_parse_dates_") :]
                if column.startswith("_parse_dates_")
                else column
            )
            map_to_columns_buffer[column] = map_to_column

        # Check if column names do not differ between dtypes and map_to_table
        dtypes_result = {
            column: column in map_to_columns_buffer for column in dtypes_buffer
        }
        map_to_columns_result = {
            column: column in dtypes_buffer for column in map_to_columns_buffer
        }

        dtypes_checked[table] = dtypes_result
        map_to_columns_checked[table] = map_to_columns_result

    return dtypes_checked, map_to_columns_checked


def check_mapping_against_db_structure(
    import_mapping: dict,
    base_db_structure: dict,
):
    """Read in an import_mapping and check if it maps against the
    internal db structure.

    Returns a dict with all tables and their columns, using boolean
    values to mark missing elemeents.
    """
    mapping_checked = {}

    # Add db structure tables to checked mapping, but keep them marked as None
    for map_to_table in base_db_structure:
        mapping_checked[map_to_table] = None

    # Check if tables from base db structure appear in mapping
    for mapping_object in import_mapping.values():
        map_to_table = mapping_object["map_to"]

        # Mark tables that do not appear in the base db structure
        if map_to_table not in base_db_structure:
            mapping_checked[map_to_table] = False

        else:
            # Remove columns that do not appear in base db structure
            base_columns = base_db_structure[map_to_table]["columns"]
            map_to_columns = mapping_object["map_to_columns"]

            filtered_map_to_columns = {
                csv_column: map_to_column
                for csv_column, map_to_column in map_to_columns.items()
                if map_to_column in base_columns
            }

            # Check if columns from base db structure appear in mapping
            for base_column in base_columns:
                if base_column not in filtered_map_to_columns.values():
                    # Create a dict for checked columns
                    # Columns that can't be mapped to base structure get noted
                    # here as False
                    mapping_checked[map_to_table] = {
                        base_column: (
                            base_column in filtered_map_to_columns.values()
                        )
                        for base_column in base_columns
                    }
                else:
                    # Create dict for checked columns that exist in mapping and
                    # base db
                    mapping_checked[map_to_table] = {
                        base_column: (
                            base_column in filtered_map_to_columns.values()
                        )
                        for base_column in base_columns
                    }

    return mapping_checked


def run_import_validation():
    """Write CSV tables to a database compatible with the simulator.

    A mapping file must be supplied to align CSV files with expected
    database structure.
    """
    logger.info("CSV Import gestartet...")

    # Check if base db structure file exists
    base_db_structure = file_utils.read_json(
        consts.FOLDER_UTILS,
        consts.FILENAME_BASE_DB_STRUCTURE,
    )
    if base_db_structure is None:
        logger.error(
            "Datei für Basis Datenbank Struktur nicht vorhanden."
            " Bitte Projekt neu installieren/entpacken oder Datenbank"
            " Struktur Datei im angegebenen Ordner platzieren."
            f"\nÜberprüfter Ordner: '{consts.FOLDER_UTILS}'",
        )
        raise FileNotFoundError
    logger.info(f"Datei '{consts.FILENAME_BASE_DB_STRUCTURE}' vorhanden.")

    # Check if import mapping file exists
    import_mapping = file_utils.read_json(
        consts.FOLDER_CSV_IMPORT,
        consts.FILENAME_IMPORT_MAPPING,
    )
    if import_mapping is None:
        logger.error(
            "Datei für Import Mapping nicht im CSV Import Ordner gefunden."
            " Bitte überprüfen und ggf. laut Doku erstellen.",
        )
        raise FileNotFoundError
    logger.info(f"Datei '{consts.FILENAME_IMPORT_MAPPING}' vorhanden.")

    # Check if csv files named in mapping are present in import folder
    logger.info(
        "Prüfe ob alle angegebenen CSV Dateien der JSON Struktur"
        " gefunden werden...",
    )
    csv_files = check_csv_presence(consts.FOLDER_CSV_IMPORT, import_mapping)
    for csv_file in csv_files:
        if not csv_file:
            logger.error(
                f"Datei '{csv_file} nicht im Import-Ordner zu finden, wurde"
                " jedoch im Import-Mapping angegeben.",
            )

    if not all(csv_files.values()):
        logger.error(
            "Nicht alle angegebenen CSV Dateien aus JSON Struktur gefunden."
            " Abbruch.",
        )
        raise FileNotFoundError

    logger.info(
        f"{consts.CONSOLE_GREEN}Alle angegebenen CSV Dateien aus JSON"
        f" Struktur gefunden.{consts.CONSOLE_ENDCMD}",
    )

    # Check mapping integrity (if dtypes and map_to_columns match up)
    logger.info(
        "Prüfe ob interne Struktur des Import Mappings übereinstimmt...",
    )
    (dtypes_checked, map_to_columns_checked) = verify_mapping_structure(
        import_mapping,
    )
    for table in dtypes_checked:
        for column_dtypes, value in dtypes_checked[table].items():
            if not value:
                logger.error(
                    "'dtypes' in JSON Datei stimmt nicht mit 'map_to_columns'"
                    f" überein: Spalte '{column_dtypes}' in Tabelle '{table}'"
                    " kann nicht zu einer Spalte in 'map_to_columns'"
                    " zugeordnet werden.",
                )
                raise KeyError
    for table in map_to_columns_checked:
        for column, value in map_to_columns_checked[table].items():
            if not value:
                logger.error(
                    "'map_to_columns' in JSON Datei stimmt nicht mit 'dtypes'"
                    " überein: Spalte '{column}' in Tabelle '{table}' kann"
                    " nicht zu einer Spalte in 'dtypes' zugeordnet werden.",
                )
                raise KeyError
    logger.info(
        f"{consts.CONSOLE_GREEN}Interne Struktur des Import Mappings"
        f" stimmt.{consts.CONSOLE_ENDCMD}",
    )

    # Check if mapping to base db structure succeeds
    mapping_checked = check_mapping_against_db_structure(
        import_mapping,
        base_db_structure,
    )
    for table, column in mapping_checked.items():
        if mapping_checked[table] is None:
            logger.error(
                f"Tabelle '{table}' wird von der Datenbank Struktur verlangt,"
                " ist jedoch nicht im Mapping vorhanden.",
            )
            raise KeyError
        elif table is None:
            logger.warning(
                f"Eine Tabelle ist im Mapping als '{table}' markiert und wird"
                " daher verworfen.",
            )
        elif mapping_checked[table] is False:
            logger.warning(
                f"Tabelle '{table}' ist im Mapping vorhanden, wird jedoch"
                " nicht von der Basis Datenbank Struktur verlangt.",
            )
        else:
            for column, value in mapping_checked[table].items():
                if not value:
                    logger.error(
                        f"Spalte '{column}' in Tabelle '{table}' wird von der"
                        " Datenbank Basis Struktur verlangt, ist jedoch nicht"
                        " im Mapping vorhanden.",
                    )
                    raise KeyError

    return True
