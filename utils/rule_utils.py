"""Utils for rule appliaction in the simulator."""

import os
import sqlite3
from contextlib import closing
from pathlib import Path
import numbers

import pandas as pd

from . import constants as consts
from . import db_utils, file_utils
from .logger import logger


def check_and_transform_rule(rule, add_suffix=True):
    """Validate if a rule is correctly formatted.

    Add suffix to specific rule compositions for "unique" column names.
    This results in column names having their table added as suffix,
    which should eliminate two columns with the same name.
    Important when merging different tables via pandas.

    Input:
    ------
    Rule = namedtuple("Rule", ["table_x", "column_x", "operator_symbol",
                        "table_y", "column_y"])
    """
    # Skip check
    if rule is None:
        return None

    # Check if input types are valid
    # Table x must always be a string, otherwise there's no column from which
    # a comparison can be made
    if not isinstance(rule.table_x, str):
        logger.error(
            f"Typ von Tabellenname '{rule.table_x}' darf nicht None sein und"
            " muss ein String sein, da sonst keine Regelberechnung stattfinden"
            " kann.",
        )
        raise TypeError(rule.table_x)
    # Operator in list of valid operators?
    if rule.operator_symbol not in consts.OPERATORS:
        logger.error(
            f"Operator ('{rule.operator_symbol}') für Regel '{rule}' wurde"
            " nicht in der Liste an zulässiger Operatoren gefunden.",
        )
        raise KeyError(rule.operator_symbol)
    # Table y can be a string or None. None if the column value x should be
    # compared with a loose integer or string
    if rule.table_y is not None and not isinstance(rule.table_y, str):
        logger.error(
            f"Typ von Tabellenname '{rule.table_y}' muss ein String oder None"
            " sein, da sonst keine Regelberechnung stattfinden kann.",
        )
        raise TypeError(rule.table_y)

    # Only add suffix if specified
    if add_suffix:
        # Rename column to be unique, add table name as suffix
        rule = rule._replace(column_x=rule.column_x + "__" + rule.table_x)

    # Add suffix to x only if column y is not None, which means column x
    # and y should be compared.
    # Do not add if table y is None, then it's a loose string to compare to!
    if add_suffix:
        if isinstance(rule.column_y, str) and rule.table_y is not None:
            rule = rule._replace(column_y=rule.column_y + "__" + rule.table_y)
    # Do not rename column y if it's a number or a string
    elif rule.table_y is None and isinstance(
        rule.column_y,
        numbers.Number,
    ):
        rule = rule._replace(column_y=rule.column_y)

    else:
        print(type(rule.column_y))
        logger.error(
            f"Typ von Spalte '{rule.column_y}' muss ein String oder eine Zahl"
            " sein.",
        )
        raise TypeError(rule.column_y)

    return rule


def apply_rule_to_df(df, column_x, operator_symbol, table_y, column_y):
    """Apply a rule to a dataframe.

    Explanation of dataframe manipulation:

    - Choose the operator_symbol from a global dict of operators.
    - OPERATORS[operator_symbol] returns a boolean value based on
        the comparison of it's arguments.
    - (df[rule_setter], rule) are the two arguments to be compared
    - df.loc() then uses the results to locate every row thats True
    """
    if table_y is None:
        df_rule_applied = df.loc[
            consts.OPERATORS[operator_symbol](
                df[column_x],
                column_y,
            )
        ].copy()

    else:
        df_rule_applied = df.loc[
            consts.OPERATORS[operator_symbol](
                df[column_x],
                df[column_y],
            )
        ].copy()

    return df_rule_applied


def get_ruleset_filelist():
    """Return a list of ruleset files present in the apps rule_files folder."""
    ruleset_folder = file_utils.get_folder(consts.FOLDER_RULE_FILES)
    files = os.listdir(ruleset_folder)
    return [file for file in files if file.endswith(".json")]


def read_rule_file(folder: Path, filename: str):
    """Read in a json file containing bundles of rules.

    Returns rule namedtuples. One singular rule namedtuple for rule
    preselection and a list of assignment namedtuples.
    """
    rule_set = file_utils.read_json(folder, filename)

    if rule_set["rule_preselection"]:
        rule_preselection = consts.RULE(**rule_set["rule_preselection"])
    else:
        rule_preselection = None

    # Read in all assignment rules and create their namedtuples
    list_rule_assignments = []
    for rule in rule_set["rules_assignment"]:
        rule_name = rule["rule_name"]
        rule_assign = consts.RULE(**rule["rule_assignment"])
        rule_op = rule["rule_join_operation"]
        rule_assign_2 = (
            consts.RULE(**rule["rule_assignment_2"])
            if rule["rule_assignment_2"]
            else None
        )

        # Check for valid rule operator
        if rule_op not in consts.JOIN_OPERATORS and rule_op is not None:
            logger.error(
                "Ungültige Operation für den Regelvergleich:"
                f" Operatorion muss in '{consts.JOIN_OPERATORS}' sein.\n",
                f"Fehlerhafte Regel: {rule_assign}, {rule_op},"
                f" {rule_assign_2}",
            )
            raise ValueError

        list_rule_assignments.append(
            {
                "rule_name": rule_name,
                "rule_assignment": rule_assign,
                "rule_join_operation": rule_op,
                "rule_assignment_2": rule_assign_2,
            },
        )

    return rule_preselection, list_rule_assignments


