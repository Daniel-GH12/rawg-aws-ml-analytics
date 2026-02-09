"""
Extracción histórica RAWG (10 años) -> S3
- Lee API key desde Secrets Manager (o env var)
- Recorre un rango de fechas día a día (como el notebook)
- Pagina todas las páginas de RAWG para cada fecha
- Guarda UN archivo por día en S3 (evita un JSON gigantesco)
"""

import json
import os
from datetime import datetime, timedelta, date
from time import sleep

import boto3
import requests

BASE_URL = "https://api.rawg.io/api/games"


BUCKET_NAME = os.environ.get("RAWG_BUCKET", "project-api-load-rawg-cris")
SECRET_ID = os.environ.get("RAWG_SECRET_ID", "RAWG_API_KEY")


S3_PREFIX = os.environ.get("RAWG_HIST_PREFIX", "historical/rawg/games_by_day")


def get_rawg_api_key(secret_id: str) -> str:
    """
    Lee API key desde Secrets Manager.
    Soporta secreto en texto plano o JSON (api_key/key/RAWG_API_KEY). :contentReference[oaicite:2]{index=2}
    """
    client = boto3.client("secretsmanager")
    response = client.get_secret_value(SecretId=secret_id)

    secret_str = response.get("SecretString")
    if not secret_str:
        raise RuntimeError(f"El secreto {secret_id} no tiene SecretString")

    # Intentar JSON
    try:
        obj = json.loads(secret_str)
        for k in ("RAWG_API_KEY", "api_key", "key", "RAWG_KEY"):
            if k in obj and obj[k]:
                return obj[k]
        raise RuntimeError(
            f"El secreto {secret_id} es JSON pero no contiene RAWG_API_KEY/api_key/key/RAWG_KEY"
        )
    except json.JSONDecodeError:
        return secret_str.strip()


def s3_key_for_day(fecha: str) -> str:
    # day = "YYYY-MM-DD"
    yyyy, mm, dd = day.split("-")
    return f"{S3_PREFIX}/games_{fecha}.json"

def extraer_rawg_por_dia(api_key: str, fecha: str):
    """
    1 request por día (sin paginar).
    Maneja 429 con espera y reintento simple.
    """
    params = {
        "key": api_key,
        "page_size": PAGE_SIZE,
        "dates": f"{fecha},{fecha}"
    }
    try:
        r = requests.get(BASE_URL, params=params, timeout=30)

        if r.status_code == 200:
            data = r.json()
            count = data.get("count", 0)
            juegos = data.get("results", [])
            print(f"{count} juegos encontrados para {fecha}")
            return juegos, None
            
        if r.status_code == 429:
            print("Rate limit (429). Esperando 5s y reintentando...")
            sleep(5)
            r2 = requests.get(BASE_URL, params=params, timeout=30)
            if r2.status_code == 200:
                data = r2.json()
                count = data.get("count", 0)
                juegos = data.get("results", [])
                print(f"{count} juegos encontrados para {fecha} (reintento)")
                return juegos, None
            return [], {"fecha": fecha, "status": r2.status_code, "body": r2.text[:200]}

        return [], {"fecha": fecha, "status": r.status_code, "body": r.text[:200]}

    except requests.exceptions.Timeout:
        return [], {"fecha": fecha, "error": "timeout"}

    except Exception as e:
        return [], {"fecha": fecha, "error": str(e)}

def run_historico(start_date: str, end_date: str):
   
    print("\n" + "=" * 70)
    print(f"=== EXTRACCIÓN HISTÓRICO DATOS DESDE {start_date} HASTA {end_date} ===")
    print("=" * 70)

    api_key = get_rawg_api_key_cached()
    s3 = boto3.client("s3")

    fecha_inicio = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    fecha_fin = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    dias_total = (fecha_fin - fecha_inicio).days + 1  # fin incluido

    print(f"Extrayendo datos desde {fecha_inicio.strftime('%Y-%m-%d')} hasta {fecha_fin.strftime('%Y-%m-%d')}")
    print(f"Total de días a procesar: {dias_total}\n")

    resultados = []
    errores = []

    for i in range(dias_total):
        fecha = (fecha_inicio + timedelta(days=i)).strftime("%Y-%m-%d")

        print(f"\n--- Día {i+1}/{dias_total}: {fecha} ---")

        juegos, err = extraer_rawg_por_dia(api_key, fecha)

        
        resultados.append({"fecha": fecha, "results": juegos})
        if err:
            errores.append(err)

        key = s3_key_for_day(fecha)
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=key,
            Body=json.dumps(juegos, ensure_ascii=False),
            ContentType="application/json",
            Metadata={"fecha": fecha, "total_juegos": str(len(juegos))}
        )
        print(f"Guardado en S3: s3://{BUCKET_NAME}/{key} (juegos: {len(juegos)})")

        # Pausa suave para no quemar rate limit (muy parecido a notebook)
        sleep(1)

    # Guardar un resumen final (manifest) como “cierre”
    manifest_key = f"{S3_PREFIX}/manifest_{start_date}_to_{end_date}.json"
    manifest = {
        "start_date": start_date,
        "end_date": end_date,
        "dias_total": dias_total,
        "errores_count": len(errores),
        "errores": errores,
        "generated_at_utc": datetime.now(timezone.utc).isoformat()
    }

    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=manifest_key,
        Body=json.dumps(manifest, ensure_ascii=False, indent=2),
        ContentType="application/json"
    )


    print("\n" + "=" * 70)
    print("FIN HISTÓRICO")
    print(f"Errores: {len(errores)}")
    print(f"Manifest: s3://{BUCKET_NAME}/{manifest_key}")
    print("=" * 70)


if __name__ == "__main__":
    # Ajusta aquí el rango como en tu notebook
    run_historico(start_date="2016-01-01", end_date="2026-01-26")