# jobs/sync_tournaments.py
import logging
import os
from scrapers.cbx.cbx_tournaments import fetch_tournaments_raw
from database.session import SessionLocal
from database.models import Tournament, SyncJob
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone
import requests

logger = logging.getLogger("sync_tournaments")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def upsert_tournament(db, item):
    """
    Atualiza um objeto Tournament ORM (passado pelo caller) ou cria um novo.
    A função espera que caller já tenha determinado 'existing' (ou não).
    Retorna a instância (nova ou atualizada).
    """
    # NOTE: nesta implementação nós tratamos conversões simples; o caller faz commit.
    if isinstance(item, Tournament):
        return item  # nothing to do if caller passes an ORM object (not used here)

    # Build ORM fields defensively
    def safe_int(v):
        try:
            return int(v) if v is not None and v != "" else None
        except Exception:
            return None

    t = Tournament(
        federation=item.get("federation"),
        external_id=item.get("external_id"),
        name=item.get("name") or "unnamed",
        status=item.get("status"),
        time_control=item.get("time_control"),
        rating=item.get("rating"),
        total_players=safe_int(item.get("total_players")),
        organizer=item.get("organizer"),
        place=item.get("place"),
        fide_players=safe_int(item.get("fide_players")),
        period=item.get("period"),
        observation=item.get("observation"),
        regulation=item.get("regulation"),
        year=item.get("year"),
        month=item.get("month"),
        scraped_at=datetime.now(timezone.utc)
    )
    db.add(t)
    return t


def _find_existing(db, r):
    """
    Tenta localizar um torneio existente com heurísticas:
    1) external_id (mais confiável)
    2) regulation (link)
    3) name + year + month (fallback)
    """
    if r.get("external_id"):
        q = db.query(Tournament).filter(
            Tournament.federation == r.get("federation"),
            Tournament.external_id == r.get("external_id")
        ).one_or_none()
        if q:
            return q

    if r.get("regulation"):
        q = db.query(Tournament).filter(
            Tournament.federation == r.get("federation"),
            Tournament.regulation == r.get("regulation")
        ).one_or_none()
        if q:
            return q

    # fallback by name + year + month (can have collisions; acceptable as last resort)
    name = r.get("name")
    if name:
        q = db.query(Tournament).filter(
            Tournament.federation == r.get("federation"),
            Tournament.name == name,
            Tournament.year == r.get("year"),
            Tournament.month == r.get("month")
        ).one_or_none()
        if q:
            return q

    return None


