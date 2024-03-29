import asyncio
import re
from datetime import datetime

import httpx

from .modelos import SiteAsync


async def parser_cnn_econ(self: SiteAsync, s: httpx.Client, noticia_url: str) -> dict:
    noticia = {"f": self.site, "url": noticia_url}
    soup_materia = await self._construir_soup(s, noticia_url)

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


def atualizar_cnn_econ(self: SiteAsync):
    async def request_noticias():
        async with httpx.AsyncClient() as s:
            s.headers.update({"User-Agent": self.agent})
            pag_inicial = await self._construir_soup(s, self.url)
            noticias = pag_inicial.find_all(
                "a", href=re.compile(r"\.com\.br\/economia\/.+")
            )
            noticias_url = [noticia.get("href") for noticia in noticias]

            tasks = [self.parser_noticias(s, url) for url in noticias_url]
            noticias_atualizadas = await asyncio.gather(*tasks)

        return noticias_atualizadas

    noticias_atualizadas = asyncio.run(request_noticias())

    noticias_atualizadas = filter(bool, noticias_atualizadas)

    self._gravar_noticias(noticias_atualizadas)


cnn = SiteAsync(
    "CNN Brasil",
    "https://www.cnnbrasil.com.br/economia/",
    atualizar_cnn_econ,
    parser_cnn_econ,
)
