# Urban Traffic Flow

**Urban Traffic Flow** es un proyecto para la recolección y consulta de alertas de tráfico en la ciudad de Santiago, Chile. Incluye un scraper que segmenta la zona metropolitana y consulta la API de Waze para obtener alertas, las almacena en MongoDB, y expone un servicio FastAPI con Redis como caché. También permite realizar experimentos para comparar diferentes configuraciones de Redis y métodos de selección de alertas.

## Características principales

- 📡 **Scraping de alertas de tráfico** desde la API de Waze, segmentando Santiago en subregiones.
- 🗃 **Almacenamiento en MongoDB**, evitando duplicados.
- 🚀 **Servicio web con FastAPI** para consultar alertas por UUID.
- ⚡ **Uso de Redis como caché**, para mejorar tiempos de respuesta.
- 🧪 **Generador de trafico** para comparar configuraciones de Redis (LRU vs LFU, etc).
- 🐳 **Contenedores Docker y orquestación con Docker Compose**.


## 🚦 ¿Qué hace este proyecto?

- Divide Santiago en subregiones para realizar múltiples consultas paralelas a la API de Waze.
- Recolecta alertas de tráfico como accidentes, congestión, cierres, etc.
- Guarda las alertas en una base de datos MongoDB, evitando duplicados.
- Expone una API REST (FastAPI) para consultar alertas por `uuid`.
- Implementa Redis como caché para acelerar las consultas repetidas.
- Permite generar trafico para evaluar cómo varía el rendimiento con distintas configuraciones de Redis y distribuciones.

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
│   └── app.py                  # API FastAPI que responde a consultas por UUID, con Redis como caché y Mongodb com database
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


## Instalación

### Requisitos

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

### Pasos

1. Clona el repositorio:

   ```bash
   git clone https://github.com/METRO3H/urban_traffic_flow.git
   cd urban_traffic_flow
