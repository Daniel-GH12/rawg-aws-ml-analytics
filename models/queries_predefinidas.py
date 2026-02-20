"""
Queries SQL predefinidas para exploración, feature extraction y análisis
"""

# ==========================================
# QUERIES EXPLORATORIAS
# ==========================================

EXPLORATORY_QUERIES = {
    
    'total_games': """
        SELECT COUNT(*) as total_juegos
        FROM games;
    """,
    
    'general_stats': """
        SELECT 
            COUNT(*) as total_juegos,
            COUNT(rating) as con_rating,
            COUNT(metacritic) as con_metacritic,
            COUNT(esrb_rating_id) as con_esrb,
            ROUND(AVG(rating)::numeric, 2) as avg_rating,
            ROUND(AVG(metacritic)::numeric, 2) as avg_metacritic,
            ROUND(AVG(ratings_count)::numeric, 0) as avg_ratings_count,
            ROUND(AVG(added)::numeric, 0) as avg_added
        FROM games;
    """,
    
    'rating_distribution': """
        SELECT 
            CASE 
                WHEN rating >= 4.5 THEN 'Excelente (4.5+)'
                WHEN rating >= 4.0 THEN 'Muy Bueno (4.0-4.5)'
                WHEN rating >= 3.0 THEN 'Bueno (3.0-4.0)'
                ELSE 'Regular (<3.0)'
            END as categoria_rating,
            COUNT(*) as cantidad_juegos,
            ROUND(AVG(metacritic)::numeric, 2) as avg_metacritic,
            ROUND(AVG(ratings_count)::numeric, 0) as avg_ratings_count,
            ROUND(AVG(added)::numeric, 0) as avg_added
        FROM games
        WHERE rating IS NOT NULL
        GROUP BY 
            CASE 
                WHEN rating >= 4.5 THEN 'Excelente (4.5+)'
                WHEN rating >= 4.0 THEN 'Muy Bueno (4.0-4.5)'
                WHEN rating >= 3.0 THEN 'Bueno (3.0-4.0)'
                ELSE 'Regular (<3.0)'
            END
        ORDER BY categoria_rating DESC;
    """,
    
   
    
    'null_analysis': """
        SELECT 
            'rating' as campo,
            COUNT(*) FILTER (WHERE rating IS NULL) as nulos,
            COUNT(*) FILTER (WHERE rating IS NOT NULL) as no_nulos,
            ROUND(100.0 * COUNT(*) FILTER (WHERE rating IS NULL) / COUNT(*), 2) as porcentaje_nulos
        FROM games
        
        UNION ALL
        
        SELECT 
            'released',
            COUNT(*) FILTER (WHERE released IS NULL),
            COUNT(*) FILTER (WHERE released IS NOT NULL),
            ROUND(100.0 * COUNT(*) FILTER (WHERE released IS NULL) / COUNT(*), 2)
        FROM games
        
        UNION ALL
        
        SELECT 
            'esrb_rating_id',
            COUNT(*) FILTER (WHERE esrb_rating_id IS NULL),
            COUNT(*) FILTER (WHERE esrb_rating_id IS NOT NULL),
            ROUND(100.0 * COUNT(*) FILTER (WHERE esrb_rating_id IS NULL) / COUNT(*), 2)
        FROM games;
    """,
    
    'top_genres': """
        SELECT 
            g.name as genero,
            COUNT(*) as num_juegos,
            ROUND(AVG(ga.rating)::numeric, 2) as avg_rating
        FROM genres g
        JOIN game_genres gg ON g.id = gg.genre_id
        JOIN games ga ON gg.game_id = ga.id
        WHERE ga.rating IS NOT NULL
        GROUP BY g.name
        ORDER BY num_juegos DESC
        LIMIT 15;
    """,
    
    'top_platforms': """
        SELECT 
            p.name as plataforma,
            COUNT(*) as num_juegos,
            ROUND(AVG(g.rating)::numeric, 2) as avg_rating
        FROM platforms p
        JOIN game_platforms gp ON p.id = gp.platform_id
        JOIN games g ON gp.game_id = g.id
        WHERE g.rating IS NOT NULL
        GROUP BY p.name
        ORDER BY num_juegos DESC
        LIMIT 15;
    """,
    
    'games_by_year': """
        SELECT 
            EXTRACT(YEAR FROM released) as año,
            COUNT(*) as num_juegos,
            ROUND(AVG(rating)::numeric, 2) as avg_rating,
            ROUND(AVG(metacritic)::numeric, 2) as avg_metacritic
        FROM games
        WHERE released IS NOT NULL
        GROUP BY EXTRACT(YEAR FROM released)
        HAVING EXTRACT(YEAR FROM released) >= 2000
        ORDER BY año DESC;
    """,
    
    'top_tags': """
        SELECT 
            t.name as tag,
            COUNT(*) as num_juegos,
            ROUND(AVG(g.rating)::numeric, 2) as avg_rating
        FROM tags t
        JOIN game_tags gt ON t.id = gt.tag_id
        JOIN games g ON gt.game_id = g.id
        WHERE g.rating IS NOT NULL
        GROUP BY t.name
        ORDER BY num_juegos DESC
        LIMIT 20;
    """
}


