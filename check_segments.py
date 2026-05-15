import sys, json
sys.path.insert(0, '.')

with open('data/segments/segments.json') as f:
    segs = json.load(f)

print(f'Total segments: {len(segs)}')
print()
for i, s in enumerate(segs):
    dur = s['end'] - s['start']
    print(f"  [{i+1:2d}] {s['start']:6.1f}s -> {s['end']:6.1f}s  dur={dur:5.1f}s  {s['text'][:50]}...")