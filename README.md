# RAWG Video Games Analytics — AWS End-to-End System

**End-to-end Data Engineering & ML system deployed on AWS.**  
ETL pipeline + PostgreSQL RDS + LLM-powered Text-to-SQL API + XGBoost ML prediction, deployed on EC2.

---

## 📋 Índice

- [Descripción](#descripción)
- [Arquitectura](#arquitectura)
- [Fase 1: ETL Pipeline](#fase-1-etl-pipeline)
- [Fase 2: API — Predicción ML y Text-to-SQL](#fase-2-api--predicción-ml-y-text-to-sql)
- [Fase 3: Despliegue en EC2](#fase-3-despliegue-en-ec2)
- [Tecnologías](#tecnologías)
- [Instalación](#instalación)
- [Uso](#uso)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Seguridad](#seguridad)
- [Limitaciones conocidas](#limitaciones-conocidas)
- [Autora](#autora)

---

## Descripción del Proyecto

Sistema completo de análisis de datos de videojuegos que combina:

1. **ETL automatizado en AWS** — extracción diaria de ~20.000 videojuegos desde RAWG API
2. **API REST multifuncional** — predicción ML con XGBoost y consultas en lenguaje natural via Gemini AI
3. **Despliegue en producción** — FastAPI corriendo en EC2 con conexión a RDS PostgreSQL gestionada por AWS Secrets Manager

### Características Principales

- ✅ Extracción automática de ~20.000 videojuegos desde RAWG API
- ✅ Almacenamiento en PostgreSQL RDS (AWS)
- ✅ Predicción de éxito de videojuegos con XGBoost (accuracy 86%)
- ✅ Consultas en lenguaje natural con Gemini AI (Text-to-SQL)
- ✅ Visualizaciones automáticas con Matplotlib
- ✅ API desplegada en EC2 y accesible públicamente

---

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                         FASE 1: ETL                             │
│                                                                 │
│  RAWG API → Lambda Extractor → Lambda Transformer →            │
│  → Lambda Loader → PostgreSQL RDS                               │
│                                                                 │
│  Orquestación: EventBridge (cada 24h)                          │
│  Seguridad: AWS Secrets Manager                                │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      FASE 2: API ML                             │
│                                                                 │
│  Usuario → FastAPI → XGBoost (predicción)                      │
│                   ↓                                             │
│            Gemini AI (Text-to-SQL) → PostgreSQL RDS            │
│                   ↓                                             │
│            Matplotlib (Visualización)                           │
│                   ↓                                             │
│            Respuesta JSON / Gráfico PNG                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    FASE 3: DESPLIEGUE EC2                       │
│                                                                 │
│  GitHub → EC2 (Amazon Linux 2023) → uvicorn → FastAPI          │
│                   ↓                                             │
│         IAM Role → Secrets Manager → RDS PostgreSQL            │
│                   ↓                                             │
│         Acceso público: http://<EC2-IP>:8000/docs              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Fase 1: ETL Pipeline

### Componentes AWS

| Servicio | Función | Configuración |
|----------|---------|---------------|
| **Lambda Extractor** | Extrae datos de RAWG API | Python 3.11, 512 MB RAM |
| **Lambda Transformer** | Transforma y limpia datos | Python 3.11, 512 MB RAM |
| **Lambda Loader** | Carga datos en PostgreSQL | Python 3.11, 512 MB RAM |
| **RDS PostgreSQL** | Base de datos principal | db.t3.micro, PostgreSQL 16 |
| **EventBridge** | Orquestación automática | cron(0 2 * * ? *) — cada 24h |
| **Secrets Manager** | Credenciales DB | Rotación: Manual |

### Esquema de Base de Datos

**Tablas principales:** `games`, `genres`, `platforms`, `tags`, `stores`, `games_status` y tablas relacionales N:M.

**Campos clave:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `game_rating` | NUMERIC(4,2) | Rating promedio |
| `released_ym` | CHAR(7) | Fecha lanzamiento "YYYY-MM" |
| `game_added` | BIGINT | Veces agregado a colecciones |
| `playtime` | INTEGER | Tiempo promedio de juego |

---

## Fase 2: API — Predicción ML y Text-to-SQL

### URLs de acceso

| Entorno | Swagger UI | ReDoc |
|---------|-----------|-------|
| **Local** | http://localhost:8000/docs | http://localhost:8000/redoc |
| **EC2** | http://\<EC2-IP-PUBLICA\>:8000/docs | http://\<EC2-IP-PUBLICA\>:8000/redoc |

> ⚠️ La IP pública de EC2 cambia en cada reinicio de la instancia.

### Endpoints

#### POST `/predict`
Predice si un videojuego será un éxito usando el modelo XGBoost (11 features, accuracy 86%).

| Entorno | URL |
|---------|-----|
| Local | `http://localhost:8000/predict` |
| EC2 | `http://<EC2-IP-PUBLICA>:8000/predict` |

**Ejemplo:**
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "num_platforms": 5, "num_stores": 3, "num_genres": 2,
    "num_tags": 10, "years_since_release": 2, "recency_score": 2,
    "esrb_name": "Everyone", "release_year": 2022,
    "has_multiplayer": 1, "has_singleplayer": 1, "is_indie": 0
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

#### GET `/ask-visual`
Pregunta en lenguaje natural → SQL generado por Gemini → gráfico en base64 PNG.

| Entorno | URL |
|---------|-----|
| Local | `http://localhost:8000/ask-visual` |
| EC2 | `http://<EC2-IP-PUBLICA>:8000/ask-visual` |

**Ejemplo:**
```bash
curl "http://localhost:8000/ask-visual?question=Top%2010%20géneros%20con%20más%20juegos"
```

**Respuesta:**
```json
{
  "question": "Top 10 géneros con más juegos",
  "sql_generated": "SELECT g.genre_name AS label, COUNT(*)::bigint AS value...",
  "data": [...],
  "chart_base64": "iVBORw0KGgo...",
  "rows_count": 10
}
```

---

#### GET `/ask-visual-image`
Igual que `/ask-visual` pero devuelve la **imagen PNG directamente** — se puede abrir en el navegador.

| Entorno | URL |
|---------|-----|
| Local | `http://localhost:8000/ask-visual-image` |
| EC2 | `http://<EC2-IP-PUBLICA>:8000/ask-visual-image` |

```
http://localhost:8000/ask-visual-image?question=Top 10 géneros con más juegos
```

---

#### GET `/ask-text`
Pregunta en lenguaje natural → SQL generado por Gemini → respuesta textual.

| Entorno | URL |
|---------|-----|
| Local | `http://localhost:8000/ask-text` |
| EC2 | `http://<EC2-IP-PUBLICA>:8000/ask-text` |

**Ejemplo:**
```bash
curl "http://localhost:8000/ask-text?question=¿Cuál%20es%20el%20juego%20mejor%20valorado?"
```

**Respuesta:**
```json
{
  "question": "¿Cuál es el juego mejor valorado?",
  "sql_generated": "SELECT game_name, game_rating FROM rawg.games ORDER BY game_rating DESC LIMIT 1",
  "answer": "El juego mejor valorado es The Witcher 3 con una puntuación de 4.89.",
  "data": [...],
  "rows_count": 1
}
```

---

### Ejemplos de Preguntas Soportadas

**Para `/ask-visual` y `/ask-visual-image`:**
- "Top 10 géneros con más juegos"
- "Evolución de juegos lanzados por año desde 2015"
- "Plataformas más populares"
- "Rating promedio por género"

**Para `/ask-text`:**
- "¿Cuál es el juego mejor valorado?"
- "¿Cuántos juegos hay en total?"
- "¿Qué género tiene mejor rating promedio?"
- "¿Cuáles son los 5 juegos con más playtime?"

---

## Fase 3: Despliegue en EC2

### Configuración de la Instancia

| Parámetro | Valor |
|-----------|-------|
| **AMI** | Amazon Linux 2023 (kernel-6.1) |
| **Tipo** | t2.micro (capa gratuita) |
| **Región** | eu-north-1 (Estocolmo) |
| **Security Group** | SSH (22), HTTP (80), Custom TCP (8000) |
| **Credenciales RDS** | AWS Secrets Manager via IAM Role |

### Pasos de despliegue

```bash
# 1. Clonar rama del proyecto
git clone https://github.com/Daniel-GH12/rawg-aws-ml-analytics.git

# 2. Instalar dependencias
cd rawg-aws-ml-analytics/fast_api
pip install -r requirements.txt

# 3. Exportar Gemini API Key
export GEMINI_API_KEY=tu_api_key

# 4. Lanzar API
uvicorn main:app --host 0.0.0.0 --port 8000
```

> ℹ️ Las credenciales de RDS se obtienen automáticamente via **IAM Role + Secrets Manager**, sin variables de entorno ni archivos de configuración. Ver `docs/aws_deployments_instructions.md` para instrucciones detalladas.

### Conexión EC2 → RDS

| Componente | Configuración |
|-----------|--------------|
| **IAM Role** | `ec2-rawg-role` con política `SecretsManagerReadWrite` |
| **Security Group RDS** | Inbound PostgreSQL (5432) desde EC2 — configurado via "Set up EC2 connection" |
| **Credenciales** | Gestionadas automáticamente por AWS Secrets Manager |

---

## Tecnologías

| Categoría | Tecnologías |
|-----------|------------|
| **Lenguaje** | Python 3.11 |
| **API** | FastAPI, uvicorn |
| **ML** | XGBoost, scikit-learn 1.5.2, pandas |
| **IA generativa** | Gemini 2.5 Flash (Text-to-SQL), Hugging Face (clasificación de intención) |
| **Visualización** | Matplotlib, Seaborn |
| **Base de datos** | PostgreSQL 16 (AWS RDS), psycopg2, SQLAlchemy |
| **Infraestructura AWS** | EC2, Lambda, RDS, EventBridge, Secrets Manager, IAM |
| **DevOps** | Git/GitHub, SCP, SSH |
| **Desarrollo** | Jupyter Notebook, pgAdmin 4 |

---

## Instalación

### Prerrequisitos

- Python 3.11+
- Cuenta AWS con permisos para Lambda, RDS, Secrets Manager, EC2, IAM
- API Key de RAWG ([obtener aquí](https://rawg.io/apidocs))
- API Key de Gemini ([obtener aquí](https://aistudio.google.com/apikey))

### Paso 1: Clonar Repositorio
```bash
git clone https://github.com/CrisRguezA/rawg-aws-ml-analytics.git
cd rawg-aws-ml-analytics
```

### Paso 2: Instalar Dependencias
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Paso 3: Configurar Credenciales

Las credenciales de la base de datos se obtienen automáticamente desde **AWS Secrets Manager** — no se usan ficheros `.env` ni variables de entorno para la BD.

```bash
# Credenciales AWS (local)
aws configure

# Gemini API Key
export GEMINI_API_KEY=tu_gemini_api_key
```

> ℹ️ En EC2, las credenciales AWS se gestionan mediante un **IAM Role** asignado a la instancia, sin necesidad de `aws configure`.

### Paso 4: Ejecutar FastAPI
```bash
cd fast_api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Abrir en navegador: http://localhost:8000/docs

---

## Uso

### Desde Swagger UI
1. Abrir http://localhost:8000/docs
2. Seleccionar endpoint
3. Click en "Try it out" → rellenar parámetros → "Execute"

### Desde cURL
```bash
curl "http://localhost:8000/ask-visual?question=Top%2010%20géneros"
curl "http://localhost:8000/ask-text?question=¿Cuántos%20juegos%20hay?"
```

### Desde Python
```python
import requests, base64

response = requests.get(
    "http://localhost:8000/ask-visual",
    params={"question": "Top 10 géneros con más juegos"}
)
data = response.json()
img_bytes = base64.b64decode(data['chart_base64'])
with open('chart.png', 'wb') as f:
    f.write(img_bytes)
```

---

## Estructura del Proyecto

```
rawg-aws-ml-analytics/
│
├── etl/                                     # Scripts ETL
│   ├── create_rawg_local_database.py
│   ├── lambda_daily_extract.py
│   ├── lambda_extract_rawg.py
│   ├── lambda_loader.py
│   ├── transform_rawg.py
│   └── aws_lambda/                          # Layers Lambda
│       ├── boto3310/
│       ├── lambda_loader_package/
│       ├── psycopg2/
│       ├── requests/
│       ├── sqlalchemy/
│       └── lambda-loader.zip
│
├── models/                                  # Modelo ML
│   ├── text_to_sql_gemini.py                # Text-to-SQL con Gemini AI
│   ├── db_connection.py                     # Conexión a PostgreSQL
│   ├── __init__.py
│   ├── xgb_success_model_*.pkl              # Modelo entrenado
│   └── success_features.pkl                 # Features del modelo
│
├── fast_api/                                # API REST
│   ├── main.py
│   ├── requirements.txt
│   └── README.md
│
├── docs/
│   ├── screen_shots/
│   ├── aws_deployments_instructions.md      # Instrucciones detalladas EC2 + Lambda
│   ├── database_schema_sql.md
│   ├── api_documentation.md
│   └── test_endpoints.txt
│
├── notebooks/
│   ├── etl_notebooks/                       # Pipeline ETL
│   └── models_notebooks/                    # Feature engineering y modelado
│
├── utils/
│   ├── __init__.py
│   └── aws_secrets.py                       # Helper Secrets Manager
│
├── sql/
│   ├── create_schema.sql
│   ├── drop_schema.sql
│   └── queries/
│
├── bootstrap.py
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Seguridad

- ✅ Solo permite queries `SELECT` (bloquea `DROP`, `DELETE`, `UPDATE`, `INSERT`)
- ✅ Credenciales de BD gestionadas por AWS Secrets Manager
- ✅ Validación de SQL antes de ejecutar
- ✅ Acceso a EC2 solo mediante par de claves `.pem`
- ✅ Permisos AWS gestionados mediante IAM Roles (sin credenciales hardcodeadas)
- ✅ Archivos sensibles excluidos de GitHub via `.gitignore`

---

## Limitaciones conocidas

El modelo XGBoost usa **11 features** seleccionadas para evitar *data leakage*. Las más predictivas (`ratings_count`, `game_rating`, `engagement_score`) fueron excluidas por derivarse del target. Esto limita el poder discriminativo del modelo en casos límite, aunque el accuracy global es del **86%**. Ver `fast_api/README.md` para más detalle.

---

## 📊 Métricas del Proyecto

| Métrica | Valor |
|---------|-------|
| **Juegos en BD** | ~20.000 |
| **Tablas** | 10 |
| **Endpoints API** | 4 |
| **Accuracy modelo** | 86% |
| **Costo mensual AWS** | ~$15-30 |

---

## 🎓 Aprendizajes Clave

- Arquitectura ETL serverless en AWS (Lambda + EventBridge + RDS)
- Text-to-SQL dinámico con LLMs (Gemini AI)
- Predicción ML con XGBoost y gestión de data leakage
- Despliegue de API en EC2 con Amazon Linux
- Gestión de permisos AWS con IAM Roles y Secrets Manager
- Resolución de incompatibilidades de versiones en producción

---

## 📝 Notas

- Gemini 2.5 Flash: límite de 1.500 requests/día (gratuito)
- La variable `GEMINI_API_KEY` debe exportarse en cada sesión SSH o añadirse a `~/.bashrc`
- Instrucciones detalladas de despliegue en `docs/aws_deployments_instructions.md`
- La lógica de predicción está integrada directamente en `fast_api/main.py`
- El modelo fue entrenado en `notebooks/models_notebooks/03_modelado.ipynb` y exportado como `.pkl`

---

## Autora

**Cristina Rodríguez Arroyo**  
AI Engineer en formación — Bootcamp AI & Data Science, Hack a Boss (2025-2026)  
🔗 github.com/CrisRguezA

---

## Agradecimientos

- [RAWG.io](https://rawg.io/) por la API de videojuegos
- AWS por la infraestructura cloud
- Hack a Boss por la formación en Data Science
