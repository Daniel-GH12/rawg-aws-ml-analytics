# FastAPI — RAWG Videogames ML + Text-to-SQL

API REST multifuncional para análisis de videojuegos RAWG.  
Combina predicción ML con XGBoost y consultas en lenguaje natural via Gemini AI.

---

##  Características

-  Predicción de éxito de videojuegos con modelo **XGBoost** (`/predict`)
-  Text-to-SQL dinámico con **Gemini AI**
-  Respuestas visuales con gráficos PNG (`/ask-visual`, `/ask-visual-image`)
-  Respuestas textuales en lenguaje natural (`/ask-text`)
-  Credenciales de base de datos gestionadas con **AWS Secrets Manager**
-  Validación de seguridad SQL (solo SELECT)
-  Documentación interactiva automática (Swagger UI)

---

##  Estructura del Proyecto

```
├── fast_api/                     # Aplicación FastAPI principal
│   ├── main.py
│   ├── README.md               
│   └── requirements.txt
├── models/
│   ├── db_connection.py          # Conexión PostgreSQL via AWS Secrets Manager
│   ├── text_to_sql_gemini.py     # Generación SQL y respuestas con Gemini
│   ├── xgb_success_model_*.pkl   # Modelo XGBoost (cargado dinámicamente)
│   └── success_features.pkl      # Features del modelo
└── docs/
    ├── api_documentation.md
    ├── database_schema_sql.md
    ├── aws_deployment_instructions.md
    └── screen_shots/
```

---

##  Instalación

```bash
# 1. Crear entorno virtual
python -m venv venv
source venv/bin/activate       # En Windows: venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt
```

---

##  Configuración — AWS Secrets Manager

Las credenciales de la base de datos **no se almacenan en `.env`**.  
Se obtienen automáticamente desde **AWS Secrets Manager** en cada conexión.

Para que funcione correctamente necesitas:

**1. Credenciales AWS configuradas** en tu entorno:

```bash
# Opción A: Variables de entorno
export AWS_ACCESS_KEY_ID=tu_access_key
export AWS_SECRET_ACCESS_KEY=tu_secret_key
export AWS_DEFAULT_REGION=eu-west-1      # o tu región

# Opción B: AWS CLI
aws configure
```

**2. El secreto en AWS Secrets Manager** debe contener:

```json
{
  "host": "tu-rds-endpoint.rds.amazonaws.com",
  "dbname": "videogames_db",
  "username": "tu_usuario",
  "password": "tu_password",
  "port": "5432"
}
```

**3. Variable de entorno con la Gemini API Key:**

```bash
export GEMINI_API_KEY=tu_api_key    # Obtener en https://aistudio.google.com/apikey
```

>  En EC2, las credenciales AWS se pueden gestionar mediante un **IAM Role** asociado a la instancia, sin necesidad de exportar variables.

---

##  Ejecutar

```bash
# Modo desarrollo (con auto-reload)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Modo producción
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

Al iniciar, la API carga automáticamente el modelo XGBoost más reciente disponible en `models/`.

---

##  Documentación

Con el servidor en marcha:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Documentación completa:** `docs/api_documentation.md`

---

##  Endpoints

### GET `/`
Información general de la API y estado del modelo ML.

---

### GET `/health`
Verifica que el servicio está activo y que el modelo ML está cargado.

```bash
curl http://localhost:8000/health
```

```json
{
  "status": "healthy",
  "service": "rawg-ml-api",
  "version": "3.0.0",
  "model_loaded": true,
  "features_count": 11
}
```

---

### POST `/predict`
Predice si un videojuego será un **éxito** usando el modelo XGBoost.

**Ejemplo:**
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

**Respuesta:**
```json
{
  "prediction": "Éxito",
  "prediction_class": 1,
  "probability_success": 0.87,
  "probability_no_success": 0.13,
  "confidence": "Alta",
  "features_used": 11
}
```

---

### GET `/ask-visual`
Pregunta en lenguaje natural → SQL generado por Gemini → gráfico en **base64 PNG**.

```bash
curl "http://localhost:8000/ask-visual?question=Top%2010%20géneros%20con%20más%20juegos"
```

```json
{
  "question": "Top 10 géneros con más juegos",
  "sql_generated": "SELECT genre_name AS label, COUNT(*) AS value ...",
  "data": [...],
  "chart_base64": "iVBORw0KGgo...",
  "rows_count": 10
}
```

---

### GET `/ask-visual-image`
Igual que `/ask-visual` pero devuelve la **imagen PNG directamente**.  
Se puede abrir en el navegador.

```
http://localhost:8000/ask-visual-image?question=Top 10 géneros con más juegos
```

---

### GET `/ask-text`
Pregunta en lenguaje natural → SQL generado por Gemini → **respuesta textual**.

```bash
curl "http://localhost:8000/ask-text?question=¿Cuál%20es%20el%20juego%20mejor%20valorado?"
```

```json
{
  "question": "¿Cuál es el juego mejor valorado?",
  "sql_generated": "SELECT name, rating FROM games ORDER BY rating DESC LIMIT 1",
  "answer": "El juego mejor valorado es The Witcher 3 con una puntuación de 4.66.",
  "data": [...],
  "rows_count": 1
}
```

---

##  Ejemplos de Preguntas

### `/ask-visual` y `/ask-visual-image` (gráficos)
- `Top 10 géneros con más juegos`
- `Evolución de juegos lanzados por año desde 2015`
- `Plataformas más populares`
- `Rating promedio por género`
- `Top stores con más juegos`

### `/ask-text` (respuestas textuales)
- `¿Cuál es el juego mejor valorado?`
- `¿Cuántos juegos hay en total?`
- `¿Qué género tiene mejor rating promedio?`
- `¿Cuáles son los 5 juegos con más playtime?`
- `¿Qué desarrolladora tiene más juegos?`

---

##  Seguridad

- Solo permite queries `SELECT`
- Bloquea `DROP`, `DELETE`, `UPDATE`, `INSERT`
- Credenciales de BD gestionadas por AWS Secrets Manager (nunca en texto plano)
- Validación de SQL antes de ejecutar
- Manejo de errores robusto con códigos HTTP apropiados

---

##  Notas

- La API usa **Gemini 2.5 Flash** (gratuito con límites)
- Límite Gemini: ~15 requests/minuto, 1.500/día
- Los gráficos se retornan en base64 PNG (endpoint `/ask-visual`) o PNG directo (endpoint `/ask-visual-image`)
- El modelo XGBoost se carga automáticamente al iniciar: busca el archivo `.pkl` más reciente en `models/`
- Si el modelo no está disponible, la API arranca igualmente pero el endpoint `/predict` devuelve `503`

---

##  Troubleshooting

**Error 503 en `/predict`:**
- El modelo `.pkl` no se encontró en `models/`
- Verifica que `success_features.pkl` también existe

**Error 429 en Gemini (Quota exceeded):**
- Espera 1 minuto entre requests
- La cuota se renueva cada 24 horas

**Error de conexión a la base de datos:**
- Verifica que las credenciales AWS están configuradas correctamente
- Comprueba que el secreto existe en AWS Secrets Manager con el nombre correcto
- Verifica los Security Groups de RDS (puerto 5432 abierto desde EC2)

**SQL incorrecto generado:**
- Reformula la pregunta con más detalle
- Para `/ask-visual`, asegúrate de que la pregunta implica una comparación o ranking