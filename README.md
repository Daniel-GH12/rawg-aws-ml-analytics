# 🎮 RAWG Game Success Predictor & Intelligent Analytics

Este proyecto es una solución **End-to-End** de Ingeniería de Datos y Machine Learning. Integra la extracción automatizada de datos desde la API de RAWG, su almacenamiento y procesamiento en la nube de AWS, y la exposición de una API inteligente potenciada por Inteligencia Artificial (Gemini).

## 🚀 Arquitectura del Sistema

El proyecto implementa un flujo completo de datos:
1.  **Pipeline de Datos:** Extracción y carga (ETL) mediante AWS Lambda hacia AWS RDS.
2.  **ML Ops:** Scripts dedicados para la obtención de datos locales y el entrenamiento del modelo XGBoost.
3.  **Servicio Cloud:** API robusta en FastAPI desplegada en AWS EC2 con capacidades de NLP y visualización dinámica.

---

## 📂 Estructura del Proyecto

<pre>```text
RAWG_ML_PROJECT/
├── api/                        # Núcleo de la aplicación FastAPI (Desplegado en EC2)
│   ├── main.py                 # Lógica de endpoints, integración de Gemini y XGBoost
│   ├── requirements.txt        # Dependencias de producción (fastapi, uvicorn, xgboost, etc.)
│   └── models/                 # Artefactos del modelo entrenado
│       ├── game_predictor.json # Modelo XGBoost listo para inferencia
│       └── model_columns.pkl   # Serialización de las columnas del set de datos
│
├── infraestructure/            # Infraestructura Cloud y Persistencia
│   ├── aws_lambdas/            # Funciones Serverless para el flujo ETL
│   │   ├── lambda_extraction.py    # Extracción RAWG -> S3/RDS
│   │   └── lambda_transformation.py# Transformación y limpieza de datos
│   └── sql/                    # Scripts de base de datos
│       └── create_tables.sql       # DDL para la estructura en AWS RDS (PostgreSQL)
│
├── scripts_entrenamiento/      # Pipeline de Machine Learning
│   ├── data_fetcher.py         # Script para la obtención de datos de entrenamiento
│   └── train_model.py          # Script de entrenamiento y exportación del modelo XGBoost
│
├── data/                       # Almacenamiento de datos locales (Ignorado en Git)
│   └── raw_dataset.csv         # Dataset crudo para entrenamiento
│
└── .gitignore                  # Exclusión de archivos (Secrets, venv, datos pesados y logs)
```</pre>

## 🛠️ Stack Tecnológico

**Backend:** Python 3.9+, FastAPI, Uvicorn.
**Infraestructura Cloud:** AWS EC2, AWS RDS (PostgreSQL), AWS Lambda.
**IA & Machine Learning:** Google Gemini Pro (NLP), XGBoost, Scikit-learn.
**Visualización:** Matplotlib, Seaborn.

## 🔌 Capacidades de la API

La API expone tres servicios críticos:
**Predicción de Éxito (/predict):** Inferencia en tiempo real sobre el éxito de un título mediante el modelo XGBoost.
**Consultoría IA (/ask-text):** Traducción de lenguaje natural a SQL para consultas complejas sobre la DB mediante Gemini.
**Visualización Inteligente (/ask-visual):** Generación de reportes gráficos automáticos basados en la data de RAWG.

<pre>

⚙️ Guía de Ejecución en AWS EC2
Instalación de dependencias: ```bash pip install -r api/requirements.txt ```

Lanzamiento en segundo plano (Inmortal): ```bash nohup python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 & ``` </pre>