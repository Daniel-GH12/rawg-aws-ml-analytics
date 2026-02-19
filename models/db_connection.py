"""
Módulo de conexión a PostgreSQL RDS
Proyecto: rawg-aws-ml-analytics

Este módulo proporciona funciones para conectarse y consultar
la base de datos PostgreSQL en AWS RDS de forma segura.
"""

import psycopg2
import pandas as pd
import os
from typing import Optional, Dict, Any, List
import re
from contextlib import contextmanager


# ============================================================================
# CONFIGURACIÓN DE CONEXIÓN
# ============================================================================

# Credenciales desde variables de entorno
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'videogames_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'port': int(os.getenv('DB_PORT', '5432')),
    'sslmode': os.getenv('DB_SSLMODE', 'require'),
    'connect_timeout': int(os.getenv('DB_TIMEOUT', '10'))
}

# Schema por defecto
DB_SCHEMA = os.getenv('DB_SCHEMA', 'rawg')


# ============================================================================
# VALIDACIÓN DE SEGURIDAD
# ============================================================================

# Patrón para detectar comandos SQL peligrosos
FORBIDDEN_PATTERN = re.compile(
    r'(;|--|/\*|\*/|\b(insert|update|delete|drop|alter|create|truncate|grant|revoke)\b)',
    re.IGNORECASE
)


def validate_sql_security(sql: str) -> bool:
    """
    Valida que una query SQL sea segura (solo SELECT)
    
    Args:
        sql: Query SQL a validar
        
    Returns:
        True si es segura, False si contiene comandos peligrosos
        
    Raises:
        ValueError: Si la query contiene comandos no permitidos
    """
    sql_clean = sql.strip().lower()
    
    # Debe empezar con SELECT
    if not sql_clean.startswith('select'):
        raise ValueError("Solo se permiten queries SELECT")
    
    # Buscar patrones peligrosos
    if FORBIDDEN_PATTERN.search(sql):
        raise ValueError("Query contiene comandos SQL no permitidos")
    
    return True


# ============================================================================
# GESTIÓN DE CONEXIONES
# ============================================================================

def get_connection():
    """
    Crea una conexión a PostgreSQL RDS
    
    Returns:
        psycopg2.connection: Objeto de conexión
        
    Raises:
        psycopg2.Error: Si n