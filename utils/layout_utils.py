"""Utils for layout specific tasks."""

import plotly.express as px
import sqlite3
from contextlib import closing

import utils.constants as consts
import utils.db_utils as db_utils
import utils.file_utils as file_utils


def validate_input_field_values(*values):
    """Check if a list of values is neither None, empty nor an empty string."""
    return all(
        value and value is not None and not str.isspace(value)
        for value in values
    )


def create_barchart_for_rules(df, stat_info):
    # Group status and rule number
    assignments_per_rule = (
        df.groupby(["sortierwert", "status"]).size().reset_index(name="Anzahl")
    )

    # Sort count ascending
    assignments_per_rule = assignments_per_rule.sort_values(
        by="Anzahl", ascending=False
    )

    figure = px.bar(
        assignments_per_rule,
        x="sortierwert",
        y="Anzahl",
        color="status",
        barmode="stack",
        template=consts.VISU_SETTING_PLOTLY_THEME,
        text_auto=True,
        color_discrete_sequence=px.colors.qualitative.Bold,
        category_orders={"status": assignments_per_rule["status"].tolist()},
    )

    # Update font size and text position
    figure.update_traces(
        textfont_size=12,
        textposition="outside",
        cliponaxis=False,
    )

    # Rule names on X-axis
    # Get the total amount of rules
    max_sort = df["sortierwert"].max()
    rules_total = df["sortierwert"].value_counts().sort_index()
    rules_total = rules_total.reindex(range(1, max_sort + 1), fill_value=0)

    # X-axis labels
    rule_names = [
        rule["rule_name"] for rule in stat_info["ruleset_rules_assignment"]
    ]
    tick_labels = [
        f"{rule_names[x-1]}:<br>{rules_total[x]}"
        for x in range(1, max_sort + 1)
    ]

    # X-axis update
    figure.update_xaxes(
        ticktext=tick_labels,
        tickvals=list(range(1, max_sort + 1)),
        tickfont_size=14,
        title_text="Regeln",
    )

    return figure


def create_piechart_for_assignment_status(df):
    """Count the number of assignments per status"""
    assignments_per_status = df["status"].value_counts().reset_index()
    assignments_per_status.columns = ["status", "counts"]

    figure = px.pie(
        assignments_per_status,
        values="counts",
        names="status",
        template=consts.VISU_SETTING_PLOTLY_THEME,
        color_discrete_sequence=px.colors.qualitative.Bold,
    )
    figure.update_traces(
        textposition="inside", hoverinfo="label+value", textinfo="label+value"
    )

    return figure


def expand_db_value_names(df, column, database_name):
    """Changes the shown table values from abbreviated db form
    to full text via descriptors file.
    
    Also adds full names to study program and group id numbers.
    """
    descriptors = file_utils.read_json(
        consts.FOLDER_UTILS, "base_db_value_descriptors.json"
    )

    if column in descriptors:
        for key, value in descriptors[column].items():
            df.loc[df[column] == key, column] = value

    if column in ["studiengangs_id", "gruppen_id", "veranstaltungs_id"]:
        unique_ids = df[column].drop_duplicates().tolist().copy()
        if column == "studiengangs_id":
            table_name = "studiengang"
        elif column == "veranstaltungs_id":
            table_name = "veranstaltung"
        else:
            table_name = "i_gruppe"

        if column == "studiengangs_id":
            column_name = "kurztext"
        elif column == "veranstaltungs_id":
            column_name = "kurztext"
        else:
            column_name = "text"

        database_path = db_utils.get_db_path(
            database_name, check_file_presence=True
        )
        with closing(sqlite3.connect(database_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            for id in unique_ids:
                cursor.execute(
                    f"SELECT * FROM {table_name} WHERE _pk_id = ? LIMIT 1",
                    (id,),
                )
                result = cursor.fetchone()

                if result is not None:
                    value = result[column_name]
                    df[column] = df[column].astype(str)
                    df.loc[df[column] == str(id), column] = value

    return df
