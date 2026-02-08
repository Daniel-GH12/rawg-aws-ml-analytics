import json
import boto3
import psycopg2
from psycopg2.extras import execute_batch
from datetime import date


# --------------------------------------------------
# AWS
# --------------------------------------------------

s3 = boto3.client("s3")


# --------------------------------------------------
# CONFIG
# --------------------------------------------------

BUCKET = "rawg-hab-data"

RAW_PREFIX = "raw/full/"
PROCESSED_PREFIX = "processed/loaded/"


DB = {
    "host": "rawg-db.cf0ec26s6wkm.eu-north-1.rds.amazonaws.com",
    "database": "postgres",
    "user": "rawg_admin",
    "password": "rawg2026-daniel",
    "port": 5432,
    "connect_timeout": 5
}


# --------------------------------------------------


def connect():
    return psycopg2.connect(**DB)


# --------------------------------------------------


def move_to_processed(key):

    new_key = key.replace(RAW_PREFIX, PROCESSED_PREFIX)

    s3.copy_object(
        Bucket=BUCKET,
        CopySource={"Bucket": BUCKET, "Key": key},
        Key=new_key
    )

    s3.delete_object(
        Bucket=BUCKET,
        Key=key
    )

    return new_key


# --------------------------------------------------


def load_json(bucket, key):

    try:

        obj = s3.get_object(Bucket=bucket, Key=key)

        raw = obj["Body"].read().decode().strip()

        if not raw:
            return None

        return json.loads(raw)

    except Exception as e:

        print("JSON load error:", e)
        return None


# --------------------------------------------------


def lambda_handler(event, context):

    print("=== RAWG LOADER STARTED ===")


    record = event["Records"][0]

    bucket = record["s3"]["bucket"]["name"]
    key = record["s3"]["object"]["key"]


    print("File:", key)


    # Ignore processed
    if key.startswith(PROCESSED_PREFIX):

        print("Already processed. Skip.")
        return {"statusCode": 200}


    # --------------------------------------------------
    # Download
    # --------------------------------------------------

    data = load_json(bucket, key)

    if data is None or not isinstance(data, list):

        print("Invalid file format")
        return {"statusCode": 400}


    # --------------------------------------------------
    # Containers
    # --------------------------------------------------

    games = []
    metrics = []

    platforms = set()
    gplats = []

    tags = set()
    gtags = []


    SNAPSHOT = date.today()


    # --------------------------------------------------
    # Parse
    # --------------------------------------------------

    for g in data:

        gid = g["id"]


        # ---------- GAMES ----------

        games.append((
            gid,
            g.get("name"),
            g.get("slug"),
            g.get("released"),
            g.get("playtime"),
            g.get("background_image")
        ))


        # ---------- METRICS ----------

        metrics.append((
            gid,
            SNAPSHOT,
            g.get("rating"),
            g.get("ratings_count"),
            g.get("reviews_count"),
            g.get("metacritic"),
            g.get("added"),
            g.get("community_rating")
        ))


        # ---------- PLATFORMS ----------

        for p in g.get("platforms", []):

            pl = p["platform"]

            platforms.add((
                pl["id"],
                pl["name"]
            ))

            gplats.append((gid, pl["id"]))


        # ---------- TAGS ----------

        for t in g.get("tags", []):

            tags.add((
                t["id"],
                t["name"]
            ))

            gtags.append((gid, t["id"]))


    # --------------------------------------------------
    # SQL
    # --------------------------------------------------

    SQL_GAMES = """
    INSERT INTO games
    VALUES (%s,%s,%s,%s,%s,%s)
    ON CONFLICT (game_id)
    DO UPDATE SET
     name=EXCLUDED.name,
     release_date=EXCLUDED.release_date;
    """


    SQL_METRICS = """
    INSERT INTO game_metrics
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    ON CONFLICT (game_id, snapshot_date)
    DO UPDATE SET
     rating=EXCLUDED.rating,
     ratings_count=EXCLUDED.ratings_count,
     reviews_count=EXCLUDED.reviews_count,
     metacritic=EXCLUDED.metacritic,
     added=EXCLUDED.added,
     community_rating=EXCLUDED.community_rating;
    """


    SQL_PLATFORMS = """
    INSERT INTO platforms
    VALUES (%s,%s)
    ON CONFLICT DO NOTHING;
    """


    SQL_GAME_PLATFORMS = """
    INSERT INTO game_platforms
    VALUES (%s,%s)
    ON CONFLICT DO NOTHING;
    """


    SQL_TAGS = """
    INSERT INTO tags
    VALUES (%s,%s)
    ON CONFLICT DO NOTHING;
    """


    SQL_GAME_TAGS = """
    INSERT INTO game_tags
    VALUES (%s,%s)
    ON CONFLICT DO NOTHING;
    """


    # --------------------------------------------------
    # Insert
    # --------------------------------------------------

    conn = connect()
    cur = conn.cursor()


    execute_batch(cur, SQL_GAMES, games, page_size=500)

    execute_batch(cur, SQL_METRICS, metrics, page_size=500)

    execute_batch(cur, SQL_PLATFORMS, list(platforms), page_size=500)

    execute_batch(cur, SQL_GAME_PLATFORMS, gplats, page_size=1000)

    execute_batch(cur, SQL_TAGS, list(tags), page_size=500)

    execute_batch(cur, SQL_GAME_TAGS, gtags, page_size=1000)


    conn.commit()

    cur.close()
    conn.close()


    # --------------------------------------------------
    # Move file
    # --------------------------------------------------

    new_key = move_to_processed(key)


    print("Moved to:", new_key)
    print("Games:", len(games))


    return {
        "statusCode": 200,
        "inserted": len(games),
        "processed_file": new_key
    }