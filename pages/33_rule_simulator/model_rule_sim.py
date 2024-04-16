"""Simulate course assignments via a given set of prioritization rules.

rule_preselection = studiengang, veranstaltung, fachsemester, etc ...
Use to reduce the set of assignments. Can only use assignment table.


rule_assignment = any two table columns that can be merged and then compared or
a table column that can be compared to loose data.
Use to compare values in the selection set to further reduce it into rule
"chunks" or ranks. Ranks that fit into a given lecture get accepted,
others get denied. Lottery chooses if ranks happen to be hit the max
participant threshold.
"""

import sqlite3
from contextlib import closing

import pandas as pd

import utils.constants as consts
from utils import db_utils, rule_utils
from utils.logger import logger

from . import (
    model_rule_sim_apply_lecture_combinations,
    model_rule_sim_apply_participant_slots,
    model_rule_sim_apply_rule,
)


def check_for_duplicate_ids(df_all_assignments):
    """Safety check to warn if duplicates are created.
    Deletes them if present.

    Expanding the assignment table on 1:n fks can result in duplicates.
    Keep only the first duplicate occurence, as duplicate rows are added
    at the end of the assignment table
    """
    duplicates = df_all_assignments[
        df_all_assignments.duplicated(subset=consts.COLUMN_NAME_ASSIGNMENTS_ID)
    ]
    if not duplicates.empty:
        logger.warning(
            "Es wurden Duplikate bei der Regelanwendung erzeugt. Bitte Zeilen"
            f" prüfen:\n{duplicates}",
        )
        logger.warning("Duplikate werden gelöscht...")
        df_all_assignments = df_all_assignments.drop_duplicates(
            subset=consts.COLUMN_NAME_ASSIGNMENTS_ID,
            keep="first",
        )


def write_assignments_back_to_db(
    df_all_assignments,
    current_round,
    database_path,
):
    """Write assignments table with applied set of rules back to db."""
    logger.info("Schreibe veränderte Zeilen zurück in die Datenbank...")
    try:
        with closing(sqlite3.connect(database_path)) as conn:
            cursor = conn.cursor()

            # Delete every row from assignments table, then append new
            # assignments table dataframe rows.
            # Doesn't replace the whole table! Or else FKs, datatypes and
            # other table info get deleted.
            cursor.execute(f"DELETE FROM {consts.TABLE_NAME_ASSIGNMENTS}")

            # Add all rules to assignment table, use append to not overwrite
            # fk relations
            df_all_assignments.to_sql(
                consts.TABLE_NAME_ASSIGNMENTS,
                conn,
                if_exists="append",
                index=False,
            )

            conn.commit()

            db_utils.write_new_round_counter_and_timestamp(current_round, conn)
            db_utils.vacuum_db(conn)

    except Exception:
        logger.error(
            "Veränderte Zeilen konnten nicht in die Datenbank"
            " zurückgeschrieben werden.",
        )
        raise


