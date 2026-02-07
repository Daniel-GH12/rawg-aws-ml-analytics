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
import re
from fastapi.responses import StreamingResponse

# --- CONFIGURACIÓN ---
DB_CONFIG = {
    "host": "data-rawg.cfsieqiau5qy.eu-north-1.rds.amazonaws.com",
    "database": "postgres",
    "user": "postgres",
    "password": "data-rawg",
    "port": "5432"
}

# Configuración Gemini (Se usa para ambos endpoints de lenguaje natural)
genai.configure(api_key="AIzaSyBYO-mhkqcwA5jOprPTyYz4CEzU0DtCXXY")
gemini_model = genai.GenerativeModel('models/gemini-2.5-flash')

# --- INICIALIZAR APP ---
app = FastAPI(title="RAWG Games API - XGBoost + Gemini")

# --- CARGAR MODELO XGBOOST ---
MODEL_PATH = "./api/models/game_predictor.json"
COLUMNS_PATH = "./api/models/model_columns.pkl"

if not os.path.exists(MODEL_PATH) or not os.path.exists(COLUMNS_PATH):
    raise RuntimeError("No se han encontrado los archivos del modelo XGBoost.")

xgb_model = xgb.XGBClassifier()
xgb_model.load_model(MODEL_PATH)
model_columns = joblib.load(COLUMNS_PATH)

# --- SCHEMAS ---
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

# --- ENDPOINTS ---

@app.get("/")
def home():
    return {"message": "API RAWG v1.0"}

@app.post("/predict")
def predict(data: GameData):
    try:
        input_dict = data.dict()
        input_df = pd.DataFrame([input_dict])
        
        top_tags = ['Singleplayer', 'Multiplayer', 'Atmospheric', 'Great Soundtrack', 'Open World']
        for tag in top_tags:
            input_df[f'tag_{tag}'] = 1 if tag in input_dict['tags'] else 0
        
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

esquema_completo = """
ESTRUCTURA DE LA BASE DE DATOS (PostgreSQL):
1. games (game_id, game_name, game_released, game_rating, playtime, suggestions_count)
   - Tabla principal de juegos.
2. developers (developer_id, developer_name)
3. genres (genre_id, genre_name)
4. platforms (platform_id, platform_name)
5. games_status (game_id, yet, owned, beaten, toplay, dropped, playing)
   - Contiene contadores numéricos de usuarios para cada estado. No hay una columna 'status'.
6. TABLAS INTERMEDIAS (Relaciones):
   - games_developers (game_id, developer_id)
   - games_genres (game_id, genre_id)
   - games_platforms (game_id, platform_id)

REGLAS CRÍTICAS DE SQL:
- Usa ILIKE para comparaciones de texto (ej: game_name ILIKE '%Witcher%').
- Para filtrar por género, desarrollador o plataforma, DEBES hacer JOIN con la tabla intermedia correspondiente.
- NO uses CTEs (WITH...AS). Usa consultas SELECT directas.
- Si la pregunta pide 'los mejores', ordena por game_rating DESC.
- Si pide 'los más populares' o 'los que más tiene la gente', usa la columna 'owned' de games_status.
- Responde SOLO el código SQL, sin bloques markdown ```sql ni texto adicional.
"""

@app.post("/ask-text")
def ask_text(question: Question):
    try:
        prompt = f"{esquema_completo}\nTarea: SQL para responder: '{question.text}'\nSQL: SELECT"
        response = gemini_model.generate_content(prompt)
        
        # Limpieza por si acaso
        sql_query = response.text.strip().replace("```sql", "").replace("```", "").split(";")[0].strip()
        if not sql_query.upper().startswith("SELECT"):
            sql_query = "SELECT " + sql_query

        conn = psycopg2.connect(**DB_CONFIG)
        df = pd.read_sql_query(sql_query, conn)
        conn.close()

        return {"question": question.text, "sql": sql_query, "results": df.to_dict(orient="records")}
    except Exception as e:
        return {"error": str(e), "sql_intentado": sql_query if 'sql_query' in locals() else "N/A"}

@app.post("/ask-visual")
def ask_visual(question: Question):
    try:
        prompt = f"{esquema_completo}\nTarea: Generar SQL con exactamente 2 COLUMNAS (Eje X y Eje Y) para: '{question.text}'\nSQL: SELECT"
        response = gemini_model.generate_content(prompt)
        
        sql_query = response.text.strip().replace("```sql", "").replace("```", "").split(";")[0].strip()
        if not sql_query.upper().startswith("SELECT"):
            sql_query = "SELECT " + sql_query

        conn = psycopg2.connect(**DB_CONFIG)
        df = pd.read_sql_query(sql_query, conn)
        conn.close()

        if df.empty: return {"error": "No hay datos"}

        plt.figure(figsize=(12, 6))
        # Seleccionamos automáticamente la columna de texto para X y la numérica para Y
        sns.barplot(x=df.iloc[:, 0], y=df.iloc[:, 1], data=df, palette="coolwarm")
        plt.title(f"Visualización: {question.text}")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        plt.close()
        return StreamingResponse(buf, media_type="image/png")
    except Exception as e:
        return {"error": str(e), "sql": sql_query if 'sql_query' in locals() else "N/A"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

## Correr en local en http://127.0.0.1:8000/docs