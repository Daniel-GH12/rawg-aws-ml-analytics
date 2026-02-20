"""
FastAPI - Endpoints Text-to-SQL con Gemini + Predicción ML
Proyecto: rawg-aws-ml-analytics
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import joblib
from typing import Optional, List, Dict, Any
from pathlib import Path
import sys
import os

# Configurar paths
sys.path.insert(0, os.path.abspath('..'))

# Imports del proyecto
from models.db_connection import query_to_dataframe
from models.text_to_sql_gemini import (
    generate_sql_for_visual,
    generate_sql_for_text,
    generate_text_response
)

# Configurar matplotlib
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# ============================================================================
# CARGAR MODELO ML Y FEATURES
# ============================================================================

# Ruta al directorio de modelos
MODELS_DIR = Path(__file__).parent.parent / 'models'

def load_latest_model():
    """
    Carga el modelo XGBoost más reciente y sus features
    """
    try:
        # Buscar todos los modelos disponibles
        model_files = list(MODELS_DIR.glob('xgb_success_model_*.pkl'))
        
        if not model_files:
            return None, None
        
        # Obtener el modelo más reciente por timestamp
        latest_model_file = max(model_files, key=lambda x: x.stat().st_mtime)
        
        # Cargar modelo
        model = joblib.load(latest_model_file)
        print(f"Modelo cargado: {latest_model_file.name}")
        
        # Cargar features
        features_file = MODELS_DIR / 'success_features.pkl'
        
        if not features_file.exists():
            print(f"Archivo de features no encontrado")
            return model, None
        
        features = joblib.load(features_file)
        print(f"Features cargadas: {len(features)} features")
        
        return model, features
        
    except Exception as e:
        print(f"No se pudo cargar el modelo: {e}")
        return None, None


# Cargar modelo al iniciar la aplicación
print("\n" + "=" * 80)
print("INICIANDO FASTAPI - RAWG VIDEOGAMES")
print("=" * 80)

ML_MODEL, MODEL_FEATURES = load_latest_model()

if ML_MODEL is not None:
    print(f"API lista con modelo ML")
    if MODEL_FEATURES:
        print(f"   Features: {len(MODEL_FEATURES)}")
else:
    print("API iniciará sin endpoint /predict")
    print("   (modelo ML no disponible)")

print("=" * 80 + "\n")


# ============================================================================
# CREAR APP FASTAPI
# ============================================================================

app = FastAPI(
    title="RAWG Videogames API -ML + Text-to-SQL",
    description="API con predicción ML (XGBoost) y Text-to-SQL (Gemini) para análisis de videojuegos"
   )

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# MODELOS PYDANTIC
# ============================================================================

class GameInput(BaseModel):
    """Datos de entrada para predicción - 11 features en orden exacto del modelo"""
    
    # ORDEN EXACTO según success_features.pkl:
    # 0: num_platforms
    num_platforms: int = Field(..., ge=1, description="Número de plataformas")
    # 1: num_stores
    num_stores: int = Field(..., ge=1, description="Número de tiendas")
    # 2: num_genres
    num_genres: int = Field(..., ge=1, description="Número de géneros")
    # 3: num_tags
    num_tags: int = Field(..., ge=1, description="Número de tags")
    # 4: years_since_release
    years_since_release: int = Field(..., ge=0, description="Años desde lanzamiento")
    # 5: recency_score
    recency_score: int = Field(..., ge=0, description="Score de antigüedad")
    # 6: esrb_name
    esrb_name: str = Field(..., description="Clasificación ESRB")
    # 7: release_year
    release_year: str = Field(..., description="Año de lanzamiento")
    # 8: has_multiplayer
    has_multiplayer: str = Field(..., description="Tiene multijugador: '0' o '1'")
    # 9: has_singleplayer
    has_singleplayer: str = Field(..., description="Tiene un jugador: '0' o '1'")
    # 10: is_indie
    is_indie: str = Field(..., description="Es indie: '0' o '1'")
    
    class Config:
        json_schema_extra = {
            "example": {
                "num_platforms": 5,
                "num_stores": 3,
                "num_genres": 2,
                "num_tags": 10,
                "years_since_release": 2,
                "recency_score": 2,
                "esrb_name": "Everyone",
                "release_year": "2022",
                "has_multiplayer": "1",
                "has_singleplayer": "1",
                "is_indie": "0"
            }
        }
class PredictionResponse(BaseModel):
    """Respuesta del endpoint /predict"""
    prediction: str = Field(..., description="Predicción: 'Éxito' o 'No Éxito'")
    prediction_class: int = Field(..., description="Clase predicha: 1 (Éxito) o 0 (No Éxito)")
    probability_success: float = Field(..., description="Probabilidad de éxito (0-1)")
    probability_no_success: float = Field(..., description="Probabilidad de no éxito (0-1)")
    confidence: str = Field(..., description="Nivel de confianza: Alta, Media, Baja")
    features_used: int = Field(..., description="Número de features utilizadas")
    
    class Config:
        json_schema_extra = {
            "example": {
                "prediction": "Éxito",
                "prediction_class": 1,
                "probability_success": 0.87,
                "probability_no_success": 0.13,
                "confidence": "Alta",
                "features_used": 45
            }
        }


class VisualResponse(BaseModel):
    """Respuesta del endpoint /ask-visual"""
    question: str = Field(..., description="Pregunta original del usuario")
    sql_generated: str = Field(..., description="SQL generado por Gemini")
    data: List[Dict[str, Any]] = Field(..., description="Datos obtenidos")
    chart_base64: str = Field(..., description="Gráfico en formato base64")
    rows_count: int = Field(..., description="Número de filas retornadas")
    
class TextResponse(BaseModel):
    """Respuesta del endpoint /ask-text"""
    question: str = Field(..., description="Pregunta original del usuario")
    sql_generated: str = Field(..., description="SQL generado por Gemini")
    answer: str = Field(..., description="Respuesta en lenguaje natural")
    data: List[Dict[str, Any]] = Field(..., description="Datos obtenidos")
    rows_count: int = Field(..., description="Número de filas retornadas")
    
class HealthResponse(BaseModel):
    """Respuesta del health check"""
    status: str
    service: str
    version: str
    model_loaded: bool
    features_count: Optional[int]

# ============================================================================
# FUNCIONES AUXILIARES PARA ML
# ============================================================================

def create_features_dataframe(game_input: GameInput) -> pd.DataFrame:
    """
    Crea DataFrame con las 11 features en el orden EXACTO del modelo
    
    Orden según success_features.pkl:
    0-num_platforms, 1-num_stores, 2-num_genres, 3-num_tags,
    4-years_since_release, 5-recency_score, 6-esrb_name, 7-release_year,
    8-has_multiplayer, 9-has_singleplayer, 10-is_indie
    """
    
    # Crear lista en el orden exacto (NO dict para evitar reordenamientos)
    data = {
        'num_platforms': game_input.num_platforms,
        'num_stores': game_input.num_stores,
        'num_genres': game_input.num_genres,
        'num_tags': game_input.num_tags,
        'years_since_release': game_input.years_since_release,
        'recency_score': game_input.recency_score,
        'esrb_name': game_input.esrb_name,
        'release_year': game_input.release_year,
        'has_multiplayer': game_input.has_multiplayer,
        'has_singleplayer': game_input.has_singleplayer,
        'is_indie': game_input.is_indie,
    }
    
    # Crear DataFrame
    df = pd.DataFrame([data])
    
    # Reordenar según MODEL_FEATURES
    if MODEL_FEATURES is not None:
        df = df[MODEL_FEATURES]
    
    # Asegurar tipos correctos
    numeric_cols = ['num_platforms', 'num_stores', 'num_genres', 'num_tags', 
                    'years_since_release', 'recency_score']
    for col in numeric_cols:
        df[col] = df[col].astype('int64')
    
    categorical_cols = ['esrb_name', 'release_year', 'has_multiplayer', 
                       'has_singleplayer', 'is_indie']
    for col in categorical_cols:
        df[col] = df[col].astype('object')
    
    return df

    
def get_confidence_level(probability: float) -> str:
  
    if probability >= 0.8 or probability <= 0.2:
        return "Alta"
    elif probability >= 0.65 or probability <= 0.35:
        return "Media"
    else:
        return "Baja"


# ============================================================================
# FUNCIONES AUXILIARES PARA VISUALIZACIÓN
# ============================================================================

def create_chart(df: pd.DataFrame, chart_type: str = "auto") -> plt.Figure:
    """
    Crea gráfico matplotlib desde DataFrame
    
    Args:
        df: DataFrame con columnas label y value
        chart_type: "barh", "line", "auto"
        
    Returns:
        Figure de matplotlib
    """
    
    if df.empty or not {"label", "value"}.issubset(df.columns):
        raise ValueError("DataFrame debe tener columnas 'label' y 'value'")
    
    # Detectar tipo automático
    if chart_type == "auto":
        try:
            # Intentar parsear como fecha
            pd.to_datetime(df['label'].iloc[0])
            chart_type = "line"
        except:
            chart_type = "barh"
    
    # Crear figura
    fig, ax = plt.subplots(figsize=(12, 7))
    
    if chart_type == "barh":
        # Gráfico de barras horizontales
        df_sorted = df.sort_values("value", ascending=True).tail(15)  # Top 15
        colors = plt.cm.viridis(range(len(df_sorted)))
        
        ax.barh(df_sorted["label"].astype(str), df_sorted["value"], color=colors, edgecolor='black', linewidth=0.8)
        ax.set_xlabel("Valor", fontweight='bold', fontsize=12)
        ax.set_ylabel("Categoría", fontweight='bold', fontsize=12)
        
        # Añadir valores en las barras
        for i, (idx, row) in enumerate(df_sorted.iterrows()):
            ax.text(row['value'] + (df_sorted['value'].max() * 0.01), i, 
                   f"{row['value']:,.0f}", va='center', fontweight='bold', fontsize=10)
        
    elif chart_type == "line":
        # Gráfico de línea temporal
        df['label_dt'] = pd.to_datetime(df['label'] + '-01')  # Añadir día si falta
        df_sorted = df.sort_values("label_dt")
        
        ax.plot(df_sorted["label_dt"], df_sorted["value"], 
               marker='o', linewidth=2.5, markersize=8, color='steelblue')
        ax.fill_between(df_sorted["label_dt"], df_sorted["value"], alpha=0.3, color='steelblue')
        
        ax.set_xlabel("Fecha", fontweight='bold', fontsize=12)
        ax.set_ylabel("Valor", fontweight='bold', fontsize=12)
        plt.xticks(rotation=45, ha='right')
    
    ax.set_title("Visualización de Datos - RAWG Videogames", 
                fontsize=14, fontweight='bold', pad=20)
    ax.grid(alpha=0.3, linestyle='--')
    plt.tight_layout()
    
    return fig


def fig_to_base64(fig: plt.Figure) -> str:
    """
    Convierte figura matplotlib a string base64
    
    Args:
        fig: Figure de matplotlib
        
    Returns:
        String base64 de la imagen PNG
    """
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_base64


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/", tags=["Root"])
def root():
    """Endpoint raíz con información de la API"""
    return {
        "message": "RAWG Videogames API -ML + Text-to-SQL con Gemini",
        "version": "2.0.0",
        "description":"API con predicción ML (XGBoost) y consultas en lenguaje natural (Gemini)",
        "endpoints": {
            "predict": "POST /predict - Predice éxito de videojuego",
            "visual": "GET /ask-visual - Consulta con gráfico",
            "text": "GET /ask-text - Consulta con respuesta textual",
            "health": "GET /health - Estado del servicio",
            "docs": "GET /docs - Documentación interactiva"
        },
        "model_status": {
            "loaded": ML_MODEL is not None,
            "features_count": len(MODEL_FEATURES) if MODEL_FEATURES else 0
        },
        "examples": {
            "predict": {
                "method": "POST",
                "url": "/predict",
                "body": {
                    "game_rating": 4.5,
                    "ratings_count": 1000,
                    "game_added": 5000,
                    "num_platforms": 5,
                    "num_stores": 3
                }
            },
            "visual": [
                "Top 10 géneros con más juegos",
                "Evolución de juegos por año desde 2015"
            ],
            "text": [
                "¿Cuál es el juego mejor valorado?",
                "¿Cuántos juegos hay en total?"
            ]
        }
    }

@app.post("/predict", response_model=PredictionResponse, tags=["Machine Learning"])
def predict_success(game_input: GameInput):
    """Predice si un videojuego será un éxito"""
    
    # Verificar que el modelo está cargado
    if ML_MODEL is None:
        raise HTTPException(
            status_code=503,
            detail="Modelo de predicción no disponible"
        )  # ← Faltaba cerrar aquí
    
    try:
        # Crear features
        X = create_features_dataframe(game_input)
        
        # El Pipeline hace preprocesamiento + predicción automáticamente
        prediction_class = int(ML_MODEL.predict(X)[0])
        prediction_proba = ML_MODEL.predict_proba(X)[0]
        
        prob_no_success = float(prediction_proba[0])
        prob_success = float(prediction_proba[1])
        
        confidence = get_confidence_level(prob_success)
        
        return PredictionResponse(
            prediction="Éxito" if prediction_class == 1 else "No Éxito",
            prediction_class=prediction_class,
            probability_success=round(prob_success, 4),
            probability_no_success=round(prob_no_success, 4),
            confidence=confidence,
            features_used=11
        )
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Error en predicción",
                "message": str(e),
                "traceback": error_details
            }
        )

@app.get("/ask-visual", response_model=VisualResponse, tags=["Text-to-SQL"])
def ask_visual(
    question: str = Query(
        ..., 
        description="Pregunta para visualizar",
        example="Top 10 géneros con más juegos"
    )
):
    """
    Endpoint para preguntas con respuesta visual (gráfico)
    
    Genera SQL automáticamente usando Gemini, ejecuta la query,
    y retorna gráfico en base64.
    
    **Proceso:**
    1. Gemini genera SQL a partir de la pregunta
    2. Se ejecuta el SQL en la base de datos
    3. Se valida que retorne columnas 'label' y 'value'
    4. Se genera gráfico automáticamente
    5. Se retorna datos + gráfico en base64
    
    **Ejemplos de preguntas:**
    - "Top 10 géneros con más juegos"
    - "Evolución de juegos lanzados por año desde 2015"
    - "Plataformas más populares"
    - "Rating promedio por año"
    - "Top stores con más juegos"
    """
    
    # Validar pregunta
    if not question or len(question.strip()) < 5:
        raise HTTPException(
            status_code=400, 
            detail="La pregunta debe tener al menos 5 caracteres"
        )
    
    try:
        # Paso 1: Generar SQL con Gemini
        sql = generate_sql_for_visual(question)
        
        if not sql:
            raise HTTPException(
                status_code=500,
                detail="No se pudo generar SQL válido. Intenta reformular la pregunta."
            )
        
        # Paso 2: Ejecutar SQL
        df = query_to_dataframe(sql)
        
        if df.empty:
            raise HTTPException(
                status_code=404,
                detail="La consulta no retornó datos. Intenta con otra pregunta."
            )
        
        # Paso 3: Validar formato
        if not {"label", "value"}.issubset(df.columns):
            raise HTTPException(
                status_code=500,
                detail=f"El SQL generado no retornó el formato correcto. Columnas obtenidas: {list(df.columns)}"
            )
        
        # Paso 4: Crear gráfico
        fig = create_chart(df, chart_type="auto")
        chart_base64 = fig_to_base64(fig)
        
        # Paso 5: Preparar respuesta
        return VisualResponse(
            question=question,
            sql_generated=sql,
            data=df.to_dict(orient='records'),
            chart_base64=chart_base64,
            rows_count=len(df)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando la pregunta: {str(e)}"
        )

@app.get("/ask-visual-image", tags=["Text-to-SQL"])
def ask_visual_image(
    question: str = Query(
        ..., 
        description="Pregunta para visualizar",
        example="Top 10 géneros con más juegos"
    )
):
    """
    Pregunta con gráfico directo (PNG)
    
    A diferencia de /ask-visual que retorna JSON con base64,
    este endpoint retorna la imagen PNG directamente.
    Puedes abrirlo directamente en el navegador.
    """
    
    if not question or len(question.strip()) < 5:
        raise HTTPException(
            status_code=400, 
            detail="La pregunta debe tener al menos 5 caracteres"
        )
    
    try:
        # Generar SQL con Gemini
        sql = generate_sql_for_visual(question)
        
        if not sql:
            raise HTTPException(
                status_code=500,
                detail="No se pudo generar SQL válido"
            )
        
        # Ejecutar query
        df = query_to_dataframe(sql)
        
        if df.empty:
            raise HTTPException(
                status_code=404,
                detail="La consulta no retornó datos"
            )
        
        if not {"label", "value"}.issubset(df.columns):
            raise HTTPException(
                status_code=500,
                detail=f"SQL no retornó formato correcto. Columnas: {list(df.columns)}"
            )
        
        # Crear gráfico
        fig = create_chart(df, chart_type="auto")
        
        # Convertir a bytes (en memoria)
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        
        # Retornar imagen directamente
        return StreamingResponse(buf, media_type="image/png")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )



@app.get("/ask-text", response_model=TextResponse, tags=["Text-to-SQL"])
def ask_text(
    question: str = Query(
        ...,
        description="Pregunta para respuesta textual",
        example="¿Cuál es el juego mejor valorado?"
    )
):
    """
    Endpoint para preguntas con respuesta textual
    
    Genera SQL automáticamente usando Gemini, ejecuta la query,
    y retorna respuesta en lenguaje natural.
    
    **Proceso:**
    1. Gemini genera SQL a partir de la pregunta
    2. Se ejecuta el SQL en la base de datos
    3. Gemini genera respuesta en lenguaje natural
    4. Se retorna respuesta + datos
    
    **Ejemplos de preguntas:**
    - "¿Cuál es el juego mejor valorado?"
    - "¿Cuántos juegos hay en total?"
    - "¿Qué género tiene mejor rating promedio?"
    - "¿Cuáles son los juegos con más playtime?"
    - "¿Qué juegos se están jugando más ahora?"
    """
    
    # Validar pregunta
    if not question or len(question.strip()) < 5:
        raise HTTPException(
            status_code=400,
            detail="La pregunta debe tener al menos 5 caracteres"
        )
    
    try:
        # Paso 1: Generar SQL con Gemini
        sql = generate_sql_for_text(question)
        
        if not sql:
            raise HTTPException(
                status_code=500,
                detail="No se pudo generar SQL válido. Intenta reformular la pregunta."
            )
        
        # Paso 2: Ejecutar SQL
        df = query_to_dataframe(sql)
        
        if df.empty:
            return TextResponse(
                question=question,
                sql_generated=sql,
                answer="No se encontraron datos para responder tu pregunta. Intenta reformularla.",
                data=[],
                rows_count=0
            )
        
        # Paso 3: Generar respuesta textual con Gemini
        data_summary = df.to_string(index=False, max_rows=20)
        
        try:
            answer = generate_text_response(question, data_summary)
        except Exception:
            # Si falla Gemini, respuesta genérica
            answer = f"Encontré {len(df)} resultado(s). Ver datos para más detalles."
        
        # Paso 4: Preparar respuesta
        return TextResponse(
            question=question,
            sql_generated=sql,
            answer=answer,
            data=df.to_dict(orient='records'),
            rows_count=len(df)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando la pregunta: {str(e)}"
        )

@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """
    Health check endpoint
    
    Verifica que el servicio está funcionando correctamente.
    """
    return HealthResponse(
        status="healthy",
        service="rawg-ml-api",
        version="3.0.0",
        model_loaded=ML_MODEL is not None,  # ← Añadir
        features_count=len(MODEL_FEATURES) if MODEL_FEATURES else None  # ← Añadir
    )


# ============================================================================
# EJECUTAR SERVIDOR
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    print("\nIniciando servidor FastAPI...")
    print("URL: http://localhost:8000")
    print("Docs: http://localhost:8000/docs")
    print("\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )