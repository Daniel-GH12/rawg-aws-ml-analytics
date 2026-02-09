
DROP SCHEMA IF EXISTS rawg CASCADE;
CREATE SCHEMA rawg;

CREATE SCHEMA IF NOT EXISTS rawg;

-- =========================
-- DIMENSIONES / CATÁLOGOS
-- =========================

CREATE TABLE IF NOT EXISTS rawg.esrb_ratings (
  esrb_id   INT PRIMARY KEY,
  esrb_name VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS rawg.platforms (
  platform_id   INT PRIMARY KEY,
  platform_name VARCHAR(200) NOT NULL
);

CREATE TABLE IF NOT EXISTS rawg.genres (
  genre_id          INT PRIMARY KEY,
  genre_name        VARCHAR(100) NOT NULL,
  genre_games_count BIGINT
);

CREATE TABLE IF NOT EXISTS rawg.stores (
  store_id   INT PRIMARY KEY,
  store_name VARCHAR(200) NOT NULL
);

CREATE TABLE IF NOT EXISTS rawg.tags (
  tag_id          BIGINT PRIMARY KEY,
  tag_name        VARCHAR(200) NOT NULL,
  tag_language    VARCHAR(50),
  tag_games_count BIGINT
);

-- =========================
-- HECHO PRINCIPAL
-- =========================

CREATE TABLE IF NOT EXISTS rawg.games (
  game_id           BIGINT PRIMARY KEY,
  game_name         VARCHAR(500) NOT NULL,
  tba               BOOLEAN,
  released_ym       CHAR(7),
  updated_ym        CHAR(7),

  game_rating        NUMERIC(4,2),
  ratings_count      BIGINT,
  game_added         BIGINT,
  playtime           INTEGER,
  suggestions_count  BIGINT,

  esrb_id           INT NULL,
  created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT fk_games_esrb
    FOREIGN KEY (esrb_id) REFERENCES rawg.esrb_ratings(esrb_id)
);

CREATE TABLE IF NOT EXISTS rawg.games_status (
  game_id BIGINT PRIMARY KEY
    REFERENCES rawg.games(game_id) ON DELETE CASCADE,
  yet     BIGINT NOT NULL DEFAULT 0,
  owned   BIGINT NOT NULL DEFAULT 0,
  beaten  BIGINT NOT NULL DEFAULT 0,
  toplay  BIGINT NOT NULL DEFAULT 0,
  dropped BIGINT NOT NULL DEFAULT 0,
  playing BIGINT NOT NULL DEFAULT 0
);

-- Distribución de ratings por juego (típicamente 4 filas por juego)
CREATE TABLE IF NOT EXISTS rawg.ratings_distribution (
  game_id        BIGINT NOT NULL,
  ratingd_id     INT NOT NULL,
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
  platform_id INT NOT NULL,
  released_at VARCHAR(10),
  PRIMARY KEY (game_id, platform_id),
  FOREIGN KEY (game_id) REFERENCES rawg.games(game_id) ON DELETE CASCADE,
  FOREIGN KEY (platform_id) REFERENCES rawg.platforms(platform_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS rawg.game_genres (
  game_id  BIGINT NOT NULL,
  genre_id INT NOT NULL,
  PRIMARY KEY (game_id, genre_id),
  FOREIGN KEY (game_id) REFERENCES rawg.games(game_id) ON DELETE CASCADE,
  FOREIGN KEY (genre_id) REFERENCES rawg.genres(genre_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS rawg.game_stores (
  game_id  BIGINT NOT NULL,
  store_id INT NOT NULL,
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
-- ÍNDICES
-- =========================
CREATE INDEX IF NOT EXISTS ix_games_released ON rawg.games(released_ym);
CREATE INDEX IF NOT EXISTS ix_games_esrb_id ON rawg.games(esrb_id);
CREATE INDEX IF NOT EXISTS ix_ratings_distribution_game ON rawg.ratings_distribution(game_id);
CREATE INDEX IF NOT EXISTS ix_game_platforms_platform ON rawg.game_platforms(platform_id);
CREATE INDEX IF NOT EXISTS ix_game_genres_genre ON rawg.game_genres(genre_id);
CREATE INDEX IF NOT EXISTS ix_game_stores_store ON rawg.game_stores(store_id);
CREATE INDEX IF NOT EXISTS ix_game_tags_tag ON rawg.game_tags(tag_id);
