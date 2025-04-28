from pymongo import MongoClient
import json
import os
import logging
import requests
import time
import sys

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

# Crear la URI de conexión para MongoDB con autenticación
mongo_uri = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource=admin"

# Conectar al cliente de MongoDB
client = MongoClient(mongo_uri)

# Acceder a la base de datos y colección
db = client[MONGO_DB]
collection = db[MONGO_COLLECTION]
# check if collection has more than 10000 documents

if collection.count_documents({}) > 10000:
    logger.info("Collection has more than 10000 documents")
    sys.exit(0)


# Definir la región general de Santiago
TOP = -32.9
BOTTOM = -34.3
LEFT = -69.7
RIGHT = -71.8

# Número de divisiones
DIVISIONS = 5

# Calcular tamaño de cada subárea
lat_step = (TOP - BOTTOM) / DIVISIONS
lon_step = (RIGHT - LEFT) / DIVISIONS

NUM_OF_ALERTS_TO_CAPTURE = 10056

captured_uuids = set()  # 🔥 Conjunto para guardar uuids únicos

def Get_Alerts():
    iteration = 1
    total_inserted = 0

    while True:
        logger.info(f"Iteration: {iteration}")
        for i in range(DIVISIONS):
            for j in range(DIVISIONS):
                sub_top = TOP - i * lat_step
                sub_bottom = sub_top - lat_step
                sub_left = LEFT + j * lon_step
                sub_right = sub_left + lon_step

                url = f"https://www.waze.com/live-map/api/georss?top={sub_top}&bottom={sub_bottom}&left={sub_left}&right={sub_right}&env=row&types=alerts"

                logger.info(f"  ↳ Consultando zona {i+1}-{j+1}| Top: {sub_top:.4f} | Bottom: {sub_bottom:.4f} | Left: {sub_left:.4f} | Right: {sub_right:.4f}| Insertados: {total_inserted}")

                try:
                    response = requests.get(url)
                    if response.status_code == 200:
                        try:
                            data = response.json()
                        except json.JSONDecodeError:
                            logger.warning(f"Respuesta no es JSON válido para zona {i}-{j}")
                            continue
                    
                        if 'alerts' in data:
                            for alert in data['alerts']:
                                
                                uuid = alert['uuid']
                                if uuid not in captured_uuids:
                                    captured_uuids.add(uuid)
                                    
                                    if 'comments' in alert:
                                        del alert['comments']
                                        
                                    collection.insert_one(alert)
                                    total_inserted += 1
                    else:
                        logger.warning(f"Error en la consulta: {response.status_code}")     
                                   
                    if total_inserted >= NUM_OF_ALERTS_TO_CAPTURE:
                        return len(captured_uuids)
                    
                    
                except Exception as e:
                    logger.error(f"Error: {e}")

                # Pequeño delay
                time.sleep(1)
        
        iteration += 1


alerts_captured = Get_Alerts()

logger.info(f"Total de alertas únicas capturadas: { alerts_captured }")

sys.exit(0)

