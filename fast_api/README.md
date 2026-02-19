# FastAPI - Text-to-SQL con Gemini

API REST para consultas en lenguaje natural sobre base de datos de videojuegos RAWG.

##  Características

- ✅ Text-to-SQL dinámico con Gemini AI
- ✅ Dos endpoints: `/ask-visual` (gráficos) y `/ask-text` (respuestas textuales)
- ✅ Validación de seguridad SQL
- ✅ Documentación interactiva automática
- ✅ Esquema actualizado con estructura real de RDS

##  Instalación
```bash
# 1. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales
```

##  Configuración

Editar archivo `.env`:
```env
GEMINI_API_KEY=tu_api_key  # Obtener en https://aistudio.google.com/apikey
DB_HOST=tu-rds-endpoint.rds.amazonaws.com
DB_NAME=videogames_db
DB_USER=tu_usuario
DB_PASSWORD=tu_password
DB_SCHEMA=rawg
```

##  Ejecutar
```bash
# Modo desarrollo
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Modo producción
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

##  Documentación

Una vez iniciado el servidor:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

##  Endpoints

### GET `/ask-visual`

Pregunta con respuesta visual (gráfico)

**Parámetros:**
- `question` (string, required): Pregunta en lenguaje natural

**Ejemplo:**
```bash
curl "http://localhost:8000/ask-visual?question=Top%2010%20géneros%20con%20más%20juegos"
```

**Respuesta:**
```json
{
  "question": "Top 10 géneros con más juegos",
  "sql_generated": "SELECT g.genre_name AS label...",
  "data": [...],
  "chart_base64": "iVBORw0KGgo...",
  "rows_count": 10
}
```

### GET `/ask-text`

Pregunta con respuesta textual

**Parámetros:**
- `question` (string, required): Pregunta en lenguaje natural

**Ejemplo:**
```bash
curl "http://localhost:8000/ask-text?question=¿Cuál%20es%20el%20juego%20mejor%20valorado?"
```

**Respuesta:**
```json
{
  "question": "¿Cuál es el juego mejor valorado?",
  "sql_generated": "SELECT game_name...",
  "answer": "El juego mejor valorado es...",
  "data": [...],
  "rows_count": 1
}
```

##  Ejemplos de Preguntas

### Visual (gráficos)
- "Top 10 géneros con más juegos"
- "Evolución de juegos lanzados por año desde 2015"
- "Plataformas más populares"
- "Rating promedio por año"
- "Top stores con más juegos"

### Text (respuestas textuales)
- "¿Cuál es el juego mejor valorado?"
- "¿Cuántos juegos hay en total?"
- "¿Qué género tiene mejor rating promedio?"
- "¿Cuáles son los 5 juegos con más playtime?"
- "¿Qué juegos se están jugando más ahora?"

##  Seguridad

-  Solo permite queries SELECT
-  Bloquea DROP, DELETE, UPDATE, INSERT
-  Validación de SQL antes de ejecutar
-  Manejo de errores robusto

##  Notas

- La API usa Gemini 2.5 Flash (gratis con límites)
- Límite: 15 requests/minuto, 1,500/día
- Los gráficos se retornan en base64 PNG
- Esquema actualizado con nombres reales: `game_rating`, `game_added`, `released_ym`

##  Troubleshooting

**Error 429 (Quota exceeded)**:
- Espera 1 minuto entre requests
- Cuota se renueva cada 24 horas

**Error de conexión DB**:
- Verifica credenciales en `.env`
- Verifica security groups de RDS

**SQL incorrecto generado**:
- Reformula la pregunta con más detalle
- Usa nombres de campos específicos