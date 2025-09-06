# database/migration.py
from database.session import engine, Base
from database import models  # garante que os modelos sejam importados

def create_tables():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    print("Creating Tables in the DataBase...")
    create_tables()
    print("Tables Created!")
