# database/migration.py
from database.session import engine, Base
from database import models  # garante que os modelos sejam importados

def create_tables():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    print("Criando tabelas no DB...")
    create_tables()
    print("Tabelas criadas.")
