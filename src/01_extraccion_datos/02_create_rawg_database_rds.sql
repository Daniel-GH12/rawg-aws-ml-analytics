
-- SCRIPT SQL PARA RDS EN AWS: BASE DE DATOS RAWG - VIDEOJUEGOS
-- Autor: Manuel Serrano (rama manel-rawg)
-- Objetivo: Esquema mínimo funcional para RDS en AWS
-- Nota: Este script se ejecutará en la instancia RDS, no en localhost

-- PASO 1: CREAR TABLAS MAESTRAS
CREATE TABLE IF NOT EXISTS esrb_ratings (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS genres (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS platforms (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- PASO 2: CREAR TABLA PRINCIPAL (games)
CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    released DATE,
    rating NUMERIC(3,2),
    ratings_count INTEGER,
    metacritic INTEGER,
    playtime INTEGER,
    status_yet INTEGER DEFAULT 0,
    status_owned INTEGER DEFAULT 0,
    status_beaten INTEGER DEFAULT 0,
    status_toplay INTEGER DEFAULT 0,
    status_dropped INTEGER DEFAULT 0,
    status_playing INTEGER DEFAULT 0,
    success BOOLEAN DEFAULT FALSE,
    esrb_rating_id INTEGER REFERENCES esrb_ratings(id) ON DELETE SET NULL,
    updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para optimización
CREATE INDEX IF NOT EXISTS idx_games_rating ON games(rating DESC);
CREATE INDEX IF NOT EXISTS idx_games_success ON games(success);
CREATE INDEX IF NOT EXISTS idx_games_esrb ON games(esrb_rating_id);

-- PASO 3: CREAR TABLAS DE RELACIÓN
CREATE TABLE IF NOT EXISTS game_genres (
    game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    genre_id INTEGER NOT NULL REFERENCES genres(id) ON DELETE CASCADE,
    PRIMARY KEY (game_id, genre_id)
);

CREATE TABLE IF NOT EXISTS game_platforms (
    game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    platform_id INTEGER NOT NULL REFERENCES platforms(id) ON DELETE CASCADE,
    released_at DATE,
    PRIMARY KEY (game_id, platform_id)
);

-- PASO 4: VISTA Y FUNCIÓN
CREATE OR REPLACE VIEW games_for_ml AS
SELECT 
    g.id, g.name, EXTRACT(YEAR FROM g.released) AS release_year,
    g.rating, g.ratings_count, g.metacritic, g.playtime,
    g.status_yet, g.status_owned, g.status_beaten, g.status_toplay, g.status_dropped, g.status_playing,
    g.success, er.name AS esrb_rating,
    STRING_AGG(DISTINCT ge.name, ', ') AS genres_list,
    STRING_AGG(DISTINCT p.name, ', ') AS platforms_list
FROM games g
LEFT JOIN esrb_ratings er ON g.esrb_rating_id = er.id
LEFT JOIN game_genres gg ON g.id = gg.game_id
LEFT JOIN genres ge ON gg.genre_id = ge.id
LEFT JOIN game_platforms gp ON g.id = gp.game_id
LEFT JOIN platforms p ON gp.platform_id = p.id
GROUP BY g.id, g.name, g.released, g.rating, g.ratings_count, g.metacritic, 
         g.playtime, g.status_yet, g.status_owned, g.status_beaten, 
         g.status_toplay, g.status_dropped, g.status_playing, g.success, er.name;

CREATE OR REPLACE FUNCTION calculate_success() 
RETURNS VOID AS $$
BEGIN
    UPDATE games 
    SET success = CASE 
        WHEN rating >= 4.0 AND ratings_count >= 1000 THEN TRUE
        ELSE FALSE
    END
    WHERE rating IS NOT NULL AND ratings_count IS NOT NULL;
END;
$$ LANGUAGE plpgsql;

-- Datos iniciales para ESRB
INSERT INTO esrb_ratings (id, name) VALUES
    (1, 'Everyone'), (2, 'Everyone 10+'), (3, 'Teen'),
    (4, 'Mature'), (5, 'Adults Only'), (6, 'Rating Pending')
ON CONFLICT (id) DO NOTHING;

-- FIN DEL SCRIPT PARA RDS
