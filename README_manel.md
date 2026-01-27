# 🎮 Proyecto RAWG – Pipeline y API en AWS  
**Autor**: Manuel Enrique Serrano Berrocal  
**Rama**: `manel-rawg`  
**Fecha**: 28 enero 2026  

## 📌 Contexto
Basado en el documento `rawg.md`, este proyecto implementa un pipeline de datos y una API para analizar videojuegos usando:
- API de [RAWG](https://rawg.io/)
- Amazon Web Services (S3, Lambda, RDS, EC2)
- Python (FastAPI, pandas, boto3, scikit-learn)

## 🧩 Mi contribución planificada
Como parte del equipo, me enfocaré en:
1. **Extracción de datos** con Python (`requests` + paginación).
2. **Pipeline en AWS Lambda** para carga inicial y diaria.
3. **API FastAPI** con endpoints `/predict`, `/ask-text`, `/ask-visual`.
4. **Despliegue en EC2**.

> 📁 Este repositorio ya contiene:  
> - `README.md` (general)  
> - `descripcion_rawg` (otro compañero)  
> - Ahora añado `README_manel.md` como mi plan de trabajo.

## ✅ Próximos pasos inmediatos
- [ ] Obtener API Key de RAWG  
- [ ] Crear script `extract_rawg.py`  
- [ ] Subir avances progresivamente a esta rama
