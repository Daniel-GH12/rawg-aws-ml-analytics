# RAWG Video Games Analytics - ETL Pipeline

Pipeline completo de extracción, transformación y carga (ETL) de datos de videojuegos desde la API de RAWG hacia una base de datos PostgreSQL en AWS RDS, con procesamiento serverless mediante AWS Lambda.

---

## Descripción del Proyecto

Este proyecto implementa una arquitectura ETL en la nube para analizar datos de videojuegos obtenidos de [RAWG Video Games Database API](https://rawg.io/apidocs). El sistema procesa información de más de 850,000 videojuegos, incluyendo sus plataformas, géneros, tiendas, clasificaciones ESRB, ratings y etiquetas.

### Objetivo

Crear un data warehouse en PostgreSQL que permita análisis avanzados sobre:
- Tendencias de la industria del videojuego
- Popularidad de plataformas y géneros
- Evolución de ratings a lo largo del tiempo
- Relaciones entre clasificaciones ESRB y éxito comercial
- Análisis de tags y categorización de juegos

---

## Arquitectura del Sistema
```
┌─────────────────────────────────────────────────────────────────┐
│                         RAWG API                                 │
│                    (850K+ videojuegos)                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
            ┌────────────────────────┐
            │  Lambda Extraction     │  ← Extracción periódica
            │  (Python 3.11)         │     (Scheduled EventBridge)
            └────────┬───────────────┘
                     │
                     ↓
            ┌────────────────────────┐
            │   S3 Bucket (Raw)      │
            │  - extraccion_         │
            │    historica.json      │
            │  - games_YYYY-MM-DD    │
            │    .json               │
            └────────┬───────────────┘
                     │
                     │ Trigger (ObjectCreated)
                     ↓
       ┌─────────────────────────────────┐
       │  Lambda ETL Pipeline            │
       │  (Python 3.11 + Layers)         │
       │                                 │
       │  1. Detecta tipo (histórico/    │
       │     incremental)                │
       │  2. Transforma datos            │
       │  3. Limpia FK inválidas         │
       │  4. Carga a RDS                 │
       │     - INSERT (histórico)        │
       │     - UPSERT (incremental)      │
       └────────┬────────────────────────┘
                │
                ↓
       ┌─────────────────────────────────┐
       │   PostgreSQL RDS                │
       │   (Esquema: rawg)               │
       │                                 │
       │   • 5 tablas dimensión          │
       │   • 1 tabla de hechos           │
       │   • 2 tablas de estado/métricas │
       │   • 4 tablas de relación N:M    │
       └─────────────────────────────────┘
```

---

##  Tecnologías Utilizadas

### **Cloud & Infrastructure**
- **AWS Lambda** - Procesamiento serverless
- **AWS S3** - Almacenamiento de datos raw
- **AWS RDS PostgreSQL** - Data warehouse
- **AWS Secrets Manager** - Gestión segura de credenciales
- **AWS EventBridge** - Scheduling de extracciones

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
├── models/                                   #
│   ├──                                       # 
│   └──                                       # 
│   
├── fast_api/                              # fast_api
│   ├──                                       # 
|   └── 
│
├── docs/                                     # Documentación
|   └── AWS_DEPLOYMENTS_INSTRUCTIONS.ipynb    # Instrucciones aws lambda_loader y lambda_daily_extract
│   └── database_schema.md                    # Documentación del modelo de datos
│
├── notebooks/                                # Jupyter Notebooks
│   └── etl_notebooks/
│   |   ├── 00_exploración_rawg.ipynb         # Análisis exploratorio
│   |   └── 01_extraccion_rawg.ipynb          # Desarrollo del pipeline
|   |   ├── 02_validacion_datos_rawg.ipynb    # Desarrollo del pipeline
│   |   └── 03_transformacion_rawg            # Desarrollo del pipeline
|   |   ├── 04_.create_database_local.ipynb   # Desarrollo del pipeline
│   |   └── 05_transf_load_rawg_local.ipynb   # Desarrollo del pipeline
|   |   └── 06_trasf_load_rawg_aws.ipynb      # Desarrollo del pipeline
|   |
|   └── models_notebooks/
|   └── fast_api_notebooks/
│
├── utils/                                    # Utilidades
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

## Modelo de Datos

### **Esquema: `rawg`**

#### **Tablas Dimensión (Catálogos)**
- `esrb_ratings` - Clasificaciones ESRB (Everyone, Teen, Mature, etc.)
- `platforms` - Plataformas de juego (PC, PlayStation, Xbox, etc.)
- `genres` - Géneros (Action, RPG, Strategy, etc.)
- `stores` - Tiendas digitales (Steam, Epic Games, GOG, etc.)
- `tags` - Etiquetas de categorización (4,000+ tags únicos)

#### **Tabla Principal (Hechos)**
- `games` - Información principal de cada videojuego
  - Métricas: rating, ratings_count, playtime, suggestions_count
  - Metadatos: nombre, fecha de lanzamiento, clasificación ESRB

#### **Tablas de Estado y Métricas**
- `games_status` - Estado del juego por usuarios (owned, beaten, playing, etc.)
- `ratings_distribution` - Distribución de ratings (exceptional, recommended, meh, skip)

#### **Tablas de Relación N:M (Bridge Tables)**
- `game_platforms` - Juegos ↔ Plataformas
- `game_genres` - Juegos ↔ Géneros
- `game_stores` - Juegos ↔ Tiendas
- `game_tags` - Juegos ↔ Tags

### **Diagrama ERD simplificado**
```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│ platforms    │       │   genres     │       │   stores     │
├──────────────┤       ├──────────────┤       ├──────────────┤
│ platform_id  │       │ genre_id PK  │       │ store_id PK  │
│ platform_name│       │ genre_name   │       │ store_name   │
└──────┬───────┘       └──────┬───────┘       └──────┬───────┘
       │                      │                      │
       │                      │                      │
       └──────────┬───────────┴──────────┬───────────┘
                  │                      │
         ┌────────▼────────┐    ┌────────▼────────┐
         │ game_platforms  │    │  game_genres    │
         ├─────────────────┤    ├─────────────────┤
         │ game_id    FK   │    │ game_id    FK   │
         │ platform_id FK  │    │ genre_id   FK   │
         └────────┬────────┘    └────────┬────────┘
                  │                      │
                  └──────────┬───────────┘
                             │
                    ┌────────▼────────┐
                    │     GAMES       │ ← Tabla central
                    ├─────────────────┤
                    │ game_id     PK  │
                    │ game_name       │
                    │ rating          │
                    │ released_ym     │
                    │ esrb_id     FK  │
                    └─────────────────┘
```

---

## Configuración e Instalación

### **1. Requisitos previos**

- Python 3.11+
- Cuenta AWS con permisos para: Lambda, S3, RDS, Secrets Manager
- API Key de RAWG ([obtener aquí](https://rawg.io/apidocs))

### **2. Instalación local**
```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/rawg-aws-ml-analytics.git
cd rawg-aws-ml-analytics

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### **3. Configurar credenciales AWS**

Crear secreto en AWS Secrets Manager con el nombre `Postgre`:
```json
{
  "username": "tu_usuario",
  "password": "tu_password",
  "host": "tu-rds-endpoint.rds.amazonaws.com",
  "port": 5432,
  "dbname": "rawg_db"
}
```

### **4. Crear base de datos RDS**
```bash
# Ejecutar script de creación del esquema
psql -h tu-rds-endpoint -U usuario -d rawg_db -f sql/create_schema.sql
```

O usar el notebook de desarrollo para crear el esquema.

---


### **5. Configurar pgAdmin 4 (opcional, recomendado)**

pgAdmin 4 facilita la administración de la base de datos RDS y la ejecución de queries.

#### **Instalación:**

**Windows:**
- Descargar desde [pgAdmin.org](https://www.pgadmin.org/download/pgadmin-4-windows/)
- Instalar ejecutable

**Linux:**
```bash
# Ubuntu/Debian
sudo apt install pgadmin4
```

**macOS:**
```bash
brew install --cask pgadmin4
```
#### **Conectar a RDS:**

1. Abrir pgAdmin 4
2. Click derecho en **"Servers"** → **"Register"** → **"Server"**
3. Configurar:

**General tab:**
- Name: `RAWG Production DB`

**Connection tab:**
- Host: `tu-rds-endpoint.rds.amazonaws.com`
- Port: `5432`
- Maintenance database: `rawg_db`
- Username: `tu_usuario`
- Password: `tu_password`
- Save password: s

**SSL tab:**
- SSL mode: `Require`

4. Click **"Save"**
Ahora puedes explorar el esquema `rawg` visualmente y ejecutar queries.

#### **Queries recomendadas:**

Ver estructura de tablas:
```sql
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns 
     WHERE table_schema = 'rawg' AND table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'rawg'
ORDER BY table_name;
```

Verificar conteo de registros:
```sql
SELECT 
    'games' as tabla, COUNT(*) as registros FROM rawg.games
UNION ALL
SELECT 'platforms', COUNT(*) FROM rawg.platforms
UNION ALL
SELECT 'genres', COUNT(*) FROM rawg.genres
UNION ALL
SELECT 'stores', COUNT(*) FROM rawg.stores
UNION ALL
SELECT 'tags', COUNT(*) FROM rawg.tags
ORDER BY registros DESC;
```


## Deployment en AWS Lambda

### **Paso 1: Empaquetar código**
```bash
# Crear directorio de deployment
mkdir lambda-deploy
cd lambda-deploy

# Copiar archivos necesarios
cp ../01_etl/aws_lambda/lambda_loader.py .
cp ../01_etl/transform_rawg.py .
cp -r ../utils .

# Crear ZIP
zip -r lambda-etl-pipeline.zip .
```

### **Paso 2: Crear función Lambda**
```bash
aws lambda create-function \
  --function-name rawg-etl-pipeline \
  --runtime python3.11 \
  --handler lambda_function.lambda_handler \
  --role arn:aws:iam::ACCOUNT_ID:role/lambda-execution-role \
  --zip-file fileb://lambda-etl-pipeline.zip \
  --timeout 300 \
  --memory-size 1024 \
  --environment Variables={PYTHONUNBUFFERED=1}
```

### **Paso 3: Añadir Lambda Layers**
```bash
# Layer de pandas
aws lambda update-function-configuration \
  --function-name rawg-etl-pipeline \
  --layers \
    arn:aws:lambda:eu-west-1:336392948345:layer:AWSSDKPandas-Python311:13 \
    arn:aws:lambda:us-east-1:898466741470:layer:psycopg2-py311:1
```

### **Paso 4: Configurar trigger S3**
```bash
aws s3api put-bucket-notification-configuration \
  --bucket project-api-load-rawg-cris \
  --notification-configuration file://s3-trigger-config.json
```

**s3-trigger-config.json:**
```json
{
  "LambdaFunctionConfigurations": [
    {
      "LambdaFunctionArn": "arn:aws:lambda:region:account:function:rawg-etl-pipeline",
      "Events": ["s3:ObjectCreated:*"],
      "Filter": {
        "Key": {
          "FilterRules": [
            {"Name": "suffix", "Value": ".json"}
          ]
        }
      }
    }
  ]
}
```

---

## Uso del Sistema

### **Carga inicial (histórica)**
```bash
# 1. Extraer datos históricos
python 01_etl/extract_rawg.py --mode historical --output extraccion_historica.json

# 2. Subir a S3 (esto dispara Lambda automáticamente)
aws s3 cp extraccion_historica.json s3://project-api-load-rawg-cris/

# Lambda detecta "historica" en el nombre:
# → Borra esquema existente
# → Recrea esquema limpio
# → Ejecuta INSERT masivo
```

### **Cargas incrementales (diarias)**
```bash
# 1. Extraer datos del día
python 01_etl/extract_rawg.py --mode daily --output games_2025-02-08.json

# 2. Subir a S3
aws s3 cp games_2025-02-08.json s3://project-api-load-rawg-cris/

# Lambda detecta archivo sin "historica":
# → Mantiene esquema existente
# → Ejecuta UPSERT (actualiza existentes, inserta nuevos)
```

### **Automatización con EventBridge**

Programar extracción diaria:
```bash
aws events put-rule \
  --name rawg-daily-extraction \
  --schedule-expression "cron(0 2 * * ? *)"  # 2 AM UTC diario
```

---

## Queries Analíticas de Ejemplo

### **Top 10 juegos mejor valorados**
```sql
SELECT 
    game_name,
    game_rating,
    ratings_count,
    released_ym
FROM rawg.games
WHERE ratings_count > 1000
ORDER BY game_rating DESC, ratings_count DESC
LIMIT 10;
```
### **Distribución de juegos por género**
```sql
SELECT 
    g.genre_name, 
    COUNT(*) as cantidad
FROM rawg.game_genres gg
JOIN rawg.genres g ON gg.genre_id = g.genre_id
GROUP BY g.genre_name
ORDER BY cantidad DESC;
```
### **Distribución de juegos por plataforma**
```sql
SELECT 
    p.platform_name,
    COUNT(DISTINCT gp.game_id) as total_games
FROM rawg.platforms p
JOIN rawg.game_platforms gp ON p.platform_id = gp.platform_id
GROUP BY p.platform_name
ORDER BY total_games DESC;
```



---

## Métricas del Sistema

### **Volumen de datos**

- **Juegos totales:** ~850,000 registros
- **Plataformas:** ~50 plataformas
- **Géneros:** ~20 géneros
- **Tags:** ~4,000 tags únicos
- **Relaciones game_platforms:** ~3.5M registros
- **Relaciones game_tags:** ~10M registros

### **Performance**

- **Carga histórica:** ~15-20 minutos (850K juegos)
- **Carga incremental:** ~2-5 minutos (1,000-5,000 juegos/día)
- **Tamaño base de datos:** ~5 GB (datos + índices)

---

##  Seguridad

-  Credenciales almacenadas en AWS Secrets Manager
-  Lambda con rol IAM de mínimos privilegios
-  RDS en VPC privada
-  Conexiones SSL/TLS a base de datos
-  API Key de RAWG como variable de entorno

---

##  Troubleshooting

### **Error: Foreign Key violation (esrb_id)**

**Causa:** Juegos con `esrb_id=0` que no existe en `esrb_ratings`

**Solución:** El pipeline convierte automáticamente `esrb_id=0` a `NULL`

### **Error: Column "released_at" does not exist**

**Causa:** Esquema desactualizado en RDS

**Solución:** 
```sql
DROP SCHEMA rawg CASCADE;
-- Volver a ejecutar create_schema.sql
```

### **Lambda timeout**

**Causa:** Archivo muy grande (>100K juegos)

**Solución:** Aumentar timeout y memoria:
```bash
aws lambda update-function-configuration \
  --function-name rawg-etl-pipeline \
  --timeout 600 \
  --memory-size 2048
```

---

## Roadmap

- [ ] Dashboard interactivo con Streamlit/Plotly
- [ ] Modelo de Machine Learning para predicción de ratings
- [ ] API REST para consultas al data warehouse
- [ ] Integración con más fuentes de datos (Metacritic, Steam)
- [ ] Análisis de sentimiento de reviews
- [ ] Sistema de recomendación de juegos

---

## Autora

**Cristina Rodríguez Arroyo**
-  Bootcamp AI & Data Science - Hack a Boss (2025-2026)
-  Santiago de Compostela, Galicia, España
-  Background: Ingeniería Forestal + Educación (Matemáticas) + GIS + BELLAS ARTES

---

## Licencia

Este proyecto es de código abierto bajo licencia MIT.

---

## Agradecimientos

- [RAWG.io](https://rawg.io/) por proporcionar la API de videojuegos
- AWS por la infraestructura serverless
- Hack a Boss por la formación en Data Science

---

