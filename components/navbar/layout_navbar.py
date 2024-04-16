"""Layout for common navbar used by all pages."""

import dash_bootstrap_components as dbc
from dash import html

import utils.constants as consts

layout = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                dbc.Row(
                    [
                        dbc.Col(html.Img(src=consts.APP_LOGO, height="30px")),
                        dbc.Col(
                            dbc.NavbarBrand(consts.APP_NAME, className="ms-3"),
                        ),
                    ],
                    align="center",
                    className="g-0",
                ),
                href=consts.PAGE_HOME_URL,
                style={"textDecoration": "none"},
            ),
        ],
        fluid=False,
    ),
    color="dark",  # Navbar color
    dark=True,  # Mode for text color
)
