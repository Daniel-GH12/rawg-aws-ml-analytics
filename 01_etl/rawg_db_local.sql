CREATE SCHEMA IF NOT EXISTS rawg;

-- =========================
-- DIMENSIONES
-- =========================

CREATE TABLE IF NOT EXISTS rawg.esrb_ratings (
  esrb_id   INTEGER,
  esrb_name VARCHAR(100) NOT NULL,
  PRIMARY KEY (esrb_id)
);

CREATE TABLE IF NOT EXISTS rawg.games (
  game_id           SERIAL,
  game_name         VARCHAR(500) NOT NULL,
  tba               BOOLEAN,
  released_ym       CHAR(7),
  updated_ym        CHAR(7),

  game_rating        NUMERIC(4,2),
  ratings_count      BIGINT,
  game_added         BIGINT,
  playtime           INTEGER,
  suggestions_count  BIGINT,

  esrb_id            INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (game_id),
  FOREIGN KEY (esrb_id) REFERENCES rawg.esrb_ratings(esrb_id)
  
);

CREATE TABLE  IF NOT EXISTS rawg.games_status (
  game_id BIGINT PRIMARY KEY REFERENCES rawg.games(game_id) ON DELETE CASCADE,
  yet     BIGINT NOT NULL DEFAULT 0,
  owned   BIGINT NOT NULL DEFAULT 0,
  beaten  BIGINT NOT NULL DEFAULT 0,
  toplay  BIGINT NOT NULL DEFAULT 0,
  dropped BIGINT NOT NULL DEFAULT 0,
  playing BIGINT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS rawg.platforms (
  platform_id   SERIAL,
  platform_name VARCHAR(200) NOT NULL,
  relased_at VARCHAR(7),   -- Formato YYYY-MM
  PRIMARY KEY (platform_id)
);

CREATE TABLE IF NOT EXISTS rawg.genres (
  genre_id         SERIAL,
  genre_name       VARCHAR(100) NOT NULL,
  genre_games_count BIGINT,
  PRIMARY KEY (genre_id)
);

CREATE TABLE IF NOT EXISTS rawg.stores (
  store_id   SERIAL,
  store_name VARCHAR(200) NOT NULL,
  PRIMARY KEY (store_id)
);

CREATE TABLE IF NOT EXISTS rawg.tags (
  tag_id          SERIAL,
  tag_name        VARCHAR(200) NOT NULL,
  tag_language    VARCHAR (200),
  tag_games_count BIGINT,
  PRIMARY KEY (tag_id)
);

-- =========================
-- HECHOS / DETALLE
-- =========================

-- Distribución de ratings por juego (4 filas típicas por juego)
CREATE TABLE IF NOT EXISTS rawg.ratings_distribution (
  game_id        BIGINT NOT NULL,
  ratingd_id     BIGINT NOT NULL,
  ratingd_title  VARCHAR(50),
  ratingd_count  BIGINT DEFAULT 0,
  ratingd_percent NUMERIC(6,2) DEFAULT 0.0,
  PRIMARY KEY (game_id, ratingd_id),
  FOREIGN KEY (game_id) REFERENCES rawg.games(game_id) ON DELETE CASCADE
);

-- =========================
-- RELACIONES N:M (BRIDGES)
-- =========================

CREATE TABLE IF NOT EXISTS rawg.game_platforms (
  game_id     BIGINT NOT NULL,
  platform_id BIGINT NOT NULL,
  PRIMARY KEY (game_id, platform_id),
  FOREIGN KEY (game_id) REFERENCES rawg.games(game_id) ON DELETE CASCADE,
  FOREIGN KEY (platform_id) REFERENCES rawg.platforms(platform_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS rawg.game_genres (
  game_id  BIGINT NOT NULL,
  genre_id BIGINT NOT NULL,
  PRIMARY KEY (game_id, genre_id),
  FOREIGN KEY (game_id) REFERENCES rawg.games(game_id) ON DELETE CASCADE,
  FOREIGN KEY (genre_id) REFERENCES rawg.genres(genre_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS rawg.game_stores (
  game_id  BIGINT NOT NULL,
  store_id BIGINT NOT NULL,
  PRIMARY KEY (game_id, store_id),
  FOREIGN KEY (game_id) REFERENCES rawg.games(game_id) ON DELETE CASCADE,
  FOREIGN KEY (store_id) REFERENCES rawg.stores(store_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS rawg.game_tags (
  game_id BIGINT NOT NULL,
  tag_id  BIGINT NOT NULL,
  PRIMARY KEY (game_id, tag_id),
  FOREIGN KEY (game_id) REFERENCES rawg.games(game_id) ON DELETE CASCADE,
  FOREIGN KEY (tag_id) REFERENCES rawg.tags(tag_id) ON DELETE CASCADE
);

-- =========================
-- ÍNDICES (para joins rápidos)
-- =========================
CREATE INDEX IF NOT EXISTS ix_games_released ON rawg.games(released_ym);
CREATE INDEX IF NOT EXISTS ix_games_esrb_id ON rawg.games(esrb_id);
CREATE INDEX IF NOT EXISTS ix_ratings_distribution_game ON rawg.ratings_distribution(game_id);
CREATE INDEX IF NOT EXISTS ix_game_platforms_platform ON rawg.game_platforms(platform_id);
CREATE INDEX IF NOT EXISTS ix_game_genres_genre ON rawg.game_genres(genre_id);
CREATE INDEX IF NOT EXISTS ix_game_stores_store ON rawg.game_stores(store_id);
CREATE INDEX IF NOT EXISTS ix_game_tags_tag ON rawg.game_tags(tag_id);

ALTER TABLE rawg.games
  ALTER COLUMN ratings_count TYPE BIGINT,
  ALTER COLUMN suggestions_count TYPE BIGINT,
  ALTER COLUMN game_added TYPE BIGINT,
  ALTER COLUMN esrb_id TYPE INTEGER;

ALTER TABLE rawg.games_status
  ALTER COLUMN game_id TYPE BIGINT,
  ALTER COLUMN yet TYPE BIGINT,
  ALTER COLUMN owned TYPE BIGINT,
  ALTER COLUMN beaten TYPE BIGINT,
  ALTER COLUMN toplay TYPE BIGINT,
  ALTER COLUMN dropped TYPE BIGINT,
  ALTER COLUMN playing TYPE BIGINT;

ALTER TABLE rawg.genres
  ALTER COLUMN genre_games_count TYPE BIGINT;

ALTER TABLE rawg.tags 
  ALTER COLUMN tag_games_count TYPE BIGINT;

ALTER TABLE rawg.ratings_distribution 
  ALTER COLUMN game_id TYPE BIGINT,
  ALTER COLUMN ratingd_count TYPE BIGINT;

 ALTER TABLE rawg.game_platforms
  ALTER COLUMN game_id TYPE BIGINT,
  ALTER COLUMN platform_id  TYPE BIGINT;

 ALTER TABLE rawg.game_genres
  ALTER COLUMN game_id TYPE BIGINT,
  ALTER COLUMN genre_id TYPE BIGINT;

 ALTER TABLE rawg.game_stores
  ALTER COLUMN game_id TYPE BIGINT,
  ALTER COLUMN store_id TYPE BIGINT;

 ALTER TABLE rawg.game_tags
  ALTER COLUMN game_id TYPE BIGINT,
  ALTER COLUMN tag_id TYPE BIGINT;  

SELECT
  column_name,
  data_type
FROM information_schema.columns
WHERE table_schema = 'rawg'
  AND table_name = 'games'
ORDER BY ordinal_position;

SELECT
  column_name,
  data_type
FROM information_schema.columns
WHERE table_schema = 'rawg'
  AND table_name = 'esrb_ratings'
ORDER BY ordinal_position;