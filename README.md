# RAWG Video Games Analytics - AWS ETL Pipeline

Pipeline completo de extracción, transformación y carga (ETL) de datos de videojuegos desde la API de RAWG hacia una base de datos PostgreSQL en AWS RDS, con procesamiento serverless mediante AWS Lambda. Y análisis de videojuegos usando AWS, PostgreSQL, Gemini AI y Hugging Face.

## 📋 Índice

- [Descripción](#descripción)
- [Arquitectura](#arquitectura)
- [Fase 1: ETL Pipeline](#fase-1-etl-pipeline)
- [Fase 2: API Text-to-SQL](#fase-2-api-text-to-sql)
- [Tecnologías](#tecnologías)
- [Instalación](#instalación)
- [Uso](#uso)
- [Estructura del Proyecto](#estructura-del-proyecto)

---

## Descripción del Proyecto
Sistema de análisis de datos de videojuegos que combina:

1. **ETL automatizado en AWS** para extracción diaria de datos de RAWG API
2. **API REST con Text-to-SQL** usando modelos de IA (Gemini + Hugging Face)
3. **Visualizaciones automáticas** generadas dinámicamente

### Características Principales

- ✅ Extracción automática de ~20,000 videojuegos desde RAWG API
- ✅ Procesamiento y almacenamiento en PostgreSQL RDS
- ✅ Consultas en lenguaje natural (español/inglés)
- ✅ Generación automática de SQL con Gemini AI
- ✅ Clasificación de intenciones con Hugging Face
- ✅ Gráficos generados automáticamente con Matplotlib
- ✅ Respuestas en lenguaje natural
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
│  Usuario → FastAPI → Gemini (Text-to-SQL) → PostgreSQL         │
│                   ↓                                             │
│            Hugging Face (Clasificación)                         │
│                   ↓                                             │
│            Matplotlib (Visualización)                           │
│                   ↓                                             │
│            Respuesta JSON + Gráfico Base64                      │
└─────────────────────────────────────────────────────────────────┘
```

---
## Fase 1: ETL Pipeline

### Componentes AWS

| Servicio | Función | Configuración |
|----------|---------|---------------|
| **Lambda Extractor** | Extrae datos de RAWG API | Runtime: Python 3.11, 512 MB RAM |
| **Lambda Transformer** | Transforma y limpia datos | Runtime: Python 3.11, 512 MB RAM |
| **Lambda Loader** | Carga datos en PostgreSQL | Runtime: Python 3.11, 512 MB RAM |
| **RDS PostgreSQL** | Base de datos principal | db.t3.micro, PostgreSQL 14 |
| **EventBridge** | Orquestación automática | Trigger: cron(0 2 * * ? *) |
| **Secrets Manager** | Credenciales DB + API | Rotación: Manual |

### Esquema de Base de Datos

**Tablas principales:**
- `games` - Información de videojuegos (20,000+ registros)
- `genres`, `platforms`, `tags`, `stores` - Catálogos
- `games_status` - Estado de juego (playing, owned, etc.)
- Tablas relacionales N:M para vincular juegos con géneros, plataformas, etc.

**Campos clave:**
- `game_rating` (NUMERIC 4,2) - Rating promedio
- `released_ym` (CHAR 7) - Fecha lanzamiento "YYYY-MM"
- `game_added` (BIGINT) - Veces agregado a colecciones
- `playtime` (INTEGER) - Tiempo promedio de juego

---
## Fase 2: API Text-to-SQL

### Endpoints

#### GET `/ask-visual`

Pregunta en lenguaje natural → SQL → Gráfico

**Ejemplo:**
```bash
GET /ask-visual?question=Top 10 géneros con más juegos
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

#### GET `/ask-text`

Pregunta en lenguaje natural → SQL → Respuesta textual

**Ejemplo:**
```bash
GET /ask-text?question=¿Cuál es el juego mejor valorado?
```

**Respuesta:**
```json
{
  "question": "¿Cuál es el juego mejor valorado?",
  "sql_generated": "SELECT game_name AS juego, game_rating...",
  "answer": "El juego mejor valorado es The Witcher 3 con 4.89...",
  "data": [...],
  "rows_count": 1
}
```
### Modelos de IA Utilizados

| Modelo | Uso | Proveedor |
|--------|-----|-----------|
| **Gemini 2.5 Flash** | Text-to-SQL dinámico | Google AI |
| **paraphrase-MiniLM-L3-v2** | Clasificación de intención | Hugging Face |

### Ejemplos de Preguntas Soportadas

**Visualización:**
- "Top 10 géneros con más juegos"
- "Evolución de juegos lanzados por año desde 2015"
- "Plataformas más populares"
- "Rating promedio por año"

**Textual:**
- "¿Cuál es el juego mejor valorado?"
- "¿Cuántos juegos hay en total?"
- "¿Qué género tiene mejor rating promedio?"
- "¿Cuáles son los juegos con más playtime?"

---


##  Tecnologías

### Backend
- **FastAPI** - Framework web
- **Python 3.11** - Lenguaje principal
- **psycopg2** - Conexión PostgreSQL
- **pandas** - Análisis de datos

### Machine Learning
- **Gemini API** (Google) - Text-to-SQL
- **Hugging Face Transformers** - Clasificación NLP
- **sentence-transformers** - Embeddings semánticos

### Visualización
- **Matplotlib** - Gráficos estáticos
- **Seaborn** - Estilos visuales

### Infraestructura AWS
- **Lambda** - Funciones serverless
- **RDS PostgreSQL** - Base de datos
- **EventBridge** - Orquestación
- **Secrets Manager** - Gestión de credenciales
- **EC2** - Hosting de FastAPI (t3.small)

### **Lenguajes y Frameworks**
- **Python 3.11**
- **pandas** - Transformación de datos
- **psycopg2** - Conexión a PostgreSQL
- **SQLAlchemy** - ORM y generación de queries
- **boto3** - SDK de AWS
- **requests** - Consumo de API REST

### **Base de Datos**
- **PostgreSQL 16** en AWS RDS
- **pgAdmin 4** - Administración y queries interactivas
- Esquema relacional normalizado
- Índices optimizados para consultas analíticas

### **Desarrollo y Testing**
- **Jupyter Notebook** - Prototipado y análisis exploratorio
- **Git/GitHub** - Control de versiones

---

##  Instalación

### Prerrequisitos

- Python 3.11+
- Cuenta AWS con permisos para: Lambda, S3, RDS, Secrets Manager
- API Key de RAWG ([obtener aquí](https://rawg.io/apidocs))
- API Key de Gemini (https://aistudio.google.com/apikey)

### Paso 1: Clonar Repositorio
```bash
git clone https://github.com/tu-usuario/rawg-aws-ml-analytics.git
cd rawg-aws-ml-analytics
```

### Paso 2: Instalar Dependencias
```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### Paso 3: Configurar Variables de Entorno
```bash
# Copiar template
cp .env.example .env

# Editar .env con tus credenciales
nano .env
```

**Contenido de `.env`:**
```env
# Gemini API
GEMINI_API_KEY=tu_gemini_api_key

# PostgreSQL RDS
DB_HOST=tu-rds-endpoint.rds.amazonaws.com
DB_NAME=videogames_db
DB_USER=tu_usuario
DB_PASSWORD=tu_password
DB_SCHEMA=rawg

# RAWG API (solo para ETL)
RAWG_API_KEY=tu_rawg_api_key
```

### Paso 4: Ejecutar FastAPI
```bash
cd fast_api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Abrir en navegador: http://localhost:8000/docs

---


## Uso

### Desde Swagger UI (Recomendado)

1. Abrir http://localhost:8000/docs
2. Seleccionar endpoint `/ask-visual` o `/ask-text`
3. Click en "Try it out"
4. Escribir pregunta en campo `question`
5. Click en "Execute"

### Desde cURL
```bash
# Ejemplo visual
curl "http://localhost:8000/ask-visual?question=Top%2010%20géneros"

# Ejemplo textual
curl "http://localhost:8000/ask-text?question=¿Cuántos%20juegos%20hay?"
```

### Desde Python
```python
import requests

# Ask Visual
response = requests.get(
    "http://localhost:8000/ask-visual",
    params={"question": "Top 10 géneros con más juegos"}
)
data = response.json()

# Decodificar imagen base64
import base64
img_bytes = base64.b64decode(data['chart_base64'])
with open('chart.png', 'wb') as f:
    f.write(img_bytes)
```

---

##  Estructura del Proyecto
```
rawg-aws-ml-analytics/
│
├── etl/                                     # Scripts ETL
│   ├── create_rawg_local_database.py        # Creación de esquema y tablas de rawg-db
│   ├── lambda_daily_extract.py              # Extracción diaria desde API
│   └── lambda_extract_rawg.py               # Extracción masiva de la API
|   └── lambda_loader.py                     # Pipeline transformación JSON de S3 y carga en RDS, con trigger
|   └── transform_rawg.py 
|   |__ aws_lambda                           # Layers Lambda
|       ├── boto3310/                 
|       ├── lambda_loader_package/                
│       └── psycopg2/                 
│       └── requests/
|       └── sqlalchemy/
|       └── lambda-loader.zip
|    
├── models/                                  # Scripts modelado
|   ├── text_to_sql_gemini.py                # Generación SQL con Gemini
|   ├── predictor.py                         # Modelo predicción de éxito de un juego
│   └── train.py                             # Entrenamiento modelo predicción
│   
├── fast_api/                                # API REST
│   ├── main.py                              # FastAPI endpoints
│   ├── requirements.txt                     # Dependencias
|   └── README.md                            # Docs de la API
│
├── docs/                                     # Documentación
|   ├── screen_shots/                         # screen shots Lambdas y FasAPI
│   ├── aws_deployments_instructions.md       # Instrucciones aws lambda_loader y lambda_daily_extract
│   ├── database_schema_sql.md                # sql: esquema data base 
│   ├── api_documentation.md                  # documentación FastAPI con los endpoints
│   └── test_endpoints.txt                    # Preguntas preparadas para probar la FastAPI
│
├── notebooks/                                # Jupyter Notebooks
│   └── etl_notebooks/
│   |   ├── 00_exploración_rawg.ipynb         # Análisis exploratorio
│   |   ├── 01_extraccion_rawg.ipynb          # Desarrollo del pipeline
|   |   ├── 02_validacion_datos_rawg.ipynb    # Desarrollo del pipeline
│   |   ├── 03_transformacion_rawg            # Desarrollo del pipeline
|   |   ├── 04_.create_database_local.ipynb   # Desarrollo del pipeline
│   |   ├── 05_transf_load_rawg_local.ipynb   # Desarrollo del pipeline
|   |   └── 06_trasf_load_rawg_aws.ipynb      # Desarrollo del pipeline
|   |
|   └── models_notebooks/
|        ├──01_text_to_sql.ipynb              # Pruebas text_to_sql
|        ├──02_feature_engineering.ipynb      # Features entrenamiento modelo predicción
|        └──03_modelado.ipynb                 # Preprocesado y entrenamiento de modelo predicción
|   
│
├── utils/                                    # Utilidades
|   ├──__init__.py                            
│   └── aws_secrets.py                        # Helper para Secrets Manager
│       
├── sql/                                      # Scripts SQL
│   ├── create_schema.sql                     # Creación del esquema
|   ├── drop_schema.sql                       # Eliminación del esquema con todos los datos
|   └── queries/                              # Queries analíticas
│   
│── .gitignore
├── bootstrap.py                              # Configuración de paths del proyecto
├── descripcion_rawg                          # Descripción de la propuesta del proyecto
├── README.md
└── requirements.txt                          # Dependencias del proyecto
```

---

## Seguridad

- ✅ Solo permite queries `SELECT` (no `DROP`, `DELETE`, etc.)
- ✅ Credenciales en AWS Secrets Manager
- ✅ Validación de SQL antes de ejecutar
- ✅ Conexiones SSL a RDS
- ✅ Rate limiting en Lambda

---

## 📊 Métricas del Proyecto

| Métrica | Valor |
|---------|-------|
| **Juegos en BD** | ~20,000 |
| **Tablas** | 10 |
| **Endpoints API** | 2 principales |
| **Modelos ML** | 2 (Gemini + HF) |
| **Costo mensual AWS** | ~$15-30 |

---

## 🎓 Aprendizajes Clave

- ✅ Arquitectura serverless en AWS
- ✅ Integración de múltiples modelos de IA
- ✅ Text-to-SQL dinámico con LLMs
- ✅ FastAPI para APIs de ML
- ✅ Manejo de seguridad en SQL
- ✅ Visualización automática de datos

---

## 📝 Notas

- La API usa Gemini 2.5 Flash con límite de 1,500 requests/día (gratis)
- Los gráficos se retornan en base64 PNG
- El ETL se ejecuta automáticamente cada 24 horas
- Esquema optimizado para consultas analíticas

---
## Autora

**Cristina Rodríguez Arroyo** - Data Science Bootcamp Student
-  Bootcamp AI & Data Science - Hack a Boss (2025-2026)

---

## Licencia

Este proyecto es parte de un bootcamp educativo.

---

## Agradecimientos

- [RAWG.io](https://rawg.io/) por proporcionar la API de videojuegos
- AWS por la infraestructura serverless
- Hack a Boss por la formación en Data Science

---

