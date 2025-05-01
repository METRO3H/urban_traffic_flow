from pymongo import MongoClient
import os

# Leer variables de entorno
MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.getenv('MONGO_PORT', '27017'))
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

db_collection = db[MONGO_COLLECTION]

def close_mongo_client():
    """
    Cierra la conexión con el cliente de MongoDB.
    """
    if client:
        
        client.close()
        print("Conexión con MongoDB cerrada.")