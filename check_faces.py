import sys, json
sys.path.insert(0, '.')

with open('data/temp/scores.json') as f:
    scores = json.load(f)

print('Top segments face positions:')
for s in scores[:8]:
    print(f"  [{s['start']}s - {s['end']}s]  face_x={s.get('face_center_x', 'MISSING')}  face={s.get('face', 'MISSING')}  score={s['score']}")