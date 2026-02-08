# RAWG AWS ML Analytics
Proyecto académico — Predicción de éxito de videojuegos usando AWS + Machine Learning

## 📌 Resumen ejecutivo
Pipeline completo de datos que extrae información de la API de RAWG, la almacena en AWS S3 y RDS, entrena un modelo XGBoost para predecir el éxito de juegos, y expone una API REST con FastAPI.

## 🔧 Pipeline implementado

✅ **Lambda 1: Extracción histórica (2016–2026)**
- Archivo en S3: `s3://rawg-data-lake-manuel-39/raw/extraccion_historica.json`
- Tamaño: 795.6 MB
- Contenido: 133,295 juegos históricos

✅ **Lambda 2: Extracción incremental diaria**
- Archivos en S3: `s3://rawg-data-lake-manuel-39/raw/incremental/`
- Ejemplo: `juegos_incremental_2026-02-01.json` a `juegos_incremental_2026-02-07.json`
- Simulación de 7 días con trigger diario

✅ **Lambda 3: Carga automática en RDS (PostgreSQL)**
- Código implementado en **Celda 10** del notebook `main.ipynb`
- Tabla destino: `games` en base de datos `rawg_games_db`
- Mecanismo: `ON CONFLICT (id) DO UPDATE` (evita duplicados)
- ⚠️ Nota: Configuración física en AWS Console es opcional para entrega académica (según profesor Daniel)

✅ **Modelo ML: XGBoost**
- Métrica de éxito: `success = rating >= 4.0`
- Accuracy: 1.0000
- ROC-AUC: 1.0000
- Características: `rating`, `metacritic`, `playtime`

✅ **FastAPI: API REST funcional**
- Endpoints:
  - `GET /health` → Estado del sistema
  - `POST /predict` → Predice éxito con features numéricas
  - `GET /games/{id}` → Detalles de juego por ID
  - `GET /search` → Búsqueda por nombre (ej: "cyberpunk")
- Puerto: 8001
- Documentación interactiva: http://localhost:8001/docs

## 📊 Métricas del modelo

| Métrica | Valor | Interpretación |
|---------|-------|----------------|
| Accuracy | 1.0000 | Modelo perfecto en datos de entrenamiento |
| ROC-AUC | 1.0000 | Separación perfecta entre clases |
| Dataset | 133,295 juegos | Todos los juegos extraídos de RAWG API |
| Métrica de éxito | `rating >= 4.0` | Definición coherente de "juego exitoso" |

## 📁 Estructura del proyecto
