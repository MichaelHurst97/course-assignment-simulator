"""Global app constants and settings."""

import configparser
import json
import logging
import operator
import os
from collections import namedtuple
from pathlib import Path


def change_setting(setting_section, setting, value):
    """Writes an altered setting to settings file"""
    settings = configparser.ConfigParser()
    settings.read(SETTINGS_FILE)

    if not settings.has_section(setting_section):
        raise AttributeError(
            f"Section nicht in Settings Datei gefunden: {setting_section}"
        )

    if not settings.has_option(setting_section, setting):
        raise AttributeError(
            f"Option nicht in Settings Datei gefunden: {setting}"
        )

    settings.set(setting_section, setting, str(value))

    with open(SETTINGS_FILE, "w") as settings_file:
        settings.write(settings_file)
    logging.info(f"Einstellung geschrieben '{setting}' = '{value}'")


def check_setting_alphabetic(text: str):
    """Warn if non-alphabetic characters are contained in a settings string.

    Used for assignment status strings that are imported via settings ini.
    """
    if text.isalpha():
        return text

    logging.warning(
        f"Der angegebene Statuswert '{text}' in der Einstellungsdatei enthält"
        " Zeichen, die möglicherweise keinen Status in der Datenbank abbilden."
        " Ist dies gewollt?",
    )
    return text


def validate_db_constants_against_base_db_structure(db_constants: dict):
    """Validate if hardcoded constants can be matched with base DB structure.

    May happen if changes the base DB structure are made but not the constants.
    This can be helpful to check if table and column names that are essential
    for the simulator to function are present.
    """
    file_path = Path(FOLDER_UTILS, FILENAME_BASE_DB_STRUCTURE)
    try:
        with Path.open(file_path, encoding="utf-8") as f:
            base_db_structure = json.load(f)

            table = db_constants["table"]
            columns = db_constants["columns"]

            if table not in base_db_structure:
                logging.warning(
                    (
                        f"Der Tabellenname '{table}' wurde in den Constants"
                        " definiert, kommt aber nicht in der Base DB Structure"
                        " vor. Dies wird dazu führen, dass importierte Daten"
                        " nicht korrekt vom Simulator referenziert werden."
                    ),
                )

            elif columns is not None:
                for column in columns:
                    # https://realpython.com/any-python/ (last accessed: 14.04.2024)
                    if not any(
                        column in base_db_structure[table]["columns"]
                        for table in base_db_structure
                    ):
                        logging.warning(
                            f"Der Spaltenname '{column}' aus der Tabelle"
                            f" '{table}' wurde in den Constants definiert,"
                            " kommt aber nicht in der Base DB Structure vor."
                            " Dies wird dazu führen, dass importierte Daten"
                            " nicht korrekt vom Simulator referenziert"
                            " werden.",
                        )
    except FileNotFoundError:
        logging.exception("Datei für Basis Datenbank Struktur nicht gefunden")
        raise


# App Infos
APP_LOGO = "assets/favicon.ico"
APP_NAME = "Kursbelegungs-Simulator"
APP_VERSION = "1.0"
LOG_LEVEL = (
    logging.INFO
)  # Should stay set to a minimum of "info" for all app progress to be shown


# Subclass and variables for rule definition
RULE = namedtuple(
    "Rule",
    ["table_x", "column_x", "operator_symbol", "table_y", "column_y"],
)

OPERATORS = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    "<": operator.lt,
    ">=": operator.ge,
    "<=": operator.le,
}

JOIN_OPERATORS = ["AND", "OR", "NOT"]


# Paths to various programm locations
FOLDER_UTILS = Path(__file__).parent
FOLDER_ROOT = Path(FOLDER_UTILS, os.pardir)
FOLDER_USERDATA = Path(FOLDER_ROOT, "userdata")
FOLDER_DB = Path(FOLDER_USERDATA, "databases")
FOLDER_CSV_IMPORT = Path(FOLDER_USERDATA, "import_files")
FOLDER_LOGS = Path(FOLDER_USERDATA, "logs")
FOLDER_RULE_FILES = Path(FOLDER_USERDATA, "rule_files")
FOLDER_STAT_FILES = Path(FOLDER_USERDATA, "stats")


# Standardized filenames
FILENAME_BASE_DB_STRUCTURE = "base_db_structure.json"
FILENAME_IMPORT_MAPPING = "import_mapping.json"
FILENAME_STAT_INFO = "stat_info.json"
FILENAME_SETTINGS = "settings.ini"
SETTINGS_FILE = Path(FOLDER_USERDATA, FILENAME_SETTINGS)


