from datetime import datetime

import httpx
from bs4 import Tag
from modelos import Site


def parser_v_econ(self: Site, noticia_tag: Tag) -> dict:
    noticia = {"f": self.site}
    noticia["mat"] = noticia_tag.find("title").text
    noticia["url"] = noticia_tag.find("link").text
    noticia["dt"] = datetime.strptime(
        noticia_tag.find("pubDate").text, "%a, %d %b %Y %H:%M:%S %z"
    )
    noticia["img"] = noticia_tag.find("content").get("url")
    return noticia


def atualizar_v_econ(self: Site):
    s = httpx.Client()
    s.headers.update({"User-Agent": self.agent})
    pag_inicial = self._construir_soup(s, self.url, "xml")
    noticias = pag_inicial.find_all("item")
    noticias_atualizadas = [self.parser_noticias(x) for x in noticias]
    noticias_atualizadas = filter(bool, noticias_atualizadas)

    self._gravar_noticias(noticias_atualizadas)


v_econ = Site(
    "valor-economico",
    "https://pox.globo.com/rss/valor",
    atualizar_v_econ,
    parser_v_econ,
)
