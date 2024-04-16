"""Functions to apply rules to a dataframe."""

import datetime
import sqlite3
from contextlib import closing

import pandas as pd

import utils.constants as consts
from utils import db_utils, file_utils, rule_utils
from utils.logger import logger

from . import model_rule_sim_custom_patches


# Used as base: https://en.wikipedia.org/wiki/Breadth-first_search (last accessed 12.04.2024)
def find_path(start, goals, fk_relations):
    """Use a tweaked Breadth First Algorithm to determine the path between a
    start table and multiple goal tables based on their foreign key
    relationships.
    """
    # Create a dict to save relations between tables
    graph = {}
    for relation in fk_relations:
        if relation[0] not in graph:
            graph[relation[0]] = []
        graph[relation[0]].append(relation)

    # Initialize queue with starting table
    queue = [(start, [])]

    # Use an unordered set to store the visited tables
    visited = set()

    # Paths to return
    # If theres no path to a goal, these will stay None
    paths_to_goals = {goal: None for goal in goals}

    # Check every item in the queue as long as the queue has elements and 
    # unvisited nodes exist
    while queue and any(path is None for path in paths_to_goals.values()):
        # Remove first node from queue
        node, path = queue.pop(0)

        if node not in visited:
            visited.add(node)

            # If the node has neighbors, add all neighboring nodes of current
            # node to queue
            if node in graph:
                for neighbor in graph[node]:
                    new_path = path + [neighbor]
                    # Check if current node is a goal and it hasnt been visited
                    # yet
                    if (
                        neighbor[2] in goals
                        and paths_to_goals[neighbor[2]] is None
                    ):
                        # Node is a goal, so add it's path to final goals list
                        paths_to_goals[neighbor[2]] = new_path
                    # Add neighbor to queue if not a goal or is goal but has
                    # been found already
                    queue.append((neighbor[2], new_path))

    # Return list of all found paths
    return list(paths_to_goals.values())


def load_and_merge_tables(
    df_assignment_buffer,
    rule_assignment,
    rule_assignment_2,
    database_name: str,
):
    """Merge multiple Dataframes as left join depending on a path of their
    database foreign keys.
    """
    # Copy start table so original start table stays untouched.
    # Start table could be returned for later updating of changed lines and
    # writing back to db
    df_merge = df_assignment_buffer.copy()

    # Add suffixes to all column names of all assignment table, so column names
    # will be unique in case of overlapping column names with other tables.
    # Important when merging
    df_merge.columns = [
        f"{col}__{consts.TABLE_NAME_ASSIGNMENTS}"
        if f"__{consts.TABLE_NAME_ASSIGNMENTS}" not in col
        else col
        for col in df_merge.columns
    ]

    # Define the goals for the merger path to fulfill, means these are the
    # tables that need to be merged
    if rule_assignment_2 is not None:
        pathfinding_goals = [
            rule_assignment.table_x,
            rule_assignment.table_y,
            rule_assignment_2.table_x,
            rule_assignment_2.table_y,
        ]
    else:
        pathfinding_goals = [
            rule_assignment.table_x,
            rule_assignment.table_y,
        ]

    database_path = db_utils.get_db_path(database_name, True)
    with closing(sqlite3.connect(database_path)) as conn:
        # Get foreign key relations, as these define the connections that can
        # be made between tables
        fk_relations = db_utils.get_foreign_key_relations(conn)

    # Check which tables can be connected through breadth first search
    paths = find_path(
        consts.TABLE_NAME_ASSIGNMENTS,
        pathfinding_goals,
        fk_relations,
    )

    # Init list for already merged tables. Used if paths to table 1, 2, 3 and
    # 4 have a common node table. Otherwise there would be duplicate merges
    processed_tables = [consts.TABLE_NAME_ASSIGNMENTS]

    # base db structure for getting dtypes of different dataframes that need
    # to be merged
    base_db_structure = file_utils.read_json(
        consts.FOLDER_UTILS,
        consts.FILENAME_BASE_DB_STRUCTURE,
    )

    with closing(sqlite3.connect(database_path)) as conn:
        # Merge dataframes by cycling through paths
        for path in paths:
            if path is None:
                continue
            for relation in path:
                table1, fk1, table2, fk2 = relation
                if table2 not in processed_tables:
                    # Get tables from db as df
                    dtypes = db_utils.get_dtypes(base_db_structure, table2)
                    df = model_rule_sim_custom_patches.run_custom_rule_patches(
                        table2,
                        dtypes,
                        conn,
                    )

                    # Rename column names to make them unique
                    df.columns = [
                        f"{col}__{table2}" if f"__{table2}" not in col else col
                        for col in df.columns
                    ]
                    
                    # Check to warn for righthandise merge overflow
                    row_amount_lefthandside = len(df_merge)

                    # Merge via left_on and right_on names from their foreign
                    # key relationship
                    # Pandas Merge Variants: https://stackoverflow.com/questions/53645882/pandas-merging-101 (last accessed: 14.04.2024)
                    df_merge = pd.merge(
                        df_merge,
                        df,
                        left_on=f"{fk1}__{table1}",
                        right_on=f"{fk2}__{table2}",
                        how="left",
                    ).reset_index(drop=True)
                    
                    # Check to warn for righthandise merge overflow
                    if len(df_merge) > row_amount_lefthandside:
                        logger.warning(f"""Bei der Tabellenverknüpfung von {table1}
                        mit {table2} entstanden mehr Reihen in der Belegungstabelle.
                        Bitte überprüfen und ggf. patchen.""")

                    processed_tables.append(table2)

    # Returns one (sometimes big) dataframe with all data needed to apply a
    # given rule
    return df_merge


