"""Common data store for all layout tabs.

This way stat data only needs to be loaded once. The common / global variable
stat_data should be treated as read only when imported as manipulating this
variable could result in race conditions.

Consideration:
The native dash component dcc.Store can also save data between callbacks.
But dataframes must be converted to and from dataframes when using dcc.Store,
resulting in very long processing times. Browser storage options from dcc.Store
also aren't feasable because of size limitations when using big dataframes.

Some dash apps load all their static data from dataframes when the program /
server starts, avoiding dcc.Store entirely.
In this app, the loaded data is chosen by the user so it needs to happen at
runtime.
"""

import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, callback, html

import utils.constants as consts
from utils import db_utils, file_utils, rule_utils
from utils.logger import logger

# Dict containing stat data that other files can import.
# Only create_data_store() should ever write to or manipulate the data_store.
data_store = {}

loading_spinner = html.Div(
    [
        dbc.Spinner(
            children=html.Div(id="spinner-visualizer-data-store"),
            size="md",
            fullscreen=True,
        ),
        dbc.Alert(
            color="warning",
            id="alert-visualizer",
            is_open=False,
        ),
    ],
)


def create_data_store(stat_name: str, stat_suffix: str):
    """Load stat folder by name into dict."""
    logger.info(f"Visualizer Data Store lädt für '{stat_name}'...")
    (
        stat_info,
        df_accepted_assignments,
        df_denied_assignments,
        df_accepted_lecture_combinations,
        df_assignments,
    ) = rule_utils.read_stat_files(stat_name)

    if df_accepted_assignments.empty and df_denied_assignments.empty:
        return None

    # Add stat name and info to store
    data_store[f"stat_name{stat_suffix}"] = stat_name
    data_store[f"stat_info{stat_suffix}"] = stat_info

    # Load students table to dataframe
    database_name = stat_info["database_filename"]
    df_students = db_utils.get_df(
        database_name,
        "studierende",
        condition="_pk_semester",
        condition_value=stat_info["assignment_semester"],
    )
    df_students = df_students.drop_duplicates(
        subset="_pk_matrikelnummer", keep="first"
    )

    # Merge student columns to each dataframe
    student_columns = [
        "_pk_matrikelnummer",
        "hoererstatus",
        "studiumsart",
        "studiumstyp",
    ]

    dataframes = {
        "df_accepted_assignments": df_accepted_assignments,
        "df_denied_assignments": df_denied_assignments,
        "df_accepted_lecture_combinations": df_accepted_lecture_combinations,
        "df_assignments": df_assignments,
        "df_all_new_assignments": pd.concat(
            [
                df_accepted_assignments,
                df_denied_assignments,
            ],
        ),
    }

    for name, df in dataframes.items():
        if not df.empty:
            df = df.merge(
                df_students[student_columns],
                left_on="matrikelnummer",
                right_on="_pk_matrikelnummer",
                how="left",
            )
        data_store[f"{name}{stat_suffix}"] = df

    logger.info(f"Visualizer Data Store für '{stat_name}' fertig geladen.")
    return data_store


@callback(
    Output("data-store-loaded-check", "hidden"),
    Output("spinner-visualizer-data-store", "children"),
    Output("alert-visualizer", "is_open"),
    Output("alert-visualizer", "children"),
    Input("url-visualizer", "search"),
    Input("url-visualizer", "pathname"),
)
def load_stats_into_store(
    search,
    pathname,
):
    """Load stats into store dict depending on stat names in query string.

    Activates on page load by checking query string for stat names.
    """
    if search and pathname == consts.PAGE_VISUALIZER_URL:
        stat_name_a = file_utils.get_query_string(search, "stat_a")
        stat_name_b = file_utils.get_query_string(search, "stat_b")
        # Use data_store declared outisde of this function
        global data_store

        if stat_name_a:
            data_store = create_data_store(stat_name_a, "_a")
            if data_store is None:
                return (
                    False,
                    "",
                    True,
                    f"{stat_name_a} hat keine neuen Einschreibungen, daher kann nichts visualisiert werden.",
                )

            data_store.update(data_store)

        if stat_name_b:
            data_store_b = create_data_store(stat_name_b, "_b")
            if data_store_b is None:
                return (
                    False,
                    "",
                    True,
                    f"{stat_name_b} hat keine neuen Einschreibungen, daher kann nichts visualisiert werden.",
                )

            data_store.update(data_store_b)

            # Pre-calculate a common dataframe for a and b
            df_all_new_assignments_a = data_store["df_all_new_assignments_a"]
            df_all_new_assignments_b = data_store["df_all_new_assignments_b"]
            df_all_new_assignments_a["Statistik"] = stat_name_a
            df_all_new_assignments_b["Statistik"] = stat_name_b

            df_all_new_assignments_a_b = pd.concat(
                [df_all_new_assignments_a, df_all_new_assignments_b],
            )
            df_all_new_assignments_a_b.reset_index(drop=True, inplace=True)
            data_store["df_all_new_assignments_a_b"] = (
                df_all_new_assignments_a_b
            )

            logger.info("Data Store geladen.")

        return True, "", False, ""

    return False, "", False, ""
