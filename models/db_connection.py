"""
Conexión a PostgreSQL RDS
Proyecto: rawg-aws-ml-analytics

Este módulo solo maneja la conexión a RDS.
Las queries SQL son generadas dinámicamente por Gemini API.
"""

import os
import json
import psycopg2
import pandas as pd
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError
import sys


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.aws_secrets import get_rds_credentials

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

SECRET_NAME = os.getenv("DB_SECRET_NAME", "Postgre")
REGION_NAME = os.getenv('AWS_REGION', 'eu-north-1')
DB_SCHEMA = os.getenv("DB_SCHEMA", "rawg")  

# ============================================================================
# FUNCIONES DE CONEXIÓN
# ============================================================================

def get_connection():

    try:
        creds = get_rds_credentials(SECRET_NAME) 
        # Conectar a RDS
        conn = psycopg2.connect(
            host=creds["host"],
            port=int(creds["port"]),
            dbname=creds["dbname"],
            user=creds["username"],
            password=creds["password"],
            sslmode="require",
            connect_timeout=10,
        )
                
        return conn
        

    except Exception as e:
        raise Exception(f"Error conectando a PostgreSQL RDS: {e}")


def query_to_dataframe(sql: str, params: Optional[tuple] = None) -> pd.DataFrame:
   
    conn = None
    
    try:
        # Conectar a RDS
        conn = get_connection()
        
        # Ejecutar query y convertir a DataFrame
        if params:
            df = pd.read_sql_query(sql, conn, params=params)
        else:
            df = pd.read_sql_query(sql, conn)
        
        return df
        
    except psycopg2.Error as e:
        # Error SQL (query inválida, tabla no existe, etc.)
        error_msg = e.pgerror if hasattr(e, 'pgerror') else str(e)
        raise psycopg2.Error(f"Error SQL: {error_msg}")
        
    except Exception as e:
        # Error de conexión u otro
        raise Exception(f"Error ejecutando query: {str(e)}")
        
    finally:
        # Siempre cerrar conexión
        if conn:
            conn.close()


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """
    Script de prueba de conexión
    Ejecutar: python models/db_connection.py
    """
    
    print("=" * 80)
    print("TEST DE CONEXIÓN A RDS")
    print("=" * 80)
    
    print(f"\nConfiguración:")
    print(f"   Secret Name: {SECRET_NAME}")
    print(f"   AWS Region: {REGION_NAME}")
    print(f"   DB Schema: {DB_SCHEMA}")

    # Test 1: Obtener credenciales
    print(f"\nObteniendo credenciales desde Secrets Manager...")
    
    try:
        secret = get_rds_credentials(
            secret_name=SECRET_NAME,
            region_name=REGION_NAME
        )
        print(f"   Credenciales obtenidas correctamente")
        print(f"   Host: {secret['host']}")
        print(f"   Database: {secret.get('dbname', secret.get('database'))}")
        print(f"   User: {secret['username']}")
        print(f"   Port: {secret.get('port', 5432)}")
        
    except Exception as e:
        print(f"   Error obteniendo credenciales: {e}")
        print(f"\nVerifica:")
        print(f"   - AWS credentials configuradas: aws configure")
        print(f"   - Secret existe: aws secretsmanager list-secrets")
        print(f"   - Nombre correcto: {SECRET_NAME}")
        print(f"   - Región correcta: {REGION_NAME}")
        print(f"   - Permisos IAM: secretsmanager:GetSecretValue")
        exit(1)
    
    # Test 2: Conexión a RDS
    print(f"\nProbando conexión...")
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Obtener versión de PostgreSQL
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0].split(',')[0]
        
        cursor.close()
        conn.close()
        
        print(f"   Conexión exitosa")
        print(f"   {version}")
        
    except Exception as e:
        print(f"   Error de conexión: {e}")
        exit(1)
    
    # Test 3: Verificar schema
    print(f"\nVerificando schema '{DB_SCHEMA}'...")
    try:
        sql = f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.schemata 
                WHERE schema_name = '{DB_SCHEMA}'
            );
        """
        df = query_to_dataframe(sql)
        schema_exists = df.iloc[0, 0]

        if schema_exists:
            print(f"   Schema '{DB_SCHEMA}' existe")
        else:
            print(f"   Schema '{DB_SCHEMA}' NO existe")
            exit(1)
            
    except Exception as e:
        print(f"   Error verificando schema: {e}")
        exit(1)
    
    # Test 4: Contar tablas
    print(f"\nContando tablas en schema...")
    try:
        sql = f"""
            SELECT COUNT(*) as total_tablas
            FROM information_schema.tables 
            WHERE table_schema = '{DB_SCHEMA}'
              AND table_type = 'BASE TABLE';
        """
        df = query_to_dataframe(sql)
        total_tablas = df.iloc[0, 0]
        
        print(f"   Tablas encontradas: {total_tablas}")
        
    except Exception as e:
        print(f"   Error contando tablas: {e}")
        exit(1)
    
    # Test 5: Contar juegos
    print(f"\nContando registros en tabla 'games'...")
    try:
        sql = f"SELECT COUNT(*) as total FROM {DB_SCHEMA}.games;"
        df = query_to_dataframe(sql)
        total_games = df.iloc[0, 0]
        
        print(f"   Juegos en base de datos: {total_games:,}")
        
    except Exception as e:
        print(f"   Error contando juegos: {e}")
        exit(1)
    
    # Test 6: Query con JOIN (verificar integridad de FK)
    print(f"\nProbando query con JOIN...")
    try:
        sql = f"""
            SELECT COUNT(*) as total
            FROM {DB_SCHEMA}.game_genres gg
            JOIN {DB_SCHEMA}.genres g ON g.genre_id = gg.genre_id
            JOIN {DB_SCHEMA}.games ga ON ga.game_id = gg.game_id;
        """
        df = query_to_dataframe(sql)
        total_relations = df.iloc[0, 0]
        
        print(f"   Relaciones games-genres: {total_relations:,}")
        
    except Exception as e:
        print(f"   Error en JOIN: {e}")
        exit(1)
    
    print("\n" + "=" * 80)
    print("TODOS LOS TESTS PASARON - CONEXIÓN RDS FUNCIONAL")
    print("=" * 80)