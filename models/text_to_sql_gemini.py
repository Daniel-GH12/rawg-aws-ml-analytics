"""
Generación de SQL usando Gemini API
Proyecto: rawg-aws-ml-analytics
"""

import google.generativeai as genai
import os
from typing import Optional

# Configurar Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY no configurada en variables de entorno")

genai.configure(api_key=GEMINI_API_KEY)

# Usar modelo disponible
model = genai.GenerativeModel('models/gemini-2.5-flash')

# Schema de la BD
DB_SCHEMA = os.getenv("DB_SCHEMA", "rawg")

# ============================================================================
# ESQUEMA DE LA BASE DE DATOS
# ============================================================================

DATABASE_SCHEMA = f"""
Base de datos PostgreSQL - Schema: {DB_SCHEMA}

════════════════════════════════════════════════════════════════════════════
TABLAS DE DIMENSIONES / CATÁLOGOS
════════════════════════════════════════════════════════════════════════════

1. {DB_SCHEMA}.esrb_ratings
   - esrb_id (INT, PK)
   - esrb_name (VARCHAR 100)

2. {DB_SCHEMA}.platforms
   - platform_id (INT, PK)
   - platform_name (VARCHAR 200)

3. {DB_SCHEMA}.genres
   - genre_id (INT, PK)
   - genre_name (VARCHAR 100)
   - genre_games_count (BIGINT)

4. {DB_SCHEMA}.stores
   - store_id (INT, PK)
   - store_name (VARCHAR 200)

5. {DB_SCHEMA}.tags
   - tag_id (BIGINT, PK)
   - tag_name (VARCHAR 200)
   - tag_language (VARCHAR 50)
   - tag_games_count (BIGINT)

════════════════════════════════════════════════════════════════════════════
TABLA PRINCIPAL: {DB_SCHEMA}.games
════════════════════════════════════════════════════════════════════════════

Columnas:
- game_id (BIGINT, PK)
- game_name (VARCHAR 500)
- tba (BOOLEAN)
- released_ym (CHAR 7) - Formato "YYYY-MM"
- updated_ym (CHAR 7)
- game_rating (NUMERIC 4,2) - Rating 0.00-5.00
- ratings_count (BIGINT)
- game_added (BIGINT) - Veces agregado
- playtime (INTEGER)
- suggestions_count (BIGINT)
- esrb_id (INT, FK)
- created_at (TIMESTAMP)

════════════════════════════════════════════════════════════════════════════
TABLA: {DB_SCHEMA}.games_status
════════════════════════════════════════════════════════════════════════════

- game_id (BIGINT, PK/FK)
- yet, owned, beaten, toplay, dropped, playing (BIGINT)

════════════════════════════════════════════════════════════════════════════
TABLAS DE RELACIÓN N:M
════════════════════════════════════════════════════════════════════════════

- {DB_SCHEMA}.game_platforms (game_id, platform_id, released_at)
- {DB_SCHEMA}.game_genres (game_id, genre_id)
- {DB_SCHEMA}.game_stores (game_id, store_id)
- {DB_SCHEMA}.game_tags (game_id, tag_id)

"""


# ============================================================================
# FUNCIONES DE VALIDACIÓN
# ============================================================================

def validate_sql_security(sql: str) -> bool:
    """Valida que el SQL sea seguro (solo SELECT)"""
    sql_lower = sql.lower().strip()
    
    if not sql_lower.startswith('select'):
        return False
    
    forbidden = ['drop', 'delete', 'update', 'insert', 'alter', 'truncate', 'create']
    return not any(word in sql_lower for word in forbidden)


# ============================================================================
# GENERACIÓN DE SQL PARA VISUALIZACIÓN
# ============================================================================

