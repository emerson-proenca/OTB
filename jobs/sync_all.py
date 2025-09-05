# jobs/sync_all.py
"""
Lightweight orchestrator for sync jobs.

Features:
- Run any subset of: tournaments, players, news, announcements
- --daily: run incremental for current month/year (tournaments gets --year/--month; players default state ALL)
- --full: pass --full to child jobs and perform table cleanup before each job
- --clean: optional, perform table cleanup before each job (even if not --full)
- --limit: single global limit passed to children
- --pages: pages passed to players job
- --start-year / --end-year: passed to tournaments (useful with --full)
- Streams child logs in real time
- Uses repo root as cwd for subprocesses and inherits environment
"""
from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from database.session import SessionLocal
from database import models

# Which jobs are supported
JOB_KEYS = ["tournaments", "players", "news", "announcements"]

PYTHON_BIN = sys.executable
DEFAULT_TIMEOUT = 1800  # 30 minutes

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("sync_all")


def build_child_args(job: str,
                     *,
                     state: str,
                     limit: Optional[int],
                     pages: Optional[int],
                     full: bool,
                     start_year: Optional[int],
                     end_year: Optional[int],
                     year: Optional[int],
                     month: Optional[int]) -> List[str]:
    base = [PYTHON_BIN, "-m", f"jobs.sync_{job}"]

    if job == "tournaments":
        if limit is not None:
            base += ["--limit", str(limit)]
        if year is not None:
            base += ["--year", str(year)]
        if month is not None:
            base += ["--month", str(month)]
        if full:
            base += ["--full"]
            if start_year is not None:
                base += ["--start-year", str(start_year)]
            if end_year is not None:
                base += ["--end-year", str(end_year)]

    elif job == "players":
        base += ["--state", str(state)]
        if pages is not None:
            base += ["--pages", str(pages)]
        if limit is not None:
            base += ["--limit", str(limit)]
        if full:
            base += ["--full"]

    elif job in ("news", "announcements"):
        if limit is not None:
            base += ["--limit", str(limit)]
        # these jobs support --full as well
        if full:
            base += ["--full"]

    return base


def wipe_table_for_job(job: str) -> None:
    """
    Delete all rows in the table related to the job.
    Logs an INFO line in the pattern you requested.
    """
    mapping = {
        "tournaments": models.Tournament,
        "players": models.CBXPlayer,
        "news": models.CBXNews,
        "announcements": models.CBXAnnouncement,
    }
    model = mapping.get(job)
    if not model:
        logger.warning(f"No model mapping for job {job}; skip wipe.")
        return

    db = SessionLocal()
    try:
        cnt = db.query(model).delete(synchronize_session=False)
        db.commit()
        logger.info(f"sync_all FULL mode enabled for sync_{job}: cleaning {model.__name__} table before full import.")
        logger.info(f"sync_{job} Deleted {cnt} existing {model.__name__} (cleanup before import).")
    except Exception:
        db.rollback()
        logger.exception(f"Failed to wipe table for job {job}")
    finally:
        db.close()


def stream_subprocess(args: List[str], cwd: str, timeout: int) -> int:
    """
    Run subprocess streaming stdout/stderr in real-time.
    Returns exit code (or non-zero if killed by timeout).
    """
    logger.info(f"Executing: {' '.join(args)} (timeout={timeout}s) cwd={cwd}")
    # Start process
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, cwd=cwd, env=os.environ.copy())

    start = time.time()
    stdout_buf = []
    stderr_buf = []

    # Read until process ends or timeout
    try:
        while True:
            # read stdout
            if proc.stdout:
                line = proc.stdout.readline()
                if line:
                    stdout_buf.append(line)
                    # forward to parent's stdout (preserve child log format)
                    print(line, end="", flush=True)

            # read stderr
            if proc.stderr:
                eline = proc.stderr.readline()
                if eline:
                    stderr_buf.append(eline)
                    print(eline, end="", flush=True)

            # check if process finished
            if proc.poll() is not None:
                # drain remaining
                if proc.stdout:
                    for line in proc.stdout:
                        stdout_buf.append(line)
                        print(line, end="", flush=True)
                if proc.stderr:
                    for line in proc.stderr:
                        stderr_buf.append(line)
                        print(line, end="", flush=True)
                break

            # timeout check
            if timeout is not None and (time.time() - start) > timeout:
                proc.kill()
                logger.error("Subprocess timeout expired; killed.")
                return 124  # common timeout exit code
            # small sleep to avoid busy loop
            time.sleep(0.01)

    except Exception:
        proc.kill()
        logger.exception("Exception while streaming subprocess - killed it.")
        return 1

    return proc.returncode if proc.returncode is not None else 0