# Settings
# Not strict const variables because they can be reloaded but treated similarly
settings = configparser.RawConfigParser()
settings.read(SETTINGS_FILE)
# Rule application settings
# Second parameter in "get" functions acts as a fallback if setting not found
RULE_SETTING_CURRENT_SEMESTER = settings["Rule Application"].getint(
    "CURRENT_SEMESTER",
    20241,
)
RULE_SETTING_LOGGING_PER_LECTURE = settings["Rule Application"].getboolean(
    "LOGGING_PER_LECTURE",
    False,
)
RULE_SETTING_FALLBACK_PARTICIPANT_SIZE = settings["Rule Application"].getint(
    "FALLBACK_PARTICIPANT_SIZE",
    22,
)
RULE_SETTING_FALLBACK_GROUP_NUMBER = settings["Rule Application"].getint(
    "FALLBACK_GROUP_NUMBER",
    9,
)
RULE_SETTING_STATUS_PROPOSED = check_setting_alphabetic(
    settings["Rule Application"].get("STATUS_PROPOSED", "PR"),
)
RULE_SETTING_STATUS_ACCEPTED = check_setting_alphabetic(
    settings["Rule Application"].get("STATUS_ACCEPTED", "AKZ"),
)
RULE_SETTING_STATUS_DENIED = check_setting_alphabetic(
    settings["Rule Application"].get("STATUS_DENIED", "AB"),
)
RULE_SETTING_STATUS_ENROLLED = check_setting_alphabetic(
    settings["Rule Application"].get("STATUS_ENROLLED", "ZU"),
)
RULE_SETTING_STATUS_SELF_DISENROLLED = check_setting_alphabetic(
    settings["Rule Application"].get("STATUS_SELF_DISENROLLED", "SA"),
)
RULE_SETTING_STAT_FILE_ACCEPTED = settings["Rule Application"].get(
    "STAT_FILE_ACCEPTED",
    "accepted_assignments.xz",
)
RULE_SETTING_STAT_FILE_DENIED = settings["Rule Application"].get(
    "STAT_FILE_DENIED",
    "denied_assignments.xz",
)
RULE_SETTING_STAT_FILE_ACCEPTED_LECTURE_COMBINATIONS = settings[
    "Rule Application"
].get(
    "STAT_FILE_ACCEPTED_LECTURE_COMBINATIONS",
    "accepted_lecture_combinations.xz",
)
RULE_SETTING_STAT_FILE_ASSIGNMENTS = settings["Rule Application"].get(
    "STAT_FILE_ASSIGNMENTS",
    "assignments.xz",
)

# Sim Overview Settings
OVERVIEW_SETTING_MAX_PREVIEW_SIZE = settings["Overview"].getint(
    "OVERVIEW_MAX_PREVIEW_SIZE",
    10000,
)
OVERVIEW_SETTING_AUTO_UPDATE = settings["Overview"].getboolean(
    "OVERVIEW_AUTO_UPDATE",
    True,
)

# DB Utils
DB_SETTING_OVERWRITE_IMPORT = settings["Database"].getboolean(
    "OVERWRITE_IMPORT",
    False,
)
# Change if RAM get's too full when importing huge datasets
DB_SETTING_READ_CSV_CHUNKSIZE = settings["Database"].getint(
    "READ_CSV_CHUNKSIZE",
    100000,
)
# Change if importer can't decode a character in csv.
# Use 'detect' for auto detection, but this takes longer and can fill up ram!
# 'iso-8859-1' is standard
DB_SETTING_READ_CSV_ENCODING = settings["Database"].get(
    "READ_CSV_ENCODING",
    "iso-8859-1",
)
DB_SETTING_IMPORT_NAME_DATEFORMAT = settings["Database"].get(
    "IMPORT_NAME_DATEFORMAT",
    "%d_%m_%Y %H_%M_%S",
)
DB_SETTING_INTERNAL_ID_LENGTH = settings["Database"].getint(
    "INTERNAL_ID_LENGTH",
    8,
)

# Generator
GENERATOR_SETTING_DEFAULT_DISENROLL_CHANCE = settings["Generator"].getfloat(
    "DEFAULT_DISENROLL_CHANCE",
    0.12853,
)

# Visualization
VISU_SETTING_PLOTLY_THEME = settings["Visualization"].get(
    "PLOTLY_THEME",
    "plotly",
)


# DB mapping names - Need to be hardcoded here as a naming link between
# app variables and base db structure definition
# Rule algorithm table
TABLE_NAME_ASSIGNMENTS = "belegungen"
COLUMN_NAME_ASSIGNMENTS_ID = "_pk_id"
COLUMN_NAME_ASSIGNMENTS_LECTURE_ID = "veranstaltungs_id"
COLUMN_NAME_ASSIGNMENTS_STATUS = "status"
COLUMN_NAME_ASSIGNMENTS_MATRICULE_NUMBER = "matrikelnummer"
COLUMN_NAME_ASSIGNMENTS_STUDY_PROGRAM_ID = "studiengangs_id"
COLUMN_NAME_ASSIGNMENTS_APPLICATION_ORDER_INFO = "sortierwert"
COLUMN_NAME_ASSIGNMENTS_SYSTEM_MESSAGE = "systemnachricht"
COLUMN_NAME_ASSIGNMENTS_SYSTEM_METHOD = "belegungs_verfahren"
COLUMN_NAME_ASSIGNMENTS_GROUP_ID = "gruppen_id"
COLUMN_NAME_ASSIGNMENTS_SEMESTER = "semester"
COLUMN_NAME_ASSIGNMENTS_TIMESTAMP = "zeitstempel"
validation_assignments = {
    "table": TABLE_NAME_ASSIGNMENTS,
    "columns": [
        COLUMN_NAME_ASSIGNMENTS_ID,
        COLUMN_NAME_ASSIGNMENTS_LECTURE_ID,
        COLUMN_NAME_ASSIGNMENTS_STATUS,
        COLUMN_NAME_ASSIGNMENTS_MATRICULE_NUMBER,
        COLUMN_NAME_ASSIGNMENTS_STUDY_PROGRAM_ID,
        COLUMN_NAME_ASSIGNMENTS_APPLICATION_ORDER_INFO,
        COLUMN_NAME_ASSIGNMENTS_SYSTEM_MESSAGE,
        COLUMN_NAME_ASSIGNMENTS_SYSTEM_METHOD,
        COLUMN_NAME_ASSIGNMENTS_GROUP_ID,
        COLUMN_NAME_ASSIGNMENTS_SEMESTER,
        COLUMN_NAME_ASSIGNMENTS_TIMESTAMP,
    ],
}
validate_db_constants_against_base_db_structure(validation_assignments)

# Lecture combination table
TABLE_NAME_LECTURE_COMBINATIONS = "veranstaltung_kombo"
validation_lecture_combinations = {
    "table": TABLE_NAME_LECTURE_COMBINATIONS,
    "columns": None,
}
validate_db_constants_against_base_db_structure(
    validation_lecture_combinations,
)

# Student table
TABLE_NAME_STUDENT = "studierende"
COLUMN_NAME_STUDENT_SEMESTER = "_pk_semester"
validation_student = {
    "table": TABLE_NAME_STUDENT,
    "columns": [COLUMN_NAME_STUDENT_SEMESTER],
}
validate_db_constants_against_base_db_structure(validation_student)

# Internal database table, must not be validated because created by app itself
TABLE_NAME_INTERNAL = "METAINFO"
COLUMN_NAME_INTERNAL_ID = "id"
COLUMN_NAME_INTERNAL_ROUND = "runde"
COLUMN_NAME_INTERNAL_CREATION_DATE = "erstellungs_datum"
COLUMN_NAME_INTERNAL_EDIT_DATE = "änderungs_datum"


# Frontend names
# Layout DB manager ag grid table
AG_COLUMN_NAME_DBM_NAME = "Name"

# Layout rule editor
STANDARD_NAME_FREE_INPUT = "Freie Eingabe"
EMPTY_STRING = " "


# Browser page urls and titles
PAGE_HOME_URL = "/"
PAGE_HOME_TITLE_NAME = "Kursbelegungs-Simulator"

PAGE_IMPORT_DB_FILE_URL = "/import-db-file-check/"
PAGE_IMPORT_DB_FILE_TITLE_NAME = "Simulator - Datenbank Datei Import"

PAGE_IMPORT_DB_FILE_PROCESS_URL = "/import-db-file-process/"
PAGE_IMPORT_DB_FILE_PROCESS_TITLE_NAME = "Simulator - Datenbank Datei Import"

PAGE_DB_MANAGER_URL = "/db-manager/"
PAGE_DB_MANAGER_TITLE_NAME = "Simulator - Datenbank Manager"

PAGE_SIM_START_URL = "/start-overview/"
PAGE_SIM_START_TITLE_NAME = "Simulator - Übersicht"

PAGE_SIM_RULE_EDITOR_URL = "/rule-editor/"
PAGE_SIM_RULE_EDITOR_TITLE_NAME = "Simulator - Regeleditor"

PAGE_SIM_PROCESS_URL = "/rule-simulator/"
PAGE_SIM_PROCESS_TITLE_NAME = "Simulator - Regelanwendung"

PAGE_SIM_DONE_URL = "/end-overview/"
PAGE_SIM_DONE_TITLE_NAME = "Simulator - Endübersicht"

PAGE_VISUALIZER_URL = "/visualizer/"
PAGE_VISUALIZER_TITLE_NAME = "Simulator - Visualisierungs-Tool"

PAGE_GENERATOR_URL = "/generator/"
PAGE_GENERATOR_TITLE_NAME = "Simulator - Datenbank aus Generator"

PAGE_ABOUT_URL = "/about/"
PAGE_ABOUT_TITLE_NAME = "Simulator - Über diese Anwendung"


# ANSI Codes for console logger
# https://stackoverflow.com/questions/4842424/list-of-ansi-color-escape-sequences (last accessed: 14.04.2024)
CONSOLE_RED = "\033[91m"
CONSOLE_RED_BOLD = "\033[91;1m"
CONSOLE_YELLOW = "\033[93m"
CONSOLE_GREEN = "\033[92m"
CONSOLE_BLUE = "\033[94m"
CONSOLE_ENDCMD = "\033[0m"
