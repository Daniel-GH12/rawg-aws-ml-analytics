import boto3
import json
from botocore.exceptions import ClientError

# Cache para NO repetir llamadas a Secrets Manager
_CACHE = {}

def get_secret(secret_name: str, region_name: str = "eu-north-1"):
    """
    Devuelve:
    - dict si el secreto es JSON
    - str si el secreto es string plano
    Cachea por nombre de secreto.
    """
    if secret_name in _CACHE:
        return _CACHE[secret_name]

    client = boto3.client("secretsmanager", region_name = region_name)

    try:
        response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        raise e

    s = response["SecretString"].strip()

    if s.startswith("{") and s.endswith("}"):
        value = json.loads(s)
    else:
        value = s

    _CACHE[secret_name] = value
    return value



_RAWG_KEY = None

def get_rawg_api_key():
    secret = get_secret(secret_name = "rawg/api_key", region_name = "eu-north-1")
    return secret["RAWG_API_KEY"].strip()

def get_rawg_api_key_cached():
    global _RAWG_KEY
    if _RAWG_KEY is None:
        _RAWG_KEY = get_rawg_api_key()
    return _RAWG_KEY



def get_rds_credentials(secret_name: str = "Postgre", region_name: str = "eu-north-1")-> dict:
    secret = get_secret(secret_name, region_name = "eu-north-1")
    if not isinstance(secret, dict):
        raise TypeError(f"El secreto {secret_name} no es JSON.")
    return secret

