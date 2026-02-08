from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Crear la clase Usuario con Pydantic
class Features(BaseModel):
    age_days: int
    ratings_count: int
    reviews_coun: int
    community_rating: int
    platform_count: int
    tag_count: int

@app.post("/predict")
# Recibe los datos de un videojuego y devuelve la predicción del modelo
def success_predictor(datos: Features) -> dict:
    
    






 
