
# INSTRUCCIONES PARA COMPLETAR LA FASE 01 EN AWS

## PASO 1: CREAR INSTANCIA RDS
1. Ir a AWS Console → RDS → Create database
2. Seleccionar: PostgreSQL 13+
3. DB instance identifier: rawg-games-db
4. Master username: postgres
5. Master password: [tu_contraseña_segura]
6. DB instance class: db.t3.micro (Free Tier)
7. Storage: 20 GB
8. VPC security group: Permitir conexiones desde Lambda
9. Database options: Initial database name = rawg_games_db

## PASO 2: CONFIGURAR BUCKET S3
1. Bucket ya existe: rawg-data-lake-manuel-39
2. En Permissions → Bucket Policy, añadir permisos para Lambda:
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Principal": {"Service": "lambda.amazonaws.com"},
         "Action": ["s3:GetObject", "s3:PutObject"],
         "Resource": "arn:aws:s3:::rawg-data-lake-manuel-39/*"
       }
     ]
   }

## PASO 3: CREAR FUNCIONES LAMBDA
### Lambda 3 (Carga a RDS):
1. Crear función: lambda_load_to_rds
2. Runtime: Python 3.9
3. Architecture: x86_64
4. Upload from: .zip file (empaquetar src/lambda_load_to_rds/)
5. Variables de entorno:
   - DB_HOST: [endpoint-de-tu-RDS]
   - DB_NAME: rawg_games_db  
   - DB_USER: postgres
   - DB_PASSWORD: [tu_contraseña]
   - S3_BUCKET_NAME: rawg-data-lake-manuel-39

### Lambda 2 (Extracción diaria):
1. Crear función: lambda_daily
2. Mismo runtime y arquitectura
3. Variables de entorno:
   - RAWG_API_KEY: 53721c9ba8a74e818865f9bb81ccb779
   - S3_BUCKET_NAME: rawg-data-lake-manuel-39

## PASO 4: CONFIGURAR AUTOMATIZACIÓN
### Trigger S3 para Lambda 3:
1. Ir a S3 → rawg-data-lake-manuel-39 → Properties → Event notifications
2. Crear notificación:
   - Prefix: raw/
   - Events: ObjectCreated (All)
   - Destination: Lambda function → lambda_load_to_rds

### EventBridge para Lambda 2:
1. Ir a EventBridge → Rules → Create rule
2. Schedule pattern: Rate(1 day)
3. Target: Lambda function → lambda_daily

## PASO 5: EJECUTAR HISTÓRICA (una sola vez)
1. Subir archivo histórico a S3:
   - s3://rawg-data-lake-manuel-39/raw/historical_20260201.json
2. Esto activará automáticamente Lambda 3 para cargar datos en RDS

# FASE 01 COMPLETADA

