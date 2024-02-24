import os
from dataclasses import dataclass
from datetime import datetime

import httpx
import pendulum
from bs4 import BeautifulSoup, Tag
from dotenv import load_dotenv
from fake_useragent import UserAgent
from pymongo import MongoClient

load_dotenv()

mongo = MongoClient(os.environ.get("DB_ECONODATA"))


@dataclass
class Noticia:
    f: str = None
    mat: str = None
    url: str = None
    img: str = None
    dt: datetime = None


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

    def _construir_soup(
        self, s: httpx.Client, url: str, features: str = "lxml"
    ) -> BeautifulSoup:
        page = s.get(url)
        resposta = page.content
        soup = BeautifulSoup(resposta, features)
        return soup

    def _gravar_noticias(self, noticias_atualizadas: list = None) -> None:
        if self.debug:
            print(list(noticias_atualizadas))
            return None
        noticias_atualizadas = [
            x for x in noticias_atualizadas if x["dt"] > self.dt_max
        ]
        if noticias_atualizadas:
            r = mongo["Econodata"]["Notícias"].insert_many(noticias_atualizadas)
            print(f"{self.site}: {len(r.inserted_ids)} notícias atualizadas")
        else:
            print(f"{self.site}: Sem notícias para atualizar")

    def _ler_noticias(self):
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


@dataclass
class SiteAsync(Site):
    async def _construir_soup(self, s: httpx.AsyncClient, url: str) -> BeautifulSoup:
        page = await s.get(url)
        resposta = page.content
        soup = BeautifulSoup(resposta, "lxml")
        return soup


def parser_googlerss(self: Site, noticia_tag: Tag) -> dict:
    noticia = {"f": self.site}
    noticia["mat"] = noticia_tag.find("title").text.strip()
    noticia["url"] = noticia_tag.find("link").text
    noticia["dt"] = datetime.strptime(
        noticia_tag.find("pubdate").text, "%a, %d %b %Y %H:%M:%S %Z"
    )
    noticia["img"] = None
    return noticia


def atualizar_googlerss(self: Site):
    s = httpx.Client()
    s.headers.update({"User-Agent": self.agent})
    pag_inicial = self._construir_soup(s, self.url)
    noticias = pag_inicial.find_all("item")
    noticias_atualizadas = [self.parser_noticias(x) for x in noticias]
    noticias_atualizadas = filter(bool, noticias_atualizadas)

    self._gravar_noticias(noticias_atualizadas)


@dataclass
class SiteGoogleRSS(Site):
    parser_noticias: callable = parser_googlerss
    atualizar_noticias: callable = atualizar_googlerss

    def __post_init__(self):
        self.url = f"https://news.google.com/rss/search?q=site%3A{self.url}%20when%3A7d&hl=en-US&gl=US&ceid=US%3Aen"
        return super().__post_init__()
