import asyncio
import importlib
import inspect
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
    """Processa o JSON e executa os scrapers (Suporta Sync e Async)."""
    global_args = {k: v for k, v in config.items() if not isinstance(v, dict)}

    for site_name, site_content in config.items():
        if not isinstance(site_content, dict):
            continue

        site_args = {k: v for k, v in site_content.items() if not isinstance(v, dict)}

        for data_name, data_args in site_content.items():
            if not isinstance(data_args, dict):
                continue

            ScraperClass = get_scraper_class(site_name, data_name)

            if ScraperClass:
                try:
                    scraper = ScraperClass(
                        data_args=data_args,
                        site_args=site_args,
                        global_args=global_args,
                    )

                    # VERIFICAÇÃO CRUCIAL: Se o método run for assíncrono, usa o loop
                    if inspect.iscoroutinefunction(scraper.run):
                        logger.info(f"Executando {site_name}/{data_name} em modo ASYNC")
                        try:
                            # Tenta pegar o loop atual ou cria um novo
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                # Se estivermos dentro do FastAPI, criamos uma task
                                asyncio.create_task(scraper.run())
                            else:
                                loop.run_until_complete(scraper.run())
                        except RuntimeError:
                            # Caso não haja loop (rodando via terminal puro)
                            asyncio.run(scraper.run())
                    else:
                        # Execução Síncrona Normal
                        logger.info(f"Executando {site_name}/{data_name} em modo SYNC")
                        scraper.run()

                except Exception as e:
                    logger.critical(f"Erro na execução de {site_name}/{data_name}: {e}")
            else:
                logger.warning(f"Alvo não encontrado: {site_name}/{data_name}")


if __name__ == "__main__":
    # Teste com o payload de 3 camadas
    payload = {}
    run_scrapers(payload)
