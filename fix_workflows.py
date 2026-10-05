import json
import glob
import uuid

for file in glob.glob("n8n_workflows/email_notifications/*.json"):
    with open(file, 'r') as f:
        data = json.load(f)
    
    if "id" not in data:
        # Provide a random ID for n8n
        data["id"] = str(uuid.uuid4())
        
    with open(file, 'w') as f:
        json.dump(data, f, indent=2)

print("Fixed workflow IDs")
