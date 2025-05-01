from distribution_by_importance import generate_by_importance
from distribution_by_reliability import generate_by_reliability
import time
import requests
import os
import logging
import redis
import json

# Configurar el logging para que los mensajes se registren correctamente
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', 'password')

SERVER_HOST = os.getenv('SERVER_HOST', 'localhost')
SERVER_PORT = 8000
SERVER_ENDPOINT = f"http://{SERVER_HOST}:{SERVER_PORT}"

try:
    redis_connection = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
except Exception as e:
    logger.error(f"Error connecting to Redis: {e}")
    raise

NUM_REQUESTS = 1000
REQUEST_DELAY = 0.2  
def send_request(uuid):
    try:
        request_url = SERVER_ENDPOINT + '/alert/' + uuid
        resp = requests.get(request_url, timeout=5)
        if resp.status_code == 200:
            response_data = resp.json()
            response_source = response_data.get("source", "unknown")
            
            return response_source
        else:
            logger.error(f"[{time.strftime('%X')}] Error: {resp.status_code} - {resp.text}")
            return None
            
    except Exception as e:
        logger.error(f"[{time.strftime('%X')}] Error enviando {uuid}: {e}")
        return None

def export_results(experiment_name, redis_count, db_count):
    results = {
        "experiment_name": experiment_name,
        "redis_count": redis_count,
        "db_count": db_count,
    }
    
    with open(f"./output/{experiment_name}.json", "w") as f:
        json.dump(results, f, indent=4)
    return


def importance_loop(experiment_name):
    global NUM_REQUESTS
    
    redis_count = 0
    db_count = 0
    for i in range(NUM_REQUESTS):
        logger.info(f'[{str(i+1).zfill(len(NUM_REQUESTS))}/{NUM_REQUESTS}] {experiment_name}...')
        alert = generate_by_importance()
        if alert:
            uuid = alert["uuid"]
            logger.info(f"     ↳ [Request] {uuid}")
            response_source = send_request(uuid)
            if response_source is None:
                logger.error(f"     ↳ [Response] No response for UUID={uuid}")
                continue
            if response_source == "redis":
                redis_count += 1
            else:
                db_count += 1
            logger.info(f"     ↳ [Response] {response_source}")
        else:
            logger.info(f"     ↳ [Response] No se encontró un UUID para el tipo de alerta seleccionado.")
        
        time.sleep(REQUEST_DELAY)
    
    export_results(experiment_name, redis_count, db_count)

def reliability_loop(experiment_name):
    global NUM_REQUESTS
    
    redis_count = 0
    db_count = 0
    
    for i in range(NUM_REQUESTS):
        logger.info(f'[{str(i+1).zfill(len(str(NUM_REQUESTS)))}/{NUM_REQUESTS}] {experiment_name}...')
        alert = generate_by_reliability()
        if alert:
            uuid = alert["uuid"]
            logger.info(f"     ↳ [Request] {uuid}")
            response_source = send_request(uuid)
            if response_source is None:
                logger.error(f"     ↳ [Response] No response for UUID={uuid}")
                continue
            if response_source == "redis":
                redis_count += 1
            else:
                db_count += 1
            
            logger.info(f"     ↳ [Response] {response_source}")
        else:
            logger.info(f"     ↳ [Response] No se encontró un UUID para el tipo de alerta seleccionado.")
        
        time.sleep(REQUEST_DELAY)  # Entre 1 y 10 requests por segundo
    
    export_results(experiment_name, redis_count, db_count)
    
    return

