import json
import pandas as pd

# === FUNCIÓN TRANSFORMACIÓN COMPLETA ===

# === FUNCIONES AUXILIARES DE EXTRACCIÓN ===

def extraer_campos_simples(game):
    #  Extrae campos simples

    # Extraer fechas y convertir a formato mes-año
    released_rawg = game.get('released')
    updated_rawg = game.get('updated') 

    released_ym = None
    if released_rawg:
        released_ym = pd.to_datetime(released_rawg, errors="coerce")
        released_ym = released_ym.strftime('%Y-%m') if pd.notna(released_ym) else None

    updated_ym = None
    if updated_rawg:
        updated_ym = pd.to_datetime(updated_rawg, errors="coerce")
        updated_ym = updated_ym.strftime('%Y-%m') if pd.notna(updated_ym) else None
    
    # ESRB rating
    # ESRB rating
    esrb_rating = game.get('esrb_rating')
    
    return {
        # IDENTIFICADORES BÁSICOS
        "game_id": game.get("id"),                            # id juego (int)
        "game_name": game.get("name"),                        # nombre del juego
        "tba": game.get("tba"),                                         # To Be Announced
        # CAMPOS TEMPORALES 
        "released_ym": released_ym,                           # Fecha lanzamiento (formato año - mes)
        "updated_ym": updated_ym,                             # Última actualización (formato año - mes)
        # MÉTRICAS DE VALORACIÓN
        "game_rating": game.get("rating"),                     # Puntuación promedio
        "ratings_count": game.get("ratings_count") if "ratings_count" in game else game.get("ratings_count"),     # Número total de valoraciones
        # MÉTRICAS DE ENGAGEMENT
        "game_added" : game.get("added"),                      # Usuarios que añadieron el juego
        "playtime" : game.get("playtime"),                     # Tiempo juego promedio
        "suggestions_count" : game.get("suggestions_count"),     # Número de recomendaciones
        # FK ESRB (SÓLO ID)
        "esrb_id" : esrb_rating.get('id') if esrb_rating else None,
        }
def extraer_games_status(game):
    # Extrae el estado de juego (yet, owned, beaten, etc.) para la tabla GAMES_STATUS
    game_id = game.get('id')
    added_by_status = game.get('added_by_status') or {}
    
    # Devolver UN SOLO DICCIONARIO
    return {
        'game_id': game_id,
        'yet': added_by_status.get('yet', 0),
        'owned': added_by_status.get('owned', 0),
        'beaten': added_by_status.get('beaten', 0),
        'toplay': added_by_status.get('toplay', 0),
        'dropped': added_by_status.get('dropped', 0),
        'playing': added_by_status.get('playing', 0)
    }

def extraer_esrb_ratings(game):
    # Extrae información ESRB del juego
    esrb_rating = game.get('esrb_rating') or {}
    
    # Si no tiene ESRB, devolver None
    if not esrb_rating or not esrb_rating.get('id'):
        return None
    
    # Devolver diccionario con info ESRB
    return {
        'esrb_id': esrb_rating.get('id'),
        'esrb_name': esrb_rating.get('name'),
    }       

def extraer_ratings_distribution(game):
# Extrae los ratings_distribution (lista de 4 elementos)-> Campo complejo
# Retorna: lista de diccionarios
    
    game_id = game.get('id') 
    ratings = game.get('ratings') or []
    
    ratings_list = []
    for r in ratings:
        ratings_list.append({
            'game_id': game_id,
            'ratingd_id': r.get('id'),                 # id ratings (distribución valoraciones)
            'ratingd_title': r.get('title'),           # Categorías de valoración: excepcional (5 estrellas); recommended; meh; skip
            'ratingd_count': r.get('count'),           # Número de valoraciones
            'ratingd_percent': r.get('percent')        # Porcentajes 
        })
    
    return ratings_list


