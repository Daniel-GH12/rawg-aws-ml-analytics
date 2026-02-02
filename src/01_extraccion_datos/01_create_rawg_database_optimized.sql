-- PASO 1: CREAR BASE DE DATOS (ejecutar primero en PgAdmin4)
-- CREATE DATABASE rawg_games_db
-- PASO 2: CONECTARSE A LA BASE DE DATOS

-- PASO 3: CREAR TABLAS MAESTRAS

-- TABLA: esrb_ratings (clasificación por edad)
CREATE TABLE IF NOT EXISTS esrb_ratings (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- TABLA: genres (géneros de videojuegos)
CREATE TABLE IF NOT EXISTS genres (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- TABLA: platforms (plataformas de videojuegos)
CREATE TABLE IF NOT EXISTS platforms (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- PASO 4: CREAR TABLA PRINCIPAL (games) - CON ENGAGEMENT REAL

CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    released DATE,
    
    -- Métricas de valoración (features para ML)
    rating NUMERIC(3,2),          -- Puntuación promedio (0.00-5.00)
    ratings_count INTEGER,        -- Número total de votos
    metacritic INTEGER,           -- Puntuación Metacritic (0-100)
    playtime INTEGER,             -- Tiempo promedio de juego (minutos)
    
    -- Engagement real de usuarios (features únicos para ML)
    status_yet INTEGER DEFAULT 0,      -- Por jugar (backlog)
    status_owned INTEGER DEFAULT 0,    -- En biblioteca (comprado/poseído)
    status_beaten INTEGER DEFAULT 0,   -- Completado (100%)
    status_toplay INTEGER DEFAULT 0,   -- En lista de deseos
    status_dropped INTEGER DEFAULT 0,  -- Abandonado (empezado y dejado)
    status_playing INTEGER DEFAULT 0,  -- Jugando ahora mismo
    
    -- Métrica de éxito (variable objetivo para ML)
    success BOOLEAN DEFAULT FALSE,
    
    -- Clasificación por edad
    esrb_rating_id INTEGER REFERENCES esrb_ratings(id) ON DELETE SET NULL,
    
    -- Auditoría
    updated TIMESTAMP
);

-- Índices para optimización de consultas
CREATE INDEX IF NOT EXISTS idx_games_rating ON games(rating DESC);
CREATE INDEX IF NOT EXISTS idx_games_metacritic ON games(metacritic DESC);
CREATE INDEX IF NOT EXISTS idx_games_released ON games(released DESC);
CREATE INDEX IF NOT EXISTS idx_games_success ON games(success);
CREATE INDEX IF NOT EXISTS idx_games_esrb ON games(esrb_rating_id);

-- PASO 5: CREAR TABLAS DE RELACIÓN (N:M)

-- Relación juegos-géneros
CREATE TABLE IF NOT EXISTS game_genres (
    game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    genre_id INTEGER NOT NULL REFERENCES genres(id) ON DELETE CASCADE,
    PRIMARY KEY (game_id, genre_id)
);

-- Relación juegos-plataformas
CREATE TABLE IF NOT EXISTS game_platforms (
    game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    platform_id INTEGER NOT NULL REFERENCES platforms(id) ON DELETE CASCADE,
    released_at DATE,  -- Fecha de lanzamiento en esta plataforma
    PRIMARY KEY (game_id, platform_id)
);

-- Índices para relaciones
CREATE INDEX IF NOT EXISTS idx_game_genres_genre ON game_genres(genre_id);
CREATE INDEX IF NOT EXISTS idx_game_platforms_platform ON game_platforms(platform_id);

-- PASO 6: VISTA PARA ENTRENAMIENTO DEL MODELO DE ML

CREATE OR REPLACE VIEW games_for_ml AS
SELECT 
    g.id,
    g.name,
    EXTRACT(YEAR FROM g.released) AS release_year,
    g.rating,
    g.ratings_count,
    g.metacritic,
    g.playtime,
    g.status_yet,
    g.status_owned,
    g.status_beaten,
    g.status_toplay,
    g.status_dropped,
    g.status_playing,
    g.success,
    er.name AS esrb_rating,
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

-- PASO 7: FUNCIÓN PARA CALCULAR MÉTRICA DE ÉXITO

-- Éxito = TRUE si: rating >= 4.0 Y ratings_count >= 1000
-- (Métrica simple basada SOLO en números, como pidió el profesor)
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

-- PASO 8: DATOS DE EJEMPLO PARA ESRB_RATINGS (para evitar errores en inserciones)

INSERT INTO esrb_ratings (id, name) VALUES
    (1, 'Everyone'),
    (2, 'Everyone 10+'),
    (3, 'Teen'),
    (4, 'Mature'),
    (5, 'Adults Only'),
    (6, 'Rating Pending')
ON CONFLICT (id) DO NOTHING;

-- FIN DEL SCRIPT
-- ✅ PARA EJECUTAR EN PGADMIN4:
--    1. Abrir Query Tool
--    2. Conectarse a base de datos 'rawg_games_db'
--    3. Pegar este script completo
--    4. Ejecutar con F5
--    5. Verificar que las 6 tablas se crearon correctamente
-- ============================================================================
-- ✅ PARA USAR LA MÉTRICA DE ÉXITO:
--    SELECT calculate_success();
--    SELECT * FROM games WHERE success = TRUE LIMIT 10;
-- ============================================================================
