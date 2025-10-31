"""
Seed script para popular o banco de dados do OTB com dados realistas.

Execute com:
    python seed_db.py
"""

import random
from datetime import datetime, timedelta, date
from faker import Faker
from argon2 import PasswordHasher

from database.session import SessionLocal, engine, Base
from database.models import People, Club, Tournament

fake = Faker()
ph = PasswordHasher()

# Limpa e recria todas as tabelas
print("🧹 Limpando e recriando tabelas...")
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# ---------------------------------------
# Funções auxiliares
# ---------------------------------------
def random_country():
    return random.choice(["Brazil", "Argentina", "USA", "Spain", "France", "Germany"])

def random_region(country):
    if country == "Brazil":
        return random.choice(["SP", "RJ", "MG", "RS", "PR"])
    elif country == "USA":
        return random.choice(["NY", "CA", "TX", "FL"])
    else:
        return fake.state_abbr()

def random_time_control():
    return random.choice(["10+5", "15+10", "30+0", "90+30", "3+2"])

def random_rating_system():
    return random.choice(["FIDE", "CBX", "Lichess", "OTB"])

# ---------------------------------------
# Cria usuários (People)
# ---------------------------------------
print("👤 Criando usuários...")
people_list = []
for _ in range(10):
    username = fake.user_name()
    email = fake.email()
    password = ph.hash("password123")
    gender = random.choice(["male", "female", None])
    birthdate = fake.date_of_birth(minimum_age=16, maximum_age=60)
    country = random_country()
    region = random_region(country)
    bio = fake.sentence(nb_words=12)

    person = People(
        username=username,
        email=email,
        password=password,
        gender=gender,
        birthdate=str(birthdate),
        country=country,
        region=region,
        active=1,
        role="player",
        profile_picture=None,
        rating_id=None,
        bio=bio,
    )
    people_list.append(person)
    db.add(person)

db.commit()
print(f"✅ {len(people_list)} usuários criados.")

# ---------------------------------------
# Cria clubes (Club)
# ---------------------------------------
print("🏛️ Criando clubes...")
clubs_list = []
for _ in range(5):
    name = f"{fake.city()} Chess Club"
    email = fake.company_email()
    password = ph.hash("clubpass")
    country = random_country()
    region = random_region(country)
    owner = random.choice(people_list)

    club = Club(
        name=name,
        email=email,
        password=password,
        country=country,
        region=region,
        active=1,
        owner_id=owner.id,
    )
    clubs_list.append(club)
    db.add(club)

db.commit()
print(f"✅ {len(clubs_list)} clubes criados.")

# ---------------------------------------
# Cria torneios (Tournament)
# ---------------------------------------
print("♟️ Criando torneios...")
tournaments_list = []
for club in clubs_list:
    for _ in range(random.randint(2, 5)):
        title = f"{fake.city()} Open {fake.year()}"
        place = fake.city()
        start_date = date.today() + timedelta(days=random.randint(-60, 60))
        end_date = start_date + timedelta(days=random.randint(0, 2))
        time_control = random_time_control()
        rating = random_rating_system()
        image_url = f"https://picsum.photos/seed/{fake.uuid4()[:8]}/600/400"

        tournament = Tournament(
            title=title,
            place=place,
            start_date=start_date,
            end_date=end_date,
            time_control=time_control,
            rating=rating,
            image_url=image_url,
            club_id=club.id,
        )
        tournaments_list.append(tournament)
        db.add(tournament)

db.commit()
print(f"✅ {len(tournaments_list)} torneios criados.")

# ---------------------------------------
# Finalização
# ---------------------------------------
db.close()
print("🎉 Banco de dados populado com sucesso!")
