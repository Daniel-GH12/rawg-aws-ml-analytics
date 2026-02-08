import json
import boto3
import psycopg2
import os

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    # Credenciales de la RDS
    db_config = {
        "host": "data-rawg.cfsieqiau5qy.eu-north-1.rds.amazonaws.com",
        "database": "postgres",
        "user": "postgres",
        "password": "data-rawg" 
    }
    
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    
    try:
        # Obtener información del archivo que acaba de llegar a S3
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        
        print(f"Procesando archivo: {key} desde bucket: {bucket}")
        
        response = s3_client.get_object(Bucket=bucket, Key=key)
        data = json.loads(response['Body'].read().decode('utf-8'))
        
        for item in data:
            g = item.get('main_game', {})
            game_id = g.get('game_id')
            
            if not game_id: continue # Seguridad: si no hay ID, saltamos

            # ESRB_RATINGS (Maestra)
            esrb = item.get('esrb_ratings', {})
            if esrb.get('esrb_id'):
                cur.execute("INSERT INTO esrb_ratings (esrb_id, esrb_name) VALUES (%s, %s) ON CONFLICT (esrb_id) DO NOTHING", 
                            (esrb['esrb_id'], esrb['esrb_name']))

            # GAMES (Principal)
            cur.execute("""
                INSERT INTO games (game_id, game_name, tba, game_released, game_updated, game_rating, rating_count, game_added, playtime, suggestions_count, esrb_rating_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (game_id) DO UPDATE SET 
                    game_updated = EXCLUDED.game_updated, 
                    game_rating = EXCLUDED.game_rating,
                    rating_count = EXCLUDED.rating_count
            """, (game_id, g['game_name'], g['tba'], g['game_released'], g['update'], g['game_rating'], g['rating_count'], g['game_added'], g['playtime'], g['suggestions_count'], g['esrb_rating_id']))

            # RATINGS_DISTRIBUTION (Dependiente)
            for r in item.get('ratings_distribution', []):
                cur.execute("""
                    INSERT INTO ratings_distribution (ratingd_id, game_id, ratingd_title, ratingd_count, ratingd_percent)
                    VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING
                """, (r['ratingd_id'], game_id, r['ratingd_title'], r['ratingd_count'], r['ratingd_percent']))

            # GAMES_STATUS (Dependiente)
            s = item.get('games_status', {})
            cur.execute("""
                INSERT INTO games_status (game_id, yet, owned, beaten, toplay, dropped, playing)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (game_id) DO UPDATE SET owned = EXCLUDED.owned, beaten = EXCLUDED.beaten
            """, (game_id, s['yet'], s['owned'], s['beaten'], s['toplay'], s['dropped'], s['playing']))

            # PLATFORMS y GAMES_PLATFORMS (N:M)
            for p in item.get('platforms', []):
                cur.execute("INSERT INTO platforms (platform_id, platform_name, platform_released) VALUES (%s, %s, %s) ON CONFLICT (platform_id) DO NOTHING",
                            (p['platform_id'], p['platform_name'], p['platform_released']))
                cur.execute("INSERT INTO games_platforms (game_id, platform_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (game_id, p['platform_id']))

            # GENRES y GAMES_GENRES (N:M)
            for gen in item.get('genres', []):
                cur.execute("INSERT INTO genres (genre_id, genre_name, genres_games_count) VALUES (%s, %s, %s) ON CONFLICT (genre_id) DO NOTHING",
                            (gen['genre_id'], gen['genre_name'], gen['genres_games_count']))
                cur.execute("INSERT INTO games_genres (game_id, genre_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (game_id, gen['genre_id']))

            # STORES y GAMES_STORES (N:M)
            for st in item.get('stores', []):
                cur.execute("INSERT INTO stores (store_id, store_name) VALUES (%s, %s) ON CONFLICT (store_id) DO NOTHING",
                            (st['store_id'], st['store_name']))
                cur.execute("INSERT INTO games_stores (game_id, store_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (game_id, st['store_id']))

            # TAGS y GAMES_TAGS (N:M)
            for t in item.get('tags', []):
                cur.execute("INSERT INTO tags (tag_id, tag_name, tag_language, tag_games_count) VALUES (%s, %s, %s, %s) ON CONFLICT (tag_id) DO NOTHING",
                            (t['tag_id'], t['tag_name'], t['tag_language'], t['tag_games_count']))
                cur.execute("INSERT INTO games_tags (game_id, tag_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (game_id, t['tag_id']))
            
            # DEVELOPERS Y GAME_DEVELOPERS (N:M)
            for dev in item.get('developers', []):
                cur.execute(" INSERT INTO developers (developer_id, developer_name, games_count) VALUES (%s, %s, %s) ON CONFLICT (developer_id) DO NOTHING",
                            (dev['developer_id'], dev['developer_name'], dev.get('developer_games_count')))
                cur.execute("INSERT INTO games_developers (game_id, developer_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (game_id, dev['developer_id']))
        
        conn.commit()
        return {"status": "success", "message": f"Se han procesado {len(data)} juegos correctamente."}

    except Exception as e:
        conn.rollback()
        print(f"ERROR: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        cur.close()
        conn.close()