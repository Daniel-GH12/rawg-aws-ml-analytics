from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


@app.post("/ask-text")
# Recibe una pregunta en texto, la convierte a SQL usando un modelo de **Hugging Face**, consulta la base de datos y devuelve una respuesta en texto.