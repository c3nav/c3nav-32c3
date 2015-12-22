#!/usr/bin/env python3
import json
import math
import sys

import matplotlib.cm as cm
import numpy as np
from matplotlib import pyplot as plt
from scipy.interpolate import LinearNDInterpolator
from scipy.misc import imread
from scipy.spatial.distance import cdist

graph = json.load(open('graph.dev.json'))

# group multiple scans at the same position
scans_by_position = {}
for scan in graph['wifidata']:
    pos = (scan['level'], scan['x'], scan['y'])
    if pos not in scans_by_position:
        scans_by_position[pos] = {}
    for station in scan['stations']:
        sid = (station['bssid'], station['ssid'])
        if sid not in scans_by_position[pos]:
            scans_by_position[pos][sid] = []
        scans_by_position[pos][sid].append(station['level'])

for pos, stations in scans_by_position.items():
    count = max(len(s) for s in stations.values())
    for sid in tuple(stations.keys()):
        # if len(stations[sid]) < count:
        #    del stations[sid]
        # else:
        stations[sid] = (sum(stations[sid])+(-100*(count-len(stations[sid]))))/count


# group scans by station
station_positions = {}
for pos, statlist in scans_by_position.items():
    for sid, level in statlist.items():
        if sid not in station_positions:
            station_positions[sid] = {}
        station_positions[sid][pos] = level

# group stations
for sid, values in stations.items():
    break
    print(sid)
    for val in values:
        print(val)
    print('')


# print(scans_by_position)

#        if sid not in stations:
#            stations[sid] = []
#        if not stations[sid] or stations[sid][-1][-1] != station['level']:
#            stations[sid].append((pos) + (station['level'],))


def dbm_to_linear(value, frequency=2400):
    return 10**((27.55-(20*math.log10(frequency))+value)/20)

stations = [sid for sid, values in station_positions.items() if len(values) >= 3]
print('%d stations in total' % len(stations))

positions = tuple(scans_by_position.keys())
np_positions = np.array(positions)
np_positions = np_positions[:, 1:]
for sid in stations:
    if sid[1] not in ('codingcatgirl', 'Freifunk', 'Telekom'):
        continue

    measured_values = station_positions[sid]
    station_values = np.array(tuple(measured_values.get(pos, -100) for pos in positions))
    weakest_value = min(measured_values.values())

    center = np_positions[np.argmax(station_values)]
    print(sid, center)

    if sid[1] == 'Freifunk':
        center = np.array((581, 403))
    frequency = 2400

    # Turn measured positions inter polar coordinates
    polar = np.dstack((np.arctan2(*(np_positions-center).transpose())/np.pi/2*360,
                       cdist([center], np_positions)[0]))[0]

    # Interpolate
    polar = np.concatenate((polar-np.array((360, 0)), polar, polar+np.array((360, 0))))
    station_values = np.concatenate((station_values, station_values, station_values))
    # f = CloughTocher2DInterpolator(polar, dbm_to_linear(station_values, frequency))
    f = LinearNDInterpolator(polar, dbm_to_linear(station_values, frequency))

    # Turn back into cartesian system
    cartesian_coordinates = np.vstack(np.dstack(np.mgrid[0:graph['width']:2, 0:graph['height']:2]))
    polar = np.array((np.arctan2(*(cartesian_coordinates-center).transpose())/np.pi/2*360,
                      cdist([center], cartesian_coordinates)[0]))
    cartesian = f(*polar).reshape((graph['width']//2, graph['height']//2))
    cartesian[cartesian <= dbm_to_linear(-90)] = np.nan
    # print(cartesian)
    # print('convert to %d cartesian coordinates' % len(cartesian_coordinates))

    plt.imshow(imread('static/img/levels/dev/level0.jpg')[::2, ::2])
    plt.imshow(cartesian.transpose(), alpha=.5, cmap=cm.jet, origin='upper')
    plt.show()


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
