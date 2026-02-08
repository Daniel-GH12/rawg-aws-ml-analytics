
"""
Lambda ETL Pipeline COMPLETO para RAWG
- Borra y recrea el esquema (solo para carga histórica)
- Lee JSON desde S3
- Transforma datos
- Carga a RDS con INSERT o UPSERT según el archivo
"""

import json
import boto3
import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

# Importar función de transformación
from transform_rawg import transf_rawg_data

def get_rds_credentials():
    """Obtiene credenciales desde Secrets Manager"""
    client = boto3.client('secretsmanager')
    secret = client.get_secret_value(SecretId='Postgre')
    return json.loads(secret['SecretString'])

# SQL para recrear esquema completo
SCHEMA_SQL = """
DROP SCHEMA IF EXISTS rawg CASCADE;
CREATE SCHEMA rawg;

-- =========================
-- DIMENSIONES / CATÁLOGOS
-- =========================

CREATE TABLE rawg.esrb_ratings (
  esrb_id   INT PRIMARY KEY,
  esrb_name VARCHAR(100) NOT NULL
);

CREATE TABLE rawg.platforms (
  platform_id   INT PRIMARY KEY,
  platform_name VARCHAR(200) NOT NULL
);

CREATE TABLE rawg.genres (
  genre_id          INT PRIMARY KEY,
  genre_name        VARCHAR(100) NOT NULL,
  genre_games_count BIGINT
);

CREATE TABLE rawg.stores (
  store_id   INT PRIMARY KEY,
  store_name VARCHAR(200) NOT NULL
);

CREATE TABLE rawg.tags (
  tag_id          BIGINT PRIMARY KEY,
  tag_name        VARCHAR(200) NOT NULL,
  tag_language    VARCHAR(50),
  tag_games_count BIGINT
);

-- =========================
-- HECHO PRINCIPAL
-- =========================

CREATE TABLE rawg.games (
  game_id           BIGINT PRIMARY KEY,
  game_name         VARCHAR(500) NOT NULL,
  tba               BOOLEAN,
  released_ym       CHAR(7),
  updated_ym        CHAR(7),
  game_rating       NUMERIC(4,2),
  ratings_count     BIGINT,
  game_added        BIGINT,
  playtime          INTEGER,
  suggestions_count BIGINT,
  esrb_id           INT NULL,
  created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_games_esrb
    FOREIGN KEY (esrb_id) REFERENCES rawg.esrb_ratings(esrb_id)
);

CREATE TABLE rawg.games_status (
  game_id BIGINT PRIMARY KEY
    REFERENCES rawg.games(game_id) ON DELETE CASCADE,
  yet     BIGINT NOT NULL DEFAULT 0,
  owned   BIGINT NOT NULL DEFAULT 0,
  beaten  BIGINT NOT NULL DEFAULT 0,
  toplay  BIGINT NOT NULL DEFAULT 0,
  dropped BIGINT NOT NULL DEFAULT 0,
  playing BIGINT NOT NULL DEFAULT 0
);

CREATE TABLE rawg.ratings_distribution (
  game_id         BIGINT NOT NULL,
  ratingd_id      INT NOT NULL,
  ratingd_title   VARCHAR(50),
  ratingd_count   BIGINT DEFAULT 0,
  ratingd_percent NUMERIC(6,2) DEFAULT 0.0,
  PRIMARY KEY (game_id, ratingd_id),
  FOREIGN KEY (game_id) REFERENCES rawg.games(game_id) ON DELETE CASCADE
);

-- =========================
-- RELACIONES N:M (BRIDGES)
-- =========================

CREATE TABLE rawg.game_platforms (
  game_id     BIGINT NOT NULL,
  platform_id INT NOT NULL,
  released_at VARCHAR(10),
  PRIMARY KEY (game_id, platform_id),
  FOREIGN KEY (game_id) REFERENCES rawg.games(game_id) ON DELETE CASCADE,
  FOREIGN KEY (platform_id) REFERENCES rawg.platforms(platform_id) ON DELETE CASCADE
);

CREATE TABLE rawg.game_genres (
  game_id  BIGINT NOT NULL,
  genre_id INT NOT NULL,
  PRIMARY KEY (game_id, genre_id),
  FOREIGN KEY (game_id) REFERENCES rawg.games(game_id) ON DELETE CASCADE,
  FOREIGN KEY (genre_id) REFERENCES rawg.genres(genre_id) ON DELETE CASCADE
);

CREATE TABLE rawg.game_stores (
  game_id  BIGINT NOT NULL,
  store_id INT NOT NULL,
  PRIMARY KEY (game_id, store_id),
  FOREIGN KEY (game_id) REFERENCES rawg.games(game_id) ON DELETE CASCADE,
  FOREIGN KEY (store_id) REFERENCES rawg.stores(store_id) ON DELETE CASCADE
);

CREATE TABLE rawg.game_tags (
  game_id BIGINT NOT NULL,
  tag_id  BIGINT NOT NULL,
  PRIMARY KEY (game_id, tag_id),
  FOREIGN KEY (game_id) REFERENCES rawg.games(game_id) ON DELETE CASCADE,
  FOREIGN KEY (tag_id) REFERENCES rawg.tags(tag_id) ON DELETE CASCADE
);

-- =========================
-- ÍNDICES
-- =========================

CREATE INDEX ix_games_released ON rawg.games(released_ym);
CREATE INDEX ix_games_esrb_id ON rawg.games(esrb_id);
CREATE INDEX ix_ratings_distribution_game ON rawg.ratings_distribution(game_id);
CREATE INDEX ix_game_platforms_platform ON rawg.game_platforms(platform_id);
CREATE INDEX ix_game_genres_genre ON rawg.game_genres(genre_id);
CREATE INDEX ix_game_stores_store ON rawg.game_stores(store_id);
CREATE INDEX ix_game_tags_tag ON rawg.game_tags(tag_id);
"""