def get_stat_filelist():
    """Return a list of stat folders present in the apps stats folder."""
    stats_folder = file_utils.get_folder(consts.FOLDER_STAT_FILES)
    return [
        name
        for name in os.listdir(stats_folder)
        if Path.is_dir(Path(stats_folder, name))
    ]


def read_stat_files(stat_folder_name: str):
    """Read in pickled dataframes from a prior rule application and the
    rules that were applied.

    """
    logger.info(f"Bereite Stat Files für {stat_folder_name} vor...")

    stat_folder = file_utils.get_folder(
        Path(consts.FOLDER_STAT_FILES, stat_folder_name),
    )

    stat_info = file_utils.read_json(stat_folder, consts.FILENAME_STAT_INFO)

    # Unpickle dataframes from disk
    df_accepted_assignments = pd.read_pickle(
        Path(stat_folder, consts.RULE_SETTING_STAT_FILE_ACCEPTED),
        compression="infer",
    )
    df_denied_assignments = pd.read_pickle(
        Path(stat_folder, consts.RULE_SETTING_STAT_FILE_DENIED),
        compression="infer",
    )
    df_accepted_lecture_combinations = pd.read_pickle(
        Path(
            stat_folder,
            consts.RULE_SETTING_STAT_FILE_ACCEPTED_LECTURE_COMBINATIONS,
        ),
        compression="infer",
    )
    df_assignments = pd.read_pickle(
        Path(
            stat_folder,
            consts.RULE_SETTING_STAT_FILE_ASSIGNMENTS,
        ),
        compression="infer",
    )

    logger.info("Stat Files fertig vorbereitet.")

    return (
        stat_info,
        df_accepted_assignments,
        df_denied_assignments,
        df_accepted_lecture_combinations,
        df_assignments,
    )


def write_stat_files(
    database_filename: str,
    ruleset_filename: str,
    new_stat_folder_name: str,
    assignment_round: int,
    assignment_semester,
    df_accepted_assignments,
    df_denied_assignments,
    df_accepted_lecture_combinations,
    df_assignments,
):
    """Save dataframes from rule application and the used rules to disk."""
    # Create new folder for stat files
    new_stat_folder = file_utils.get_folder(
        Path(consts.FOLDER_STAT_FILES, new_stat_folder_name),
    )

    # Pickle dataframes to save them to disk
    # New assignments with status applied this round
    df_accepted_assignments.to_pickle(
        Path(new_stat_folder, consts.RULE_SETTING_STAT_FILE_ACCEPTED),
        compression="infer",
    )
    df_denied_assignments.to_pickle(
        Path(new_stat_folder, consts.RULE_SETTING_STAT_FILE_DENIED),
        compression="infer",
    )
    df_accepted_lecture_combinations.to_pickle(
        Path(
            new_stat_folder,
            consts.RULE_SETTING_STAT_FILE_ACCEPTED_LECTURE_COMBINATIONS,
        ),
        compression="infer",
    )
    # All assignments from chosen semester / preselection including previously
    # accepted and denied ones, self disenrollments, leftover enrollments..
    # Every other df is redundant to this one, but tracking and handling of
    # new assignments is easier when splitting them into seperate dfs.
    # Could be mittigated by using the timestamp or a round tracking column
    # together with the semester to detect new assignments with the downside
    # of needing to write a lot of dataframe selection code.
    # This approach scarifices hard drive space for code readability and
    # ease of use.
    df_assignments.to_pickle(
        Path(
            new_stat_folder,
            consts.RULE_SETTING_STAT_FILE_ASSIGNMENTS,
        ),
        compression="infer",
    )

    # Get db id for later ruleset comparisons.
    # Only rulesets that were applied on the same db should be compared later
    database_path = db_utils.get_db_path(
        database_filename,
        check_file_presence=True,
    )
    with closing(sqlite3.connect(database_path)) as conn:
        database_id = db_utils.get_db_id(conn)

    # Include rules in the stats because trusting the filename
    # alone isnt enough. Rule files can and will change
    rule_preselection, rules_assignment = read_rule_file(
        consts.FOLDER_RULE_FILES,
        ruleset_filename,
    )

    # Write info file next to pickled dataframes
    stat_info = {
        "database_filename": database_filename,
        "database_id": database_id,
        "assignment_round": assignment_round,
        "assignment_semester": assignment_semester,
        "ruleset_filename": ruleset_filename,
        "ruleset_rule_preselection": rule_preselection,
        "ruleset_rules_assignment": rules_assignment,
    }
    file_utils.write_json(
        stat_info,
        new_stat_folder,
        consts.FILENAME_STAT_INFO,
    )