def cleanup_assignment_df(df):
    """Remove all merged columns so that only assignment table is leftover."""
    cols_to_keep = [
        col
        for col in df.columns
        if col.endswith(f"__{consts.TABLE_NAME_ASSIGNMENTS}")
    ]
    df = df[cols_to_keep]

    # Remove suffix from column names, not needed anymore
    df.columns = [
        col.replace("__" + consts.TABLE_NAME_ASSIGNMENTS, "")
        for col in df.columns
    ]

    return df


def join_assignment_dfs(df_rule_applied, df_rule_applied_2, operation):
    """Join two dataframes together using a union operator."""
    # Prepare for DF combination, add suffix to avoid crashing columns with the
    # same name together
    suffix = "_df_rule_applied_2"

    df_rule_applied_2 = df_rule_applied_2.add_suffix(suffix)

    # Actual join happens here
    if operation == "AND":
        result_df = df_rule_applied.join(df_rule_applied_2, how="inner")
    elif operation == "OR":
        result_df = df_rule_applied.join(df_rule_applied_2, how="outer")
    elif operation == "NOT":
        result_df = df_rule_applied[
            ~df_rule_applied.index.isin(df_rule_applied_2.index)
        ]
    else:
        # Rules should always be prepared as a bundle, which checks the
        # validity of operation. raise just for safety
        raise ValueError(
            "Ungültige Operation für den Regelvergleich:"
            f" Operatorion muss in '{consts.JOIN_OPERATORS}' sein.",
        )

    # Remove identical duplicated rows that were created by join operation
    result_df = result_df.drop_duplicates(keep="first")

    for col in df_rule_applied.columns:
        # Move values from right side with suffix to left side without suffix
        result_df.update({col: result_df[col + suffix]})
        # Delete these columns to get old df structure back
        result_df = result_df.drop(columns=[col + suffix])

    return result_df


def apply_preselection_rule(
    df_assignment_buffer,
    rule_preselection,
    database_name: str,
):
    """Apply a rule for preselecting assignment table items.

    Can be used to e.g. select only one lecture.
    """
    # Merge all tables needed for rule application
    # Column names have their origin table added as suffix to be unique
    df_merged_required_tables = load_and_merge_tables(
        df_assignment_buffer,
        rule_preselection,
        None,
        database_name,
    )

    # Apply preselection
    df_rule_applied = rule_utils.apply_rule_to_df(
        df_merged_required_tables,
        rule_preselection.column_x,
        rule_preselection.operator_symbol,
        rule_preselection.table_y,
        rule_preselection.column_y,
    )
    # Remove every table other than assignments table and rename column back again without suffix
    return cleanup_assignment_df(df_rule_applied)