# Configuración de tablas
TABLA_CONFIG = {
    'orden_carga': [
        'esrb_ratings', 'platforms', 'genres', 'stores', 'tags',
        'games', 'games_status', 'ratings_distribution',
        'game_platforms', 'game_genres', 'game_stores', 'game_tags'
    ],
    
    'primary_keys': {
        'esrb_ratings': ['esrb_id'],
        'platforms': ['platform_id'],
        'genres': ['genre_id'],
        'stores': ['store_id'],
        'tags': ['tag_id'],
        'games': ['game_id'],
        'games_status': ['game_id'],
        'ratings_distribution': ['game_id', 'ratingd_id'],
        'game_platforms': ['game_id', 'platform_id'],
        'game_genres': ['game_id', 'genre_id'],
        'game_stores': ['game_id', 'store_id'],
        'game_tags': ['game_id', 'tag_id']
    },
    
    'columnas': {
        'esrb_ratings': ['esrb_id', 'esrb_name'],
        'platforms': ['platform_id', 'platform_name'],
        'genres': ['genre_id', 'genre_name', 'genre_games_count'],
        'stores': ['store_id', 'store_name'],
        'tags': ['tag_id', 'tag_name', 'tag_language', 'tag_games_count'],
        'games': ['game_id', 'game_name', 'tba', 'released_ym', 'updated_ym',
                  'game_rating', 'ratings_count', 'game_added', 'playtime',
                  'suggestions_count', 'esrb_id'],
        'games_status': ['game_id', 'yet', 'owned', 'beaten', 'toplay', 'dropped', 'playing'],
        'ratings_distribution': ['game_id', 'ratingd_id', 'ratingd_title',
                                 'ratingd_count', 'ratingd_percent'],
        'game_platforms': ['game_id', 'platform_id', 'released_at'],
        'game_genres': ['game_id', 'genre_id'],
        'game_stores': ['game_id', 'store_id'],
        'game_tags': ['game_id', 'tag_id']
    }
}

