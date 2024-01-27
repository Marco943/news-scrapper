from pathlib import Path

import dash_mantine_components as dmc
import polars as pl
from dash import Dash
from dash_iconify import DashIconify

from db import mongo

noticias = (
    pl.concat(
        [
            pl.read_json(arquivo)
            for arquivo in Path().joinpath("noticias").glob("*.json")
        ],
        how="diagonal_relaxed",
    )
    .with_columns(pl.col.dt.str.to_datetime())
    .sort("dt", descending=True)
)

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
                                src=noticia["img"],
                                width=150,
                                height=80,
                                withPlaceholder=True,
                                display="block" if noticia["img"] else None,
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
                    color="gray",
                ),
                bg="#f4f4f4",
                px="0.5rem",
            ),
        ],
        radius="md",
        withBorder=True,
        mb="1rem",
    )


app.layout = dmc.Container(
    [caixa_noticia(noticia) for noticia in noticias.iter_rows(named=True)]
)

server.run(debug=True)
