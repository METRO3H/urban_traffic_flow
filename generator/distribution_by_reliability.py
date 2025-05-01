
from mongodb_client import db_collection
import random


reliability = [5, 6, 7, 8, 9, 10]

# Retrieve UUIDs by reliability level
documents_by_reliability = {}
for level in reliability:
    documents_by_reliability[level] = list(
        db_collection.find({"reliability": level}, {"uuid": 1, "_id": 0})
    )
    

def generate_by_reliability():
    # Select a reliability level based on the defined weights
    reliability_selected = random.choices(reliability, weights=reliability, k=1)[0]
    
    documents_selected = documents_by_reliability.get(reliability_selected, [])
    
    if not documents_selected:
        return None
    
    uuid_selected = random.choice(documents_selected)["uuid"]
        
    return {"reliability": reliability_selected, "uuid": uuid_selected}
