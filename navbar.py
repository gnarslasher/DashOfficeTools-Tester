import dash_bootstrap_components as dbc


def Navbar():
    navbar = dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink("Home", href="/")),
            dbc.DropdownMenu(
                children=[
                    dbc.DropdownMenuItem("Links", header=True, style={'color': 'white'}),
                    dbc.DropdownMenuItem(divider=True),
                    dbc.DropdownMenuItem("MT NRCS Snow Homepage", href="https://www.nrcs.usda.gov/wps/portal/nrcs/mt/snow/"
                                                                       "/snow/", target="_blank"),
                    dbc.DropdownMenuItem("NWCC Hompage", href="https://www.nrcs.usda.gov/wps/portal/wcc/home/", target="_blank"),
                ],
                nav=True,
                in_navbar=True,
                label="More",
                right=True,
            ),
        ],
        brand="Office Tools",
        color="primary",
        dark=True,
        fluid=True,
    )
    return navbar
