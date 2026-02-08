# RAWG AWS ML ANALYTICS
## Pipeline y Sistema de Predicción del Éxito de Videojuegos

---

## 1. Introducción

Este proyecto implementa un sistema completo de:

- Extracción de datos desde la API RAWG
- Almacenamiento en AWS S3
- Procesamiento y carga en PostgreSQL (RDS)
- Entrenamiento de un modelo Machine Learning
- Preparación para despliegue mediante API

El objetivo es predecir el éxito de videojuegos utilizando métricas de popularidad
y engagement.

---

## 2. Arquitectura General

### Componentes principales

1. RAWG API
2. AWS Lambda
3. AWS S3
4. AWS Step Functions
5. AWS RDS (PostgreSQL)
6. Jupyter Notebooks
7. XGBoost
8. FastAPI (pendiente)

### Flujo de datos

RAWG API  
↓  
Lambda Extractor  
↓  
S3 (raw data)  
↓  
Lambda Loader  
↓  
RDS PostgreSQL  
↓  
ML Notebook  
↓  
Modelo entrenado  

---

## 3. Estructura del Repositorio

rawg-aws-ml-analytics/
│
├── etl/
├── docs/
├── models/
├── FastAPI/
├── README.txt
└── .gitignore


---

## 4. Carpeta ETL

### 4.1 01_init_rds_schema.ipynb

Inicializa desde cero la base de datos PostgreSQL en AWS RDS.

Funciones:
- Eliminación segura de tablas existentes
- Creación del esquema relacional
- Índices
- Tabla de control ETL

Tablas principales:
- games
- game_metrics
- platforms
- tags
- game_platforms
- game_tags
- etl_runs

---

### 4.2 02_rawg_full_extractor_lambda.py

Lambda de extracción masiva inicial.

Funciones:
- Paginación sobre la API RAWG
- Descarga completa del catálogo
- Almacenamiento en S3

Uso:
Se ejecuta una sola vez al inicializar el sistema.

---

### 4.3 03_rawg_full_extraction_pipeline.py

Step Function de orquestación.

Funciones:
- Divide la extracción masiva
- Controla reintentos
- Evita límites de tiempo de Lambda
- Garantiza completitud

---

### 4.4 04_rawg_extractor_lambda.py

Lambda incremental diaria.

Funciones:
- Obtiene juegos actualizados
- Filtra por fecha
- Actualiza S3 diariamente

Uso:
Programada con EventBridge.

---

### 4.5 05_rawg_loader_lambda.py

Lambda de carga en RDS.

Funciones:
- Activada por eventos S3
- Lee archivos JSON
- Normaliza datos
- Inserta en PostgreSQL
- Actualiza histórico

Incluye:
- Control de duplicados
- Manejo de errores
- Movimiento a processed/

---

## 5. Carpeta models

### 5.1 rawg_success_predictor.ipynb

Notebook principal de Machine Learning.

Funciones:
- Carga datos desde RDS
- Limpieza
- Ingeniería de features
- Definición de etiquetas
- Entrenamiento XGBoost
- Evaluación
- Exportación del modelo

---

### 5.2 rawg_popularity_model.pkl

Modelo XGBoost entrenado.

Uso:
- Cargado posteriormente en FastAPI
- Utilizado en endpoint /predict

---

### 5.3 rawg_features.pkl

Lista ordenada de variables del modelo.

Permite:
- Validación de inputs
- Consistencia entre entrenamiento y predicción

---

## 6. Definición de Éxito

Se define éxito como:

> Juegos situados en el top 20% por número de usuarios que los han añadido
> a su biblioteca (added).

Justificación:
- Métrica directa de popularidad
- Disponible para la mayoría de juegos
- No depende de ratings escasos

Label:

success = added >= P80

---

## 7. Modelo Machine Learning

### Algoritmo

- XGBoost Classifier

### Variables

- age_days
- ratings_count
- reviews_count
- community_rating
- platform_count
- tag_count

### Métricas

Resultados típicos:

- AUC ≈ 0.96
- F1 ≈ 0.80
- Accuracy ≈ 0.92

Sin data leakage.

---

## 8. Pipeline de Entrenamiento

1. Consulta SQL desde RDS
2. Limpieza
3. Filtrado de ruido
4. Construcción de etiquetas
5. Split train/test
6. Entrenamiento
7. Evaluación
8. Guardado del modelo

---

## 9. Carpeta FastAPI

Reservada para:

- Backend REST
- Endpoints predictivos
- NLP → SQL
- Visualizaciones

Actualmente pendiente de implementación.

---

## 10. Despliegue

Infraestructura prevista:

- EC2 para FastAPI
- RDS gestionado
- Lambdas serverless
- IAM roles
- Security Groups

---

## 11. Replicación del Proyecto

### Paso 1: Infraestructura

1. Crear RDS
2. Ejecutar 01_init_rds_schema.ipynb

---

### Paso 2: Extracción inicial

1. Desplegar Lambdas
2. Ejecutar Step Function
3. Poblar S3

---

### Paso 3: Carga

1. Configurar trigger S3
2. Activar loader
3. Verificar RDS

---

### Paso 4: Entrenamiento

1. Ejecutar rawg_success_predictor.ipynb
2. Generar .pkl
3. Validar métricas

---

### Paso 5: API (futuro)

1. Crear FastAPI
2. Cargar modelo
3. Desplegar en EC2

---

## 12. Limitaciones

- No hay datos de ventas reales
- Alta proporción de juegos sin ratings
- Métricas dependientes de RAWG
- Histórico aún limitado

---

## 13. Trabajo Futuro

- Series temporales
- Reentrenamiento automático
- Feature store
- Dashboard
- MLOps

---