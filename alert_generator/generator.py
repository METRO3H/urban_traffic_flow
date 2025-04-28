import random
import threading
import time
from pymongo import MongoClient
import requests
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
collection = db[MONGO_COLLECTION]


SERVER_HOST = os.getenv('SERVER_HOST', 'localhost')
SERVER_ENDPOINT = f"http://{SERVER_HOST}:8000"
alert_uuids = collection.distinct("uuid")


def send_request(uuid):
    """Envía una petición GET al servicio, con un uuid dado."""
    try:
        resp = requests.get(f"{SERVER_ENDPOINT}/alert/{uuid}", timeout=5)
        print(f"[{time.strftime('%X')}] UUID={uuid} → {resp.status_code}")
    except Exception as e:
        print(f"[{time.strftime('%X')}] Error enviando {uuid}: {e}")

def traffic_generator(name, uuids, rate, distribution):

    print(f"Arrancando generador '{name}' [{distribution}] con λ={rate} req/s")
    while True:
        # Escogemos un uuid al azar
        uuid = random.choice(uuids)

        # Enviamos la petición
        send_request(uuid)

        # Calculamos el siguiente intervalo de espera
        if distribution == 'poisson':
            # Inter-arribos exponenciales: media = 1/rate
            wait = random.expovariate(rate)
        elif distribution == 'uniform':
            # Uniforme entre 0 y 2*(1/rate) para misma media
            wait = random.uniform(0, 2.0/rate)
        else:
            # Distribución constante
            wait = 1.0/rate

        time.sleep(wait)

if __name__ == "__main__":
    try:
        # Parámetros de ejemplo
        RATE_POISSON = float(2.5)
        RATE_UNIFORM = float(2.5)

        # Creamos y lanzamos dos hilos:
        t1 = threading.Thread(
            target=traffic_generator,
            args=('thread-poisson', alert_uuids, RATE_POISSON, 'poisson'),
            daemon=True
        )
        t2 = threading.Thread(
            target=traffic_generator,
            args=('thread-uniform', alert_uuids, RATE_UNIFORM, 'uniform'),
            daemon=True
        )

        t1.start()
        t2.start()

        # Mantenemos el main vivo hasta Ctrl+C
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("Deteniendo generadores de tráfico...")
        client.close()
        print("Conexión a MongoDB cerrada.")
        exit(0)
 
        
        