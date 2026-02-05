import pandas as pd
from sqlalchemy import create_engine
import os

# Configuración de conexión
DB_USER = "postgres"
DB_PASS = "data-rawg"
DB_HOST = "data-rawg.cfsieqiau5qy.eu-north-1.rds.amazonaws.com"
DB_PORT = "5432"
DB_NAME = "postgres"

def get_data_from_rds():
    # Creamos el motor de conexión
    conn_str = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(conn_str)

    # Traemos el juego y concatenamos sus géneros y plataformas en strings para luego procesarlos en Python
    query = """
    SELECT 
        g.game_id,
        g.game_rating,
        g.playtime,
        g.suggestions_count,
        -- Extraemos el mes de la fecha de lanzamiento
        EXTRACT(MONTH FROM g.game_released) as release_month,
        -- Traemos los nombres de desarrolladores, géneros, plataformas y tags como texto
        STRING_AGG(DISTINCT dev.developer_name, ',') as developers,
        STRING_AGG(DISTINCT gen.genre_name, ',') as genres,
        STRING_AGG(DISTINCT p.platform_name, ',') as platforms,
        STRING_AGG(DISTINCT t.tag_name, ',') as tags
    FROM games g
    LEFT JOIN games_developers gd ON g.game_id = gd.game_id
    LEFT JOIN developers dev ON gd.developer_id = dev.developer_id
    LEFT JOIN games_genres gg ON g.game_id = gg.game_id
    LEFT JOIN genres gen ON gg.genre_id = gen.genre_id
    LEFT JOIN games_platforms gp ON g.game_id = gp.game_id
    LEFT JOIN platforms p ON gp.platform_id = p.platform_id
    LEFT JOIN games_tags gt ON g.game_id = gt.game_id
    LEFT JOIN tags t ON gt.tag_id = t.tag_id
    WHERE g.rating_count > 5
    GROUP BY g.game_id;
    """

    print("Conectando a RDS y extrayendo datos...")
    df = pd.read_sql(query, engine)
    
    # Guardado
    output_path = "./data/raw_dataset.csv"
    os.makedirs("./data", exist_ok=True)
    df.to_csv(output_path, index=False)
    
    print(f"Extracción completada. Dataset guardado en: {output_path}")
    print(f"Total de registros extraídos: {len(df)}")
    
    return df

if __name__ == "__main__":
    get_data_from_rds()