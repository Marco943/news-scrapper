import os
from dataclasses import dataclass

import httpx
import pendulum
import polars as pl
from bs4 import BeautifulSoup, Tag
from dotenv import load_dotenv
from fake_useragent import UserAgent
from pymongo import MongoClient

load_dotenv()

mongo = MongoClient(os.environ.get("DB_ECONODATA"))


@dataclass
class Site:
    site: str
    url: str
    atualizar_noticias: callable
    parser_noticias: callable
    debug: bool = False

    def __post_init__(self):
        self.atualizar_noticias = self.atualizar_noticias.__get__(self)
        self.parser_noticias = self.parser_noticias.__get__(self)
        self._ler_noticias()
        self.agent = UserAgent().random

    def _construir_soup(self, s: httpx.Client, url: str) -> BeautifulSoup:
        page = s.get(url)
        resposta = page.content
        soup = BeautifulSoup(resposta, "lxml")
        return soup

    def _gravar_noticias(self, noticias_atualizadas: list = None) -> None:
        if not self.debug:
            print(noticias_atualizadas)
            return None
        noticias_atualizadas = [
            x for x in noticias_atualizadas if x["dt"] > self.dt_max
        ]
        r = mongo["Econodata"]["Notícias"].insert_many(noticias_atualizadas)
        print(f"{len(r.inserted_ids)} notícias atualizadas")

    def _ler_noticias(self) -> pl.DataFrame:
        dt_max_r = list(
            mongo["Econodata"]["Notícias"].aggregate(
                [
                    {"$match": {"f": self.site}},
                    {"$sort": {"dt": -1}},
                    {"$limit": 1},
                ]
            )
        )
        if dt_max_r:
            self.dt_max = pendulum.parse(dt_max_r[0]["dt"].isoformat())
        else:
            self.dt_max = pendulum.datetime(1990, 1, 1)
