"""
Lambda para extracción diaria de datos de RAWG API
Trigger: EventBridge (cron diario a las 2 AM UTC)
Output: JSON en S3
"""

import json
import os
from datetime import datetime, timedelta, timezone
from time import sleep

import boto3
import requests



BUCKET_NAME = os.environ.get("RAWG_BUCKET", "project-api-load-rawg-cris")
SECRET_ID = os.environ.get("RAWG_SECRET_ID", "RAWG_API_KEY")  # nombre/ARN del secreto
RAWG_BASE_URL = "https://api.rawg.io/api/games"


def lambda_handler(event, context):
    print("=" * 70)
    print("INICIANDO EXTRACCIÓN DIARIA DE RAWG")
    print("=" * 70)

    try:
        # 1) Credenciales
        print("\nObteniendo credenciales...")
        api_key = get_rawg_api_key(secret_id=SECRET_ID)

        # 2) Fecha (UTC) - ayer
        fecha_extraccion = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
        output_key = f"games_{fecha_extraccion}.json"

        print(f"Fecha de extracción (UTC): {fecha_extraccion}")
        print(f"S3 output: s3://{BUCKET_NAME}/{output_key}")

        # 3) Extraer
        print("\nExtrayendo datos desde RAWG API...")
        resultados, errores = extraer_rawg_diario(api_key, fecha_extraccion)

        print(f"Juegos extraídos: {len(resultados)}")
        if errores:
            print(f"Errores encontrados: {len(errores)}")

        # 4) Sin datos: OK y salimos
        if not resultados:
            return {
                "statusCode": 200,
                "body": json.dumps(
                    {
                        "mensaje": "No hay juegos nuevos para esta fecha",
                        "fecha": fecha_extraccion,
                        "registros": 0,
                    },
                    ensure_ascii=False,
                ),
            }

        # 5) Guardar en S3
        s3 = boto3.client("s3")
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=output_key,
            Body=json.dumps(resultados, ensure_ascii=False),  # sin indent para ahorrar tamaño
            ContentType="application/json",
            Metadata={
                "fecha_extraccion": fecha_extraccion,
                "total_juegos": str(len(resultados)),
                "errores": str(len(errores)),
            },
        )

        print("\nEXTRACCIÓN COMPLETADA EXITOSAMENTE")
        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "mensaje": "Extracción diaria completada",
                    "fecha": fecha_extraccion,
                    "registros": len(resultados),
                    "archivo": output_key,
                    "errores": len(errores),
                },
                ensure_ascii=False,
            ),
        }

    except Exception as e:
        import traceback

        print("\n" + "=" * 70)
        print("ERROR EN EXTRACCIÓN")
        print("=" * 70)
        print(f"Error: {e}")
        traceback.print_exc()

        return {
            "statusCode": 500,
            "body": json.dumps(
                {"error": str(e), "traceback": traceback.format_exc()},
                ensure_ascii=False,
            ),
        }


def get_rawg_api_key(secret_id: str) -> str:
    """
    Obtiene la API Key de RAWG desde Secrets Manager.

    Soporta dos formatos de secreto:
    1) Texto plano: "TU_API_KEY"
    2) JSON: {"RAWG_API_KEY":"..."} o {"api_key":"..."} o {"key":"..."}
    """
    client = boto3.client("secretsmanager")
    response = client.get_secret_value(SecretId=secret_id)

    secret_str = response.get("SecretString")
    if not secret_str:
        raise RuntimeError(f"El secreto {secret_id} no tiene SecretString")

    # 1) Intentar JSON
    try:
        obj = json.loads(secret_str)
        # claves típicas
        for k in ("RAWG_API_KEY", "api_key", "key", "RAWG_KEY"):
            if k in obj and obj[k]:
                return obj[k]
        # si era JSON pero no encontramos clave
        raise RuntimeError(
            f"El secreto {secret_id} es JSON pero no contiene una clave válida (RAWG_API_KEY/api_key/key/RAWG_KEY)"
        )
    except json.JSONDecodeError:
        # 2) Texto plano
        return secret_str.strip()


def extraer_rawg_diario(api_key: str, fecha: str):
    """
    Extrae juegos de RAWG API para una fecha (YYYY-MM-DD).
    """
    resultados = []
    errores = []

    params = {"key": api_key, "page_size": 40, "dates": f"{fecha},{fecha}"}

    # Reintentos simples ante 429 / errores transitorios
    for intento in range(1, 4):
        try:
            resp = requests.get(RAWG_BASE_URL, params=params, timeout=30)

            if resp.status_code == 200:
                data = resp.json()
                print(f'{data.get("count", 0)} juegos encontrados para {fecha}')
                resultados.extend(data.get("results", []))
                return resultados, errores

            if resp.status_code == 429:
                espera = 2 * intento
                print(f"429 Rate limit. Reintento {intento}/3 en {espera}s...")
                sleep(espera)
                continue

            # Otros errores HTTP
            errores.append({"fecha": fecha, "status": resp.status_code, "body": resp.text[:200]})
            return resultados, errores

        except requests.exceptions.Timeout:
            errores.append({"fecha": fecha, "error": "timeout"})
            return resultados, errores

        except Exception as e:
            errores.append({"fecha": fecha, "error": str(e)})
            return resultados, errores

    return resultados, errores
