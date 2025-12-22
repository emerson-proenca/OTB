import logging

from fastapi import BackgroundTasks, FastAPI, HTTPException

from dispatcher import run_scrapers

# O logger seguirá o padrão que definimos no Dispatcher
logger = logging.getLogger("API")

app = FastAPI(title="Over-The-Board Scraper")


@app.get("/healthz")
def health_check():
    """Rota para o Render verificar se o serviço está online."""
    return {"status": "alive", "message": "Over-The-Board Scraper is running"}


@app.post("/scrape")
async def trigger_scraping(payload: dict, background_tasks: BackgroundTasks):
    """
    Recebe o JSON de 3 camadas e inicia os scrapers em segundo plano.
    """
    if not payload:
        raise HTTPException(status_code=400, detail="Payload vazio")

    logger.info(f"Requisição recebida para os sites: {list(payload.keys())}")

    # Adiciona a tarefa para rodar sem travar a resposta HTTP
    background_tasks.add_task(run_scrapers, payload)

    return {
        "message": "Processamento iniciado em segundo plano",
        "sites_afetados": [k for k in payload.keys() if isinstance(payload[k], dict)],
    }


if __name__ == "__main__":
    import uvicorn

    # Roda localmente para teste: python main.py
    uvicorn.run(app, host="0.0.0.0", port=8000)
