import pytest

from src.dispatcher import get_scraper_class

# Lista de todos os seus scrapers atuais
SCRAPERS_TO_TEST = [
    ("CBX", "comunicados"),
    ("CBX", "noticias"),
    ("CBX", "jogadores"),
    ("CBX", "torneios"),
    ("FIDE", "torneios"),
]


@pytest.mark.parametrize("site, target", SCRAPERS_TO_TEST)
def test_all_classes_instantiation(site, target):
    """Garante que todas as classes podem ser instanciadas e têm o método run."""
    klass = get_scraper_class(site, target)
    assert klass is not None, f"Classe {site}/{target} não encontrada ou erro de import"

    # Instancia com argumentos mínimos para não disparar o erro do __init__
    instance = klass(
        data_args={
            "year": "2024",
            "month": "1",
            "state": "SP",
            "country": "BRA",
            "period": "2024-01",
        }
    )
    assert hasattr(instance, "run")
