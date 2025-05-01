from mongodb_client import db_collection
import random


# Probabilities by type
probabilities = {
    "ACCIDENT": 0.25,
    "ROAD_CLOSED": 0.20,
    "HAZARD": 0.20,
    "POLICE": 0.15,
    "JAM": 0.15,
    "CHIT_CHAT": 0.05
}

documents_by_type = {}

for type in probabilities:
    documents_by_type[type] = list(
        db_collection.find({"type": type}, {"uuid": 1, "_id": 0})
    )
    
types = list(probabilities.keys())
type_probability_values = list(probabilities.values())

# Generates a random document based on the defined priority probabilities.
# Returns a dictionary with the type and uuid of the selected document.
def generate_by_importance():
    type_selected = random.choices(types, weights=type_probability_values, k=1)[0]
    
    documents_selected = documents_by_type.get(type_selected, [])
    
    if not documents_selected:
        return None
    
    uuid_selected = random.choice(documents_selected)["uuid"]
    
    return {"type": type_selected, "uuid": uuid_selected}
    