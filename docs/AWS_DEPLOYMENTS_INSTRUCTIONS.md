

LAMBDA LOADER

Realiza la tarea de Procesamiento y Carga:

Esta función procesa los ficheros JSON y los carga de forma estructurada en la base de datos PostgreSQL en AWS RDS.
Se activa mediante un trigger de S3 al recibir nuevos datos.

| Característica | Descripción |
|----------------|-------------|
| **Detección automática** | Por nombre de archivo (histórico vs diario) |
| **Recreación de esquema** | Solo para archivos históricos |
| **Limpieza de FKs** | Automática antes de cargar |
| **INSERT o UPSERT** | Según el modo detectado |
| **Logs detallados** | Por fases para debugging |
| **Manejo de errores** | Try/catch con traceback completo |

## Flujo de ejecución

ARCHIVO: extraccion_historica.json
├─  Detecta "histórica"
├─   Borra esquema rawg
├─  Crea esquema limpio
├─  Lee JSON
├─  Transforma
├─  Limpia FKs
└─  INSERT masivo

ARCHIVO: games_2025-02-07.json
├─  Detecta archivo diario
├─  Mantiene esquema existente
├─  Lee JSON
├─  Transforma
├─  Limpia FKs
└─  UPSERT incremental

