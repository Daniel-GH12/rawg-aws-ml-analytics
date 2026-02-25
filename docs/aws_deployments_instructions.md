# Guía de Deployment — AWS (Lambda ETL + EC2 FastAPI)

Esta guía cubre el despliegue completo del sistema en AWS:
- **Parte 1:** Lambda Loader (ETL pipeline)
- **Parte 2:** FastAPI en EC2 (API ML + Text-to-SQL)

---

## Tabla de Contenidos

1. [Pre-requisitos](#pre-requisitos)
2. [Parte 1: Lambda Loader (ETL)](#parte-1-lambda-loader-etl)
   - [Preparar el código](#1-preparar-el-código)
   - [Crear la función Lambda](#2-crear-la-función-lambda)
   - [Configurar Lambda Layers](#3-configurar-lambda-layers)
   - [Añadir trigger S3](#4-añadir-trigger-s3)
   - [Configurar permisos](#5-configurar-permisos)
   - [Probar la función](#6-probar-la-función)
   - [Monitorear ejecuciones](#7-monitorear-ejecuciones)
3. [Parte 2: FastAPI en EC2](#parte-2-fastapi-en-ec2)
   - [Crear la instancia EC2](#1-crear-la-instancia-ec2)
   - [Conectar y preparar EC2](#2-conectar-y-preparar-ec2)
   - [Clonar el repositorio](#3-clonar-el-repositorio)
   - [Instalar dependencias](#4-instalar-dependencias)
   - [Configurar credenciales](#5-configurar-credenciales)
   - [Conectar EC2 a RDS](#6-conectar-ec2-a-rds)
   - [Lanzar la API](#7-lanzar-la-api)
   - [Dificultades encontradas y soluciones](#8-dificultades-encontradas-y-soluciones)

---

## Pre-requisitos

Antes de comenzar, asegúrate de tener:

- Cuenta AWS con acceso a: Lambda, S3, RDS, Secrets Manager, IAM, CloudWatch, EC2
- Servicios ya creados:
  - Bucket S3: `project-api-load-rawg-cris`
  - RDS PostgreSQL con esquema `rawg` creado
  - Secreto en Secrets Manager: `Postgre` con credenciales de RDS
- Código preparado en local:
  - `lambda_loader.py`, `transform_rawg.py`, `utils/aws_secrets.py`
  - Par de claves `.pem` para acceso SSH a EC2
- API Key de Gemini ([obtener aquí](https://aistudio.google.com/apikey))

---

## Parte 1: Lambda Loader (ETL)

### 1. Preparar el código

#### **1.1 Estructura del paquete**
```
lambda-loader.zip/
├── lambda_loader.py         # Handler principal
├── transform_rawg.py        # Script de transformación
├── pg8000/                  # Driver PostgreSQL (sustituye a psycopg2)
├── scramp/
├── asn1crypto/
├── dateutil/
└── utils/
    └── aws_secrets.py       # Helper de Secrets Manager
```

#### **1.2 Crear el ZIP**

```powershell
# Ir al directorio del proyecto
cd C:\Users\crisr\dev\rawg-aws-ml-analytics

# Crear directorio temporal
mkdir lambda_loader_package
cd lambda_loader_package

# Copiar archivos
Copy-Item ..\lambda\lambda_loader.py .
Copy-Item ..\01_etl\transform_rawg.py .
Copy-Item -Recurse ..\utils .

# Crear ZIP
Compress-Archive -Path * -DestinationPath lambda-loader.zip
```

**Resultado:** Archivo `lambda_loader.zip` (~50-100 KB)

> ⚠️ Se sustituyó `psycopg2` por `pg8000` para evitar errores de incompatibilidad de versiones al ejecutar en entorno Linux (Lambda).

---

### 2. Crear la función Lambda

#### **2.1 Acceder a Lambda Console**

1. Ir a [AWS Lambda Console](https://console.aws.amazon.com/lambda/)
2. Click en **"Create function"**

#### **2.2 Configuración básica**

| Campo | Valor |
|-------|-------|
| **Function name** | `loader` |
| **Runtime** | Python 3.10 |
| **Architecture** | x86_64 |
| **Execution role** | Create a new role with basic Lambda permissions |

3. Click en **"Create function"**

#### **2.3 Subir código**

1. En **"Code source"** → click **"Upload from"** → **".zip file"**
2. Seleccionar `lambda-loader.zip`
3. Click **"Save"**

#### **2.4 Configurar Runtime settings**

1. Scroll hasta **"Runtime settings"** → click **"Edit"**

| Campo | Valor |
|-------|-------|
| **Handler** | `lambda_loader.lambda_handler` |

2. Click **"Save"**

#### **2.5 Configurar General configuration**

1. Pestaña **"Configuration"** → **"General configuration"** → **"Edit"**

| Campo | Valor | Explicación |
|-------|-------|-------------|
| **Memory** | 1024 MB | Suficiente para datasets grandes |
| **Timeout** | 5 min (300 sec) | Tiempo máximo de ejecución |
| **Ephemeral storage** | 512 MB | Default OK |

2. Click **"Save"**

---

### 3. Configurar Lambda Layers

#### **3.1 Layer de SQLAlchemy (custom)**

Crear el layer localmente:

```bash
# Crear estructura
mkdir -p sqlalchemy-layer/python/lib/python3.11/site-packages

# Instalar SQLAlchemy
pip install sqlalchemy -t sqlalchemy-layer/python/lib/python3.11/site-packages/

# Crear ZIP
cd sqlalchemy-layer
zip -r ../sqlalchemy-layer.zip python
```

Subir a AWS:

1. **Lambda Console** → **Layers** → **"Create layer"**

| Campo | Valor |
|-------|-------|
| **Name** | `sqlalchemy-py310` |
| **Upload** | `sqlalchemy-layer.zip` |
| **Compatible runtimes** | Python 3.10 |

2. Click **"Create"**

Añadir a la función:

1. Función `loader` → **Layers** → **"Add a layer"**
2. Seleccionar **"Custom layers"** → `sqlalchemy-py310`
3. Click **"Add"**

---

### 4. Añadir trigger S3

1. Click **"Add trigger"** → seleccionar **S3**

| Campo | Valor |
|-------|-------|
| **Bucket** | `project-api-load-rawg-cris` |
| **Event type** | All object create events |
| **Suffix** | `.json` |

2. Marcar: **"I acknowledge that using the same S3 bucket..."**
3. Click **"Add"**

Resultado esperado en el diagrama:
```
S3 (project-api-load-rawg-cris) → loader
```

---

### 5. Configurar permisos

El rol de ejecución de Lambda necesita permisos para acceder a S3, RDS y Secrets Manager. Asignar las políticas correspondientes desde **IAM → Roles → tu rol de Lambda → Add permissions**.

---

### 6. Probar la función

Desde **Lambda Console** → pestaña **"Test"** → crear evento de prueba con un JSON de ejemplo y verificar que la ejecución termina con `Status: Succeeded`.

---

### 7. Monitorear ejecuciones

**Lambda Console** → pestaña **"Monitor"** → **"View CloudWatch logs"** para ver logs de cada invocación.

---

## Parte 2: FastAPI en EC2

### 1. Crear la instancia EC2

Desde **AWS Console → EC2 → Launch Instance**:

| Parámetro | Valor |
|-----------|-------|
| **Nombre** | `rawg-api-server` |
| **AMI** | Amazon Linux 2023 (kernel-6.1) |
| **Tipo** | t2.micro (capa gratuita) |
| **Región** | eu-north-1 (Estocolmo) |
| **Almacenamiento** | Standard |
| **Security Group** | SSH (22), HTTP (80), Custom TCP (8000) — Allow All / Anywhere |
| **Key pair** | Crear nuevo par de claves y guardar el `.pem` |

> ⚠️ Guardar el `.pem` en una carpeta local fuera del repositorio — nunca subirlo a GitHub.

---

### 2. Conectar y preparar EC2

Conectar via SSH desde Git Bash o terminal local:

```bash
ssh -i "tu-clave.pem" ec2-user@<EC2-IP-PUBLICA>
```

Actualizar el sistema e instalar herramientas base:

```bash
sudo yum update -y
sudo yum install -y git python3 tmux nc
```

#### Crear memoria swap (obligatorio para t2.micro)

La instancia t2.micro tiene solo 1GB de RAM, insuficiente para instalar XGBoost (297MB). Crear swap antes de instalar dependencias:

```bash
sudo dd if=/dev/zero of=/swapfile bs=128M count=16
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

### 3. Clonar el repositorio

El repositorio es público, por lo que no requiere SSH. Clonar directamente la rama de trabajo:

```bash
git clone -b cristina https://github.com/Daniel-GH12/rawg-aws-ml-analytics.git
cd rawg-aws-ml-analytics/fast_api
```

Si GitHub solicita autenticación, usar un **Personal Access Token** (classic) como contraseña:

1. GitHub → **Settings → Developer Settings → Personal Access Tokens → Tokens (classic)**
2. Generar token con scope `repo`
3. Usar como contraseña al clonar

---

### 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

> ⚠️ Usar `scikit-learn==1.5.2` — la versión 1.6.1 es incompatible con Python 3.9 de Amazon Linux 2023 (error `__sklearn_tags__`). Ver tabla de dificultades.

---

### 5. Configurar credenciales

#### Gemini API Key

Exportar directamente en la terminal:

```bash
export GEMINI_API_KEY=tu_api_key
```

Para que persista entre sesiones SSH:

```bash
echo 'export GEMINI_API_KEY=tu_api_key' >> ~/.bashrc
source ~/.bashrc
```

#### Credenciales RDS

Las credenciales de la base de datos **no se configuran manualmente** — se obtienen automáticamente desde **AWS Secrets Manager** gracias al IAM Role asignado a la instancia. Ver siguiente sección.

---

### 6. Conectar EC2 a RDS

#### 6.1 Crear IAM Role para EC2

1. **IAM → Roles → Create role**
2. **Trusted entity:** AWS Service → EC2
3. **Permissions:** buscar y añadir `SecretsManagerReadWrite`
4. **Nombre:** `ec2-rawg-role`
5. Click **"Create role"**

#### 6.2 Asignar el rol a la instancia

**EC2 → tu instancia → Actions → Security → Modify IAM role** → seleccionar `ec2-rawg-role` → **"Update IAM role"**

El rol se aplica inmediatamente, sin necesidad de reiniciar.

#### 6.3 Configurar acceso de EC2 a RDS

**RDS → tu instancia → Connectivity & Security → Connected compute resources → "Set up EC2 connection"**

Seleccionar tu instancia EC2 — AWS configura automáticamente las reglas de Security Group para permitir tráfico en el puerto 5432.

| Componente | Configuración |
|-----------|--------------|
| **IAM Role** | `ec2-rawg-role` con `SecretsManagerReadWrite` |
| **Security Group RDS** | Inbound PostgreSQL (5432) desde EC2 Security Group |
| **Credenciales** | Gestionadas automáticamente por AWS Secrets Manager |

---

### 7. Lanzar la API

```bash
cd /home/ec2-user/rawg-aws-ml-analytics/fast_api
uvicorn main:app --host 0.0.0.0 --port 8000
```

Verificar que la API está corriendo accediendo desde el navegador:

```
http://<EC2-IP-PUBLICA>:8000/docs
```

> ⚠️ La IP pública de EC2 **cambia en cada reinicio** de la instancia. Consultar la nueva IP en AWS Console → EC2 → tu instancia → Public IPv4 address.

Para actualizar el código desde GitHub:

```bash
# Parar uvicorn con Ctrl+C
git pull
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

### 8. Dificultades encontradas y soluciones

| Problema | Causa | Solución |
|----------|-------|---------|
| `Killed` durante `pip install xgboost` | t2.micro tiene solo 1GB RAM — insuficiente para XGBoost (297MB) | Crear memoria swap antes de instalar: `sudo dd if=/dev/zero of=/swapfile bs=128M count=16 && sudo mkswap /swapfile && sudo swapon /swapfile` |
| `ModuleNotFoundError: utils.aws_secrets` | Archivo sensible excluido de GitHub via `.gitignore` | El módulo está en el repo pero no contiene credenciales — verificar que está presente tras el `git clone` |
| `'super' object has no attribute '__sklearn_tags__'` | Incompatibilidad entre scikit-learn 1.6.1 y Python 3.9 de Amazon Linux 2023 | Usar `scikit-learn==1.5.2` en `requirements.txt` y reentrenar el modelo en local con esa versión antes de hacer push |
| `Unable to locate credentials` | EC2 sin permisos para acceder a Secrets Manager | Crear IAM Role con política `SecretsManagerReadWrite` y asignarlo a la instancia |
| `connection timeout` a RDS | Security Group de RDS no permitía conexiones desde EC2 | Usar botón **"Set up EC2 connection"** en la consola de RDS |
| `GEMINI_API_KEY` se pierde al reconectar | Las variables de entorno no persisten entre sesiones SSH | Añadir al `~/.bashrc`: `echo 'export GEMINI_API_KEY=...' >> ~/.bashrc` |
| IP pública de EC2 cambia | Las instancias t2.micro no tienen IP elástica por defecto | Consultar la nueva IP en AWS Console tras cada reinicio, o asignar una **Elastic IP** para IP fija |
| `Could not import module "main"` | uvicorn lanzado desde la carpeta incorrecta | Navegar siempre a `rawg-aws-ml-analytics/fast_api` antes de lanzar uvicorn |

---

## Notas finales

- Los gráficos de la API se retornan en base64 PNG o PNG directo según el endpoint
- La API usa Gemini 2.5 Flash con límite de 1.500 requests/día (gratuito)
- El ETL se ejecuta automáticamente cada 24h mediante EventBridge
- Para instrucciones detalladas de los endpoints ver `fast_api/README.md`
