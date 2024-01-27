import re
from dataclasses import dataclass
from pathlib import Path

import httpx
import pendulum
import polars as pl
from bs4 import BeautifulSoup, Tag
from fake_useragent import UserAgent
from icecream import ic


@dataclass
class Site:
    site: str
    url: str
    atualizar_noticias: callable
    parser_noticias: callable

    def __post_init__(self):
        self.atualizar_noticias = self.atualizar_noticias.__get__(self)
        self.parser_noticias = self.parser_noticias.__get__(self)
        self._caminho = Path().joinpath("noticias").joinpath(f"{self.site}.json")
        self._caminho.parent.mkdir(exist_ok=True)
        self._ler_noticias()

    def _construir_soup(self, s: httpx.Client, url: str) -> BeautifulSoup:
        page = s.get(url)
        resposta = page.text
        soup = BeautifulSoup(resposta, "lxml")
        return soup

    def _gravar_noticias(self, noticias_atualizadas: list = None) -> None:
        df = pl.from_dicts(noticias_atualizadas)
        if noticias_atualizadas is not None and not self.noticias.is_empty():
            df = df.filter(~pl.col("url").is_in(self.noticias["url"].unique()))
        self.noticias = pl.concat([self.noticias, df])

        self.noticias.write_json(self._caminho, pretty=False, row_oriented=True)

    def _ler_noticias(self) -> pl.DataFrame:
        if not self._caminho.exists():
            self.noticias = pl.DataFrame()
        else:
            self.noticias = pl.read_json(self._caminho)
        return self.noticias


def parser_bbc(self: Site, noticia_tag: Tag) -> dict:
    noticia = {"f": self.site}
    noticia["mat"] = noticia_tag.text
    noticia["url"] = noticia_tag.get("href")
    noticia["img"] = noticia_tag.parent.parent.parent.find("img").get("src")
    noticia["dt"] = pendulum.from_format(
        noticia_tag.parent.parent.find("time").get("datetime"),
        "YYYY-MM-DD",
        tz="America/Sao_Paulo",
    ).to_iso8601_string()
    return noticia


def atualizar_bbc(self: Site):
    s = httpx.Client()
    s.headers.update({"User-Agent": UserAgent().random})
    pag_inicial = self._construir_soup(s, self.url)
    noticias = pag_inicial.find_all(
        "a", href=re.compile(r"\.com\/portuguese\/articles\/.+")
    )
    # if noticia.get("href") not in self.noticias.get_column("url")

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
    ).to_iso8601_string()
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
    ).to_iso8601_string()
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
    ).to_iso8601_string()
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
    ).to_iso8601_string()

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
