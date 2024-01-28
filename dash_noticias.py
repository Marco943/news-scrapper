from pathlib import Path

import dash_mantine_components as dmc
import polars as pl
from dash import Dash, Input, Output, State, callback, callback_context, dcc, html
from dash_iconify import DashIconify
from icecream import ic

from db import mongo

BATELADA_NOTICIAS = 5


app = Dash(__name__)
server = app.server


def caixa_noticia(noticia: dict):
    return dmc.Card(
        [
            dmc.CardSection(
                dmc.Grid(
                    [
                        dmc.Col(
                            dmc.Image(
                                src=noticia.get("img", None),
                                width=150,
                                height=80,
                                withPlaceholder=True,
                                display="block",
                            ),
                            span="content",
                            p=0,
                        ),
                        dmc.Col(
                            dmc.Anchor(
                                dmc.Text(noticia["mat"], size="lg"),
                                href=noticia["url"],
                            ),
                            span="auto",
                        ),
                    ],
                    m=0,
                ),
                withBorder=True,
            ),
            dmc.CardSection(
                dmc.Text(
                    [
                        noticia["f"].upper(),
                        " - ",
                        noticia["dt"].strftime("%d/%m/%Y %H:%M"),
                    ],
                    size="xs",
                    italic=True,
                    color="dimmed",
                ),
                px="0.5rem",
            ),
        ],
        radius="md",
        withBorder=True,
        mb="1rem",
    )


def main_layout():
    total_noticias = round(
        pl.scan_parquet("noticias.parquet")
        .select(pl.count())
        .collect()
        .get_column("count")
        .max()
        / BATELADA_NOTICIAS
    )
    return dmc.MantineProvider(
        id="mantine-provider",
        theme={"primaryColor": "yellow", "colorScheme": "light"},
        withCSSVariables=True,
        withGlobalStyles=True,
        withNormalizeCSS=True,
        inherit=True,
        children=[
            dmc.Container(
                [
                    dmc.Button("Tema Claro/Escuro", id="mudar-tema"),
                    html.Div(id="noticias-corpo"),
                    dmc.Pagination(total=total_noticias, id="noticias-nav", page=1),
                ]
            )
        ],
    )


app.layout = main_layout


@callback(
    Output("mantine-provider", "theme"),
    Input("mudar-tema", "n_clicks"),
    State("mantine-provider", "theme"),
)
def mudar_tema(n, theme):
    if not n:
        pass
    elif theme["colorScheme"] == "light":
        theme["colorScheme"] = "dark"
    else:
        theme["colorScheme"] = "light"
    return theme


@callback(
    Output("noticias-corpo", "children"),
    Input("noticias-nav", "page"),
)
def mudar_pagina_noticias(pag: int):
    noticias = (
        (
            pl.scan_parquet("noticias.parquet")
            .sort("dt", descending=True)
            .slice(BATELADA_NOTICIAS * (pag - 1), BATELADA_NOTICIAS)
        )
        .collect()
        .to_dicts()
    )

    return [caixa_noticia(noticia) for noticia in noticias]


app.run(debug=True)