def run_experiment():
    def verify_redis_config(expected_maxmemory, expected_policy):
        try:
            current_maxmemory = redis_connection.config_get('maxmemory').get('maxmemory')
            current_policy = redis_connection.config_get('maxmemory-policy').get('maxmemory-policy')
            
            if int(current_maxmemory) != expected_maxmemory:
                logger.error(f"Redis maxmemory mismatch: Expected {expected_maxmemory}, got {current_maxmemory}")
                return False
            if current_policy != expected_policy:
                logger.error(f"Redis maxmemory-policy mismatch: Expected {expected_policy}, got {current_policy}")
                return False
            
            logger.info(f"Redis configuration verified: maxmemory={current_maxmemory}, policy={current_policy}")
            return True
        except Exception as e:
            logger.error(f"Error verifying Redis configuration: {e}")
            return False

    
    
    """
    Experimento 1: Configuración de Redis con maxmemory 2mb, política allkeys-lru y distribución por fiabilidad
    Experimento 2: Configuración de Redis con maxmemory 2mb, política allkeys-lru y distribución por importancia
    Experimento 3: Configuración de Redis con maxmemory 3mb, política allkeys-lru y distribución por fiabilidad
    Experimento 4: Configuración de Redis con maxmemory 3mb, política allkeys-lru y distribución por importancia
    Experimento 5: Configuración de Redis con maxmemory 2mb, política allkeys-lfu y distribución por fiabilidad
    Experimento 6: Configuración de Redis con maxmemory 2mb, política allkeys-lfu y distribución por importancia
    Experimento 7: Configuración de Redis con maxmemory 3mb, política allkeys-lfu y distribución por fiabilidad
    Experimento 8: Configuración de Redis con maxmemory 3mb, política allkeys-lfu y distribución por importancia
    """
    
    #----------Redis configuration allkeys-lru and maxmemory 2mb -------------------------------
    redis_connection.flushall()
    

    
    time.sleep(11)  # Esperar 11 segundos antes de iniciar el experimento
    
    while not verify_redis_config(2 * 1024 * 1024, 'allkeys-lru'):
        logger.info("Setting Redis configuration: maxmemory 2mb and allkeys-lru policy")
        redis_connection.config_set('maxmemory', 2 * 1024 * 1024)  # 2 MB
        redis_connection.config_set('maxmemory-policy', 'allkeys-lru')
        time.sleep(1)
        
    logger.info("Starting experiment 1 - reliability with allkeys-lru and maxmemory 2mb")
    time.sleep(5)  
    reliability_loop("experiment_1_allkeys-lru_2mb_reliability")
    
    logger.info("Starting experiment 2 - importance with allkeys-lru and maxmemory 2mb")
    time.sleep(5)  
    importance_loop("experiment_2_allkeys-lru_2mb_importance")
    
    redis_connection.flushall()
    
    # ----------Redis configuration allkeys-lru and maxmemory 3mb -------------------------------
    
    
    while not verify_redis_config(3 * 1024 * 1024, 'allkeys-lru'):
        logger.info("Setting Redis configuration: maxmemory 3mb and allkeys-lru policy")
        redis_connection.config_set('maxmemory', 3 * 1024 * 1024)  # 3 MB
        redis_connection.config_set('maxmemory-policy', 'allkeys-lru')
        time.sleep(1)
        
    logger.info("Starting experiment 3 - reliability with allkeys-lru and maxmemory 3mb")
    time.sleep(5)   
    reliability_loop("experiment_3_allkeys-lru_3mb_reliability")
    
    logger.info("Starting experiment 4 - importance with allkeys-lru and maxmemory 3mb")
    time.sleep(5)  
    importance_loop("experiment_4_allkeys-lru_3mb_importance")
        
    redis_connection.flushall()
    
    # Redis configuration allkeys-lfu and maxmemory 2mb

    while not verify_redis_config(2 * 1024 * 1024, 'allkeys-lfu'):
        logger.info("Setting Redis configuration: maxmemory 2mb and allkeys-lfu policy")
        redis_connection.config_set('maxmemory', 2 * 1024 * 1024)  # 2 MB
        redis_connection.config_set('maxmemory-policy', 'allkeys-lfu')
        time.sleep(1)
    
    logger.info("Starting experiment 5 - reliability with allkeys-lfu and maxmemory 2mb")
    time.sleep(5)  
    reliability_loop("experiment_5_allkeys-lfu_2mb_reliability")
    
    logger.info("Starting experiment 6 - importance with allkeys-lfu and maxmemory 2mb")
    time.sleep(5)  
    importance_loop("experiment_6_allkeys-lfu_2mb_importance")
    
    redis_connection.flushall()
    
    # Redis configuration allkeys-lfu and maxmemory 3mb
    
    while not verify_redis_config(3 * 1024 * 1024, 'allkeys-lfu'):
        logger.info("Setting Redis configuration: maxmemory 3mb and allkeys-lfu policy")
        redis_connection.config_set('maxmemory', 3 * 1024 * 1024)  # 3 MB
        redis_connection.config_set('maxmemory-policy', 'allkeys-lfu')
        time.sleep(1)

    
    logger.info("Starting experiment 7 - reliability with allkeys-lfu and maxmemory 3mb")
    time.sleep(5)  
    reliability_loop("experiment_7_allkeys-lfu_3mb_reliability")
    
    logger.info("Starting experiment 8 - importance with allkeys-lfu and maxmemory 3mb")
    time.sleep(5)  
    importance_loop("experiment_8_allkeys-lfu_3mb_importance")
    
    redis_connection.flushall()



if __name__ == "__main__":
   
    run_experiment()
    logger.info("\nExperiments completed.")
    redis_connection.close()
