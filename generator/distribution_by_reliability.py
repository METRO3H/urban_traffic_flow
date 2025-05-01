
import logging
import time
from mongodb_client import db_collection
import random


# Configurar el logging para que los mensajes se registren correctamente
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()


reliability = [5, 6, 7, 8, 9, 10]

documents_by_reliability = {}

last_loaded = 0
cache_seconds = 60  # tiempo de actualización en segundos

def refresh_documents():
    global documents_by_reliability, last_loaded
    # Retrieve UUIDs by reliability level
    now = time.time()
    if now - last_loaded < cache_seconds:
        return

    for level in reliability:
        documents_by_reliability[level] = list(
            db_collection.find({"reliability": level}, {"uuid": 1, "_id": 0})
        )
        
    last_loaded = now
    logger.info("Documents by reliability refreshed")
        
        
def generate_by_reliability():
    
    refresh_documents()
    
    # Select a reliability level based on the defined weights
    reliability_selected = random.choices(reliability, weights=reliability, k=1)[0]
    
    documents_selected = documents_by_reliability.get(reliability_selected, [])
    
    if not documents_selected:
        return None
    
    uuid_selected = random.choice(documents_selected)["uuid"]
        
    return {"reliability": reliability_selected, "uuid": uuid_selected}
