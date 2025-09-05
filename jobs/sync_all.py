# jobs/sync_all.py
import logging
import sys
import subprocess
from datetime import datetime, timezone
from typing import Optional, Any, List

# Use sys.executable to ensure we call the same Python interpreter (important for venv)
PYTHON_BIN = sys.executable

# Mapping job_key -> list of args (base)
JOB_BASE_ARGS = {
    "news": [PYTHON_BIN, "-m", "jobs.sync_news"],
    "announcements": [PYTHON_BIN, "-m", "jobs.sync_announcements"],
    "tournaments": [PYTHON_BIN, "-m", "jobs.sync_tournaments"],
    "players": [PYTHON_BIN, "-m", "jobs.sync_players"],
}

# default timeout per job in seconds (e.g., 30 minutes)
DEFAULT_TIMEOUT_SECONDS = 30 * 60

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("sync_all")



def run_subprocess(args: List[str], timeout: int) -> dict[str, Any]:
    """
    Executa o subprocess com cwd ajustado para o root do projeto e com
    variáveis de ambiente herdadas (garante que caminhos relativos
    e o ambiente virtual sejam os mesmos).
    """
    # calcula root do repositório (dois níveis acima de jobs/sync_all.py)
    repo_root = Path(__file__).resolve().parent.parent
    cwd = str(repo_root)

    logger.info(f"Executing: {' '.join(args)} (timeout={timeout}s) cwd={cwd}")
    try:
        completed = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            env=os.environ.copy()  # herdamos o ambiente atual (venv, DB env vars, etc.)
        )
        logger.info(f"Exit {completed.returncode} - stdout len={len(completed.stdout)} stderr len={len(completed.stderr)}")
        if completed.stdout:
            logger.debug("stdout:\n" + completed.stdout)
        if completed.stderr:
            logger.debug("stderr:\n" + completed.stderr)
        return {
            "status": "success" if completed.returncode == 0 else "failed",
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr
        }
    except subprocess.TimeoutExpired as e:
        logger.exception("Job timed out")
        return {"status": "timeout", "error": str(e)}
    except Exception as e:
        logger.exception("Subprocess failed")
        return {"status": "error", "error": str(e)}



def build_args(job_key: str,
               *,
               state: str = "SP",
               max_pages: Optional[int] = None,
               limit: Optional[int] = None,
               full: Optional[bool] = None,
               start_year: Optional[int] = None,
               end_year: Optional[int] = None,
               year: Optional[int] = None,
               month: Optional[int] = None) -> List[str]:
    """
    Build argument list to call a job subprocess.
    Accepts optional year/month used by tournaments in daily mode.
    """
    base = JOB_BASE_ARGS[job_key].copy()

    # tournaments CLI params
    if job_key == "tournaments":
        if limit is not None:
            base += ["--limit", str(limit)]
        # year/month for daily
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

    # players CLI params
    elif job_key == "players":
        base += ["--state", str(state)]
        if max_pages is not None:
            base += ["--pages", str(max_pages)]
        if limit is not None:
            base += ["--limit", str(limit)]
        if full:
            base += ["--full"]

    # news CLI params
    elif job_key == "news":
        if max_pages is not None:
            base += ["--max-pages", str(max_pages)]
        if limit is not None:
            base += ["--limit", str(limit)]
        if full:
            base += ["--full"]

    # announcements CLI params
    elif job_key == "announcements":
        if max_pages is not None:
            base += ["--max-pages", str(max_pages)]
        if limit is not None:
            base += ["--limit", str(limit)]
        if full:
            base += ["--full"]

    return base


def run_job(job_key: str,
            *,
            state: str = "SP",
            max_pages: Optional[int] = None,
            limit: Optional[int] = None,
            full: Optional[bool] = None,
            start_year: Optional[int] = None,
            end_year: Optional[int] = None,
            year: Optional[int] = None,
            month: Optional[int] = None,
            timeout: int = DEFAULT_TIMEOUT_SECONDS) -> dict[str, Any]:
    if job_key not in JOB_BASE_ARGS:
        return {"job": job_key, "status": "unknown-job"}

    args = build_args(job_key,
                      state=state,
                      max_pages=max_pages,
                      limit=limit,
                      full=full,
                      start_year=start_year,
                      end_year=end_year,
                      year=year,
                      month=month)
    started = datetime.now(timezone.utc).isoformat()
    result = run_subprocess(args, timeout=timeout)
    finished = datetime.now(timezone.utc).isoformat()
    return {
        "job": job_key,
        "started": started,
        "finished": finished,
        **result
    }


