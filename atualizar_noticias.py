from sites.bbc import bbc
from sites.cnn import cnn
from sites.fsp import fsp
from sites.g1 import g1econ
from sites.modelos import Site
from sites.valor_economico import v_econ

sites: list[Site] = [bbc, fsp, v_econ, g1econ, cnn]

for site in sites:
    site.atualizar_noticias()