def recrear_esquema(creds):
    """Borra y recrea el esquema completo en RDS"""
    print(" Borrando esquema existente...")
    print(" Creando esquema limpio...")
    
    conn = None
    try:
        conn = psycopg2.connect(
            user=creds["username"],
            password=creds["password"],
            host=creds["host"],
            port=creds["port"],
            dbname=creds["dbname"],
            sslmode="require"
        )
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(SCHEMA_SQL)
        cur.close()
        conn.close()
        
        print(" Esquema recreado exitosamente")
        
    except Exception as e:
        print(f" Error recreando esquema: {e}")
        if conn:
            conn.close()
        raise

def limpiar_foreign_keys(dataframes):
    """Limpia foreign keys inválidas en games"""
    games = dataframes['games']
    esrb_ratings = dataframes['esrb_ratings']
    
    if not games.empty and 'esrb_id' in games.columns:
        # Convertir 0 a None
        count_zeros = (games['esrb_id'] == 0).sum()
        games['esrb_id'] = games['esrb_id'].replace(0, None)
        
        if count_zeros > 0:
            print(f"    {count_zeros} registros con esrb_id=0 → NULL")
        
        # Validar contra esrb_ratings
        esrb_validos = set(esrb_ratings['esrb_id'].values)
        games_esrb_ids = games['esrb_id'].dropna().unique()
        invalidos = [id for id in games_esrb_ids if id not in esrb_validos]
        
        if invalidos:
            games.loc[games['esrb_id'].isin(invalidos), 'esrb_id'] = None
            print(f"    {len(invalidos)} IDs de ESRB inválidos → NULL")
    
    dataframes['games'] = games
    return dataframes

def upsert_dataframe(engine, df, tabla_nombre, modo='upsert'):
    """Carga un DataFrame con INSERT o UPSERT"""
    if df.empty:
        print(f"     {tabla_nombre}: DataFrame vacío")
        return
    
    # Filtrar columnas esperadas
    columnas_esperadas = TABLA_CONFIG['columnas'][tabla_nombre]
    columnas_disponibles = [col for col in columnas_esperadas if col in df.columns]
    df_limpio = df[columnas_disponibles].copy()
    
    tabla_completa = f"rawg.{tabla_nombre}"
    pk_columns = TABLA_CONFIG['primary_keys'][tabla_nombre]
    temp_table = f"temp_{tabla_nombre}"
    
    try:
        with engine.begin() as conn:
            # Crear tabla temporal
            df_limpio.to_sql(
                temp_table, conn, if_exists='replace',
                index=False, schema='rawg'
            )
            
            columnas_str = ', '.join(columnas_disponibles)
            
            if modo == 'insert':
                # MODO HISTÓRICO: INSERT simple
                sql = f"""
                INSERT INTO {tabla_completa} ({columnas_str})
                SELECT {columnas_str} FROM rawg.{temp_table}
                ON CONFLICT DO NOTHING;
                """
            else:
                # MODO INCREMENTAL: UPSERT
                pk_constraint = ', '.join(pk_columns)
                columnas_update = [col for col in columnas_disponibles if col not in pk_columns]
                
                if columnas_update:
                    set_clause = ', '.join([f"{col} = EXCLUDED.{col}" for col in columnas_update])
                    sql = f"""
                    INSERT INTO {tabla_completa} ({columnas_str})
                    SELECT {columnas_str} FROM rawg.{temp_table}
                    ON CONFLICT ({pk_constraint})
                    DO UPDATE SET {set_clause};
                    """
                else:
                    sql = f"""
                    INSERT INTO {tabla_completa} ({columnas_str})
                    SELECT {columnas_str} FROM rawg.{temp_table}
                    ON CONFLICT DO NOTHING;
                    """
            
            conn.execute(text(sql))
            conn.execute(text(f"DROP TABLE IF EXISTS rawg.{temp_table}"))
            
            print(f"    {tabla_nombre}: {len(df_limpio):,} registros")
            
    except Exception as e:
        print(f"   Error en {tabla_nombre}: {e}")
        raise

