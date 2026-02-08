import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib # Para guardar el transformador de columnas
import os

def train_game_model():
    # Cargar datos
    df = pd.read_csv("./data/raw_dataset.csv")
    
    # Definir el TARGET (Qué es éxito?)
    # Consideramos éxito (1) si la nota es >= 4.0, fracaso (0) si es menor.
    df['is_success'] = (df['game_rating'] >= 4.0).astype(int)
    
    # Limpieza y feature engineering
    # Rellenamos nulos
    df['release_month'] = df['release_month'].fillna(6) # Mes 6 (Junio) como valor medio
    df['developers'] = df['developers'].fillna('Indie/Unknown')
    df['tags'] = df['tags'].fillna('')
    df['genres'] = df['genres'].fillna('Unknown')
    df['platforms'] = df['platforms'].fillna('Unknown')
    df['playtime'] = df['playtime'].fillna(df['playtime'].median())

    # Feature Engineering (Dummies)
    # Seleccionamos solo los tags que nos interesan para no crear 1000 columnas
    top_tags = ['Singleplayer', 'Multiplayer', 'Atmospheric', 'Great Soundtrack', 'Open World']
    for tag in top_tags:
        df[f'tag_{tag}'] = df['tags'].apply(lambda x: 1 if tag in str(x) else 0)

    # Dummies para lo demás (Limitamos desarrolladores a los más frecuentes para no saturar)
    gen_dummies = df['genres'].str.get_dummies(sep=',')
    plat_dummies = df['platforms'].str.get_dummies(sep=',')
    dev_dummies = df['developers'].str.get_dummies(sep=',')

    # Unir todo
    X = pd.concat([
        df[['playtime', 'suggestions_count', 'release_month']], # Numéricas
        df[[f'tag_{t}' for t in top_tags]], # Tags específicos
        gen_dummies, 
        plat_dummies,
        dev_dummies
    ], axis=1)
    
    # Reemplazamos caracteres problemáticos por nada o por guiones
    X.columns = [col.replace('[', '').replace(']', '').replace('<', '').replace('>', '') for col in X.columns]
    X.columns = [col.replace(' ', '_').replace('-', '_') for col in X.columns]
    
    # Aseguramos que todos los datos sean float
    X = X.astype(float)
    
    y = df['is_success'].astype(int)

    # Dividir dataset (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print(f"Entrenando XGBoost con {X_train.shape[1]} atributos...")

    # Configurar y Entrenar XGBoost
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
        eval_metric='logloss'
    )
    
    model.fit(X_train.values, y_train.values)

    # Evaluación
    y_pred = model.predict(X_test.values)
    print("\nRESULTADOS DEL MODELO:")
    print(classification_report(y_test, y_pred))

    # GUARDAR TODOO
    os.makedirs("./api/models", exist_ok=True)
    # Guardamos el modelo
    model.save_model("./api/models/game_predictor.json")
    # Guardamos la lista de columnas para que la API sepa el orden exacto
    joblib.dump(X.columns.tolist(), "./api/models/model_columns.pkl")
    
    print("Modelo y columnas guardados en /api/models/")

if __name__ == "__main__":
    train_game_model()