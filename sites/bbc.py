from datetime import datetime

import httpx
from bs4 import Tag

from .modelos import Site


def parser_bbc(self: Site, noticia_tag: Tag) -> dict:
    noticia = {"f": self.site}
    noticia["mat"] = noticia_tag.find("title").text.strip()
    noticia["url"] = noticia_tag.find("link").get("href")
    noticia["img"] = noticia_tag.find("thumbnail").get("url")
    noticia["dt"] = datetime.fromisoformat(noticia_tag.find("published").text)
    return noticia


def atualizar_bbc(self: Site):
    s = httpx.Client()
    s.headers.update({"User-Agent": self.agent})
    pag_inicial = self._construir_soup(s, self.url, "xml")
    noticias = pag_inicial.find_all("entry")

    noticias_atualizadas = [self.parser_noticias(x) for x in noticias]
    noticias_atualizadas = filter(bool, noticias_atualizadas)

    self._gravar_noticias(noticias_atualizadas)


bbc = Site(
    "BBC Brasil",
    "https://www.bbc.com/portuguese/topicos/economia/index.xml",
    atualizar_bbc,
    parser_bbc,
)
