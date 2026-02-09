# ==============================================
# === SCRIPT CREACIÓN DE BASE DE DATOS LOCAL ===
# ==============================================

def create_rawg_local_database(verbose = True):
    """
    Crea database a partir de DataFrames normalizados
    
    Args:
        verbose: bool, si False no imprime mensajes de progreso
    """
    
    import psycopg2
    from psycopg2 import sql

    if verbose:
        print("="*60)
        print("INICIANDO CREACIÓN DE BASE DE DATOS LOCAL...")
        print("="*60)
    
    # === 1. CREAR BASE DE DATOS LOCAL SI NO EXISTE ===
    # ==============================================
    if verbose:
        print("\n1: Verificando/creando base de datos...")
    
    
    try:
        # Inicializar Connector
        database = "rawg_db_local"
    
        db = psycopg2.connect(host     = "localhost",
                              user     = "postgres",
                              password = "sql123",
                              port     = 5432,
                              database = None)
        # Iniciar Cursor
        cursor = db.cursor()
        
        # Activar autocommit para poder ejecutar la función CREATE_DATABASE
        db.autocommit = True
        
        # Verificar si la base de datos ya existe (creada con anterioridad)
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database,))
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))  
            if verbose:
                print("Base de datos creada con éxito")
        else:
            if verbose:
                print("Base de datos ya existe")
        
        # Finalizar Cursor - Cierra el cursor
        cursor.close()
        
        # Finalizar Connector
        db.close()
        
    except Exception as e:
        print(f"Error al crear base de datos: {e}")
        return False   
    
    # === 2. CREAR ESQUEMA (SINTÁXIS SQl) Y TABLAS ===
    # ================================================
    if verbose:
        print("2. Creando esquema y tablas...")
    
    schema_sql = """
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
    """  
  
    try:
        database = "rawg_db_local"
    
        db = psycopg2.connect(host     = "localhost",
                              user     = "postgres",
                              password = "sql123",
                              port     = 5432,
                              database = database)
        cursor = db.cursor()
    
        cursor.execute(schema_sql)
    
        db.commit()
    
        cursor.close()
        db.close()
       
        if verbose:
            print("Esquema 'rawg' y tablas creadas con éxito")
        return True
        
    except Exception as e:
        print(f"Error al crear tablas: {e}")
        return False

if ___name__ == "__main__":
    create_rawg_local_database(verbose = True)