def sync_cbxtournaments(year=None, month=None, limit=None, full: bool = False, start_year: int = None, end_year: int = None):
    """
    Executa sync dos torneios CBX.

    - Se full==False: faz scraping dos parâmetros year/month (ou current year se None).
    - Se full==True: limpa DB (apenas federation='cbx'), e realiza scraping completo
      iterando por anos/meses entre start_year e end_year (ou 2005..current_year por padrão).
    """
    # 1) criar registro de job
    job_db = SessionLocal()
    job = SyncJob(federation="cbx", status="started")
    job_db.add(job)
    job_db.commit()
    job_db.refresh(job)
    job_id = job.id
    job_db.close()

    created = 0
    updated = 0

    # If full mode, optionally clean DB first
    if full:
        logger.info("FULL mode enabled: cleaning CBX tournaments from DB before full import.")
        db_clean = SessionLocal()
        try:
            deleted = db_clean.query(Tournament).filter(Tournament.federation == "cbx").delete(synchronize_session=False)
            db_clean.commit()
            logger.info(f"Deleted {deleted} existing CBX tournaments (cleanup before full import).")
        except Exception:
            db_clean.rollback()
            logger.exception("Failed cleaning CBX tournaments before full import.")
        finally:
            db_clean.close()

        # prepare year range
        now = datetime.now()
        sy = int(start_year) if start_year else 2005
        ey = int(end_year) if end_year else now.year

        # iterate years and months
        for y in range(sy, ey + 1):
            for m in range(1, 13):
                try:
                    logger.info(f"Full import: fetching year={y} month={m}")
                    rows = fetch_tournaments_raw(str(y), str(m), limit)
                except requests.exceptions.RequestException as e:
                    # update job as failed and return
                    dbj = SessionLocal()
                    j = dbj.get(SyncJob, job_id)
                    if j:
                        j.finished_at = datetime.now(timezone.utc)
                        j.status = "failed"
                        j.error = f"NetworkError (full import): {str(e)}"
                        dbj.commit()
                    dbj.close()
                    logger.exception("Network error during full CBX fetch. Aborting full import.")
                    return
                except Exception as e:
                    dbj = SessionLocal()
                    j = dbj.get(SyncJob, job_id)
                    if j:
                        j.finished_at = datetime.now(timezone.utc)
                        j.status = "failed"
                        j.error = f"UnexpectedError (full import): {str(e)}"
                        dbj.commit()
                    dbj.close()
                    logger.exception("Unexpected error during full CBX fetch. Aborting full import.")
                    return

                # persist rows
                db = SessionLocal()
                try:
                    for r in rows:
                        try:
                            existing = _find_existing(db, r)
                            if existing:
                                # update fields
                                existing.name = r.get("name") or existing.name
                                existing.status = r.get("status")
                                existing.time_control = r.get("time_control")
                                existing.rating = r.get("rating")
                                try:
                                    existing.total_players = int(r.get("total_players")) if r.get("total_players") else None
                                except Exception:
                                    existing.total_players = None
                                existing.organizer = r.get("organizer")
                                existing.place = r.get("place")
                                try:
                                    existing.fide_players = int(r.get("fide_players")) if r.get("fide_players") else None
                                except Exception:
                                    existing.fide_players = None
                                existing.period = r.get("period")
                                existing.observation = r.get("observation")
                                existing.regulation = r.get("regulation")
                                existing.year = r.get("year")
                                existing.month = r.get("month")
                                existing.scraped_at = datetime.now(timezone.utc)
                                updated += 1
                            else:
                                # create
                                upsert_tournament(db, r)
                                created += 1
                            db.commit()
                        except IntegrityError:
                            db.rollback()
                            logger.exception("IntegrityError while inserting/updating a tournament in full import, skipping.")
                        except Exception:
                            db.rollback()
                            logger.exception("Error processing individual tournament in full import, skipping.")
                finally:
                    db.close()

        logger.info(f"Full import finished: created={created}, updated={updated}")

        # finalize job as success
        db_job2 = SessionLocal()
        j = db_job2.get(SyncJob, job_id)
        if j:
            j.finished_at = datetime.now(timezone.utc)
            j.status = "success"
            j.created = created
            j.updated = updated
            db_job2.commit()
        db_job2.close()
        return

    # Non-full (incremental) mode
    try:
        rows = fetch_tournaments_raw(year, month, limit)
    except requests.exceptions.RequestException as e:
        # atualizar job como failed e salvar erro
        dbj = SessionLocal()
        j = dbj.get(SyncJob, job_id)
        if j:
            j.finished_at = datetime.now(timezone.utc)
            j.status = "failed"
            j.error = f"UnexpectedError: {str(e)}"
            dbj.commit()
        dbj.close()
        logger.exception("Erro de rede ao buscar dados da CBX. Sync abortado.")
        return
    except Exception as e:
        dbj = SessionLocal()
        j = dbj.get(SyncJob, job_id)
        if j:
            j.finished_at = datetime.now(timezone.utc)
            j.status = "failed"
            j.error = f"UnexpectedError: {str(e)}"
            dbj.commit()
        dbj.close()
        logger.exception("Erro inesperado ao buscar dados da CBX. Sync abortado.")
        return

    # 2) processar linhas e persistir (commits periódicos)
    db = SessionLocal()
    try:
        for r in rows:
            try:
                existing = _find_existing(db, r)
                if existing:
                    # update existing
                    existing.name = r.get("name") or existing.name
                    existing.status = r.get("status")
                    existing.time_control = r.get("time_control")
                    existing.rating = r.get("rating")
                    try:
                        existing.total_players = int(r.get("total_players")) if r.get("total_players") else None
                    except Exception:
                        existing.total_players = None
                    existing.organizer = r.get("organizer")
                    existing.place = r.get("place")
                    try:
                        existing.fide_players = int(r.get("fide_players")) if r.get("fide_players") else None
                    except Exception:
                        existing.fide_players = None
                    existing.period = r.get("period")
                    existing.observation = r.get("observation")
                    existing.regulation = r.get("regulation")
                    existing.year = r.get("year")
                    existing.month = r.get("month")
                    existing.scraped_at = datetime.now(timezone.utc)
                    updated += 1
                else:
                    upsert_tournament(db, r)
                    created += 1
                db.commit()
            except IntegrityError:
                db.rollback()
                logger.exception("IntegrityError ao inserir/atualizar um torneio, pulando.")
            except Exception:
                db.rollback()
                logger.exception("Erro ao processar um torneio individual, pulando.")
        logger.info(f"Sync complete: created={created}, updated={updated}")
    except Exception:
        db.rollback()
        logger.exception("Erro durante loop de sync")
    finally:
        db.close()

    # 3) atualizar registro de job como sucesso
    db_job2 = SessionLocal()
    j = db_job2.get(SyncJob, job_id)
    if j:
        j.finished_at = datetime.now(timezone.utc)
        j.status = "success"
        j.created = created
        j.updated = updated
        db_job2.commit()
    db_job2.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", default=None)
    parser.add_argument("--month", default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--full", action="store_true", help="Run full import (clears CBX tournaments and imports all years/months).")
    parser.add_argument("--start-year", type=int, default=None, help="Start year for full import (defaults to 2005).")
    parser.add_argument("--end-year", type=int, default=None, help="End year for full import (defaults to current year).")
    args = parser.parse_args()
    sync_cbxtournaments(year=args.year, month=args.month, limit=args.limit, full=args.full, start_year=args.start_year, end_year=args.end_year)
