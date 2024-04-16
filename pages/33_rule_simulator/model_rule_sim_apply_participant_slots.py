"""Functions to assign assignments to participant slots."""

import sqlite3
from contextlib import closing

import pandas as pd

import utils.constants as consts
from utils import db_utils, rule_utils
from utils.logger import logger


def get_max_participants_for_lecture(lecture_id, group_id, conn):
    """Return the available slots for a given lecture."""
    cursor = conn.cursor()

    if pd.isna(group_id):
        cursor.execute(
            """
            SELECT v._pk_id, vg.gruppen_id, vg.max_teilnehmer
            FROM veranstaltung AS v
            JOIN veranstaltung_gruppengroesse AS vg
            ON v._pk_id = vg.veranstaltungs_id
            WHERE v._pk_id = ?
                AND vg.gruppen_id IS NULL
            """,
            (lecture_id,),
        )

    else:
        cursor.execute(
            """
            SELECT v._pk_id, vg.gruppen_id, vg.max_teilnehmer
            FROM veranstaltung AS v
            JOIN veranstaltung_gruppengroesse AS vg
            ON v._pk_id = vg.veranstaltungs_id
            WHERE v._pk_id = ?
                AND vg.gruppen_id = ?
            """,
            (
                lecture_id,
                group_id,
            ),
        )

    result = cursor.fetchall()

    if result:
        row = result[0]
        return {
            "_pk_id": row[0],
            "gruppen_id": row[1],
            "max_teilnehmer": row[2],
        }

    else:
        return None


