# tests/test_cbx_logic.py
import pytest

from scrapers.cbx.jogadores import ScraperCbxJogadores
from scrapers.cbx.torneios import ScraperCbxTorneios


def test_cbx_torneios_missing_args():
    # Deve dar erro se year/month faltarem
    scraper = ScraperCbxTorneios(data_args={}, global_args={"max_pages": 1})
    with pytest.raises(ValueError, match="year' e 'month' são obrigatórios"):
        scraper.run()


def test_cbx_jogadores_validation():
    # Deve dar erro se state faltar
    scraper = ScraperCbxJogadores(data_args={})
    with pytest.raises(ValueError, match="state' é obrigatório"):
        scraper.run()
