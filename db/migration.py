# database/migration.py
from db.session import engine, Base
from db import models
from core.logger_config import logger


def create_tables():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    logger.info(f"Creating Tables in the DataBase...")
    create_tables()
    logger.info(f"Tables Created!")
