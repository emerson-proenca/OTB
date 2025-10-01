# database/migration.py
from database.session import engine, Base
from database import models
from core.logger_config import logger


def create_tables():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    logger.info(f"Creating Tables in the DataBase...")
    create_tables()
    logger.info(f"Tables Created!")
