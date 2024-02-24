from datetime import datetime

import httpx
from bs4 import Tag

from .modelos import Site


def parser_carta_cap(self: Site, noticia_tag: Tag) -> dict:
    noticia = {"f": self.site}
    noticia["mat"] = noticia_tag.find("title").text.strip()
    noticia["url"] = noticia_tag.find("link").text
    noticia["dt"] = datetime.strptime(
        noticia_tag.find("pubDate").text, "%a, %d %b %Y %H:%M:%S %z"
    )
    noticia_media = noticia_tag.find("enclosure")
    noticia["img"] = noticia_media.get("url") if noticia_media is not None else None
    return noticia


def atualizar_carta_cap(self: Site):
    s = httpx.Client()
    s.headers.update({"User-Agent": self.agent})
    pag_inicial = self._construir_soup(s, self.url, "xml")
    noticias = pag_inicial.find_all("item")
    noticias_atualizadas = [self.parser_noticias(x) for x in noticias]
    noticias_atualizadas = filter(bool, noticias_atualizadas)

    self._gravar_noticias(noticias_atualizadas)


carta_capital = Site(
    "Carta Capital",
    "https://www.cartacapital.com.br/feed/",
    atualizar_carta_cap,
    parser_carta_cap,
)