def generate_sql_for_visual(question: str) -> Optional[str]:
    """
    Genera SQL para visualización (debe retornar columnas label y value)
    
    Args:
        question: Pregunta del usuario
        
    Returns:
        SQL query o None si falla
    """
    
    prompt = f"""Eres experto en SQL PostgreSQL para visualización de datos de videojuegos.

ESQUEMA:
{DATABASE_SCHEMA}

PREGUNTA: {question}

REQUISITOS ESTRICTOS:
1. SOLO SQL PostgreSQL, sin markdown ni explicaciones
2. Retornar columnas "label" (TEXT) y "value" (NUMERIC/BIGINT)
3. Schema "{DB_SCHEMA}"
4. NOMBRES: game_rating, game_added, released_ym, game_name
5. Rankings: ORDER BY value DESC LIMIT 10
6. Series: ORDER BY label
7. NO usar DROP, DELETE, UPDATE, INSERT
8. Conteos: ::bigint, Promedios: ROUND(..., 2)

EJEMPLOS:

-- Top géneros
SELECT g.genre_name AS label, COUNT(*)::bigint AS value
FROM {DB_SCHEMA}.game_genres gg
JOIN {DB_SCHEMA}.genres g ON g.genre_id = gg.genre_id
GROUP BY g.genre_name
ORDER BY value DESC LIMIT 10;

-- Juegos por año desde 2015
SELECT SUBSTRING(released_ym, 1, 4) AS label, COUNT(*)::bigint AS value
FROM {DB_SCHEMA}.games
WHERE released_ym IS NOT NULL AND SUBSTRING(released_ym, 1, 4)::integer >= 2015
GROUP BY SUBSTRING(released_ym, 1, 4)
ORDER BY label;

-- Rating promedio por año
SELECT SUBSTRING(released_ym, 1, 4) AS label, ROUND(AVG(game_rating)::numeric, 2) AS value
FROM {DB_SCHEMA}.games
WHERE released_ym IS NOT NULL AND game_rating IS NOT NULL
GROUP BY SUBSTRING(released_ym, 1, 4)
ORDER BY label;

SQL:"""

    try:
        response = model.generate_content(prompt)
        sql = response.text.strip().replace('```sql', '').replace('```', '').strip()
        
        if not validate_sql_security(sql):
            return None
        
        return sql
        
    except Exception as e:
        print(f"Error generando SQL: {e}")
        return None


# ============================================================================
# GENERACIÓN DE SQL PARA RESPUESTA TEXTUAL
# ============================================================================

def generate_sql_for_text(question: str) -> Optional[str]:
    """
    Genera SQL para respuesta textual (columnas flexibles)
    
    Args:
        question: Pregunta del usuario
        
    Returns:
        SQL query o None si falla
    """
    
    prompt = f"""Eres experto en SQL PostgreSQL para análisis de videojuegos.

ESQUEMA:
{DATABASE_SCHEMA}

PREGUNTA: {question}

REQUISITOS:
1. SOLO SQL, sin markdown
2. Columnas descriptivas
3. Schema "{DB_SCHEMA}"
4. NOMBRES: game_rating, game_added, released_ym, game_name
5. LIMIT 20 máximo
6. NO usar DROP, DELETE, UPDATE, INSERT
7. Conteos: ::bigint, Promedios: ROUND(..., 2)

EJEMPLOS:

-- ¿Cuál es el juego mejor valorado?
SELECT game_name AS juego, game_rating AS puntuacion, ratings_count AS votos
FROM {DB_SCHEMA}.games
WHERE game_rating IS NOT NULL
ORDER BY game_rating DESC, ratings_count DESC LIMIT 1;

-- ¿Cuántos juegos hay?
SELECT COUNT(*)::bigint AS total FROM {DB_SCHEMA}.games;

-- ¿Qué género tiene mejor rating?
SELECT g.genre_name AS genero, ROUND(AVG(ga.game_rating)::numeric, 2) AS rating_avg
FROM {DB_SCHEMA}.game_genres gg
JOIN {DB_SCHEMA}.genres g ON g.genre_id = gg.genre_id
JOIN {DB_SCHEMA}.games ga ON ga.game_id = gg.game_id
WHERE ga.game_rating IS NOT NULL
GROUP BY g.genre_name
HAVING COUNT(*) >= 10
ORDER BY rating_avg DESC LIMIT 1;

SQL:"""

    try:
        response = model.generate_content(prompt)
        sql = response.text.strip().replace('```sql', '').replace('```', '').strip()
        
        if not validate_sql_security(sql):
            return None
        
        return sql
        
    except Exception as e:
        print(f"Error: {e}")
        return None


# ============================================================================
# GENERACIÓN DE RESPUESTA EN LENGUAJE NATURAL
# ============================================================================

def generate_text_response(question: str, data_summary: str) -> str:
    """
    Genera respuesta en lenguaje natural
    
    Args:
        question: Pregunta original
        data_summary: Datos en formato texto
        
    Returns:
        Respuesta textual
    """
    
    prompt = f"""Eres asistente de análisis de videojuegos.

PREGUNTA: {question}

DATOS:
{data_summary}

INSTRUCCIONES:
1. Responde clara y concisamente (3-4 oraciones)
2. Usa datos específicos
3. Top 3-5 si hay muchos resultados
4. Tono profesional y amigable
5. NO inventes datos

Respuesta:"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Datos obtenidos correctamente. Ver tabla de resultados para detalles."