def apply_assignment_rule(
    df_assignment_buffer,
    rule_assignment,
    rule_join_operation,
    rule_assignment_2,
    system_method: str,
    rule_application_order_info: int,
    database_name: str,
):
    """Apply a rule to a dataframe."""
    # Merge all tables needed for rule application
    # Column names have their origin table added as suffix to be unique
    df_merged_required_tables = load_and_merge_tables(
        df_assignment_buffer,
        rule_assignment,
        rule_assignment_2,
        database_name,
    )

    # Only use enrolled entries for rule appliance
    df_merged_required_tables = df_merged_required_tables[
        df_merged_required_tables[
            f"{consts.COLUMN_NAME_ASSIGNMENTS_STATUS}__{consts.TABLE_NAME_ASSIGNMENTS}"
        ]
        == consts.RULE_SETTING_STATUS_ENROLLED
    ]

    # Apply the first rule to df
    df_rule_applied = rule_utils.apply_rule_to_df(
        df_merged_required_tables,
        rule_assignment.column_x,
        rule_assignment.operator_symbol,
        rule_assignment.table_y,
        rule_assignment.column_y,
    )
    # Cleanup removes merged tables and column suffixes
    df_rule_applied = cleanup_assignment_df(df_rule_applied)

    # Check if there is a second rule and create another dataframe with these
    # applied rules for later join of both dfs
    try:
        if rule_join_operation is not None and rule_assignment_2 is not None:
            df_rule_applied_2 = rule_utils.apply_rule_to_df(
                df_merged_required_tables,
                rule_assignment_2.column_x,
                rule_assignment_2.operator_symbol,
                rule_assignment_2.table_y,
                rule_assignment_2.column_y,
            )
            df_rule_applied_2 = cleanup_assignment_df(df_rule_applied_2)

    except Exception:
        logger.error(
            f"Falsches Regelformat für {rule_assignment},"
            f" {rule_join_operation}, {rule_assignment_2}.",
        )
        raise

    # Join the two dataframes with applied rules
    if rule_join_operation is not None and rule_assignment_2 is not None:
        df_rule_applied = join_assignment_dfs(
            df_rule_applied,
            df_rule_applied_2,
            rule_join_operation,
        )

    # Check if there are already some rows with the accepted status.
    # These should not change and have their info not overwritten
    # Only useful when there are multiple rounds
    df_rule_applied = df_rule_applied.loc[
        df_rule_applied[f"{consts.COLUMN_NAME_ASSIGNMENTS_STATUS}"]
        != consts.RULE_SETTING_STATUS_ACCEPTED
    ]

    # Add new status info to the set of rows that made it through the rule(s)
    # Status for proposition
    df_rule_applied[f"{consts.COLUMN_NAME_ASSIGNMENTS_STATUS}"] = (
        consts.RULE_SETTING_STATUS_PROPOSED
    )

    # Order info -> what rule set the new status
    df_rule_applied[
        f"{consts.COLUMN_NAME_ASSIGNMENTS_APPLICATION_ORDER_INFO}"
    ] = rule_application_order_info

    # Timestamp
    df_rule_applied[f"{consts.COLUMN_NAME_ASSIGNMENTS_TIMESTAMP}"] = (
        datetime.datetime.now()
    )

    # System Message, e.g. for the round counter
    df_rule_applied[f"{consts.COLUMN_NAME_ASSIGNMENTS_SYSTEM_METHOD}"] = (
        system_method
    )

    # Set assignment ids as index, so modified rows overwrite their previous
    # ones in buffer with the same id
    df_rule_applied.set_index(consts.COLUMN_NAME_ASSIGNMENTS_ID, inplace=True)
    df_assignment_buffer.set_index(
        consts.COLUMN_NAME_ASSIGNMENTS_ID,
        inplace=True,
    )

    # Overwrite assignment table with modified rows. Use option to disable a
    # downcasting FutureWarning as all input data already has the correct dtype
    pd.set_option("future.no_silent_downcasting", True)
    df_assignment_buffer.update(df_rule_applied, overwrite=True)

    # Create column from index, so id is not missing
    df_rule_applied[consts.COLUMN_NAME_ASSIGNMENTS_ID] = df_rule_applied.index
    df_assignment_buffer[consts.COLUMN_NAME_ASSIGNMENTS_ID] = (
        df_assignment_buffer.index
    )

    return df_assignment_buffer, df_rule_applied
