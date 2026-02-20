# API Documentation — RAWG Videogames ML + Text-to-SQL

**Proyecto:** rawg-aws-ml-analytics  
**Versión:** 3.0.0  
**Framework:** FastAPI  
**Autor:** Cristina  
**Fecha:** Febrero 2026

---

## Índice

1. [Descripción General](#descripción-general)
2. [Arquitectura y Tecnologías](#arquitectura-y-tecnologías)
3. [URL Base y Acceso](#url-base-y-acceso)
4. [Endpoints](#endpoints)
   - [GET `/`](#get-)
   - [GET `/health`](#get-health)
   - [POST `/predict`](#post-predict)
   - [GET `/ask-text`](#get-ask-text)
   - [GET `/ask-visual`](#get-ask-visual)
   - [GET `/ask-visual-image`](#get-ask-visual-image)
5. [Modelos de Datos (Schemas)](#modelos-de-datos-schemas)
6. [Códigos de Error](#códigos-de-error)
7. [Ejemplos de Uso](#ejemplos-de-uso)

---

## Descripción General

API REST multifuncional para análisis de videojuegos construida con FastAPI. Combina tres capacidades principales:

- **Predicción ML:** Modelo XGBoost que predice si un videojuego será un "éxito" basándose en sus características.
- **Text-to-SQL (texto):** Recibe preguntas en lenguaje natural, las convierte a SQL mediante Gemini AI, consulta la base de datos PostgreSQL y devuelve una respuesta textual.
- **Text-to-SQL (visual):** Mismo flujo que el anterior pero devuelve un JSON con base64 
- **Text-to-SQL (visual-image)** Igual que `/ask-visual`, **devuelve la imagen PNG directamente**, gráfico generado con Matplotlib/Seaborn..

Los datos provienen de la API pública [RAWG](https://rawg.io/apidocs) y están almacenados en una base de datos PostgreSQL en AWS RDS.

---

## Arquitectura y Tecnologías

| Componente | Tecnología |
|------------|------------|
| Framework API | FastAPI 0.100+ |
| Modelo ML | XGBoost (Pipeline con preprocesamiento) |
| Generación SQL | Google Gemini API |
| Base de datos | PostgreSQL (AWS RDS) |
| Visualización | Matplotlib + Seaborn |
| Despliegue | AWS EC2 (Ubuntu 22.04) |
| Servidor ASGI | Uvicorn |

**Flujo general:**

```
Usuario → FastAPI → [Gemini → SQL → PostgreSQL] → [XGBoost] → Respuesta
```

---

## URL Base y Acceso

| Entorno | URL |
|---------|-----|
| Local (desarrollo) | `http://localhost:8000` |
| Producción (EC2) | `http://<EC2-PUBLIC-IP>:8000` |
| Documentación interactiva | `http://<host>:8000/docs` |
| Documentación alternativa | `http://<host>:8000/redoc` |

---

## Endpoints

---

### GET `/`

**Descripción:** Endpoint raíz. Devuelve información general de la API, estado del modelo y ejemplos de uso.

**Tags:** Root

**Autenticación:** No requerida

**Request:** Sin parámetros

**Response exitosa (200):**

```json
{
  "message": "RAWG Videogames API - ML + Text-to-SQL con Gemini",
  "version": "2.0.0",
  "description": "API con predicción ML (XGBoost) y consultas en lenguaje natural (Gemini)",
  "endpoints": {
    "predict": "POST /predict - Predice éxito de videojuego",
    "visual": "GET /ask-visual - Consulta con gráfico",
    "text": "GET /ask-text - Consulta con respuesta textual",
    "health": "GET /health - Estado del servicio",
    "docs": "GET /docs - Documentación interactiva"
  },
  "model_status": {
    "loaded": true,
    "features_count": 11
  }
}
```

---

### GET `/health`

**Descripción:** Health check. Verifica que el servicio está funcionando y que el modelo ML está cargado.

**Tags:** Health

**Autenticación:** No requerida

**Request:** Sin parámetros

**Response exitosa (200):**

```json
{
  "status": "healthy",
  "service": "rawg-ml-api",
  "version": "3.0.0",
  "model_loaded": true,
  "features_count": 11
}
```

**Casos de uso:** Ideal para monitorización, checks de CI/CD o verificar el estado antes de lanzar predicciones.

---

### POST `/predict`

**Descripción:** Predice si un videojuego será un éxito comercial usando el modelo XGBoost entrenado.

**Tags:** Machine Learning

**Autenticación:** No requerida

**Método:** `POST`

**Content-Type:** `application/json`

#### Request Body — `GameInput`

| Campo | Tipo | Requerido | Descripción | Ejemplo |
|-------|------|-----------|-------------|---------|
| `num_platforms` | integer (≥1) | ✅ | Número de plataformas en las que está disponible | `5` |
| `num_stores` | integer (≥1) | ✅ | Número de tiendas digitales donde se vende | `3` |
| `num_genres` | integer (≥1) | ✅ | Número de géneros asignados | `2` |
| `num_tags` | integer (≥1) | ✅ | Número de tags/etiquetas | `10` |
| `years_since_release` | integer (≥0) | ✅ | Años transcurridos desde el lanzamiento | `2` |
| `recency_score` | integer (≥0) | ✅ | Puntuación de antigüedad (calculada) | `2` |
| `esrb_name` | string | ✅ | Clasificación ESRB del juego | `"Everyone"` |
| `release_year` | string | ✅ | Año de lanzamiento | `"2022"` |
| `has_multiplayer` | string | ✅ | Tiene modo multijugador: `"0"` o `"1"` | `"1"` |
| `has_singleplayer` | string | ✅ | Tiene modo un jugador: `"0"` o `"1"` | `"1"` |
| `is_indie` | string | ✅ | Es un juego indie: `"0"` o `"1"` | `"0"` |

**Valores válidos para `esrb_name`:** `"Everyone"`, `"Teen"`, `"Mature"`, `"Adults Only"`, `"Rating Pending"`

**Ejemplo de request:**

```json
{
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
```

#### Response exitosa (200) — `PredictionResponse`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `prediction` | string | `"Éxito"` o `"No Éxito"` |
| `prediction_class` | integer | `1` (Éxito) o `0` (No Éxito) |
| `probability_success` | float | Probabilidad de éxito (0.0 - 1.0) |
| `probability_no_success` | float | Probabilidad de no éxito (0.0 - 1.0) |
| `confidence` | string | `"Alta"`, `"Media"` o `"Baja"` |
| `features_used` | integer | Número de features utilizadas (11) |

**Ejemplo de response:**

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

**Lógica de confianza:**

| Probabilidad de éxito | Nivel de confianza |
|-----------------------|--------------------|
| ≥ 0.80 o ≤ 0.20 | Alta |
| ≥ 0.65 o ≤ 0.35 | Media |
| Entre 0.35 y 0.65 | Baja |

#### Errores posibles

| Código | Causa |
|--------|-------|
| `503` | Modelo ML no disponible (no se cargó al iniciar) |
| `500` | Error interno en la predicción |
| `422` | Datos de entrada inválidos (validación Pydantic) |

---

### GET `/ask-text`

**Descripción:** Recibe una pregunta en lenguaje natural, genera SQL automáticamente con Gemini, consulta PostgreSQL y devuelve una respuesta textual generada también por Gemini.

**Tags:** Text-to-SQL

**Autenticación:** No requerida

**Flujo interno:**
```
Pregunta → Gemini (genera SQL) → PostgreSQL → Gemini (genera respuesta) → JSON
```

#### Query Parameter

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `question` | string (≥5 chars) | ✅ | Pregunta en lenguaje natural |

#### Response exitosa (200) — `TextResponse`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `question` | string | Pregunta original del usuario |
| `sql_generated` | string | SQL generado por Gemini |
| `answer` | string | Respuesta en lenguaje natural |
| `data` | array | Datos crudos obtenidos de la BD |
| `rows_count` | integer | Número de filas retornadas |

**Ejemplo de request:**
```
GET /ask-text?question=¿Cuál es el juego mejor valorado?
```

**Ejemplo de response:**
```json
{
  "question": "¿Cuál es el juego mejor valorado?",
  "sql_generated": "SELECT name, rating FROM games ORDER BY rating DESC LIMIT 1",
  "answer": "El juego mejor valorado es 'The Witcher 3' con una puntuación de 4.66 sobre 5.",
  "data": [
    {"name": "The Witcher 3", "rating": 4.66}
  ],
  "rows_count": 1
}
```

**Preguntas de ejemplo que funcionan bien:**
- `¿Cuál es el juego mejor valorado?`
- `¿Cuántos juegos hay en total?`
- `¿Qué género tiene mejor rating promedio?`
- `¿Cuáles son los juegos con más playtime?`
- `¿Qué desarrolladora tiene más juegos?`

#### Errores posibles

| Código | Causa |
|--------|-------|
| `400` | Pregunta demasiado corta (< 5 caracteres) |
| `500` | Error generando SQL o consultando BD |

---

### GET `/ask-visual`

**Descripción:** Recibe una pregunta orientada a visualización, genera SQL, consulta la base de datos y devuelve los datos **más un gráfico en formato base64** (PNG). El tipo de gráfico se detecta automáticamente (barras horizontales o línea temporal).

**Tags:** Text-to-SQL

**Autenticación:** No requerida

**Requisito del SQL generado:** Debe retornar exactamente dos columnas: `label` y `value`.

**Flujo interno:**
```
Pregunta → Gemini (genera SQL con label/value) → PostgreSQL → Matplotlib → JSON + base64
```

#### Query Parameter

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `question` | string (≥5 chars) | ✅ | Pregunta orientada a visualización |

#### Response exitosa (200) — `VisualResponse`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `question` | string | Pregunta original |
| `sql_generated` | string | SQL generado por Gemini |
| `data` | array | Datos con columnas `label` y `value` |
| `chart_base64` | string | Imagen PNG en base64 |
| `rows_count` | integer | Número de filas |

**Lógica de tipo de gráfico:**

| Condición | Tipo de gráfico |
|-----------|----------------|
| `label` parseable como fecha | Línea temporal |
| Cualquier otro caso | Barras horizontales |

**Ejemplo de request:**
```
GET /ask-visual?question=Top 10 géneros con más juegos
```

**Preguntas de ejemplo que funcionan bien:**
- `Top 10 géneros con más juegos`
- `Evolución de juegos lanzados por año desde 2015`
- `Plataformas más populares`
- `Rating promedio por género`
- `Top stores con más juegos`

#### Errores posibles

| Código | Causa |
|--------|-------|
| `400` | Pregunta demasiado corta |
| `404` | La consulta no retornó datos |
| `500` | SQL no generado, columnas incorrectas, o error de gráfico |

---

### GET `/ask-visual-image`

**Descripción:** Igual que `/ask-visual` pero en lugar de devolver JSON con base64, **devuelve la imagen PNG directamente**. Se puede abrir en el navegador o incrustar en un `<img>`.

**Tags:** Text-to-SQL

**Content-Type de respuesta:** `image/png`

**Autenticación:** No requerida

#### Query Parameter

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `question` | string (≥5 chars) | ✅ | Pregunta orientada a visualización |

**Ejemplo de uso en navegador:**
```
http://localhost:8000/ask-visual-image?question=Top 10 géneros con más juegos
```

**Diferencias con `/ask-visual`:**

| | `/ask-visual` | `/ask-visual-image` |
|-|---------------|---------------------|
| Formato respuesta | JSON (con base64) | PNG directo |
| Acceso desde navegador | No directo | Sí, directamente |
| Incluye SQL generado | ✅ | ❌ |
| Incluye datos crudos | ✅ | ❌ |

---

## Modelos de Datos (Schemas)

### `GameInput`
Datos de entrada para `/predict`. Los 11 campos deben enviarse en el orden indicado.

### `PredictionResponse`
Respuesta de `/predict`. Incluye predicción, probabilidades y nivel de confianza.

### `TextResponse`
Respuesta de `/ask-text`. Incluye SQL generado, respuesta textual y datos crudos.

### `VisualResponse`
Respuesta de `/ask-visual`. Incluye SQL generado, datos crudos y gráfico en base64.

### `HealthResponse`
Respuesta de `/health`. Incluye estado del servicio y del modelo ML.

---

## Códigos de Error

| Código HTTP | Significado | Cuándo ocurre |
|-------------|-------------|---------------|
| `200` | OK | Respuesta exitosa |
| `400` | Bad Request | Parámetro inválido (pregunta muy corta) |
| `404` | Not Found | La consulta no retornó datos |
| `422` | Unprocessable Entity | Validación Pydantic fallida (campos incorrectos) |
| `500` | Internal Server Error | Error en Gemini, BD o generación de gráfico |
| `503` | Service Unavailable | Modelo ML no cargado |

---

## Ejemplos de Uso

### Con `curl`

**Health check:**
```bash
curl http://localhost:8000/health
```

**Predicción:**
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

**Pregunta textual:**
```bash
curl "http://localhost:8000/ask-text?question=¿Cuál es el juego mejor valorado?"
```

**Pregunta visual (JSON con base64):**
```bash
curl "http://localhost:8000/ask-visual?question=Top 10 géneros con más juegos"
```

**Imagen directa (abrir en navegador):**
```
http://localhost:8000/ask-visual-image?question=Top 10 géneros con más juegos
```

### Con Python (`requests`)

```python
import requests

BASE_URL = "http://localhost:8000"

# Predicción
payload = {
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
response = requests.post(f"{BASE_URL}/predict", json=payload)
print(response.json())

# Pregunta textual
response = requests.get(f"{BASE_URL}/ask-text", params={"question": "¿Cuántos juegos hay?"})
print(response.json())

# Visualización - guardar imagen
import base64
response = requests.get(f"{BASE_URL}/ask-visual", params={"question": "Top 10 géneros"})
data = response.json()
img_bytes = base64.b64decode(data["chart_base64"])
with open("chart.png", "wb") as f:
    f.write(img_bytes)
```

---

## Capturas de Pantalla

Las capturas de las pruebas realizadas se encuentran en la carpeta `docs/screen_shots/`.

Para acceder a la documentación interactiva generada por FastAPI (Swagger UI), visitar:

```
http://<host>:8000/docs
```

---

*Documentación generada para el proyecto rawg-aws-ml-analytics — Bootcamp Hack a Boss, Fase 02*