# ==========================================
# QUERY PARA ANÁLISIS DE TARGET
# ==========================================

TARGET_ANALYSIS_QUERY = """
    SELECT 
        COUNT(*) as total_juegos,
        
        -- Opción 1: Rating >= 4.0
        COUNT(*) FILTER (WHERE rating >= 4.0) as exito_rating_4,
        ROUND(100.0 * COUNT(*) FILTER (WHERE rating >= 4.0) / COUNT(*), 2) as pct_exito_rating_4,
        
        -- Opción 2: Rating >= 4.0 AND ratings_count >= 100
        COUNT(*) FILTER (WHERE rating >= 4.0 AND ratings_count >= 100) as exito_rating_4_y_100votos,
        ROUND(100.0 * COUNT(*) FILTER (WHERE rating >= 4.0 AND ratings_count >= 100) / COUNT(*), 2) as pct_exito_rating_4_y_100votos,
        
        -- Opción 3: Metacritic >= 75
        COUNT(*) FILTER (WHERE metacritic >= 75) as exito_metacritic_75,
        ROUND(100.0 * COUNT(*) FILTER (WHERE metacritic >= 75) / NULLIF(COUNT(*) FILTER (WHERE metacritic IS NOT NULL), 0), 2) as pct_exito_metacritic_75,
        
        -- Opción 4: Combinado
        COUNT(*) FILTER (WHERE (rating >= 4.0 AND ratings_count >= 50) OR metacritic >= 80) as exito_combinado,
        ROUND(100.0 * COUNT(*) FILTER (WHERE (rating >= 4.0 AND ratings_count >= 50) OR metacritic >= 80) / COUNT(*), 2) as pct_exito_combinado
        
    FROM games
    WHERE rating IS NOT NULL 
      AND released IS NOT NULL;
"""


# ==========================================
# QUERY PARA EXTRACCIÓN DE FEATURES
# ==========================================

FEATURE_EXTRACTION_QUERY = """
    SELECT 
        g.id,
        g.name,
        g.slug,
        g.released,
        g.tba,
        g.rating,
        g.rating_top,
        g.ratings_count,
        g.reviews_text_count,
        g.added,
        g.playtime,
        g.suggestions_count,
        g.esrb_rating_id,
        er.name as esrb_rating_name,
        
        -- Features derivadas de fecha
        EXTRACT(YEAR FROM g.released) as release_year,
        EXTRACT(MONTH FROM g.released) as release_month,
        EXTRACT(DOW FROM g.released) as release_day_of_week,
        EXTRACT(QUARTER FROM g.released) as release_quarter,
        
        -- Antigüedad del juego en años
        EXTRACT(YEAR FROM AGE(CURRENT_DATE, g.released)) as game_age_years,
        
        -- Conteos de relaciones
        COUNT(DISTINCT gg.genre_id) as num_genres,
        COUNT(DISTINCT gp.platform_id) as num_platforms,
        COUNT(DISTINCT gt.tag_id) as num_tags,
        
        -- Features derivadas (ratios)
        CASE 
            WHEN g.ratings_count > 0 
            THEN ROUND((g.reviews_text_count::numeric / g.ratings_count::numeric), 4)
            ELSE 0 
        END as review_to_rating_ratio,
        
        CASE 
            WHEN g.added > 0 
            THEN ROUND((g.ratings_count::numeric / g.added::numeric), 4)
            ELSE 0 
        END as rating_to_added_ratio
        
    FROM games g
    LEFT JOIN esrb_ratings er ON g.esrb_rating_id = er.id
    LEFT JOIN game_genres gg ON g.id = gg.game_id
    LEFT JOIN game_platforms gp ON g.id = gp.game_id
    LEFT JOIN game_tags gt ON g.id = gt.game_id
    WHERE g.rating IS NOT NULL 
      AND g.released IS NOT NULL
    GROUP BY 
        g.id, g.name, g.slug, g.released, g.tba, g.rating, g.rating_top, 
        g.ratings_count, g.reviews_text_count, g.added, g.metacritic, 
        g.playtime, g.suggestions_count, g.esrb_rating_id, er.name
    ORDER BY g.released DESC;
"""



