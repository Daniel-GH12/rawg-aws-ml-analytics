RAWG AWS ML ANALYTICS
====================

Proyecto de análisis y predicción del éxito de videojuegos usando la API de RAWG,
AWS y Machine Learning.

--------------------------------------------------
Estructura del repositorio
--------------------------------------------------

.gitignore
    Archivos y carpetas excluidos del control de versiones.

README.txt
    Descripción básica del proyecto y su estructura.

etl/
    Scripts y notebooks para la extracción, carga y almacenamiento de datos.

    01_init_rds_schema.ipynb
        Inicializa desde cero la estructura de la base de datos en AWS RDS.

    02_rawg_full_extractor_lambda.py
        Lambda para la extracción masiva inicial desde la API de RAWG a S3.

    03_rawg_full_extraction_pipeline.py
        Step Function que orquesta la extracción masiva en múltiples ejecuciones.

    04_rawg_extractor_lambda.py
        Lambda para actualizaciones diarias de datos desde RAWG.

    05_rawg_loader_lambda.py
        Lambda activada por S3 que carga datos procesados en RDS.

docs/
    Documentación completa del proyecto.

models/
    Archivos relacionados con el entrenamiento del modelo.

    rawg_success_predictor.ipynb
        Notebook de entrenamiento del modelo XGBoost.

    rawg_popularity_model.pkl
        Modelo entrenado serializado.

    rawg_features.pkl
        Lista de variables usadas por el modelo.

FastAPI/
    Carpeta reservada para el desarrollo de la API (pendiente).

--------------------------------------------------
Objetivo
--------------------------------------------------

Construir un pipeline en AWS para extraer datos de videojuegos, almacenarlos,
procesarlos y entrenar un modelo capaz de predecir su éxito.
