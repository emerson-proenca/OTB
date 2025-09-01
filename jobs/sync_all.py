# scripts/sync_all.py
import logging
import sys
from datetime import datetime, timezone
import importlib

# nomes dos jobs (módulo : função)
JOBS = {
    "tournaments": ("jobs.sync_tournaments", "sync_cbxtournaments"),
    "players": ("jobs.sync_players", "sync_cbxplayers"),
    "news": ("jobs.sync_news", "sync_cbxnews"),
    "announcements": ("jobs.sync_announcements", "sync_cbxannouncements"),
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("sync_all")

def run_job(key, **kwargs):
    mod_name, fn_name = JOBS[key]
    logger.info(f"Running job {key} -> {mod_name}.{fn_name} with args {kwargs}")
    try:
        mod = importlib.import_module(mod_name)
        fn = getattr(mod, fn_name)
    except Exception as e:
        logger.exception(f"Failed to import job {key}")
        return {"job": key, "status": "import-failed", "error": str(e)}

    try:
        # call function with kwargs if it accepts them (most accept --limit/--state)
        fn_kwargs = {}
        # best-effort: pass known args if in kwargs
        if "state" in kwargs:
            fn_kwargs["state"] = kwargs["state"]
        if "max_pages" in kwargs:
            fn_kwargs["max_pages"] = kwargs["max_pages"]
        if "limit" in kwargs:
            fn_kwargs["limit"] = kwargs["limit"]

        started = datetime.now(timezone.utc)
        fn(**fn_kwargs)
        finished = datetime.now(timezone.utc)
        return {"job": key, "status": "success", "started": started.isoformat(), "finished": finished.isoformat()}
    except Exception as e:
        logger.exception(f"Job {key} failed")
        return {"job": key, "status": "failed", "error": str(e)}

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run all sync jobs (one-off or cron)")
    parser.add_argument("--jobs", nargs="*", choices=list(JOBS.keys()), help="Which jobs to run; default = all")
    parser.add_argument("--state", default="SP", help="State for players job (default SP)")
    parser.add_argument("--max-pages", type=int, default=None, help="Max pages to scrape per job")
    parser.add_argument("--limit", type=int, default=None, help="Limit items per job (for quick tests)")
    args = parser.parse_args()

    to_run = args.jobs if args.jobs else list(JOBS.keys())
    results = []
    for job_key in to_run:
        res = run_job(job_key, state=args.state, max_pages=args.max_pages, limit=args.limit)
        results.append(res)

    logger.info("Sync summary:")
    for r in results:
        logger.info(r)

    # exit with non-zero if any failed
    for r in results:
        if r.get("status") != "success":
            sys.exit(2)

if __name__ == "__main__":
    main()
