import os
import re
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
        noticias_atualizadas = [
            x for x in noticias_atualizadas if x["dt"] >= self.dt_max
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


def parser_fsp(self: Site, noticia_tag: Tag) -> dict:
    noticia = {"f": self.site}
    noticia["mat"] = noticia_tag.find("title").text
    noticia_url = re.findall(r"\*(http.*html)\"", noticia_tag.find("description").text)
    if not noticia_url:
        return None
    noticia["url"] = noticia_url[0]
    noticia_dt = re.findall(
        r"(\d{2}\/\d{2}\/\d{4} - \d{2}h\d{2})\)\s?$",
        noticia_tag.find("description").text,
    )[0]
    if not noticia_dt:
        return None
    noticia["dt"] = pendulum.from_format(
        noticia_dt,
        "MM/DD/YYYY [-] HH[h]mm",
        tz="America/Sao_Paulo",
    )
    return noticia


def atualizar_fsp(self: Site):
    s = httpx.Client()
    s.headers.update({"User-Agent": UserAgent().random})
    pag_inicial = self._construir_soup(s, self.url)
    noticias = pag_inicial.find_all("item")
    noticias_atualizadas = [self.parser_noticias(x) for x in noticias]
    noticias_atualizadas = filter(bool, noticias_atualizadas)

    self._gravar_noticias(noticias_atualizadas)


def parser_v_econ(self: Site, noticia_tag: Tag) -> dict:
    noticia = {"f": self.site}
    noticia["mat"] = noticia_tag.find("title").text.strip()
    noticia["url"] = noticia_tag.find("guid").text
    noticia["dt"] = pendulum.from_format(
        noticia_tag.find("pubdate").text,
        "ddd[,] DD MMM YYYY HH:mm:ss ZZ",
        tz="America/Sao_Paulo",
    )
    noticia_media = noticia_tag.find("media:content")
    noticia["img"] = noticia_media.get("url") if noticia_media is not None else None
    return noticia


def atualizar_v_econ(self: Site):
    s = httpx.Client()
    s.headers.update({"User-Agent": UserAgent().random})
    pag_inicial = self._construir_soup(s, self.url)
    noticias = pag_inicial.find_all("item")
    noticias_atualizadas = [self.parser_noticias(x) for x in noticias]
    noticias_atualizadas = filter(bool, noticias_atualizadas)

    self._gravar_noticias(noticias_atualizadas)


def parser_g1_econ(self: Site, noticia_tag: Tag) -> dict:
    noticia = {"f": self.site}
    noticia["mat"] = noticia_tag.find("title").text.strip()
    noticia["url"] = noticia_tag.find("guid").text
    noticia["dt"] = pendulum.from_format(
        noticia_tag.find("pubdate").text,
        "ddd[,] DD MMM YYYY HH:mm:ss ZZ",
        tz="America/Sao_Paulo",
    )
    noticia_media = noticia_tag.find("media:content")
    noticia["img"] = noticia_media.get("url") if noticia_media is not None else None
    return noticia


def atualizar_g1_econ(self: Site):
    s = httpx.Client()
    s.headers.update({"User-Agent": UserAgent().random})
    pag_inicial = self._construir_soup(s, self.url)
    noticias = pag_inicial.find_all("item")
    noticias_atualizadas = [self.parser_noticias(x) for x in noticias]
    noticias_atualizadas = filter(bool, noticias_atualizadas)

    self._gravar_noticias(noticias_atualizadas)


def parser_cnn_econ(self: Site, s: httpx.Client, noticia_url: str) -> dict:
    noticia = {"f": self.site, "url": noticia_url}
    soup_materia = self._construir_soup(s, noticia_url)

    post_title = soup_materia.find("h1", class_="post__title")
    if post_title is None:
        return None
    noticia["mat"] = post_title.text.strip()

    picture = soup_materia.find("picture", class_="img__destaque")
    if picture is not None:
        noticia["img"] = picture.img.get("src")

    data_post = soup_materia.find("span", class_="post__data").text.strip()
    re_data = re.search(r"\d{2}\/\d{2}\/\d{4} às \d{1,2}:\d{2}$", data_post)
    noticia["dt"] = pendulum.from_format(
        re_data.group(0), "DD/MM/YYYY [às] HH:mm", tz="America/Sao_Paulo"
    )

    return noticia


def atualizar_cnn_econ(self: Site):
    s = httpx.Client()
    s.headers.update({"User-Agent": UserAgent().random})
    pag_inicial = self._construir_soup(s, self.url)
    noticias = pag_inicial.find_all("a", href=re.compile(r"\.com\.br\/economia\/.+"))
    noticias_url = [noticia.get("href") for noticia in noticias]

    noticias_atualizadas = [self.parser_noticias(s, x) for x in noticias_url]
    noticias_atualizadas = filter(bool, noticias_atualizadas)

    self._gravar_noticias(noticias_atualizadas)
