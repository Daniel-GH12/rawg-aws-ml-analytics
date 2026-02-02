

def lambda_handler(event, context):
    """Lambda 2: Extracción diaria de juegos actualizados"""
    try:
        # 1. Calcular fecha de hoy
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        print(f"📅 Extrayendo juegos actualizados: {yesterday} → {today}")
        
        # 2. Parámetros para API de RAWG
        params = {
            "key": os.environ["RAWG_API_KEY"],
            "page_size": 100,
            "dates": f"{yesterday},{today}",
            "page": 1
        }
        
        all_games = []
        has_more = True
        
        # 3. Paginación para obtener todos los juegos del día
        while has_more:
            response = requests.get("https://api.rawg.io/api/games", params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            all_games.extend(data.get("results", []))
            
            # Verificar si hay más páginas
            if data.get("next"):
                params["page"] += 1
            else:
                has_more = False
        
        print(f"✅ Extraídos {len(all_games)} juegos actualizados")
        
        # 4. Subir a S3
        if all_games:
            s3_client = boto3.client("s3")
            filename = f"daily_{today.replace('-', '')}.json"
            s3_key = f"raw/{filename}"
            
            s3_client.put_object(
                Bucket=os.environ["S3_BUCKET_NAME"],
                Key=s3_key,
                Body=json.dumps(all_games, indent=2),
                ContentType="application/json"
            )
            
            print(f"📤 Subido a S3: s3://{os.environ['S3_BUCKET_NAME']}/{s3_key}")
            return {"statusCode": 200, "body": f"Extraídos {len(all_games)} juegos"}
        else:
            print("ℹ️  No hay juegos actualizados hoy")
            return {"statusCode": 200, "body": "No hay juegos nuevos"}
            
    except Exception as e:
        print(f"❌ Error en Lambda 2: {e}")
        raise