def rule_simulator(
    rule_preselection,
    list_rule_assignments,
    database_name,
    ruleset_name,
    stat_folder_name,
):
    """Apply rules to assignment table.

    Main function used for this task.
    """
    logger.info("Starte Regelanwendung...")

    # Get the current round from internal db table
    database_path = db_utils.get_db_path(database_name, True)
    with closing(sqlite3.connect(database_path)) as conn:
        current_round = db_utils.get_assignment_round(conn)

    # Begin new round and add method db message
    current_round += 1
    system_method = f"Sim Runde {current_round}"

    logger.info(f"Aktuelle Runde: {current_round}")

    # Initial DF based on starting table. Need to load the complete assignments
    # table because it will be dropped before writing back the modified df.
    # Pandas can't update an sql table with the same indices easily, so
    # sacrifice speed for utility
    logger.info("Lade komplette Belegungstabelle...")
    df_assignment_buffer = db_utils.get_df(
        database_name,
        consts.TABLE_NAME_ASSIGNMENTS,
    )

    # Keep copy of df_all_assignments for later comparisons
    df_all_assignments = df_assignment_buffer.copy()

    # Marks order of applied rules for tracking
    rule_application_order_info = 0

    logger.info("Wende Vorselektion an...")

    # Preselection of the current semester
    rule_semester = consts.RULE(
        "belegungen",
        "semester",
        "==",
        None,
        consts.RULE_SETTING_CURRENT_SEMESTER,
    )
    df_assignment_buffer = rule_utils.apply_rule_to_df(
        df_assignment_buffer,
        rule_semester.column_x,
        rule_semester.operator_symbol,
        rule_semester.table_y,
        rule_semester.column_y,
    )

    # Preselection to only use specified rows for rule appliance
    if rule_preselection is not None:
        rule_preselection = rule_utils.check_and_transform_rule(
            rule_preselection, add_suffix=True
        )
        
        df_assignment_buffer = (
            model_rule_sim_apply_rule.apply_preselection_rule(
                df_assignment_buffer,
                rule_preselection,
                database_name,
            )
        )

    # Loop through rules, always increasing order info per rule
    for rule in list_rule_assignments:
        rule_application_order_info += 1

        rule_name = rule["rule_name"]
        rule_assignment = rule["rule_assignment"]
        rule_assignment = rule_utils.check_and_transform_rule(rule_assignment)
        rule_join_operation = rule["rule_join_operation"]
        rule_assignment_2 = rule["rule_assignment_2"]
        rule_assignment_2 = rule_utils.check_and_transform_rule(
            rule_assignment_2,
        )

        logger.info(
            f"{consts.CONSOLE_BLUE}Wende Regel {rule_application_order_info}"
            f" von {len(list_rule_assignments)} an: '{rule_name}'"
            f" {consts.CONSOLE_ENDCMD}",
        )

        # Apply rule, then reassign modified start table. Every apply rule
        # call works on the same start table.
        # The modifed df_assignment_buffer is returned in full,
        # df_changed_assignments are returned as a set of rows that have had
        # their status altered this rule.
        (
            df_assignment_buffer,
            df_changed_assignments,
        ) = model_rule_sim_apply_rule.apply_assignment_rule(
            df_assignment_buffer,
            rule_assignment,
            rule_join_operation,
            rule_assignment_2,
            system_method,
            rule_application_order_info,
            database_name,
        )

        logger.info(
            "Anzahl der Zeilen mit Regelübereinstimmung und neuem"
            " vorläufigen Zulassungs-Status:"
            f" {len(df_changed_assignments.loc[df_changed_assignments[consts.COLUMN_NAME_ASSIGNMENTS_STATUS] == consts.RULE_SETTING_STATUS_PROPOSED].index)}",
        )

    # Set assignment _pk_id as index, removing it's column
    df_assignment_buffer.set_index(
        consts.COLUMN_NAME_ASSIGNMENTS_ID,
        inplace=True,
    )
    df_all_assignments.set_index(
        consts.COLUMN_NAME_ASSIGNMENTS_ID,
        inplace=True,
    )

    # Distribute lecture slots
    logger.info("Berechne zulässige Belegungsplätze und schreibe ein...")
    rule_count = len(list_rule_assignments)
    (
        df_assignment_buffer,
        df_accepted_assignments,
        df_denied_assignments,
    ) = model_rule_sim_apply_participant_slots.apply_participant_slots(
        df_assignment_buffer,
        database_name,
        rule_count,
        consts.RULE_SETTING_LOGGING_PER_LECTURE,
    )
    logger.info(
        f"Eingeschrieben mit Zulassung: '{len(df_accepted_assignments)}',"
        f" mit Ablehnung: '{len(df_denied_assignments)}'",
    )

    # Overwrite previous assignment table with modified rows.
    # Use option to disable a downcasting FutureWarning as all input data
    # already has the correct dtype
    pd.set_option("future.no_silent_downcasting", True)
    df_all_assignments.update(df_assignment_buffer, overwrite=True)

    # Check for and do lecture combination assignments.
    # The reason this is happening separate from the other status appliance is
    # that this feature would require a concat of all accepted assignments for
    # that lecture. Doing concats in the "apply_participant_slots" loop slows
    # down the whole process.
    logger.info(
        "Überprüfe ob Kombo-Einschreibungen getätigt werden sollen und wendet"
        " diese an...",
    )
    (
        df_all_assignments,
        df_accepted_lecture_combinations,
    ) = model_rule_sim_apply_lecture_combinations.apply_lecture_combinations(
        df_all_assignments,
        df_accepted_assignments,
        database_name,
    )

    # Get back "_pk_id" column from index. Stat files can keep _pk_id as
    # dataframe index, no need to write back as column
    df_all_assignments = df_all_assignments.reset_index(
        names=consts.COLUMN_NAME_ASSIGNMENTS_ID,
    )

    check_for_duplicate_ids(df_all_assignments)

    write_assignments_back_to_db(
        df_all_assignments,
        current_round,
        database_path,
    )

    logger.info("Schreibe Statistik Dateien...")

    rule_utils.write_stat_files(
        database_name,
        ruleset_name,
        stat_folder_name,
        current_round,
        consts.RULE_SETTING_CURRENT_SEMESTER,
        df_accepted_assignments,
        df_denied_assignments,
        df_accepted_lecture_combinations,
        df_assignment_buffer,
    )

    logger.info(
        f"{consts.CONSOLE_GREEN}Regeln erfolgreich angewandt."
        f" {consts.CONSOLE_ENDCMD}",
    )

    return True

