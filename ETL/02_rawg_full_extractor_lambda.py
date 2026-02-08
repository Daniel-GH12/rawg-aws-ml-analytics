import json
import time
import random

import boto3

from botocore.httpsession import URLLib3Session
from botocore.awsrequest import AWSRequest
from concurrent.futures import ThreadPoolExecutor, as_completed


# --------------------------------------------------
# Config
# --------------------------------------------------

S3_BUCKET = "rawg-hab-data"

RAW_FOLDER = "raw/full/"

CHECKPOINT_KEY = "checkpoints/full_extractor.json"

SECRET_1 = "rawg_api_key_1"
SECRET_2 = "rawg_api_key_2"

BASE_URL = "https://api.rawg.io/api/games"

PAGE_SIZE = 40

MAX_WORKERS = 4

MAX_PAGES = 600

REQUEST_DELAY = 0.3


# --------------------------------------------------

s3 = boto3.client("s3")
secrets = boto3.client("secretsmanager")
http = URLLib3Session()


# --------------------------------------------------


def get_keys():

    keys = []

    for name in [SECRET_1, SECRET_2]:

        res = secrets.get_secret_value(SecretId=name)

        data = json.loads(res["SecretString"])

        keys.append(data["api_key"])

    return keys


def choose(keys):

    return random.choice(keys)


def call_api(key, page):

    params = {
        "key": key,
        "page": page,
        "page_size": PAGE_SIZE
    }

    query = "&".join([f"{k}={v}" for k, v in params.items()])

    url = f"{BASE_URL}?{query}"

    req = AWSRequest("GET", url)

    resp = http.send(req.prepare())

    return resp.status_code, resp.content.decode()


def upload(data, key):

    s3.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=json.dumps(data),
        ContentType="application/json"
    )


def load_checkpoint():

    try:

        obj = s3.get_object(Bucket=S3_BUCKET, Key=CHECKPOINT_KEY)

        return json.loads(obj["Body"].read())

    except:

        return {"page": 1}


def save_checkpoint(p):

    s3.put_object(
        Bucket=S3_BUCKET,
        Key=CHECKPOINT_KEY,
        Body=json.dumps({"page": p}),
        ContentType="application/json"
    )


# --------------------------------------------------


def fetch(keys, page):

    key = choose(keys)

    status, body = call_api(key, page)

    if status != 200:
        raise Exception(status)

    return page, json.loads(body)


# --------------------------------------------------


def lambda_handler(event, context):

    print("=== FULL EXTRACTOR START ===")


    keys = get_keys()


    checkpoint = load_checkpoint()

    start = checkpoint.get("current_page", checkpoint.get("page", 1))

    end = start + MAX_PAGES


    max_done = start


    futures = []


    with ThreadPoolExecutor(MAX_WORKERS) as pool:

        for p in range(start, end):

            futures.append(pool.submit(fetch, keys, p))


        for f in as_completed(futures):

            try:

                page, data = f.result()

                results = data.get("results", [])


                if not results:
                    continue


                key = f"{RAW_FOLDER}page_{page}.json"


                upload(results, key)


                print("Saved:", key)


                max_done = max(max_done, page)


            except Exception as e:

                print("Worker error:", e)


            time.sleep(REQUEST_DELAY)


    save_checkpoint(max_done + 1)


    print("Next page:", max_done + 1)
    print("=== FULL EXTRACTOR END ===")


    return {
        "statusCode": 200,
        "start": start,
        "end": max_done,
        "processed": max_done - start + 1
    }