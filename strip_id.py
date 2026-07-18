import json
import glob

for file in glob.glob("n8n_workflows/email_notifications/*.json"):
    with open(file, 'r') as f:
        data = json.load(f)
    
    if "id" in data:
        del data["id"]
        
    with open(file, 'w') as f:
        json.dump(data, f, indent=2)

print("Stripped IDs")
