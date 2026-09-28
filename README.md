# Tarea 1 - Sistemas Distribuidos | Plataforma de Análisis de Tráfico en Región Metropolitana
![Docker](https://img.shields.io/badge/docker-ready-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-async-lightgreen)
![Redis](https://img.shields.io/badge/redis-caching-red)
![MongoDB](https://img.shields.io/badge/mongodb-storage-green)

Este es un proyecto para la recolección y consulta de alertas de tráfico en la ciudad de Santiago, Chile. Incluye un scraper que segmenta la zona metropolitana y consulta la API de Waze para obtener alertas, las almacena en MongoDB, y expone un servicio FastAPI con Redis como caché. También permite realizar experimentos para comparar diferentes configuraciones de Redis y métodos de selección de alertas.

---

## 📑 Contenidos

- [Tarea 1 - Sistemas Distribuidos | Plataforma de Análisis de Tráfico en Región Metropolitana](#tarea-1---sistemas-distribuidos--plataforma-de-análisis-de-tráfico-en-región-metropolitana)
  - [📑 Contenidos](#-contenidos)
  - [🚦 ¿Que hace este proyecto?](#-que-hace-este-proyecto)
  - [📖 Características principales](#-características-principales)
  - [📁 Estructura del repositorio](#-estructura-del-repositorio)
  - [🛠️ Infraestructura](#️-infraestructura)
  - [🚀 Instalación y ejecución](#-instalación-y-ejecución)
  - [🧪 Ejecución de experimentos](#-ejecución-de-experimentos)
  - [📌 Notas adicionales](#-notas-adicionales)
  - [👨‍💻 Autor](#-autor)

## 🚦 ¿Que hace este proyecto?

- Divide Santiago en subregiones para realizar múltiples consultas paralelas a la API de Waze.
- Recolecta alertas de tráfico como accidentes, congestión, cierres, etc.
- Guarda las alertas en una base de datos MongoDB, evitando duplicados.
- Expone una API REST (FastAPI) para consultar alertas por `uuid`.
- Implementa Redis como caché para acelerar las consultas repetidas.
- Permite generar trafico para evaluar cómo varía el rendimiento con distintas configuraciones de Redis y distribuciones.

---

## 📖 Características principales

- 📡 **Scraping de alertas de tráfico** desde la API de Waze, segmentando Santiago en subregiones.
- 🗃 **Almacenamiento en MongoDB**, evitando duplicados.
- 🚀 **Servicio web con FastAPI** para consultar alertas por UUID.
- ⚡ **Uso de Redis como caché**, para mejorar tiempos de respuesta.
- 🧪 **Generador de trafico** para comparar configuraciones de Redis (LRU vs LFU, etc).
- 🐳 **Contenedores Docker y orquestación con Docker Compose**.

---

## 📁 Estructura del repositorio

```plaintext
urban_traffic_flow/
│
├── scraper/
|   └── Dockerfile 
│   └── requirements.txt
│   └── scraper.py              # Módulo que divide Santiago, consulta Waze y almacena alertas
├── server/
│   └── Dockerfile 
│   └── requirements.txt
│   └── app.py                  # API FastAPI que responde a consultas por UUID, con Redis como caché y Mongodb como base de datos
├── generator/
|   └── Dockerfile 
│   └── requirements.txt
│   ├── generator.py            # Script principal para ejecutar experimentos
│   ├── distribution_by_importance.py
│   └── distribution_by_reliability.py
|   └── mongodb_client.py 
|
├── docker-compose.yml          # Orquestación de servicios: scraper, API, Redis, MongoDB
├── .env                        # Variables de entorno (MongoDB y Redis)
```

---
## 🛠️ Infraestructura
Cada uno de los servicios anteriormente descritos, estan creados de forma modular e independiente gracias a Docker-compose. Facilitando así,  el escalado y facil despliegue de los servicios.
El sistema está compuesto por servicios desplegados mediante Docker Compose, organizados de forma modular para facilitar pruebas y escalabilidad:

- **MongoDB**: Base de datos para almacenar las alertas.
- **Redis**: Caché para acelerar consultas repetidas.
- **Scraper**: Servicio que segmenta Santiago y consulta la API de Waze.
- **Server (FastAPI)**: Expone una API REST para consultar alertas.
- **Generator**: Generador de tráfico para realizar experimentos de carga y cache.
- **RedisInsight**: Herramienta visual para monitorear el estado del caché Redis.

Ademas, todos los servicios están conectados en una misma red Docker (`netuworku`), utilizan volúmenes persistentes y se inicializan con variables de entorno definidas en `.env`. Se configuran dependencias entre servicios para garantizar el orden de arranque.

Esto se puede ver con mas detalle en el archivo de configuración docker-compose.yml.

```yml
version: "3.9"

services:
   mongodb:
      image: mongo:8.0
      container_name: db
      restart: always
      environment:
         MONGO_INITDB_ROOT_USERNAME: ${MONGO_USERNAME}
         MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD}
         MONGO_INITDB_DATABASE: ${MONGO_DB}
      ports:
         - "27017:27017"
      volumes:
         - db_data:/data/db
      networks:
         - netuworku
      healthcheck:
         test: ["CMD", "bash", "-c", "echo > /dev/tcp/localhost/27017"]
         interval: 10s
         timeout: 5s
         retries: 5

   scraper:
      build: ./scraper
      container_name: scraper
      depends_on:
         mongodb:
            condition: service_healthy
      environment:
         - MONGO_HOST=mongodb
         - MONGO_PORT=${MONGO_PORT}
         - MONGO_DB=${MONGO_DB}
         - MONGO_USER=${MONGO_USERNAME}
         - MONGO_PASSWORD=${MONGO_PASSWORD}
         - MONGO_COLLECTION=${MONGO_COLLECTION}
      networks:
         - netuworku

   redis:
      image: bitnami/redis:latest
      container_name: redis
      restart: always
      environment:
         - REDIS_PASSWORD=${REDIS_PASSWORD}
      ports:
         - "6379:6379"
      volumes:
         - redis_data:/bitnami/redis/data
      networks:
         - netuworku
      healthcheck:
         test: ["CMD", "redis-cli", "-a", "$${REDIS_PASSWORD}", "ping"]
         interval: 10s
         timeout: 5s
         retries: 5

   redisinsight:
      image: redislabs/redisinsight:latest
      container_name: redisinsight
      restart: always
      ports:
         - "5540:5540"
      networks:
         - netuworku
      volumes:
         - redisinsight_data:/data
      depends_on:
         redis:
            condition: service_healthy
   server:
      build: ./server
      container_name: server
      restart: unless-stopped
      depends_on:
         redis:
            condition: service_healthy
         mongodb:
            condition: service_healthy
      ports:
            - "8000:8000"
      environment:
         - MONGO_HOST=mongodb
         - MONGO_PORT=${MONGO_PORT}
         - MONGO_DB=${MONGO_DB}
         - MONGO_USER=${MONGO_USERNAME}
         - MONGO_PASSWORD=${MONGO_PASSWORD}
         - MONGO_COLLECTION=${MONGO_COLLECTION}
         
         - REDIS_HOST=${REDIS_HOST}
         - REDIS_PORT=${REDIS_PORT}
         - REDIS_PASSWORD=${REDIS_PASSWORD}

      healthcheck:
         test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()"]
         interval: 10s
         timeout: 5s
         retries: 5

      networks:
         - netuworku

   generator:
      build: ./generator
      container_name: generator
      restart: no
      depends_on:
         redis:
            condition: service_healthy
         mongodb:
            condition: service_healthy
         server: 
            condition: service_healthy
      environment:
         - SERVER_HOST=server
         - MONGO_HOST=mongodb
         - MONGO_PORT=${MONGO_PORT}
         - MONGO_DB=${MONGO_DB}
         - MONGO_USER=${MONGO_USERNAME}
         - MONGO_PASSWORD=${MONGO_PASSWORD}
         - MONGO_COLLECTION=${MONGO_COLLECTION}
         - REDIS_HOST=${REDIS_HOST}
         - REDIS_PORT=${REDIS_PORT}
         - REDIS_PASSWORD=${REDIS_PASSWORD}
      volumes:
         - generator_output:/app/output
      networks:
         - netuworku

volumes:
   db_data:
   redis_data:
   redisinsight_data:
   generator_output:

networks:
   netuworku:
      driver: bridge

```

Finalmentee, se puede ver que todos los contenedores comparten la misma network. Se definieron volumenes de docker los guales guardan los datos del scrapeo, de redis, y los resultados de los experimentos a ejecutar. Los contenedores se inicializan con variables de entorno ya definidas en un archivo .env en la carpeta raiz. Y se configuraron dependencias de inicialización para ciertos contenedores, de forma que los procesos se ejecuten de forma correcta y oportuna.


## 🚀 Instalación y ejecución

1. Clona el repositorio:

```bash
git clone https://github.com/METRO3H/urban_traffic_flow.git
cd urban_traffic_flow
```

2. Crea un archivo `.env` en la raíz del proyecto con este contenido:

```env
MONGO_DB=waze_data
MONGO_PORT=27017
MONGO_USERNAME=BOB
MONGO_PASSWORD=mongo_pass_here...
MONGO_COLLECTION=urban_alerts

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=redis_pass_here...
```

3. Levanta los servicios con Docker Compose:

```yml
docker-compose up --build
```

4. Accede a los servicios disponibles

- [http://localhost:8000/docs](http://localhost:8000/docs) – Interfaz interactiva de la API (Swagger UI).
- [http://localhost:5540/](http://localhost:5540/) – Interfaz web de Redis (por ejemplo, Redis Commander, si está habilitada).

5. Ejemplo de consulta de una alerta por UUID

```bash
curl http://localhost:8000/alert/567a6cdf-1cbf-4916-8b69-250c14e7ac44
```

Respuesta esperada del server:

```json
{
   "source": "mongodb",
   "data": {
      "_id": { "$oid": "680ed2d2282cd31bddca429f" },
      "country": "CI",
      "nThumbsUp": 16,
      "reportRating": 2,
      "reportByMunicipalityUser": "false",
      "reliability": 10,
      "type": "HAZARD",
      "fromNodeId": 156127887,
      "uuid": "567a6cdf-1cbf-4916-8b69-250c14e7ac44",
      "speed": 0,
      "reportMood": 1,
      "subtype": "HAZARD_ON_SHOULDER_CAR_STOPPED",
      "street": "Ruta F-50 / Camino Lo Orozco",
      "additionalInfo": "",
      "toNodeId": 258608152,
      "id": "alert-1817530736/567a6cdf-1cbf-4916-8b69-250c14e7ac44",
      "nComments": 0,
      "inscale": true,
      "confidence": 5,
      "nearBy": "La Retuca",
      "roadType": 6,
      "magvar": 159,
      "wazeData": "world,-71.34554,-33.135944,567a6cdf-1cbf-4916-8b69-250c14e7ac44",
      "location": { "x": -71.34554, "y": -33.135944 },
      "pubMillis": 1745799221000
   }
}
```
## 🧪 Ejecución de experimentos
Los experimentos a realizar por parte del contenedor **generator** respecto a la generación de trafico son los siguientes:

- Experimento 1: Distribución por fiabilidad y Configuración de Redis con maxmemory 2mb, política allkeys-lru
- Experimento 2: Distribución por importancia y Configuración de Redis con maxmemory 2mb, política allkeys-lru
- Experimento 3: Distribución por fiabilidad y Configuración de Redis con maxmemory 3mb, política allkeys-lru
- Experimento 4: Distribución por importancia y Configuración de Redis con maxmemory 3mb, política allkeys-lru
- Experimento 5: Distribución por fiabilidad y Configuración de Redis con maxmemory 2mb, política allkeys-lfu
- Experimento 6: Distribución por importancia y Configuración de Redis con maxmemory 2mb, política allkeys-lfu
- Experimento 7: Distribución por fiabilidad y Configuración de Redis con maxmemory 3mb, política allkeys-lfu
- Experimento 8: Distribución por importancia y Configuración de Redis con maxmemory 3mb, política allkeys-lfu

Las distribuciones seleccionadas fueron la distribución por **importancia**, y la por **fiabilidad**. La distribución por **importancia** fue dada debido a que al interés de la gente respecto al evento, a la gente le interesa o le es mucho mas importante un accidente que el que haya congestión. En cuanto a la distribución por **fiabilidad**, tiene que ver con cuan probable es que el evento reportado sea cierto, lo cual interesa a los usuarios.

Ejemplo:

```python
# Probabilities by type
probabilities = {
    "ACCIDENT": 0.25,
    "ROAD_CLOSED": 0.20,
    "HAZARD": 0.20,
    "POLICE": 0.15,
    "JAM": 0.15,
    "CHIT_CHAT": 0.05
}
```

Finalmente, se toman estas probabilidades a la hora de elegir cual es el documento a consultar al server, resultando en una distribución.

---

Es importante señalar que los experimentos empiezan dentro del contenedor **generator** apenas se recolectan los primeros documentos del scrapeo, y finalizan al correr los experimentos por ultima vez apenas se obtengan mas de 10.000 documentos.

```python
if __name__ == "__main__":
    while True:
        db_collection_count = db_collection.count_documents({})
        
        if db_collection.count_documents({}) > 10000:
            run_experiment()
            break
        
        run_experiment()
        
     
    logger.info("\nExperiments completed.")
    redis_connection.close()
    db_collection.client.close()
```

---

Cada uno de los procesos anteriores (Scrapeo, Server, Generador) se pueden visualizar en directo aplicando los siguientes comandos :

```yml
docker logs -f scraper # Ver logs en vivo del contenedor scraper
docker logs -f server # Ver logs en vivo del contenedor server
docker logs -f generator # Ver logs en vivo del contenedor generator
```

---

Como dije anteriormente, los resultados de los experimentos de generación de trafico se van guardando actualizando en sus respectivos archivos .json, de acuerdo a sus politicas de remocion, tamaño de cache y distribución empleada.

Finalmente, los resultados de los experimentos se pueden obtener dentro de tu propia maquina copiando los archivos resultantes a tu propio sistema con el siguiente comando:

```yml
docker cp generator:/app/output ./experiment_results
```
Ejemplo de resultado de experimento

```json
{
    "experiment_name": "experiment_3_allkeys-lru_3mb_reliability",
    "redis_count": 360,
    "db_count": 640
}
```

## 📌 Notas adicionales

- Las alertas se almacenan en MongoDB con verificación de duplicados vía UUID.
- El scraper divide geográficamente Santiago para captar alertas de distintos sectores de la región metropolitana de santiago.

## 👨‍💻 Autor

- [METRO3H](https://github.com/METRO3H)
