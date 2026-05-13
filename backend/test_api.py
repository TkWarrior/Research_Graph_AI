import requests
data = requests.get('http://localhost:8000/api/graph/?limit=100').json()
print(f"Nodes: {len(data.get('nodes', []))} | Edges: {len(data.get('edges', []))}")
