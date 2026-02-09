# RAWG Game Success Predictor & Intelligent Analytics

Este proyecto es una solución **End-to-End** de Ingeniería de Datos y Machine Learning. Integra la extracción automatizada de datos desde la API de RAWG, su procesamiento en la nube y la exposición de modelos predictivos mediante una API inteligente.

El sistema combina ETL, Machine Learning y servicios cloud para ofrecer análisis avanzados sobre videojuegos y predicciones de éxito comercial.

---

## 🏗️ Arquitectura del Sistema

El proyecto implementa un flujo completo de datos:

1. **Pipeline de Datos (ETL):**  
   Extracción, transformación y carga mediante AWS Lambda hacia AWS RDS (PostgreSQL).

2. **ML Ops:**  
   Scripts dedicados para la obtención de datos locales y el entrenamiento del modelo XGBoost.

3. **Servicio Cloud:**  
   API desarrollada con FastAPI desplegada en AWS EC2 con capacidades de NLP y visualización dinámica.

---

## 📁 Estructura del Proyecto

<pre>
RAWG_ML_PROJECT/
├── ETL/                                # Pipeline de datos y scripts de ingestión
│   ├── 01_init_rds_schema.ipynb         # Inicialización del esquema en RDS
│   ├── 02_rawg_full_extractor_lambda.py # Lambda para extracción masiva
│   ├── 03_rawg_full_extraction_pipeline.py # Orquestación completa del ETL
│   ├── 04_rawg_extractor_lambda.py      # Extracción incremental diaria
│   ├── 05_rawg_loader_lambda.py         # Carga de datos en PostgreSQL
│   └── create_tables.sql               # Creación de tablas en la base de datos
│
├── api/                                # Núcleo de la aplicación FastAPI (EC2)
│   ├── main.py                         # Endpoints, integración de Gemini y XGBoost
│   ├── requirements.txt                # Dependencias del servicio
│   └── models/                         # Artefactos del modelo entrenado
│       ├── game_predictor.json         # Modelo XGBoost para inferencia
│       └── model_columns.pkl           # Columnas del dataset serializadas
│
├── scripts_entrenamiento/              # Pipeline de Machine Learning
│   ├── data_fetcher.py                 # Obtención y preparación de datos
│   └── train_model.py                  # Entrenamiento y exportación del modelo
│
├── .gitignore                          # Exclusión de archivos temporales y sensibles
└── README.md                           # Documentación del proyecto
</pre>

---

## 🧠 Stack Tecnológico

**Backend**
- Python
- FastAPI
- Uvicorn

**Infraestructura Cloud**
- AWS EC2
- AWS RDS (PostgreSQL)
- AWS Lambda

**IA & Machine Learning**
- Google Gemini Pro (NLP)
- XGBoost
- Scikit-learn

**Visualización**
- Matplotlib
- Seaborn

---

## 🚀 Capacidades de la API

La API expone tres servicios principales:

1. **Predicción de Éxito (`/predict`)**  
   Inferencia en tiempo real mediante el modelo XGBoost.

2. **Consultoría IA (`/ask-text`)**  
   Traducción de lenguaje natural a SQL para consultas sobre la base de datos mediante Gemini.

3. **Visualización Inteligente (`/ask-visual`)**  
   Generación automática de gráficos y reportes basados en datos RAWG.

---

 ## Acceso a la API en Producción

La API desplegada en AWS EC2 está disponible en:
https://bit.ly/rawg-fastapi
