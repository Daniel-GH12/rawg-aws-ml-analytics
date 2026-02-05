from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import xgboost as xgb
import pandas as pd
import joblib
import uvicorn
import os
import psycopg2
import google.generativeai as genai

import matplotlib.pyplot as plt
import seaborn as sns
import io
from fastapi.responses import StreamingResponse

# CONFIGURACIÓN
DB_CONFIG = {
    "host": "data-rawg.cfsieqiau5qy.eu-north-1.rds.amazonaws.com",
    "database": "postgres",
    "user": "postgres",
    "password": "data-rawg",
    "port": "5432"
}

# Configuración Gemini
genai.configure(api_key="AIzaSyBpMiEPkM1khLwMiOIBtOh6-9ZFiZoq7oU")
gemini_model = genai.GenerativeModel('models/gemini-2.5-flash')

# INICIALIZAR APP
app = FastAPI(title="RAWG Games API")

# CARGAR MODELO XGBOOST
MODEL_PATH = "./models/game_predictor.json"
COLUMNS_PATH = "./models/model_columns.pkl"

if not os.path.exists(MODEL_PATH) or not os.path.exists(COLUMNS_PATH):
    raise RuntimeError("No se encontraron los archivos del modelo XGBoost.")

xgb_model = xgb.XGBClassifier()
xgb_model.load_model(MODEL_PATH)
model_columns = joblib.load(COLUMNS_PATH)

# SCHEMAS Pydantic
class GameData(BaseModel):
    playtime: float
    suggestions_count: float
    release_month: int
    genres: str
    platforms: str
    developers: str
    tags: str

class Question(BaseModel):
    text: str

# ENDPOINTS
@app.get("/")
def home():
    return {"message": "API RAWG v1.0 - Gemini + XGBoost"}

@app.post("/predict")
def predict(data: GameData):
    try:
        input_dict = data.dict()
        input_df = pd.DataFrame([input_dict])
        
        # Procesar Tags
        top_tags = ['Singleplayer', 'Multiplayer', 'Atmospheric', 'Great Soundtrack', 'Open World']
        for tag in top_tags:
            input_df[f'tag_{tag}'] = 1 if tag in input_dict['tags'] else 0
        
        # Dummies
        genres_dummies = input_df['genres'].str.get_dummies(sep=',')
        platforms_dummies = input_df['platforms'].str.get_dummies(sep=',')
        developers_dummies = input_df['developers'].str.get_dummies(sep=',')
        
        X_input = pd.concat([
            input_df[['playtime', 'suggestions_count', 'release_month']], 
            input_df[[f'tag_{t}' for t in top_tags]],
            genres_dummies, 
            platforms_dummies,
            developers_dummies
        ], axis=1)
        
        X_input.columns = [col.replace('[','').replace(']','').replace('<','').replace('>','')
                           .replace(' ','_').replace('-','_').replace(',','') for col in X_input.columns]

        X_final = X_input.reindex(columns=model_columns, fill_value=0)

        prediction = xgb_model.predict(X_final.values)
        probability = xgb_model.predict_proba(X_final.values)[0][1]

        return {
            "success_prediction": int(prediction[0]),
            "success_probability": round(float(probability), 4),
            "verdict": "ÉXITO" if prediction[0] == 1 else "FRACASO"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask-text")
def ask_db(question: Question):
    try:
        esquema = """
        Tablas:
        - games (game_id, game_name, game_released, game_rating, playtime, suggestions_count)
        - developers (developer_id, developer_name)
        - genres (genre_id, genre_name)
        - platforms (platform_id, platform_name)
        - games_status (game_id, yet, owned, beaten, toplay, dropped, playing)
        Relaciones: games_developers, games_genres, games_platforms
        """

        prompt = f"{esquema}\nTarea: SQL de PostgreSQL para: '{question.text}'\nReglas: Solo SQL, usa ILIKE, sin ```sql."

        response = gemini_model.generate_content(prompt)
        sql_query = response.text.strip().replace("```sql", "").replace("```", "").replace(";", "")

        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(sql_query)
        result = cur.fetchall()
        cur.close()
        conn.close()

        return {"question": question.text, "sql": sql_query, "data": result}
    except Exception as e:
        return {"error": str(e)}
    
@app.post("/ask-visual")
def ask_visual(question: Question):
    try:
        # Prompt ultra estricto
        prompt = f"""
        Base de datos PostgreSQL:
        - games (game_id, game_name)
        - genres (genre_id, genre_name)
        - games_genres (game_id, genre_id)
        - platforms, developers, etc.
        
        Tarea: SQL para "{question.text}"
        Reglas:
        - Responde SOLO con el código SQL.
        - NO incluyas explicaciones, ni notas, ni bloques de código ```sql.
        - Máximo 15 resultados.
        """
        
        response = gemini_model.generate_content(prompt)
        raw_sql = response.text.strip()

        # LIMPIEZA DE SEGURIDAD (Por si Gemini ignora las reglas)
        # Buscamos dónde empieza el SELECT y dónde termina el SQL
        import re
        sql_match = re.search(r"(SELECT.*)", raw_sql, re.IGNORECASE | re.DOTALL)
        if sql_match:
            sql_query = sql_match.group(1).split(';')[0].strip()
        else:
            sql_query = raw_sql # Si no encuentra SELECT, enviamos lo que hay (fallback)

        # Obtener datos con Pandas
        conn = psycopg2.connect(**DB_CONFIG)
        # Usamos read_sql_query porque es directo para gráficos
        df = pd.read_sql_query(sql_query, conn)
        conn.close()

        if df.empty:
            return {"error": "No hay datos", "sql_intentado": sql_query}

        # Generar el gráfico
        plt.figure(figsize=(12, 6))
        # Usamos la primera columna para X y la segunda para Y
        sns.barplot(data=df, x=df.columns[0], y=df.columns[1], palette="magma")
        
        plt.title(f"Visualización: {question.text}", fontsize=15)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        # Guardar en memoria y enviar
        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        plt.close()

        return StreamingResponse(buf, media_type="image/png")

    except Exception as e:
        return {"error": str(e), "sql_raw": raw_sql if 'raw_sql' in locals() else "N/A"}

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) ## Correr en http://127.0.0.1:8000/docs