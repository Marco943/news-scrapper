from sites.bbc import bbc
from sites.carta_capital import carta_capital
from sites.cnn import cnn
from sites.exame import exame
from sites.fsp import fsp
from sites.g1 import g1econ
from sites.modelos import Site
from sites.valor_economico import v_econ

sites: list[Site] = [bbc, fsp, v_econ, g1econ, cnn, carta_capital, exame]

for site in sites:
    site.atualizar_noticias()
