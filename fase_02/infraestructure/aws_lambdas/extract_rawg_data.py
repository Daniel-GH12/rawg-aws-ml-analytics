import json
import requests
import boto3
from datetime import datetime, timedelta

# Configuración
S3_BUCKET = "rawg-data-lake-projetc"
API_KEY = "2acae05652234db8ae742fc35698e40a"
BASE_URL = "https://api.rawg.io/api/games"

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    all_extracted_data = []
    page = 1               
    max_pages = 3 
    
    # RANGO DIARIO: Ayer y Hoy
    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    date_filter = f"{yesterday},{today}"
    
    params = {
        'key': API_KEY,
        'page_size': 40,
        'page': page,
        'updated': date_filter, # Filtramos por cambios recientes
        'ordering': '-updated'   # Los últimos cambios primero
    }
    
    while page <= max_pages:
        params['page'] = page
        response = requests.get(BASE_URL, params=params)
        
        if response.status_code != 200:
            break
            
        data = response.json()
        results = data.get('results', [])
        
        if not results:
            break
            
        for game in results:
            status = game.get("added_by_status") or {}
            
            game_data = {
                "main_game": {
                    "game_id": game.get("id"),
                    "game_name": game.get("name"),
                    "tba": game.get("tba"),
                    "game_released": game.get("released"),
                    "update": game.get("updated"),
                    "game_rating": game.get("rating"),
                    "rating_count": game.get("ratings_count"),
                    "game_added": game.get("added"),
                    "playtime": game.get("playtime"),
                    "suggestions_count": game.get("suggestions_count"),
                    "esrb_rating_id": game.get("esrb_rating", {}).get("id") if game.get("esrb_rating") else None
                },
                "ratings_distribution": [
                    {
                        "ratingd_id": r.get("id"),
                        "game_id": game.get("id"),
                        "ratingd_title": r.get("title"),
                        "ratingd_count": r.get("count"),
                        "ratingd_percent": r.get("percent")
                    } for r in (game.get("ratings") or [])
                ],
                "games_status": {
                    "game_id": game.get("id"),
                    "yet": status.get("yet", 0),
                    "owned": status.get("owned", 0),
                    "beaten": status.get("beaten", 0),
                    "toplay": status.get("toplay", 0),
                    "dropped": status.get("dropped", 0),
                    "playing": status.get("playing", 0)
                },
                "esrb_ratings": {
                    "esrb_id": game.get("esrb_rating", {}).get("id") if game.get("esrb_rating") else None,
                    "esrb_name": game.get("esrb_rating", {}).get("name") if game.get("esrb_rating") else None
                },
                "platforms": [
                    {
                        "platform_id": p.get("platform", {}).get("id"),
                        "platform_name": p.get("platform", {}).get("name"),
                        "platform_released": p.get("released_at")
                    } for p in (game.get("platforms") or [])
                ],
                "genres": [
                    {
                        "genre_id": g.get("id"),
                        "genre_name": g.get("name"),
                        "genres_games_count": g.get("games_count")
                    } for g in (game.get("genres") or [])
                ],
                "stores": [
                    {
                        "store_id": s.get("store", {}).get("id"),
                        "store_name": s.get("store", {}).get("name")
                    } for s in (game.get("stores") or [])
                ],
                "tags": [
                    {
                        "tag_id": t.get("id"),
                        "tag_name": t.get("name"),
                        "tag_language": t.get("language"),
                        "tag_games_count": t.get("games_count")
                    } for t in (game.get("tags") or [])
                ],
                "developers": [
                    {
                        "developer_id": d.get("id"),
                        "developer_name": d.get("name"),
                        "developer_games_count": d.get("games_count")
                    } for d in (game.get("developers") or [])
                ],
                "games_developers": [game.get("id"), [d.get("id") for d in (game.get("developers") or [])]],
                "games_platforms": [game.get("id"), [p.get("platform", {}).get("id") for p in (game.get("platforms") or [])]],
                "games_genres": [game.get("id"), [g.get("id") for g in (game.get("genres") or [])]],
                "games_stores": [game.get("id"), [s.get("store", {}).get("id") for s in (game.get("stores") or [])]],
                "games_tags": [game.get("id"), [t.get("id") for t in (game.get("tags") or [])]]
            }
            all_extracted_data.append(game_data)
        
        page += 1

    if all_extracted_data:
        filename = f"daily_rawg_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=f"raw/{filename}",
            Body=json.dumps(all_extracted_data)
        )
        return {'statusCode': 200, 'body': f"Carga diaria completa: {len(all_extracted_data)} juegos."}
    
    return {'statusCode': 200, 'body': "Sin actualizaciones hoy."}