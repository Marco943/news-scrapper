import asyncio
import re
import time
from cProfile import Profile
from dataclasses import dataclass
from pathlib import Path
from pstats import SortKey, Stats

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
    schema = {
        "f": pl.Utf8,
        "mat": pl.Utf8,
        "url": pl.Utf8,
        "img": pl.Utf8,
        "dt": pl.Datetime,
    }

    def __post_init__(self):
        self._caminho = Path().joinpath("noticias").joinpath(f"{self.site}.json")
        if not self._caminho.parent.exists():
            Path.mkdir(self._caminho.parent)
        self._ler_noticias()

    async def _construir_soup(self, s: httpx.AsyncClient, url: str) -> BeautifulSoup:
        page = await s.get(url)
        resposta = page.text
        soup = BeautifulSoup(resposta, "lxml")
        return soup

    def _gravar_noticias(self, noticias_atualizadas: list = None) -> None:
        if noticias_atualizadas is not None:
            df = pl.from_dicts(
                noticias_atualizadas,
                schema=self.schema,
            ).filter(~pl.col("mat").is_in(self.noticias["mat"].unique()))
            self.noticias = pl.concat([self.noticias, df])

        self.noticias.write_json(self._caminho, pretty=False, row_oriented=True)

    def _ler_noticias(self) -> pl.DataFrame:
        if not self._caminho.exists():
            self.noticias = pl.DataFrame(schema=self.schema)
        else:
            self.noticias = pl.read_json(
                self._caminho, schema_overrides={"dt": pl.Datetime}
            )
        return self.noticias

    async def atualizar_noticias(self):
        pass


@dataclass
class CnnEconomia(Site):
    site: str = "cnn"
    url: str = "https://www.cnnbrasil.com.br/economia/"

    async def parsear_noticia(self, s, url_materia: str):
        soup_materia = await self._construir_soup(s, url_materia)
        materia = soup_materia.find("h1", class_="post__title").text.strip()
        picture = soup_materia.find("picture", class_="img__destaque")
        if picture is not None:
            img = picture.img.get("src")
        else:
            img = None
        data_post = soup_materia.find("span", class_="post__data").text.strip()
        re_data = re.search("\d{2}\/\d{2}\/\d{4} às \d{1,2}\:\d{2}$", data_post)
        datahora_publi = pendulum.from_format(
            re_data.group(0), "DD/MM/YYYY [às] HH:mm", tz="America/Sao_Paulo"
        )

        return {
            "f": self.site,
            "mat": materia,
            "url": url_materia,
            "img": img,
            "dt": datahora_publi,
        }

    async def atualizar_noticias(self):
        async with httpx.AsyncClient() as s:
            s.headers.update({"User-Agent": UserAgent().random})
            soup = await self._construir_soup(s, self.url)
            noticias = soup.find_all("a", href=re.compile("\.com\.br\/economia\/.+"))
            noticias = [
                noticia.get("href")
                for noticia in noticias
                if noticia.get("href") not in self.noticias.get_column("url")
                and "ultimas-noticias" not in noticia.get("href")
            ]

            noticias_atualizadas = await asyncio.gather(
                *[self.parsear_noticia(s, noticia) for noticia in noticias]
            )

            noticias_atualizadas = [
                noticia for noticia in noticias_atualizadas if noticia is not None
            ]

        self._gravar_noticias(noticias_atualizadas)


self = CnnEconomia()


async def main():
    while True:
        await self.atualizar_noticias()
        print("Atualizado", pendulum.now())
        await asyncio.sleep(60)


asyncio.run(main())
