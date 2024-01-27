from sites_sync import BbcEconomia, CnnEconomia, FolhaSPMercado, G1Econ, ValorEcon

sites = [CnnEconomia(), BbcEconomia(), FolhaSPMercado(), ValorEcon(), G1Econ()]
for site in sites:
    site.atualizar_noticias()
