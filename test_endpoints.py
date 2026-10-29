import requests

base = 'http://localhost:8000/api'
p_id = 3

projs = requests.get(f'{base}/projects').json()
print(f'1. Projects: {len(projs)}')

vers = requests.get(f'{base}/projects/{p_id}/versions').json()
print(f'2. Versions: {[v["version_tag"] for v in vers]}')

metrics = requests.get(f'{base}/projects/{p_id}/metrics').json()
print(f'3. Class Metrics: {len(metrics["class_metrics"])} classes')

dna = requests.get(f'{base}/projects/{p_id}/dna').json()
print(f'4. DNA: {len(dna)} snapshots')

muts = requests.get(f'{base}/projects/{p_id}/mutations').json()
print(f'5. Mutations: {len(muts)} detected')

esdi = requests.get(f'{base}/projects/{p_id}/esdi').json()
print(f'6. ESDI: Score={esdi["latest"]["esdi_score"]}, Health={esdi["latest"]["health_score"]}')

risks = requests.get(f'{base}/projects/{p_id}/risks').json()
print(f'7. Module Risks: {len(risks)} evaluated')

recs = requests.get(f'{base}/projects/{p_id}/recommendations').json()
print(f'8. Recommendations: {len(recs)} generated')

pred = requests.get(f'{base}/projects/{p_id}/prediction').json()
print(f'9. Prediction: {pred["trend_direction"]}, Next={pred["predicted_health"]}')

dash = requests.get(f'{base}/projects/{p_id}/dashboard').json()
print(f'10. Dashboard: OK - Project: {dash["top_cards"]["project_name"]}')
