-- 4. Tabla ESRB_Ratings (hai que poñela aquí que si no non a encontra)
CREATE TABLE esrb_ratings (
    esrb_id INT PRIMARY KEY,
    esrb_name VARCHAR(50)
);

-- 1. Tabla principal juegos
CREATE TABLE games (
    game_id INT PRIMARY KEY,
    game_name VARCHAR(255),
    tba BOOLEAN,
    game_released DATE,
    game_updated TIMESTAMP,
    game_rating DECIMAL,
    rating_count INT,
    game_added INT,
    playtime INT,
    suggestions_count INT,
    esrb_rating_id INT REFERENCES esrb_ratings(esrb_id)
);

-- 2. Tabla ratings_distribution
CREATE TABLE ratings_distribution (
    ratingd_id INT PRIMARY KEY,
    game_id INT REFERENCES games(game_id),
    ratingd_title VARCHAR(50),
    ratingd_count INT,
    ratingd_percent DECIMAL
);

-- 3. Tabla games_status
CREATE TABLE games_status (
    game_id INT PRIMARY KEY REFERENCES games(game_id),
    yet INT,
    owned INT,
    beaten INT,
    toplay INT,
    dropped INT,
    playing INT
);

-- 5. Tabla platforms
CREATE TABLE platforms (
    platform_id INT PRIMARY KEY,
    platform_name VARCHAR(100),
    platform_released DATE
);

-- 6. Tabla genres
CREATE TABLE genres (
    genre_id INT PRIMARY KEY,
    genre_name VARCHAR(100),
    genres_games_count INT
);

-- 7. Tabla stores
CREATE TABLE stores (
    store_id INT PRIMARY KEY,
    store_name VARCHAR(100)
);

-- 8. Tabla tags
CREATE TABLE tags (
    tag_id INT PRIMARY KEY,
    tag_name VARCHAR(100),
    tag_language VARCHAR(10),
    tag_games_count INT
);

-- Tabla developers
CREATE TABLE IF NOT EXISTS developers (
    developer_id INT PRIMARY KEY,
    developer_name VARCHAR(255),
    games_count INT
);

-- Tablas relacionales (N:M)
CREATE TABLE games_platforms (
	game_id INT REFERENCES games(game_id),
	platform_id INT REFERENCES platforms(platform_id), 
	PRIMARY KEY(game_id, platform_id)
);
	
CREATE TABLE games_genres (
	game_id INT REFERENCES games(game_id),
	genre_id INT REFERENCES genres(genre_id),
	PRIMARY KEY(game_id, genre_id)
);
	
CREATE TABLE games_stores (
	game_id INT REFERENCES games(game_id),
	store_id INT REFERENCES stores(store_id),
	PRIMARY KEY(game_id, store_id)
);
	
CREATE TABLE games_tags (
	game_id INT REFERENCES games(game_id),
	tag_id INT REFERENCES tags(tag_id),
	PRIMARY KEY(game_id, tag_id)
);

CREATE TABLE IF NOT EXISTS games_developers (
    game_id INT,
    developer_id INT,
    PRIMARY KEY (game_id, developer_id),
    FOREIGN KEY (game_id) REFERENCES games(game_id),
    FOREIGN KEY (developer_id) REFERENCES developers(developer_id)
);