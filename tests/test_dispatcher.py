from src.dispatcher import get_scraper_class, run_scrapers


def test_get_scraper_class_success():
    # Testa se o importlib funciona para um scraper real
    klass = get_scraper_class("CBX", "comunicados")
    assert klass is not None
    assert klass.__name__ == "ScraperCbxComunicados"


def test_get_scraper_class_invalid():
    # Testa comportamento com site que não existe
    klass = get_scraper_class("SITE_INEXISTENTE", "dado")
    assert klass is None


def test_dispatcher_argument_hierarchy():
    # Simula um payload para verificar se o dispatcher não quebra no loop
    payload = {"max_pages": 1, "CBX": {"comunicados": {}}}
    # Apenas verificamos se não levanta exceção ao processar
    run_scrapers(payload)