def normalize_jobs_arg(raw_jobs: Optional[List[str]]) -> List[str]:
    """
    Normalize --jobs input to a list of job keys.
    Accepts either: --jobs tournaments players
    or: --jobs tournaments,players (single element with commas)
    """
    if not raw_jobs:
        return list(JOB_BASE_ARGS.keys())
    # flatten and split comma-separated tokens
    out: List[str] = []
    for token in raw_jobs:
        if not token:
            continue
        parts = [p.strip() for p in token.split(",") if p.strip()]
        out.extend(parts)
    # validate
    validated = []
    for j in out:
        if j in JOB_BASE_ARGS:
            validated.append(j)
        else:
            logger.warning(f"Unknown job '{j}' ignored.")
    return validated if validated else list(JOB_BASE_ARGS.keys())


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run sync jobs as subprocesses (supports --full and --daily)")
    parser.add_argument("--jobs", nargs="*", help="Which jobs to run; default = all. Accepts space-separated or comma-separated (e.g. --jobs tournaments,players).")
    # Make state default None so we can detect whether user explicitly set it.
    parser.add_argument("--state", default=None, help="State for players job (e.g. SP). If not provided and --full is used, defaults to ALL. If not provided and neither --full nor --daily, defaults to SP.")
    parser.add_argument("--max-pages", type=int, default=None, help="Max pages to scrape per job")
    parser.add_argument("--limit", type=int, default=None, help="Limit items per job")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS, help="Timeout per job in seconds")
    parser.add_argument("--full", action="store_true", help="Run full import (when supported by the job)")
    parser.add_argument("--daily", action="store_true", help="Run daily incremental mode (uses current year/month for tournaments). Mutually exclusive with --full.")
    parser.add_argument("--start-year", type=int, default=None, help="Start year for full import (passed to tournaments job)")
    parser.add_argument("--end-year", type=int, default=None, help="End year for full import (passed to tournaments job)")
    args = parser.parse_args()

    # validate mutual exclusivity
    if args.full and args.daily:
        logger.error("Options --full and --daily are mutually exclusive. Choose one.")
        sys.exit(2)

    to_run = normalize_jobs_arg(args.jobs)
    results = []

    # compute year/month for daily mode (server local time)
    daily_year = None
    daily_month = None
    if args.daily:
        now = datetime.now()  # server local time; adjust if you require a timezone
        daily_year = now.year
        daily_month = now.month

    # Determine the effective state to pass to child jobs:
    # - If user explicitly provided --state, respect it.
    # - If user did NOT provide --state:
    #     * in --full mode -> default to "ALL" (full import should cover all states)
    #     * in --daily mode -> default to "ALL" (daily should check all states)
    #     * otherwise -> default to "SP" (keep previous default behavior)
    if args.state is not None:
        state_for_run = args.state
    else:
        if args.full or args.daily:
            state_for_run = "ALL"
        else:
            state_for_run = "SP"

    for job_key in to_run:
        logger.info(f"Starting job {job_key} (effective state={state_for_run})")

        # compute job-specific params for daily vs normal
        if args.daily:
            # daily mode: pass year/month only to tournaments; players gets state_for_run (ALL by default)
            if job_key == "tournaments":
                res = run_job(job_key,
                              state=state_for_run,
                              max_pages=args.max_pages,
                              limit=args.limit,
                              full=False,
                              start_year=args.start_year,
                              end_year=args.end_year,
                              year=daily_year,
                              month=daily_month,
                              timeout=args.timeout)
            elif job_key == "players":
                res = run_job(job_key,
                              state=state_for_run,
                              max_pages=args.max_pages,
                              limit=args.limit,
                              full=False,
                              timeout=args.timeout)
            else:
                # news / announcements incremental for daily
                res = run_job(job_key,
                              state=state_for_run,
                              max_pages=args.max_pages,
                              limit=args.limit,
                              full=False,
                              timeout=args.timeout)
        else:
            # normal mode: pass --full if requested; use state_for_run for consistency
            res = run_job(job_key,
                          state=state_for_run,
                          max_pages=args.max_pages,
                          limit=args.limit,
                          full=args.full,
                          start_year=args.start_year,
                          end_year=args.end_year,
                          timeout=args.timeout)

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