from datetime import datetime

import httpx
from bs4 import Tag
from modelos import Site


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
    s.headers.update({"User-Agent": self.agent})
    pag_inicial = self._construir_soup(s, self.url)
    noticias = pag_inicial.find("main").find("div", class_=None).find_all("li")

    noticias_atualizadas = [self.parser_noticias(x) for x in noticias]
    noticias_atualizadas = filter(bool, noticias_atualizadas)

    self._gravar_noticias(noticias_atualizadas)


bbc = Site(
    "bbc",
    "https://www.bbc.com/portuguese/topics/cvjp2jr0k9rt",
    atualizar_bbc,
    parser_bbc,
)
