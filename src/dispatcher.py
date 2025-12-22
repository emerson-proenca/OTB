import importlib
import logging
import sys


def setup_dispatcher_logging():
    """Configura o log no mesmo padrão da Classe Base."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - [%(name)s] - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    return logging.getLogger("Dispatcher")


logger = setup_dispatcher_logging()


def get_scraper_class(site_name, data_name):
    """Busca dinamicamente a classe do scraper."""
    try:
        module_path = f"scrapers.{site_name.lower()}.{data_name.lower()}"
        module = importlib.import_module(module_path)

        # Nome esperado: ScraperCbxComunicados
        class_name = f"Scraper{site_name.capitalize()}{data_name.capitalize()}"

        return getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        logger.error(f"Erro ao carregar scraper {site_name}/{data_name}: {e}")
        return None


def run_scrapers(config):
    """Processa o JSON e executa os scrapers."""
    # 1. Argumentos Globais
    global_args = {k: v for k, v in config.items() if not isinstance(v, dict)}

    # 2. Itera sobre Sites
    for site_name, site_content in config.items():
        if not isinstance(site_content, dict):
            continue

        # Argumentos do Site
        site_args = {k: v for k, v in site_content.items() if not isinstance(v, dict)}

        # 3. Itera sobre Dados
        for data_name, data_args in site_content.items():
            if not isinstance(data_args, dict):
                continue

            ScraperClass = get_scraper_class(site_name, data_name)

            if ScraperClass:
                try:
                    # Instancia e Roda
                    scraper = ScraperClass(
                        data_args=data_args,
                        site_args=site_args,
                        global_args=global_args,
                    )
                    scraper.run()
                except Exception as e:
                    logger.critical(f"Erro na execução de {site_name}/{data_name}: {e}")
            else:
                logger.warning(f"Alvo não encontrado: {site_name}/{data_name}")


if __name__ == "__main__":
    # Teste com o payload de 3 camadas
    payload = {"max_pages": 2, "CBX": {"comunicados": {}}}
    run_scrapers(payload)
