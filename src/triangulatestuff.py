#!/usr/bin/env python3
import json
import math
import sys

import matplotlib.cm as cm
import numpy as np
from matplotlib import pyplot as plt
from scipy.interpolate import griddata

# from scipy.spatial.distance import cdist


graph = json.load(open('graph.dev.json'))

stations = {}

for scan in graph['wifidata']:
    pos = (scan['level'], scan['x'], scan['y'])
    for station in scan['stations']:
        sid = (station['bssid'], station['ssid'])
        if sid not in stations:
            stations[sid] = []
        if not stations[sid] or stations[sid][-1][-1] != station['level']:
            stations[sid].append((pos) + (station['level'],))

stations = sorted([s for s in stations.items() if len(s[1]) >= 3], key=lambda s: -len(s[1]))

for sid, values in stations:
    values = np.array(values)

    if sid[1] not in ('codingcatgirl', 'Freifunk', 'Telekom'):
        pass  # continue

    grid_x, grid_y = np.mgrid[0:graph['width'], 0:graph['height']]

    frequency = 2400

    print(sid, len(values))
    print(values[:, 3].min(), values[:, 3].max())
    # grid = griddata(values[:, 1:3], values[:, 3], (grid_x, grid_y), method='cubic')
    # grid = 10000-griddata(values[:, 1:3], 10**(values[:, 3]/10), (grid_x, grid_y), method='cubic')
    # grid = 100000-griddata(values[:, 1:3], 1/(10**(values[:, 3]/10))**0.5, (grid_x, grid_y), method='cubic')
    grid = griddata(values[:, 1:3], 10**((27.55-(20*math.log10(frequency))+values[:, 3])/20), (grid_x, grid_y),
                    method='cubic')

    print(grid.min(), grid.max())

    print(grid[0][0]+10)

    plt.imshow(grid.transpose(), cmap=cm.jet, origin='upper')
    plt.show()

    # xnew = range(0, graph['width'], 2)
    # ynew = range(0, graph['height'], 2)
    # znew = f(xnew, ynew)
    # plt.plot(xnew, znew[0, :], 'b-')
    # plt.show()

    continue

    frequency = 2400
    coordinates = values[:, 1:3]
    print(coordinates)
    distances = 10**((27.55 - (20 * math.log10(frequency)) + values[:, 3]*-1)/20)
    print(distances)

    # bla = curve_fit(myfunc, coordinates, distances)
    # print(bla)
    # print(tuple(round(float(i), 2) for i in bla[0]))

    print('')

    # for val in values:
    #     print(val)
    # print('')

sys.exit(0)

coordinates = np.array([
    [-1.91373, -0.799904],
    [-0.935453, -0.493735],
    [-0.630964, -0.653075],
    [0.310857, 0.018258],
    [0.0431084, 1.24321]
])
distances = np.array([
    2.04001,
    0.959304,
    0.728477,
    0.301885,
    1.19012
])

coordinates = np.array([[0, 0], [3, 0]])
distances = np.array([1, 1])

coordinates = np.array([[2, 2, 3], [1, 1, 3], [1, 2, 6]])

distances = np.array([1, 1, 3])

# bla = curve_fit(myfunc, coordinates, distances)[0]
# print(tuple(round(i, 2) for i in bla))
