-- Members table 
CREATE TABLE members (
  id SERIAL PRIMARY KEY,
  username TEXT NOT NULL UNIQUE,
  email TEXT NOT NULL UNIQUE,
  password TEXT NOT NULL,
  gender TEXT NOT NULL,
  name TEXT,
  birthdate DATE,
  country TEXT,
  region TEXT,
  active BOOL,
  role TEXT DEFAULT 'player',
  profile_picture TEXT,
  bio TEXT,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  rating_id INT
);


-- Rating history 
CREATE TABLE rating_history (
  id SERIAL PRIMARY KEY,
  member_id INTEGER NOT NULL,
  date DATE NOT NULL,
  
  -- FIDE
  classical_fide SMALLINT,
  rapid_fide SMALLINT,
  blitz_fide SMALLINT,
  
  -- NATIONAL
  classical_national SMALLINT,
  rapid_national SMALLINT,
  blitz_national SMALLINT,
  bullet_national SMALLINT,

  -- CHESSCOM
  rapid_chesscom SMALLINT,
  blitz_chesscom SMALLINT,
  bullet_chesscom SMALLINT,
  
  -- LICHESS
  classical_lichess SMALLINT,
  rapid_lichess SMALLINT,
  blitz_lichess SMALLINT,
  bullet_lichess SMALLINT,

  CONSTRAINT fk_member_rating 
    FOREIGN KEY (member_id) 
    REFERENCES members(id) 
    ON DELETE CASCADE
);
CREATE INDEX ix_rating_history_member_date ON rating_history (member_id, date);


-- Clubs table
CREATE TABLE clubs (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  email TEXT NOT NULL UNIQUE,
  password TEXT NOT NULL,
  country TEXT,
  region TEXT,
  active BOOL DEFAULT TRUE,
  description VARCHAR(100),
  logo TEXT,
  owner_id INT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT fk_owner
    FOREIGN KEY (owner_id)
    REFERENCES members(id)
    ON DELETE CASCADE
);


-- Tournaments table
CREATE TABLE tournaments (
  id SERIAL PRIMARY KEY,
  club_id INTEGER,
  external_id TEXT,
  federation TEXT,
  title TEXT,
  status TEXT,
  total_players TEXT,
  organizer TEXT,
  place TEXT,
  fide_players TEXT,
  period TEXT,
  observation TEXT,
  regulation TEXT,
  start_date DATE,
  end_date DATE,
  time_control TEXT,
  rating TEXT,
  image_url TEXT,
  year TEXT,
  month TEXT,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT fk_club_tournament
    FOREIGN KEY (club_id) 
    REFERENCES clubs(id) 
    ON DELETE SET NULL,
  
  CONSTRAINT uix_fed_externalid 
    UNIQUE (federation, external_id)
);
CREATE INDEX ix_tournaments_external_id ON tournaments (external_id);
CREATE INDEX ix_tournaments_federation ON tournaments (federation);
CREATE INDEX ix_tournaments_club_id ON tournaments (club_id); 


-- Games table 
CREATE TABLE games (
  id SERIAL PRIMARY KEY,
  white_player_id INTEGER,
  black_player_id INTEGER,
  tournament_id INTEGER,
  result TEXT,
  round INTEGER,
  board_number INTEGER,
  utc_datetime TIMESTAMPTZ,
  white_rating INTEGER,
  black_rating INTEGER,
  white_rating_change INTEGER,
  black_rating_change INTEGER,
  variant TEXT,
  time_control TEXT,
  termination TEXT,
  opening_name TEXT,
  opening_eco TEXT,
  moves TEXT,
  played_at TIMESTAMPTZ,

  CONSTRAINT fk_white_player
    FOREIGN KEY (white_player_id) 
    REFERENCES members(id) 
    ON DELETE SET NULL,

  CONSTRAINT fk_black_player
    FOREIGN KEY (black_player_id) 
    REFERENCES members(id) 
    ON DELETE SET NULL,

  CONSTRAINT fk_tournament
    FOREIGN KEY (tournament_id) 
    REFERENCES tournaments(id) 
    ON DELETE SET NULL
);
CREATE INDEX ix_games_white_player_id ON games (white_player_id);
CREATE INDEX ix_games_black_player_id ON games (black_player_id);
CREATE INDEX ix_games_tournament_id ON games (tournament_id);


-- Tournament members table
CREATE TABLE tournament_members (
  id SERIAL PRIMARY KEY,
  tournament_id INTEGER NOT NULL,
  member_id INTEGER NOT NULL,

  CONSTRAINT fk_tournament_member
    FOREIGN KEY (tournament_id) 
    REFERENCES tournaments(id) 
    ON DELETE CASCADE,

  CONSTRAINT fk_member_tournament
    FOREIGN KEY (member_id) 
    REFERENCES members(id) 
    ON DELETE CASCADE,
  
  CONSTRAINT uix_tournament_member UNIQUE (tournament_id, member_id)
);
CREATE INDEX ix_tournament_members_tournament_id ON tournament_members (tournament_id);
CREATE INDEX ix_tournament_members_member_id ON tournament_members (member_id);


-- Club members table
CREATE TABLE club_members (
  id SERIAL PRIMARY KEY,
  club_id INT NOT NULL,
  member_id INT NOT NULL,
  role TEXT DEFAULT 'member',

  CONSTRAINT fk_club
    FOREIGN KEY (club_id)
    REFERENCES clubs(id)
    ON DELETE CASCADE,

  CONSTRAINT fk_member
    FOREIGN KEY (member_id)
    REFERENCES members(id)
    ON DELETE CASCADE,
  
  CONSTRAINT uix_club_member UNIQUE (club_id, member_id)
);
CREATE INDEX ix_club_members_club_id ON club_members (club_id);
CREATE INDEX ix_club_members_member_id ON club_members (member_id);


-- Club tournaments table
CREATE TABLE club_tournaments (
  id SERIAL PRIMARY KEY,
  club_id INTEGER NOT NULL,
  tournament_id INTEGER NOT NULL,

  CONSTRAINT fk_club_relation
    FOREIGN KEY (club_id) 
    REFERENCES clubs(id) 
    ON DELETE CASCADE,

  CONSTRAINT fk_tournament_relation
    FOREIGN KEY (tournament_id) 
    REFERENCES tournaments(id) 
    ON DELETE CASCADE,
  
  CONSTRAINT uix_club_tournament UNIQUE (club_id, tournament_id)
);
CREATE INDEX ix_club_tournaments_club_id ON club_tournaments (club_id);
CREATE INDEX ix_club_tournaments_tournament_id ON club_tournaments (tournament_id);
