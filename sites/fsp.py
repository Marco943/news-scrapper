import re
from datetime import datetime

import httpx
from bs4 import Tag
from modelos import Site


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
    s.headers.update({"User-Agent": self.agent})
    pag_inicial = self._construir_soup(s, self.url)
    noticias = pag_inicial.find_all("item")
    noticias_atualizadas = [self.parser_noticias(x) for x in noticias]
    noticias_atualizadas = filter(bool, noticias_atualizadas)

    self._gravar_noticias(noticias_atualizadas)


fsp = Site(
    "folha-sp-mercado",
    "https://feeds.folha.uol.com.br/mercado/rss091.xml",
    atualizar_fsp,
    parser_fsp,
)
