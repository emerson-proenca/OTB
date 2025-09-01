# jobs/sync_all.py
import logging
import sys
import subprocess
from datetime import datetime, timezone
from typing import Optional, Any

# Use sys.executable to ensure we call the same Python interpreter (important for venv)
PYTHON_BIN = sys.executable

# Mapping job_key -> list of args (base)
JOB_BASE_ARGS = {
    "tournaments": [PYTHON_BIN, "-m", "jobs.sync_tournaments"],
    "players": [PYTHON_BIN, "-m", "jobs.sync_players"],
    "news": [PYTHON_BIN, "-m", "jobs.sync_news"],
    "announcements": [PYTHON_BIN, "-m", "jobs.sync_announcements"],
}

# default timeout per job in seconds (e.g., 30 minutes)
DEFAULT_TIMEOUT_SECONDS = 30 * 60

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("sync_all")


def run_subprocess(args: list[str], timeout: int) -> dict[str, Any]:
    logger.info(f"Executing: {' '.join(args)} (timeout={timeout}s)")
    try:
        completed = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        logger.info(f"Exit {completed.returncode} - stdout len={len(completed.stdout)} stderr len={len(completed.stderr)}")
        if completed.stdout:
            logger.debug("stdout:\n" + completed.stdout)
        if completed.stderr:
            logger.debug("stderr:\n" + completed.stderr)
        return {"status": "success" if completed.returncode == 0 else "failed",
                "returncode": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr}
    except subprocess.TimeoutExpired as e:
        logger.exception("Job timed out")
        return {"status": "timeout", "error": str(e)}
    except Exception as e:
        logger.exception("Subprocess failed")
        return {"status": "error", "error": str(e)}


def build_args(job_key: str, *, state: str = "SP", max_pages: Optional[int] = None, limit: Optional[int] = None) -> list[str]:
    base = JOB_BASE_ARGS[job_key].copy()
    # add arguments depending on job
    if job_key == "tournaments":
        if limit is not None:
            base += ["--limit", str(limit)]
    elif job_key == "players":
        base += ["--state", str(state)]
        if max_pages is not None:
            base += ["--pages", str(max_pages)]
        if limit is not None:
            base += ["--limit", str(limit)]
    elif job_key == "news":
        if max_pages is not None:
            base += ["--max-pages", str(max_pages)]
        if limit is not None:
            base += ["--limit", str(limit)]
    elif job_key == "announcements":
        if max_pages is not None:
            base += ["--max-pages", str(max_pages)]
        if limit is not None:
            base += ["--limit", str(limit)]
    return base


def run_job(job_key: str, *, state: str = "SP", max_pages: Optional[int] = None, limit: Optional[int] = None, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> dict[str, Any]:
    if job_key not in JOB_BASE_ARGS:
        return {"job": job_key, "status": "unknown-job"}

    args = build_args(job_key, state=state, max_pages=max_pages, limit=limit)
    started = datetime.now(timezone.utc).isoformat()
    result = run_subprocess(args, timeout=timeout)
    finished = datetime.now(timezone.utc).isoformat()
    return {
        "job": job_key,
        "started": started,
        "finished": finished,
        **result
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run sync jobs as subprocesses")
    parser.add_argument("--jobs", nargs="*", choices=list(JOB_BASE_ARGS.keys()), help="Which jobs to run; default = all")
    parser.add_argument("--state", default="SP", help="State for players job")
    parser.add_argument("--max-pages", type=int, default=None, help="Max pages to scrape per job")
    parser.add_argument("--limit", type=int, default=None, help="Limit items per job")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS, help="Timeout per job in seconds")
    args = parser.parse_args()

    to_run = args.jobs if args.jobs else list(JOB_BASE_ARGS.keys())
    results = []
    for job_key in to_run:
        logger.info(f"Starting job {job_key}")
        res = run_job(job_key, state=args.state, max_pages=args.max_pages, limit=args.limit, timeout=args.timeout)
        results.append(res)
        logger.info(f"Finished job {job_key}: status={res.get('status')}")

    logger.info("Sync summary:")
    for r in results:
        logger.info(r)

    # non-zero exit if any job failed/timeout/error
    for r in results:
        if r.get("status") not in ("success",):
            sys.exit(2)


if __name__ == "__main__":
    main()
