import re
from dataclasses import dataclass
from datetime import datetime

import httpx
import polars as pl
import pytz
from bs4 import BeautifulSoup, Tag
from fake_useragent import UserAgent

from db import mongo


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

    def _construir_soup(self, s: httpx.Client, url: str) -> BeautifulSoup:
        page = s.get(url)
        resposta = page.content
        soup = BeautifulSoup(resposta, "lxml")
        return soup

    def _gravar_noticias(self, noticias_atualizadas: list = None) -> None:
        noticias_atualizadas = [
            x
            for x in noticias_atualizadas
            if x["dt"].astimezone(pytz.utc).replace(tzinfo=None) >= self.dt_max
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
            self.dt_max = dt_max_r[0]["dt"]
        else:
            self.dt_max = datetime(1990, 1, 1)


def parser_bbc(self: Site, noticia_tag: Tag) -> dict:
    noticia = {"f": self.site}
    noticia["mat"] = noticia_tag.find("a").text
    noticia["url"] = noticia_tag.find("a").get("href")
    noticia["img"] = noticia_tag.find("img").get("src")
    noticia["dt"] = datetime.strptime(
        noticia_tag.find("div", class_="promo-text").find("time").get("datetime")
        + " -0300",
        "%Y-%m-%d %z",
    )
    return noticia


def atualizar_bbc(self: Site):
    s = httpx.Client()
    s.headers.update({"User-Agent": UserAgent().random})
    pag_inicial = self._construir_soup(s, self.url)
    noticias = pag_inicial.find("main").find("div", class_=None).find_all("li")

    noticias_atualizadas = [self.parser_noticias(x) for x in noticias]
    noticias_atualizadas = filter(bool, noticias_atualizadas)

    self._gravar_noticias(noticias_atualizadas)


def parser_fsp(self: Site, noticia_tag: Tag) -> dict:
    noticia = {"f": self.site}
    noticia["mat"] = noticia_tag.find("title").text
    noticia_url = re.findall(r"\*(http.*html)\"", noticia_tag.find("description").text)
    if not noticia_url:
        return None
    noticia["url"] = noticia_url[0]
    noticia_dt = noticia_tag.find("pubdate").text
    if not noticia_dt:
        return None
    noticia["dt"] = datetime.strptime(
        noticia_tag.find("pubdate").text, "%d %b %Y %H:%M:%S %z"
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
    noticia["dt"] = datetime.strptime(
        noticia_tag.find("pubdate").text, "%a, %d %b %Y %H:%M:%S %z"
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
    noticia["dt"] = datetime.strptime(
        noticia_tag.find("pubdate").text, "%a, %d %b %Y %H:%M:%S %z"
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
    noticia["dt"] = datetime.strptime(
        re_data.group(0) + " -0300", "%d/%m/%Y às %H:%M %z"
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


bbc = Site(
    "bbc",
    "https://www.bbc.com/portuguese/topics/cvjp2jr0k9rt",
    atualizar_bbc,
    parser_bbc,
)
fsp = Site(
    "folha-sp-mercado",
    "https://feeds.folha.uol.com.br/mercado/rss091.xml",
    atualizar_fsp,
    parser_fsp,
)
v_econ = Site(
    "valor-economico",
    "https://pox.globo.com/rss/valor",
    atualizar_v_econ,
    parser_v_econ,
)
g1econ = Site(
    "g1-economia",
    "https://g1.globo.com/rss/g1/economia/",
    atualizar_g1_econ,
    parser_g1_econ,
)
cnn = Site(
    "cnn", "https://www.cnnbrasil.com.br/economia/", atualizar_cnn_econ, parser_cnn_econ
)

sites: list[Site] = [bbc, fsp, v_econ, g1econ, cnn]