def lambda_handler(event, context):
    """
    Handler principal - Pipeline ETL completo
    """
    
    print("=" * 70)
    print(" INICIANDO PIPELINE ETL RAWG")
    print("=" * 70)
    
    try:
        # ==========================================
        # 1. EXTRAER INFORMACIÓN DEL EVENTO S3
        # ==========================================
        
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        
        print(f"\n Archivo detectado: s3://{bucket}/{key}")
        
        # Determinar modo según nombre del archivo
        es_historico = "historica" in key.lower() or "historico" in key.lower()
        modo = 'insert' if es_historico else 'upsert'
        
        if es_historico:
            print(" MODO: Carga histórica completa (INSERT + Recrear esquema)")
        else:
            print(" MODO: Carga incremental (UPSERT)")
        
        # ==========================================
        # 2. OBTENER CREDENCIALES
        # ==========================================
        
        print("\n Obteniendo credenciales de RDS...")
        creds = get_rds_credentials()
        print("    Credenciales obtenidas")
        
        # ==========================================
        # 3. RECREAR ESQUEMA (SOLO PARA HISTÓRICO)
        # ==========================================
        
        if es_historico:
            print("\n  FASE: Recreación de esquema")
            print("-" * 70)
            recrear_esquema(creds)
        
        # ==========================================
        # 4. LEER JSON DESDE S3
        # ==========================================
        
        print("\n FASE: Extracción de datos")
        print("-" * 70)
        s3 = boto3.client('s3')
        obj = s3.get_object(Bucket=bucket, Key=key)
        datos_raw = json.loads(obj['Body'].read())
        print(f"    {len(datos_raw):,} registros leídos desde S3")
        
        # ==========================================
        # 5. TRANSFORMAR DATOS
        # ==========================================
        
        print("\n FASE: Transformación de datos")
        print("-" * 70)
        dataframes = transf_rawg_data(datos_raw, verbose=False)
        
        total_registros = sum(len(df) for df in dataframes.values() if not df.empty)
        print(f"    Transformación completada: {total_registros:,} registros totales")
        
        # ==========================================
        # 6. LIMPIAR FOREIGN KEYS
        # ==========================================
        
        print("\n🧹 FASE: Limpieza de Foreign Keys")
        print("-" * 70)
        dataframes = limpiar_foreign_keys(dataframes)
        
        # ==========================================
        # 7. CONECTAR A RDS
        # ==========================================
        
        print("\n🔌 FASE: Conexión a RDS")
        print("-" * 70)
        engine = create_engine(
            f"postgresql://{creds['username']}:{creds['password']}@"
            f"{creds['host']}:{creds['port']}/{creds['dbname']}",
            poolclass=NullPool,
            connect_args={"sslmode": "require"}
        )
        print("    Engine SQLAlchemy creado")
        
        # ==========================================
        # 8. CARGAR DATOS
        # ==========================================
        
        print(f"\n FASE: Carga de datos ({modo.upper()})")
        print("-" * 70)
        
        registros_cargados = 0
        
        for tabla in TABLA_CONFIG['orden_carga']:
            if tabla in dataframes:
                upsert_dataframe(engine, dataframes[tabla], tabla, modo=modo)
                registros_cargados += len(dataframes[tabla])
        
        # ==========================================
        # 9. RESULTADO FINAL
        # ==========================================
        
        print("\n" + "=" * 70)
        print(" PIPELINE COMPLETADO EXITOSAMENTE")
        print("=" * 70)
        print(f" Registros procesados: {registros_cargados:,}")
        print(f" Tablas actualizadas: {len(TABLA_CONFIG['orden_carga'])}")
        print(f" Modo utilizado: {modo.upper()}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'mensaje': 'Pipeline ETL completado exitosamente',
                'archivo': key,
                'modo': modo,
                'esquema_recreado': es_historico,
                'registros_procesados': registros_cargados,
                'tablas_actualizadas': len(TABLA_CONFIG['orden_carga'])
            }, default=str)
        }
        
    except Exception as e:
        print("\n" + "=" * 70)
        print(" ERROR EN PIPELINE")
        print("=" * 70)
        print(f"Error: {e}")
        
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'traceback': traceback.format_exc()
            })
        }