def extraer_platforms(game):
# Extrae las plataformas (lista de 7+ elementos)-> Campo complejo
# Retorna: lista de diccionarios
    game_id = game.get('id')
    platforms = game.get('platforms') or []
    
    platforms_list = []
    for p in platforms:
        platform = p.get('platform') or {}
        platforms_list.append({
            'game_id': game_id,
            'platform_id': platform.get('id'),              # id plataformas
            'platform_name': platform.get('name'),          # Nombre de la plataforma
            'released_at': p.get('released_at'),            # Lanzamiento en la plataforma
        })
    
    return platforms_list
    
def extraer_genres(game):
# Extrae TODOS los géneros (lista de 1-5 elementos)-> Campo complejo
# Retorna: lista de diccionarios
    game_id = game.get('id')
    genres = game.get('genres') or []
    
    genres_list = []
    for g in genres:
        genres_list.append({
            'game_id': game_id,                                      
            'genre_id': g.get('id'),                         # id género
            'genre_name': g.get('name'),                     # Nombre del género
            'genre_games_count': g.get('games_count')        # Número juegos en el género?????
        })
    
    return genres_list

def extraer_stores(game):
# Extrae las tiendas donde está disponible el juego -> Campo complejo
# Retorna: lista de diccionarios
    game_id = game.get('id')    
    stores = game.get('stores') or []
    
    stores_list = []    
    for s in stores:
        store = s.get('store') or {}
        if not store:
            continue
        stores_list.append({
            'game_id': game_id,
            'store_id': store.get('id'),
            'store_name': store.get('name')
        })
    
    return stores_list


def extraer_tags(game):
# Extrae TODOS los tags (lista de 19+ elementos)-> Campo complejo
# Retorna: lista de diccionarios
    game_id = game.get('id')
    tags = game.get('tags') or []
    
    tags_list = [] 
    for t in tags:
        tags_list.append({
            'game_id': game_id,
            'tag_id': t.get('id'),                               # id tag
            'tag_name': t.get('name'),                           # Nombre de la etiqueta
            'tag_language' : t.get('language'),                   # Idioma de la etiqueta
            'tag_games_count': t.get('games_count')              # Número de juegos en la etiqueta
        })
    
    return tags_list

# === FUNCIÓN PRINCIPAL DE TRANSFORMACIÓN ===

def transformar_juego_completo(game):
    # Transforma un juego completo en todas sus estructuras
    ## game_transformed = transformar_juego_completo(game)
    
    return {
        'game': extraer_campos_simples(game),
        'games_status': extraer_games_status(game),
        'esrb_ratings' : extraer_esrb_ratings(game),
        'ratings_distribution': extraer_ratings_distribution(game),
        'platforms': extraer_platforms(game),
        'genres': extraer_genres(game),
        'stores': extraer_stores(game),
        'tags': extraer_tags(game)
    }
    

