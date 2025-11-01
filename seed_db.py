"""
seed_db.py
----------------------------------
Populate the OTB database with fake data for development and testing.
RUN PIP INSTALL FAKER BEFORE USING THIS SCRIPT:

pip install faker
----------------------------------
"""

from datetime import datetime, timedelta
import random
from faker import Faker
from sqlalchemy.orm import Session
from db.session import engine, Base
from db.models import (
    Member,
    Club,
    Tournament,
    Game,
    ClubMember,
    TournamentMember,
    ClubTournament,
    RatingHistory,
)

fake = Faker()
Faker.seed(42)
random.seed(42)


def create_members(session: Session, n=20):
    members = []
    for _ in range(n):
        member = Member(
            username=fake.unique.user_name(),
            email=fake.unique.email(),
            password=fake.password(length=12),
            name=fake.name(),
            gender=random.choice(["Male", "Female", "Other"]),
            birthdate=str(fake.date_of_birth(minimum_age=12, maximum_age=80)),
            country=fake.country(),
            region=fake.state(),
            bio=fake.sentence(nb_words=10),
            role=random.choice(["player", "arbiter", "organizer"]),
            fide_id=str(fake.random_int(min=1000000, max=9999999)),
            national_id=str(fake.random_int(min=100000, max=999999)),
        )
        session.add(member)
        members.append(member)
    session.commit()
    return members


def create_clubs(session: Session, members, n=5):
    clubs = []
    for _ in range(n):
        owner = random.choice(members)
        club = Club(
            name=f"{fake.city()} Chess Club",
            email=fake.unique.company_email(),
            password=fake.password(length=10),
            country=owner.country,
            region=owner.region,
            description=fake.sentence(nb_words=8),
            logo=None,
            owner_id=owner.id,
        )
        session.add(club)
        clubs.append(club)
    session.commit()

    # Add members to clubs
    for club in clubs:
        club_members = random.sample(members, k=random.randint(3, 10))
        for m in club_members:
            session.add(ClubMember(club_id=club.id, member_id=m.id, role="member"))
    session.commit()

    return clubs


def create_tournaments(session: Session, clubs, n=10):
    tournaments = []
    for _ in range(n):
        club = random.choice(clubs)
        start_date = fake.date_this_year(before_today=False, after_today=True)
        end_date = start_date + timedelta(days=random.randint(1, 3))
        tournament = Tournament(
            external_id=str(fake.uuid4())[:8],
            federation=random.choice(["CBX", "FIDE", "LNX"]),
            title=f"{fake.word().capitalize()} Open",
            status=random.choice(["upcoming", "ongoing", "finished"]),
            total_players=str(random.randint(20, 120)),
            organizer=club.name,
            place=fake.city(),
            fide_players=str(random.randint(5, 50)),
            period=f"{start_date} - {end_date}",
            regulation="Standard FIDE Rules",
            start_date=start_date,
            end_date=end_date,
            time_control=random.choice(["90+30", "60+0", "15+10", "3+2"]),
            rating=random.choice(["FIDE", "National", "None"]),
            image_url=None,
            club_id=club.id,
            year=str(datetime.now().year),
            month=str(datetime.now().month),
        )
        session.add(tournament)
        tournaments.append(tournament)
    session.commit()
    return tournaments


def create_games(session: Session, tournaments, members, n=30):
    results = ["1-0", "0-1", "1/2-1/2"]
    variants = ["Classical", "Rapid", "Blitz"]
    terminations = ["Checkmate", "Resignation", "Time forfeit"]
    for _ in range(n):
        white, black = random.sample(members, 2)
        tournament = random.choice(tournaments)
        game = Game(
            white_player_id=white.id,
            black_player_id=black.id,
            tournament_id=tournament.id,
            result=random.choice(results),
            round=random.randint(1, 7),
            board_number=random.randint(1, 20),
            utc_datetime=fake.date_time_this_year(),
            white_rating=random.randint(1000, 2500),
            black_rating=random.randint(1000, 2500),
            white_rating_change=random.randint(-10, 10),
            black_rating_change=random.randint(-10, 10),
            variant=random.choice(variants),
            time_control=random.choice(["90+30", "15+10", "3+2"]),
            termination=random.choice(terminations),
            opening_name=random.choice(["Sicilian Defense", "Ruy Lopez", "French Defense"]),
            opening_eco=random.choice(["B20", "C60", "E00"]),
            moves="1.e4 c5 2.Nf3 d6 3.d4 cxd4 4.Nxd4 Nf6",
            played_at=fake.date_time_this_year(),
        )
        session.add(game)
    session.commit()


def create_tournament_members(session: Session, tournaments, members):
    for t in tournaments:
        players = random.sample(members, k=random.randint(8, 20))
        for m in players:
            session.add(TournamentMember(tournament_id=t.id, member_id=m.id))
    session.commit()


def create_club_tournaments(session: Session, clubs, tournaments):
    for t in tournaments:
        session.add(ClubTournament(club_id=t.club_id, tournament_id=t.id))
    session.commit()


def create_rating_history(session: Session, members):
    for m in members:
        for _ in range(3):
            date = fake.date_this_year()
            rh = RatingHistory(
                member_id=m.id,
                date=date,
                classical_fide=random.randint(1000, 2500),
                rapid_fide=random.randint(1000, 2500),
                blitz_fide=random.randint(1000, 2500),
                classical_national=random.randint(1000, 2500),
                rapid_national=random.randint(1000, 2500),
                blitz_national=random.randint(1000, 2500),
                bullet_national=random.randint(1000, 2500),
                rapid_chesscom=random.randint(1000, 2500),
                blitz_chesscom=random.randint(1000, 2500),
                bullet_chesscom=random.randint(1000, 2500),
                classical_lichess=random.randint(1000, 2500),
                rapid_lichess=random.randint(1000, 2500),
                blitz_lichess=random.randint(1000, 2500),
                bullet_lichess=random.randint(1000, 2500),
            )
            session.add(rh)
    session.commit()


def seed_database():
    Base.metadata.create_all(bind=engine)
    session = Session(bind=engine)

    print("Seeding database with fake data...")

    members = create_members(session, n=25)
    clubs = create_clubs(session, members, n=6)
    tournaments = create_tournaments(session, clubs, n=12)

    create_tournament_members(session, tournaments, members)
    create_club_tournaments(session, clubs, tournaments)
    create_games(session, tournaments, members, n=40)
    create_rating_history(session, members)

    print("Database successfully seeded with fake data!")
    session.close()


if __name__ == "__main__":
    seed_database()
