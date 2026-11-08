"""Build render_targets.json from sites.json: size m+ pages that failed or showed no hiring system and no student mention.
Usage: python prepare_render.py <workdir>"""
import json, sys
W = sys.argv[1]
R = json.load(open(W + '/sites.json'))
T = [r for r in R if r['size'] in ('m', 'l', 'xl') and (r.get('error') or (not r.get('ats') and not r.get('hits')))]
json.dump(T, open(W + '/render_targets.json', 'w'))
print(len(T), 'pages to render')