def main():
    parser = argparse.ArgumentParser(description="Run OTB sync jobs together")
    parser.add_argument("--jobs", nargs="*", help="Jobs to run (space-separated). Options: tournaments players news announcements. Default = all.")
    parser.add_argument("--state", default=None, help="State for players job (e.g. SP). If not provided and --full or --daily, defaults to ALL; otherwise defaults to SP.")
    parser.add_argument("--limit", type=int, default=None, help="Global limit per job (if supported).")
    parser.add_argument("--pages", type=int, default=None, help="Pages (passed to players as --pages).")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Timeout per job in seconds (default 1800).")
    parser.add_argument("--full", action="store_true", help="Full import (pass --full to children and wipe per-job tables before run).")
    parser.add_argument("--daily", action="store_true", help="Daily incremental import (uses current month/year for tournaments).")
    parser.add_argument("--clean", action="store_true", help="Wipe target table before running each job (even if not --full).")
    parser.add_argument("--start-year", type=int, default=None, help="Start year for tournaments full import.")
    parser.add_argument("--end-year", type=int, default=None, help="End year for tournaments full import.")
    args = parser.parse_args()

    # validate
    if args.full and args.daily:
        logger.error("--full and --daily are mutually exclusive. Choose one.")
        sys.exit(2)

    # normalize jobs list
    if args.jobs:
        jobs = [j.strip() for j in args.jobs if j.strip() in JOB_KEYS]
        if not jobs:
            jobs = JOB_KEYS.copy()
    else:
        jobs = JOB_KEYS.copy()

    # effective state decision
    if args.state is not None:
        state_for_run = args.state
    else:
        if args.full or args.daily:
            state_for_run = "ALL"
        else:
            state_for_run = "SP"

    # daily year/month
    daily_year = None
    daily_month = None
    if args.daily:
        now = datetime.now()
        daily_year = now.year
        daily_month = now.month

    repo_root = str(Path(__file__).resolve().parent.parent)

    overall_failed = False
    results = []

    for job in jobs:
        logger.info(f"Starting job {job} (effective state={state_for_run})")

        # wipe table if requested (either --full or explicit --clean)
        if args.full or args.clean:
            try:
                wipe_table_for_job(job)
            except Exception:
                logger.exception("Wipe step failed for job %s", job)

        # build args for child
        child_args = build_child_args(
            job,
            state=state_for_run,
            limit=args.limit,
            pages=args.pages,
            full=args.full,
            start_year=args.start_year,
            end_year=args.end_year,
            year=daily_year if args.daily else None,
            month=daily_month if args.daily else None,
        )

        # stream subprocess logs
        rc = stream_subprocess(child_args, cwd=repo_root, timeout=args.timeout)
        status = "success" if rc == 0 else ("timeout" if rc == 124 else "failed")
        results.append({"job": job, "rc": rc, "status": status})
        logger.info(f"Finished job {job}: status={status}")

        if status != "success":
            overall_failed = True

    # summary
    logger.info("Sync summary:")
    for r in results:
        logger.info(r)

    if overall_failed:
        sys.exit(2)


if __name__ == "__main__":
    main()