def apply_participant_slots(
    df_assignment_buffer,
    database_name,
    rule_count,
    logging_per_lecture,
):
    """Assign proposed assignments to lectures.

    Rule groups that are below the max participant threshold get their status
    set to accepted. Rule groups that partially fit into the slots use the
    lottery to assign remaining slots. Rest is denied.
    """
    # Get all lecture + group id combinations and iterate through them
    lectures = df_assignment_buffer.drop_duplicates(
        subset=["veranstaltungs_id"],
    ).copy()
    logger.info(
        f"Anzahl an zu verarbeitenden Veranstaltungen: {len(lectures)}",
    )
    lectures = lectures[["veranstaltungs_id"]]
    lectures = lectures.astype(int)

    logger.info("Erstelle Dataframes für jede Veranstaltung...")
    # Define rules for selection of a single lecture (not to be mistaken with
    # the preselection rule)
    rule_lecture_selections = [
        rule_utils.check_and_transform_rule(
            consts.RULE(
                "belegungen",
                "veranstaltungs_id",
                "==",
                None,
                row[consts.COLUMN_NAME_ASSIGNMENTS_LECTURE_ID],
            ),
            False,
        )
        for _, row in lectures.iterrows()
    ]
    # Pre-compution of seperate dataframes for all lectures by selecting every
    # lecture from the buffer
    df_current_lectures = [
        rule_utils.apply_rule_to_df(
            df_assignment_buffer,
            rule.column_x,
            rule.operator_symbol,
            rule.table_y,
            rule.column_y,
        )
        for rule in rule_lecture_selections
    ]

    # Dataframe store for all rows with new accepted across all lectures
    df_accepted_assignments_list = []
    df_denied_assignments_list = []

    # Cycle through combination of lecture data and their dataframes
    for (index, lecture), df_current_lecture in zip(
        lectures.iterrows(),
        df_current_lectures,
        strict=False,
    ):
        if logging_per_lecture:
            logger.info(
                f"{consts.CONSOLE_BLUE}Verarbeite Veranstaltung"
                f" '{lecture[consts.COLUMN_NAME_ASSIGNMENTS_LECTURE_ID]}'"
                f" '{consts.CONSOLE_ENDCMD}",
            )

        # Select only proposed assignments from buffer
        df_current_lecture = df_current_lecture.loc[
            df_current_lecture["status"] == consts.RULE_SETTING_STATUS_PROPOSED
        ]

        # Make copy of lecture for stats
        df_current_lecture_all = df_current_lecture.copy()
        
        # Drop duplicate assignments per group
        df_current_lecture = df_current_lecture.drop_duplicates(
            subset=["matrikelnummer", "gruppen_id"],
        )

        groups = df_current_lecture["gruppen_id"].unique().tolist()

        enrolled_students = []
        participants_per_group = {group: 0 for group in groups}

        # Range means 1 or 2 here, because there are only 2 priorities
        for prio in range(1, 3):
            for group in groups:
                # Check max participants, if not found use standard setting
                max_participants = (
                    consts.RULE_SETTING_FALLBACK_PARTICIPANT_SIZE
                )
                database_path = db_utils.get_db_path(database_name, True)
                with closing(sqlite3.connect(database_path)) as conn:
                    result = get_max_participants_for_lecture(
                        int(
                            lecture[consts.COLUMN_NAME_ASSIGNMENTS_LECTURE_ID],
                        ),
                        group,
                        conn,
                    )

                    if (
                        result is not None
                        and result["max_teilnehmer"] is not None
                    ):
                        max_participants = result["max_teilnehmer"]

                    elif result is None:
                        max_participants = (
                            consts.RULE_SETTING_FALLBACK_PARTICIPANT_SIZE
                        )

                # Select only currently used group id from buffer
                if pd.isna(group):
                    # Extra loc statement for NA / Null values
                    df_current_group = df_current_lecture.loc[
                        df_current_lecture["gruppen_id"].isna()
                    ].copy()

                else:
                    df_current_group = df_current_lecture.loc[
                        df_current_lecture["gruppen_id"] == group
                    ].copy()

                # Select prio
                df_current_group = df_current_group.loc[
                    df_current_group["wunsch_prio"] == prio
                ].copy()

                # Calculation which rule fits into max participants, if rule
                # only partially fits use lottery
                participants = participants_per_group[group]
                participants_accepted = participants_per_group[group]
                slots_full = False

                # Check each rule from 1 to the total amount of rules
                for rule in range(1, rule_count + 1):
                    # Select only current rule for current rule group
                    df_current_rule = df_current_group.loc[
                        df_current_group["sortierwert"] == rule
                    ]

                    # Remove already accepted students
                    df_current_rule = df_current_rule[
                        ~df_current_rule["matrikelnummer"].isin(
                            enrolled_students,
                        )
                    ]

                    # Add amount of students from current rule group to
                    # participants check
                    applicants = len(df_current_rule.index)
                    participants += applicants

                    # Add rule group to accepted if less assignments in 
                    # it than available slots
                    if participants <= max_participants:
                        df_accepted_assignments_list.append(df_current_rule)

                        # Keep track of enrolled students so students only
                        # get enrolled once per event
                        enrolled_students.extend(
                            df_current_rule["matrikelnummer"].tolist(),
                        )

                        participants_accepted += applicants
                        participants_per_group[group] = participants_accepted

                    # Less remaining slots than assignments? Give remaining
                    # ones to the ones with the highest lottery number
                    elif slots_full is False:
                        participants -= applicants
                        slots_free = max_participants - participants
                        if slots_free < 0:
                            slots_free = 0
                        df_current_rule_accepted = df_current_rule.sort_values(
                            "los_nummer",
                            ascending=False,
                        ).head(slots_free)

                        # Add to accepted list
                        df_accepted_assignments_list.append(
                            df_current_rule_accepted,
                        )

                        enrolled_students.extend(
                            df_current_rule_accepted[
                                "matrikelnummer"
                            ].tolist(),
                        )

                        participants_accepted += len(
                            df_current_rule_accepted.index,
                        )
                        participants_per_group[group] = participants_accepted

                        # Mark that all slots are full
                        participants = max_participants
                        slots_full = True

                    # Ending up here means lecture is full

                if logging_per_lecture:
                    logger.info(f"Zulassungen: '{participants_accepted}'")

        # Create denied assigments df of this lecture by collecting remaining
        # proposed assignments
        df_denied_assignments = df_current_lecture_all.copy()
        # Change all remaining proposed assignments to denied
        df_denied_assignments.loc[
            df_denied_assignments["status"] == "PR",
            "status",
        ] = "AB"
        # DF should only consist of denied assignments, so only select their
        # status
        df_denied_assignments = df_denied_assignments[
            df_denied_assignments["status"] == "AB"
        ]
        df_denied_assignments_list.append(df_denied_assignments)
    
    # Concat all at once here instead of in the loop. This dramatically speeds
    # up this algorithm because of vectorization and less concats this way
    # Write all denied assignments to buffer
    df_denied_assignments = pd.DataFrame()
    if df_denied_assignments_list:
        df_denied_assignments = pd.concat(
            df_denied_assignments_list,
            verify_integrity=True,
        )
    if not df_denied_assignments.empty:
        df_assignment_buffer.update(df_denied_assignments, overwrite=True)

    # Write all accepted assignments to buffer
    df_accepted_assignments = pd.DataFrame()
    if df_accepted_assignments_list:
        df_accepted_assignments = pd.concat(
            df_accepted_assignments_list,
            verify_integrity=True,
        )
    df_accepted_assignments["status"] = consts.RULE_SETTING_STATUS_ACCEPTED
    df_assignment_buffer.update(df_accepted_assignments, overwrite=True)

    return df_assignment_buffer, df_accepted_assignments, df_denied_assignments
