from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()



@app.post("/ask-visual")
# Recibe una pregunta orientada a visualización, consulta la base de datos y devuelve un gráfico generado con Matplotlib/Seaborn.