def transformar_datos_completo(datos, verbose = False):
    # Transforma datos brutos de RAWG en DataFrames limpios preparados para PostgreSQL
    if verbose:
        print(f"Iniciando transformación de {len(datos)} juegos...")
        print("-" * 60)

    # ==== 1. TRANSFORMAR JUEGOS INDIVIDUALES ===
    if verbose:
        print("\n Transformando juegos individuales...")

    juegos_transformados = []
    errores = []

    for i, juego in enumerate(datos):
        try:
            game_trans = transformar_juego_completo(juego)
            juegos_transformados.append(game_trans)
        except Exception as e:
            errores.append({
                'index' : i,
                'game_id' : juego.get('id', 'unknown'),
                'error' : str(e)
            })
            if verbose:
                print(f"Error en juego {i}: {e}")
    if verbose:
        print(f"{len(juegos_transformados)} juegos transformados")
        if errores:
            print(f"{len(errores)} errores encontrados")

    # === 2. CREAR DATAFRAMES ===
    if verbose:
        print("\n Creando DataFrames...")

    # Listas para cada tabla
    games_list = []
    games_status_list = []
    esrb_ratings_list = []
    ratings_dist_list = []
    platforms_list = []
    genres_list = []
    stores_list = []
    tags_list = []
    
    # Descomponer cada juego transformado
    for juego_trans in juegos_transformados:
        game_data = juego_trans.get('game')
    
        if game_data:
            games_list.append(game_data)
    
        status = juego_trans.get('games_status')
        if isinstance(status, dict) and status.get('game_id') is not None:
            games_status_list.append(status)
    
        esrb = juego_trans.get('esrb_ratings')
        if isinstance(esrb, dict) and esrb.get('esrb_id') is not None:
            esrb_ratings_list.append(esrb)
    
        if juego_trans.get('ratings_distribution'):
            ratings_dist_list.extend(juego_trans['ratings_distribution'])

        if juego_trans.get('platforms'):
            platforms_list.extend(juego_trans['platforms'])

        if juego_trans.get('genres'):
            genres_list.extend(juego_trans['genres'])
    
        if juego_trans.get('stores'):
            stores_list.extend(juego_trans['stores'])
    
        if juego_trans.get('tags'):
            tags_list.extend(juego_trans['tags'])
    
    
    # Crear DataFrames
    
    # Crear DataFrames base
    df_games = pd.DataFrame(games_list)
    df_games['esrb_id'] = df_games['esrb_id'].astype('Int64')

    df_games_status = pd.DataFrame(games_status_list)
    
    df_ratings_distribution = pd.DataFrame(ratings_dist_list)
    
    df_platforms_list = pd.DataFrame(platforms_list)
    df_genres_list = pd.DataFrame(genres_list)
    df_stores_list = pd.DataFrame(stores_list)
    df_tags_list = pd.DataFrame(tags_list)
    
    # ESRB dimension
    if len(esrb_ratings_list) > 0:
        df_esrb_ratings = (pd.DataFrame(esrb_ratings_list).drop_duplicates(subset=["esrb_id"]).sort_values("esrb_id").reset_index(drop=True))
    else:
        df_esrb_ratings = pd.DataFrame(columns=["esrb_id", "esrb_name"])
    
    # Platforms: dimensión + bridge    
    if not df_platforms_list.empty:
        df_platforms = (
            df_platforms_list[["platform_id", "platform_name", "released_at"]]
            .dropna(subset=["platform_id"])
            .drop_duplicates(subset=["platform_id"])
            .sort_values("platform_id")
            .reset_index(drop=True)
        )
        df_game_platforms = (
            df_platforms_list[["game_id", "platform_id"]]
            .dropna(subset=["game_id", "platform_id"])
            .drop_duplicates(subset=["game_id", "platform_id"])
            .reset_index(drop=True)
        )
    else:
        df_platforms = pd.DataFrame(columns=["platform_id", "platform_name", "released_at"])
        df_game_platforms = pd.DataFrame(columns=["game_id", "platform_id"])

    # Genres: dimension + bridge
    if not df_genres_list.empty:
        df_genres = (
            df_genres_list[["genre_id", "genre_name", "genre_games_count"]]
            .dropna(subset=["genre_id"])
            .drop_duplicates(subset=["genre_id"])
            .sort_values("genre_id")
            .reset_index(drop=True)
        )
        df_game_genres = (
            df_genres_list[["game_id", "genre_id"]]
            .dropna(subset=["game_id", "genre_id"])
            .drop_duplicates(subset=["game_id", "genre_id"])
            .reset_index(drop=True)
        )
    else:
        df_genres = pd.DataFrame(columns=["genre_id", "genre_name", "genre_games_count"])
        df_game_genres = pd.DataFrame(columns=["game_id", "genre_id"])

    # Stores: dimension + bridge
    if not df_stores_list.empty:
        df_stores = (
            df_stores_list[["store_id", "store_name"]]
            .dropna(subset=["store_id"])
            .drop_duplicates(subset=["store_id"])
            .sort_values("store_id")
            .reset_index(drop=True)
        )
        df_game_stores = (
            df_stores_list[["game_id", "store_id"]]
            .dropna(subset=["game_id", "store_id"])
            .drop_duplicates(subset=["game_id", "store_id"])
            .reset_index(drop=True)
        )
    else:
        df_stores = pd.DataFrame(columns=["store_id", "store_name"])
        df_game_stores = pd.DataFrame(columns=["game_id", "store_id"])
            
   # Tags: dimension + bridge
    if not df_tags_list.empty:
        df_tags = (
            df_tags_list[["tag_id", "tag_name", "tag_language", "tag_games_count"]]
            .dropna(subset=["tag_id"])
            .drop_duplicates(subset=["tag_id"])
            .sort_values("tag_id")
            .reset_index(drop=True)
        )
        df_game_tags = (
            df_tags_list[["game_id", "tag_id"]]
            .dropna(subset=["game_id", "tag_id"])
            .drop_duplicates(subset=["game_id", "tag_id"])
            .reset_index(drop=True)
        )
    else:
        df_tags = pd.DataFrame(columns=["tag_id", "tag_name", "tag_language", "tag_games_count"])
        df_game_tags = pd.DataFrame(columns=["game_id", "tag_id"])     
            
       
    if verbose:
        print(f"\nDataFrames creados:")
        print(f"   - df_games:                {df_games.shape}")
        print(f"   - df_games_status:         {df_games_status.shape}")
        print(f"   - df_esrb_ratings:           {df_esrb_ratings.shape}")
        print(f"   - df_ratings_distribution: {df_ratings_distribution.shape}")
        print(f"   - df_platforms:            {df_platforms.shape}")
        print(f"   - df_game_platforms:       {df_game_platforms.shape}")
        print(f"   - df_genres:               {df_genres.shape}")
        print(f"   - df_game_genres:          {df_game_genres.shape}")
        print(f"   - df_stores:               {df_stores.shape}")
        print(f"   - df_game_stores:          {df_game_stores.shape}")
        print(f"   - df_tags:                 {df_tags.shape}")
        print(f"   - df_game_tags:            {df_game_tags.shape}")
  
    # === 3. LIMPIAR DATOS ===
    if verbose:
        print("\nLimpiando datos... ")

    # Limpieza df_games
    # -----------------------------------------------
    if verbose:
        print("\nTABLA: df_games")
        print("-"*60)
        
        print(f"\nEstado ANTES de limpieza:")
        print(f"   Filas: {len(df_games)}")
        print(f"   Columnas: {df_games.columns.tolist()}")
        print(f"\n   Valores nulos por columna:")
        print(df_games.isnull().sum())
    
    # Eliminar duplicados por id
    duplicados_antes = df_games.duplicated(subset=['game_id']).sum()
    df_games = df_games.drop_duplicates(subset=['game_id'])
    if verbose:
        print(f"\nDuplicados eliminados: {duplicados_antes}")
    
    # Validar formato de fechas (ya están en YYYY-MM)
    if verbose:
        print(f"\nValidando formato de fechas:")
        if len(df_games) > 0:
            print(f"   Ejemplo released: {df_games['released_ym'].iloc[0]}")
            print(f"   Ejemplo updated: {df_games['updated_ym'].iloc[0]}")
    
    # Convertir tipo valores numéricos a Int64
    columnas_numericas = ['game_rating', 'ratings_count', 'game_added', 'suggestions_count', 'playtime']
    for col in columnas_numericas:
        df_games[col] = df_games[col].astype(int)
        
    if verbose:   
        print(f"\nVista previa:")
        print(df_games.head(3))
        
    # Estadísticas básicas
    if verbose:    
        print(f"\nEstadísticas básicas:")
        columnas_numericas = ['game_rating', 'ratings_count', 'game_added', 'suggestions_count', 'playtime']
        if len(df_games) > 0:
            print(df_games[columnas_numericas].describe())

    
    # Limpieza df_games_status
    # -----------------------------------------------

    if verbose:
        print("\nTABLA: df_games_status")
        print("-"*60)
        
        print(f"\nEstado ANTES:")
        print(f"   Filas: {len(df_games_status)}")
        print(f"   Columnas: {df_games_status.columns.tolist()}")
        print(f"\n   Valores nulos:")
        print(df_games_status.isnull().sum())
    
    # Eliminar filas con game_id nulo
    nulos_antes = len(df_games_status)
    df_games_status = df_games_status.dropna(subset=['game_id'])
    nulos_eliminados = nulos_antes - len(df_games_status)
    if verbose:
        print(f"\nFilas con game_id nulo eliminadas: {nulos_eliminados}")
    
    # Eliminar duplicados
    duplicados_antes = df_games_status.duplicated(subset=['game_id']).sum()
    df_games_status = df_games_status.drop_duplicates(subset=['game_id'])
    if verbose:
        print(f"Duplicados eliminados: {duplicados_antes}")
        
    # Convertir a int
    status_cols = ['yet', 'owned', 'beaten', 'toplay', 'dropped', 'playing']
    for col in status_cols:
        if col in df_games_status.columns:
            df_games_status[col] = df_games_status[col].astype(int)

    if verbose:
        print(f"\nEstado DESPUÉS:")
        print(f"   Filas: {len(df_games_status)}")
        print(f"   Nulos totales: {df_games_status.isnull().sum().sum()}")
        
        print(f"\nVista previa:")
        print(df_games_status.head(3))
    
    # LIMPIEZA df_esrb_ratings
    # -----------------------------------------------

    if verbose:
        print("\nTABLA: df_esrb_ratings")
        print("-"*60)
        
        print(f"\nEstado ANTES:")
        print(f"   Filas: {len(df_esrb_ratings)}")
    
    if df_esrb_ratings is None or df_esrb_ratings.empty:
        df_esrb_ratings = pd.DataFrame(columns=["esrb_id", "esrb_name"])
        if verbose:    
            print("Tabla vacía (ningún juego tiene ESRB rating)")
    else:
        df_esrb_ratings = df_esrb_ratings[["esrb_id", "esrb_name"]].copy()
    
    # Eliminar nulos /duplicados por esrb_id
    nulos_antes = len(df_esrb_ratings)
    df_esrb_ratings = df_esrb_ratings.dropna(subset=['esrb_id'])
    nulos_eliminados = nulos_antes - len(df_esrb_ratings)
        
    duplicados_antes = df_esrb_ratings.duplicated(subset=['esrb_id']).sum()
    df_esrb_ratings = df_esrb_ratings.drop_duplicates(subset=['esrb_id'])
        
    # Forzar tipos
    df_esrb_ratings["esrb_id"] = pd.to_numeric(df_esrb_ratings["esrb_id"], errors="coerce").astype("Int64")
    df_esrb_ratings["esrb_name"] = df_esrb_ratings["esrb_name"].astype("string")

    if verbose:
        print(f"\nFilas con nulos eliminadas: {nulos_eliminados}")
        print(f"Duplicados eliminados: {duplicados_antes}")
        print(f"\nEstado DESPUÉS: {len(df_esrb_ratings)} filas")
        print("\nVista previa:")
        print(df_esrb_ratings.head(3))        
    
    
    # LIMPIEZA df_ratings_distribution
    # -----------------------------------------------
    if verbose:
        print("\nTABLA: df_ratings_distribution")
        print("-"*60)
        
        print(f"\nEstado ANTES:")
        print(f"   Filas: {len(df_ratings_distribution)}")
        print(f"   Valores nulos:")
        print(df_ratings_distribution.isnull().sum())
    
    # Eliminar nulos en campos clave
    nulos_antes = len(df_ratings_distribution)
    df_ratings_distribution = df_ratings_distribution.dropna(subset=['game_id', 'ratingd_id'])
    nulos_eliminados = nulos_antes - len(df_ratings_distribution)
    if verbose:
        print(f"\nFilas con nulos eliminadas: {nulos_eliminados}")
     
    # Eliminar duplicados
    duplicados_antes = df_ratings_distribution.duplicated(subset=['game_id', 'ratingd_id']).sum()
    df_ratings_distribution = df_ratings_distribution.drop_duplicates(subset=['game_id', 'ratingd_id'])
    if verbose:
        print(f"Duplicados eliminados: {duplicados_antes}")

    # Forzar tipos
    df_ratings_distribution["ratingd_count"] = pd.to_numeric(df_ratings_distribution["ratingd_count"], errors="coerce").astype("Int64")
    df_ratings_distribution["ratingd_percent"] = pd.to_numeric(df_ratings_distribution["ratingd_percent"], errors="coerce").astype("Float64")
    df_ratings_distribution["ratingd_title"] = df_ratings_distribution["ratingd_title"].astype("string")
    
    if verbose:
        print(f"\nEstado DESPUÉS: {len(df_ratings_distribution)} filas")
    
    
    # LIMPIEZA df_platforms
    # -----------------------------------------------
    if verbose:
        print("\nTABLA: df_platforms")
        print("-"*60)
        
        print(f"\nEstado ANTES:")
        print(f"   Filas: {len(df_platforms)}")
        print(f"   Valores nulos:")
        print(df_platforms.isnull().sum())
    
    # Eliminar nulos en campos clave
    nulos_antes = len(df_platforms)
    df_platformss = df_platforms.dropna(subset=['platform_id'])
    nulos_eliminados = nulos_antes - len(df_platforms)
    if verbose:
        print(f"\nFilas con nulos eliminadas: {nulos_eliminados}")
    
    # Eliminar duplicados
    duplicados_antes = df_platforms.duplicated(subset=['platform_id']).sum()
    df_platforms = df_platforms.drop_duplicates(subset=['platform_id'])
    if verbose:
        print(f"Duplicados eliminados: {duplicados_antes}")
    
    # Crear tabla de plataformas únicas
    df_platforms = df_platforms[['platform_id', 'platform_name']].drop_duplicates().sort_values('platform_id').reset_index(drop=True)
    if verbose:
        print(f"\nTabla de plataformas: {len(df_platforms)} únicas")
        print(f"\nTop 10 plataformas:")
        print(df_platforms.head(10))
    
        
    # LIMPIEZA df_game_platforms
    # -----------------------------------------------
    print("\nTABLA: df_game_platforms")
    print("-"*60)
        
    if verbose:
        print(f"\nEstado ANTES:")
        print(f"   Filas: {len(df_game_platforms)}")
        print(f"   Valores nulos:")
        print(df_game_platforms.isnull().sum())
    
    # Eliminar nulos en campos clave
    nulos_antes = len(df_game_platforms)
    df_game_platforms = df_game_platforms.dropna(subset=['game_id', 'platform_id'])
    nulos_eliminados = nulos_antes - len(df_game_platforms)
    if verbose:
        print(f"\nFilas con nulos eliminadas: {nulos_eliminados}")
    
    # Eliminar duplicados
    duplicados_antes = df_game_platforms.duplicated(subset=['game_id', 'platform_id']).sum()
    df_game_platforms = df_game_platforms.drop_duplicates(subset=['game_id', 'platform_id'])
    if verbose:
        print(f"Duplicados eliminados: {duplicados_antes}")
    
    
    # LIMPIEZA df_genres
    # -----------------------------------------------
    if verbose:
        print("\nTABLA: df_genres")
        print("-"*60)
        
        
        print(f"\nEstado ANTES:")
        print(f"   Filas: {len(df_genres)}")
        print(f"   Valores nulos:")
        print(df_game_genres.isnull().sum())
    
    # Eliminar nulos
    nulos_antes = len(df_genres)
    df_genres = df_genres.dropna(subset=['genre_id'])
    nulos_eliminados = nulos_antes - len(df_genres)
    if verbose:
        print(f"\nFilas con nulos eliminadas: {nulos_eliminados}")
    
    # Eliminar duplicados
    duplicados_antes = df_genres.duplicated(subset=['genre_id']).sum()
    df_genres = df_genres.drop_duplicates(subset=['genre_id'])
    if verbose:
        print(f"Duplicados eliminados: {duplicados_antes}")
    
        print(f"\nEstado DESPUÉS: {len(df_genres)} filas")
    
    # Crear tabla de géneros únicos
    df_genres = df_genres[['genre_id', 'genre_name', 'genre_games_count']].drop_duplicates().sort_values('genre_id').reset_index(drop=True)
    if verbose:
        print(f"\nTabla de géneros: {len(df_genres)} únicos")
        print(f"\nGéneros disponibles:")
        print(df_genres)
    
    # LIMPIEZA df_game_genres
    # -----------------------------------------------
    if verbose:
        print("\nTABLA: df_game_genres")
        print("-"*60)
          
        print(f"\nEstado ANTES:")
        print(f"   Filas: {len(df_game_genres)}")
        print(f"   Valores nulos:")
        print(df_game_genres.isnull().sum())
    
    # Eliminar nulos
    nulos_antes = len(df_game_genres)
    df_game_genres = df_game_genres.dropna(subset=['game_id', 'genre_id'])
    nulos_eliminados = nulos_antes - len(df_game_genres)
    if verbose:
        print(f"\nFilas con nulos eliminadas: {nulos_eliminados}")
    
    # Eliminar duplicados
    duplicados_antes = df_game_genres.duplicated(subset=['game_id', 'genre_id']).sum()
    df_game_genres = df_game_genres.drop_duplicates(subset=['game_id', 'genre_id'])
    if verbose:
        print(f"Duplicados eliminados: {duplicados_antes}")
    
        print(f"\nEstado DESPUÉS: {len(df_game_genres)} filas")
    
    # LIMPIEZA df_stores
    # -----------------------------------------------
    if verbose:
        print("\nTABLA: df_stores")
        print("-"*60)
        
        print(f"\nEstado ANTES:")
        print(f"   Filas: {len(df_stores)}")
        print(f"   Valores nulos:")
        print(df_stores.isnull().sum())
    
    # Eliminar nulos
    nulos_antes = len(df_stores)
    df_stores = df_stores.dropna(subset=['store_id'])
    nulos_eliminados = nulos_antes - len(df_stores)
    if verbose:
        print(f"\nFilas con nulos eliminadas: {nulos_eliminados}")
    
    # Eliminar duplicados
    duplicados_antes = df_stores.duplicated(subset=['store_id']).sum()
    df_stores = df_stores.drop_duplicates(subset=['store_id'])
    if verbose:
        print(f"Duplicados eliminados: {duplicados_antes}")
    
        print(f"\nEstado DESPUÉS: {len(df_stores)} filas")
    
    # Crear tabla de stores únicas
    df_stores = df_stores[['store_id', 'store_name']].drop_duplicates().sort_values('store_id').reset_index(drop=True)
    if verbose:
        print(f"\nTabla de tiendas: {len(df_stores)} únicas")
        print(f"\nTiendas disponibles:")
        print(df_stores)
    
    # LIMPIEZA df_game_stores
    # -----------------------------------------------
    if verbose:
        print("\nTABLA: df_game_stores")
        print("-"*60)
        
        print(f"\nEstado ANTES:")
        print(f"   Filas: {len(df_game_stores)}")
        print(f"   Valores nulos:")
        print(df_game_stores.isnull().sum())
    
    # Eliminar nulos
    nulos_antes = len(df_game_stores)
    df_game_stores = df_game_stores.dropna(subset=['game_id', 'store_id'])
    nulos_eliminados = nulos_antes - len(df_game_stores)
    if verbose:
        print(f"\nFilas con nulos eliminadas: {nulos_eliminados}")
    
    # Eliminar duplicados
    duplicados_antes = df_game_stores.duplicated(subset=['game_id', 'store_id']).sum()
    df_game_stores = df_game_stores.drop_duplicates(subset=['game_id', 'store_id'])
    if verbose:
        print(f"Duplicados eliminados: {duplicados_antes}")
    
        print(f"\nEstado DESPUÉS: {len(df_game_stores)} filas")
    
    # LIMPIEZA df_tags
    # -----------------------------------------------
    if verbose:
        print("\nTABLA: df_tags")
        print("-"*60)
        
        print(f"\nEstado ANTES:")
        print(f"   Filas: {len(df_tags)}")
        print(f"   Valores nulos:")
        print(df_tags.isnull().sum())
    
    # Eliminar nulos
    nulos_antes = len(df_tags)
    df_tags = df_tags.dropna(subset=['tag_id'])
    nulos_eliminados = nulos_antes - len(df_tags)
    if verbose:
        print(f"\nFilas con nulos eliminadas: {nulos_eliminados}")
    
    # Eliminar duplicados
    duplicados_antes = df_tags.duplicated(subset=['tag_id']).sum()
    df_tags = df_tags.drop_duplicates(subset=['tag_id'])
    if verbose:
        print(f"Duplicados eliminados: {duplicados_antes}")
    
        print(f"\nEstado DESPUÉS: {len(df_tags)} filas")
    
    # Crear tabla de tags únicos
    df_tags = df_tags[['tag_id', 'tag_name', 'tag_language', 'tag_games_count']].drop_duplicates().sort_values('tag_id').reset_index(drop=True)
    if verbose:
        print(f"\nTabla de tags: {len(df_tags)} únicos")
        print(f"\nTop 10 tags más usados:")
    tag_counts = df_tags['tag_name'].value_counts().head(10)
    if verbose:
        print(tag_counts)
    
    
    # LIMPIEZA df_game_tags
    # -----------------------------------------------
    if verbose:
        print("\nTABLA: df_game_tags")
        print("-"*60)
        
        print(f"\nEstado ANTES:")
        print(f"   Filas: {len(df_game_tags)}")
        print(f"   Valores nulos:")
        print(df_game_tags.isnull().sum())
    
    # Eliminar nulos
    nulos_antes = len(df_game_tags)
    df_game_tags = df_game_tags.dropna(subset=['game_id', 'tag_id'])
    nulos_eliminados = nulos_antes - len(df_game_tags)
    if verbose:
        print(f"\nFilas con nulos eliminadas: {nulos_eliminados}")
    
    # Eliminar duplicados
    duplicados_antes = df_game_tags.duplicated(subset=['game_id', 'tag_id']).sum()
    df_game_tags = df_game_tags.drop_duplicates(subset=['game_id', 'tag_id'])
    if verbose:
        print(f"Duplicados eliminados: {duplicados_antes}")
    
        print(f"\nEstado DESPUÉS: {len(df_game_tags)} filas")
    
       
    # === Resumen final ===
    if verbose:
        print("\nRESUMEN FINAL - DATOS LIMPIOS")
        print("-"*60)
        print(f"""
    TABLAS PRINCIPALES:
       - df_games:                {df_games.shape[0]:>6} filas × {df_games.shape[1]:>2} columnas
       - df_games_status:         {df_games_status.shape[0]:>6} filas × {df_games_status.shape[1]:>2} columnas
       - df_esrb_ratings:           {df_esrb_ratings.shape[0]:>6} filas × {df_esrb_ratings.shape[1]:>2} columnas
       - df_ratings_distribution: {df_ratings_distribution.shape[0]:>6} filas × {df_ratings_distribution.shape[1]:>2} columnas
       - df_platforms:            {df_platforms.shape[0]:>6} filas × {df_platforms.shape[1]:>2} columnas
       - df_game_platforms:       {df_game_platforms.shape[0]:>6} filas × {df_game_platforms.shape[1]:>2} columnas
       - df_genres:               {df_genres.shape[0]:>6} filas × {df_genres.shape[1]:>2} columnas
       - df_game_genres:          {df_game_genres.shape[0]:>6} filas × {df_game_genres.shape[1]:>2} columnas
       - df_stores:               {df_stores.shape[0]:>6} filas × {df_stores.shape[1]:>2} columnas
       - df_game_stores:          {df_game_stores.shape[0]:>6} filas × {df_game_stores.shape[1]:>2} columnas
       - df_tags:                 {df_tags.shape[0]:>6} filas × {df_tags.shape[1]:>2} columnas
       - df_game_tags:            {df_game_tags.shape[0]:>6} filas × {df_game_tags.shape[1]:>2} columnas
    """)
    
        print("\nLimpieza completada")

    return {
        'games': df_games,
        'games_status': df_games_status,
        'esrb_ratings': df_esrb_ratings,
        'ratings_distribution': df_ratings_distribution,
        'platforms': df_platforms,
        'game_platforms': df_game_platforms,
        'genres': df_genres,
        'game_genres': df_game_genres,
        'stores': df_stores,
        'game_stores': df_game_stores,
        'tags': df_tags,
        'game_tags': df_game_tags,
    }

