"""UI layout to show information about this software and licenses."""

import json
from pathlib import Path

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

import utils.constants as consts

dash.register_page(
    __name__,
    path=consts.PAGE_ABOUT_URL,
    title=consts.PAGE_ABOUT_TITLE_NAME,
    name=consts.PAGE_ABOUT_TITLE_NAME,
)


def read_license_texts():
    """Read in all license texts that were extracted from
    third party project packages or added by hand.
    """
    license_dir = Path(consts.FOLDER_ROOT, "LICENSES")

    # Read package info from a JSON file
    with Path.open(
        Path(license_dir, "third_party_package_licenses.json"),
        encoding="utf-8",
    ) as f:
        packages = json.load(f)

    # Return the licenses with their package name, version, url, and license
    # text as a dict
    return {package["Name"]: package for package in packages}


page_heading = html.Div(
    [
        html.H2("Über diese Anwendung"),
        html.P("Masterarbeit von Michael Hurst an der HTW Berlin."),
    ],
)

# Create Accordion items depending on used packages parsed earlier into a
# license info file
licenses = read_license_texts()

accordion = [
    dbc.AccordionItem(
        [
            html.P(f"Version: {info["Version"]}"),
            html.P(f"Lizenztyp: {info["License"]}"),
            dcc.Markdown(f"Lizenztext: \n\n{info["LicenseText"]}"),
            dbc.Button(
                "Link",
                href=info["URL"],
                target="_blank",
                outline=True,
                color="primary",
            ),
        ],
        title=package,
    )
    for package, info in licenses.items()
]


license_accordions = html.Div(
    [
        dbc.Row(html.H3("Open Source Lizenzen:"), className="mb-2"),
        dbc.Row(
            [
                dbc.Accordion(
                    accordion,
                    start_collapsed=True,
                ),
            ],
        ),
    ],
)

page_navigation = html.Div(
    [
        dbc.Stack(
            [
                dbc.Button(
                    "Zurück",
                    outline=True,
                    color="primary",
                    className="me-auto",
                    href=consts.PAGE_HOME_URL,
                ),
            ],
            direction="horizontal",
        ),
    ],
)

about = html.Div(
    [
        page_heading,
        html.Hr(),
        license_accordions,
        html.Hr(className="mt-5"),
        page_navigation,
        html.Div(className="mb-5"),
    ],
    className="page-container",
)

layout = dbc.Container(about, fluid=False, className="main-container")
