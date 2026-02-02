

def safe_int(value, default=0, max_val=2147483647):
    try:
        if value is None:
            return default
        val = int(float(value))
        return min(max(val, 0), max_val)
    except (ValueError, TypeError):
        return default

def safe_numeric(value, default=0.0, max_val=5.0):
    try:
        if value is None:
            return default
        val = float(value)
        return min(max(val, 0.0), max_val)
    except (ValueError, TypeError):
        return default

def lambda_handler(event, context):
    """Lambda 3: Carga datos desde S3 a RDS"""
    try:
        # 1. Obtener información del evento S3
        bucket = event["Records"][0]["s3"]["bucket"]["name"]
        key = event["Records"][0]["s3"]["object"]["key"]
        
        print(f"Procesando archivo: s3://{bucket}/{key}")  # Sin emoji para evitar problemas
        
        # 2. Descargar archivo JSON de S3
        s3_client = boto3.client("s3")
        response = s3_client.get_object(Bucket=bucket, Key=key)
        data = json.loads(response["Body"].read())
        
        # 3. Conectar a RDS
        conn = psycopg2.connect(
            host=os.environ["DB_HOST"],
            dbname=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            port=os.environ.get("DB_PORT", "5432")
        )
        cursor = conn.cursor()
        
        # 4. Insertar datos en RDS
        games_data = []
        for game in data:  # ✅ CORRECCIÓN CRÍTICA: 'for game in data'
            added_status = game.get("added_by_status") or {}
            esrb_rating = game.get("esrb_rating") or {}
            
            games_data.append((
                safe_int(game["id"]),
                str(game["name"]) if game["name"] else "Unknown",
                game.get("released"),
                safe_numeric(game.get("rating")),
                safe_int(game.get("ratings_count")),
                safe_int(game.get("metacritic"), max_val=100),
                safe_int(game.get("playtime")),
                safe_int(added_status.get("yet", 0)),
                safe_int(added_status.get("owned", 0)),
                safe_int(added_status.get("beaten", 0)),
                safe_int(added_status.get("toplay", 0)),
                safe_int(added_status.get("dropped", 0)),
                safe_int(added_status.get("playing", 0)),
                safe_int(esrb_rating.get("id")) if esrb_rating else None
            ))
        
        # Insertar en tabla games
        cursor.executemany("""
            INSERT INTO games (
                id, name, released, rating, ratings_count, metacritic, playtime,
                status_yet, status_owned, status_beaten, status_toplay, status_dropped, status_playing,
                esrb_rating_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                released = EXCLUDED.released,
                rating = EXCLUDED.rating,
                ratings_count = EXCLUDED.ratings_count,
                metacritic = EXCLUDED.metacritic,
                playtime = EXCLUDED.playtime,
                status_yet = EXCLUDED.status_yet,
                status_owned = EXCLUDED.status_owned,
                status_beaten = EXCLUDED.status_beaten,
                status_toplay = EXCLUDED.status_toplay,
                status_dropped = EXCLUDED.status_dropped,
                status_playing = EXCLUDED.status_playing,
                esrb_rating_id = EXCLUDED.esrb_rating_id,
                updated = CURRENT_TIMESTAMP
        """, games_data)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"Carga completada: {len(games_data)} juegos insertados")
        return {"statusCode": 200, "body": f"Cargados {len(games_data)} juegos"}
        
    except Exception as e:
        print(f"Error en Lambda 3: {e}")
        raise
