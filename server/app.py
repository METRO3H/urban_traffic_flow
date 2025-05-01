from fastapi import FastAPI
from pymongo import MongoClient
from bson.json_util import dumps, loads
from fastapi.responses import Response, JSONResponse
from fastapi.exceptions import HTTPException
import redis
import os
import logging

# Configurar el logging para que los mensajes se registren correctamente
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Leer variables de entorno
MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_PORT = os.getenv('MONGO_PORT', '27017')
MONGO_DB = os.getenv('MONGO_DB', 'default_db')
MONGO_USER = os.getenv('MONGO_USER', 'admin')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', 'password')
MONGO_COLLECTION = os.getenv('MONGO_COLLECTION', 'alerts')

REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', 'password')

# Crear la URI de conexión para MongoDB con autenticación
mongo_uri = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource=admin"

# Conectar al cliente de MongoDB
client = MongoClient(mongo_uri)

# Acceder a la base de datos y colección
db = client[MONGO_DB]
collection = db[MONGO_COLLECTION]

redis_connection = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)

app = FastAPI()

redis_count = 0
db_count = 0

@app.get("/health")
def read_root():
    return {"status": "ok"}

@app.get("/alert/{uuid}")
async def get_alert(uuid: str):
    global redis_count, db_count
    try:
        redis_response = redis_connection.get(uuid)
        if redis_response:
            alert = loads(redis_response)
            json_response = dumps({"source": "redis", "data": alert})
            logger.info(f"      ↳ Alert {uuid} found in Redis cache")
            redis_count += 1
            return Response(content=json_response, media_type="application/json")
        
        alert = collection.find_one({"uuid": uuid})
        
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        json_response = dumps({"source": "mongodb", "data": alert})
        redis_connection.set(uuid, json_response, ex=3600)
        db_count += 1
            
        logger.info(f"      ↳ Alert {uuid} retrieved from MongoDB and cached in Redis")
        return Response(content=json_response, media_type="application/json")
    
    except Exception as e:
        logger.error(f"Unexpected error", exc_info=True)
        return JSONResponse(status_code=500, content={"message": "Internal server error"})


