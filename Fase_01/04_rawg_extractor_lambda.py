import json
import time
import random
from datetime import datetime, timedelta

import boto3

from botocore.httpsession import URLLib3Session
from botocore.awsrequest import AWSRequest
from botocore.exceptions import ClientError


# --------------------------------------------------
# Config
# --------------------------------------------------

S3_BUCKET_NAME = "rawg-hab-data"

S3_RAW_FOLDER = "raw/daily/"

SECRET_NAME_1 = "rawg_api_key_1"
SECRET_NAME_2 = "rawg_api_key_2"

RAWG_BASE_URL = "https://api.rawg.io/api/games"

PAGE_SIZE = 40

REQUEST_DELAY_SECONDS = 1.5


# --------------------------------------------------

s3_client = boto3.client("s3")
secrets_client = boto3.client("secretsmanager")
http_session = URLLib3Session()


# --------------------------------------------------


def get_api_keys():

    keys = []

    for name in [SECRET_NAME_1, SECRET_NAME_2]:

        res = secrets_client.get_secret_value(SecretId=name)

        data = json.loads(res["SecretString"])

        keys.append(data["api_key"])

    return keys


def choose_key(keys):

    return random.choice(keys)


def call_rawg_api(api_key, start_date, end_date, page):

    params = {
        "key": api_key,
        "dates": f"{start_date},{end_date}",
        "page": page,
        "page_size": PAGE_SIZE,
        "ordering": "-updated"
    }

    query = "&".join([f"{k}={v}" for k, v in params.items()])

    url = f"{RAWG_BASE_URL}?{query}"

    req = AWSRequest("GET", url)

    resp = http_session.send(req.prepare())

    return resp.status_code, resp.content.decode()


def upload(data, name):

    s3_client.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=S3_RAW_FOLDER + name,
        Body=json.dumps(data),
        ContentType="application/json"
    )


# --------------------------------------------------


def lambda_handler(event, context):

    print("=== DAILY EXTRACTOR START ===")


    keys = get_api_keys()

    today = datetime.utcnow().date()

    start = today - timedelta(days=1)
    end = today


    start_s = start.strftime("%Y-%m-%d")
    end_s = end.strftime("%Y-%m-%d")


    page = 1
    total = 0


    while True:

        key = choose_key(keys)

        print("Page:", page)


        status, body = call_rawg_api(key, start_s, end_s, page)


        if status != 200:

            print("API error:", status)
            break


        data = json.loads(body)

        results = data.get("results", [])


        if not results:
            break


        name = f"rawg_{start_s}_{end_s}_p{page}.json"


        upload(results, name)


        total += len(results)


        if not data.get("next"):
            break


        page += 1


        time.sleep(REQUEST_DELAY_SECONDS)


    print("Downloaded:", total)
    print("=== DAILY EXTRACTOR END ===")


    return {
        "statusCode": 200,
        "total": total
    }