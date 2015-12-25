#!/usr/bin/env python3
import json
import os
import sys
import time

import matplotlib.cm as cm
import numpy as np
from matplotlib import pyplot as plt
from scipy.misc import imread

from classes import Graph

if 'C3NAVPROJECT' in os.environ:
    project = os.environ['C3NAVPROJECT']
elif len(sys.argv) > 1:
    project = sys.argv[1]
else:
    print('Please specify project: run.py <project> or environment variable C3NAVPROJECT')
    sys.exit(1)

starttime = time.time()

graph = Graph(project, auto_connect=False, load_wifi=True)

for sid in graph.wifi.sids:
    while True:
        print('')
        print(sid)
        f, axes = plt.subplots(graph.levels)

        vmin = graph.wifi.w_to_dbm(np.min(graph.wifi.matrix[:, :, :, graph.wifi.sid_ids[sid]]))
        vmax = graph.wifi.w_to_dbm(np.max(graph.wifi.matrix[:, :, :, graph.wifi.sid_ids[sid]]))
        for i, ax in enumerate(axes):
            ax.imshow(imread('static/img/levels/dev/level%d.jpg' % i)[::graph.wifi.divide_by, ::graph.wifi.divide_by])
            ax.imshow(graph.wifi.w_to_dbm(graph.wifi.matrix[i, :, :, graph.wifi.sid_ids[sid]]).transpose(),
                      alpha=0.5, cmap=cm.jet, origin='upper', vmin=vmin, vmax=vmax)

        plt.savefig('foo.svg')

        data = json.load(open('projects/'+project+'/wifiscans.json'))
        if (sid[0] in data['wifipositions']):
            now = data['wifipositions'][sid[0]]
            if now is None:
                print('current value: ignore')
            else:
                print('current value: '+':'.join(str(n) for n in now))
        else:
            print('currently no value')

        be = input('>>> ').strip()
        if be == 'ignore':
            data['wifipositions'][sid[0]] = None
            json.dump(data, open('projects/'+project+'/wifiscans.json', 'w'), indent=4, sort_keys=True)
            print('ignore set!')
            break
        elif be:
            try:
                be = [int(i) for i in be.split(':')]
            except:
                print('nope!')
                continue
            if len(be) != 3:
                print('nope!')
                continue
            data['wifipositions'][sid[0]] = be
            json.dump(data, open('projects/'+project+'/wifiscans.json', 'w'), indent=4, sort_keys=True)
            graph = Graph(project, auto_connect=False, load_wifi=True)
            print('set!')
            continue
        else:
            break

    # plt.plot(*np_positions.transpose()//graph.wifi.divide_by, marker=',w')
    # plt.show()
