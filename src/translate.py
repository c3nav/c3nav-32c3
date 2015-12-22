#!/usr/bin/env python3
import json
import os
import sys

from classes import Graph

if 'C3NAVPROJECT' in os.environ:
    project = os.environ['C3NAVPROJECT']
elif len(sys.argv) > 1:
    project = sys.argv[1]
else:
    print('Please specify project: run.py <project> or environment variable C3NAVPROJECT')
    sys.exit(1)

if len(sys.argv) != 3:
    print('select language!')
    sys.exit(1)
lang = sys.argv[2]
print('translating into %s…' % lang)

data = Graph(project, auto_connect=False).data
rooms = list(data['rooms'].keys())
pois = list(data['pois'].keys())
superrooms = [room['superroom'] for room in data['rooms'].values() if 'superroom' in room]
roomgroups = list(sum((room.get('groups', []) for room in data['rooms'].values()), []))

for name in set(pois+roomgroups+rooms+superrooms):
    data = json.load(open('config/'+project+'/titles.json'))
    titles = data.get(name, {})

    if lang in titles:
        continue
    for l, t in titles.items():
        print('%s: %s' % (l, t))
    newtitle = input('%s [%s]: ' % (name, titles.get(lang, name))).strip()
    if not newtitle.strip():
        newtitle = titles.get(lang, name)
    titles[lang] = newtitle

    data[name] = titles
    json.dump(data, open('config/'+project+'/titles.json', 'w'), indent=4, sort_keys=True)
    print('')

print('all done.')
