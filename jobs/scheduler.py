# jobs/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from jobs.sync_tournaments import sync_cbxtournaments
import time
from core.logger_config import logger


def start_scheduler():
    scheduler = BackgroundScheduler()
    # roda todo dia (24h), aqui definido por segundos apenas para exemplo:
    scheduler.add_job(sync_cbxtournaments, "interval", hours=24, id="sync_cbx")
    scheduler.start()
    logger.info(f"Scheduler started")
    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

if __name__ == "__main__":
    start_scheduler()
