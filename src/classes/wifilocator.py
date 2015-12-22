import math

import numpy as np
from scipy.interpolate import LinearNDInterpolator
from scipy.spatial.distance import cdist


class WifiLocator():
    connection_types = ('default', 'steps-up', 'steps-down', 'stairs-up', 'stairs-down',
                        'escalator-up', 'escalator-down', 'elevator-up', 'elevator-down')
    diag = 2**0.5

    divide_by = 4

    def __init__(self, graph, data):
        self.graph = graph
        import time
        starttime = time.time()

        # group multiple scans at the same position
        scans_by_position = {}
        for scan in data:
            pos = (scan['level'], scan['x'], scan['y'])
            if pos not in scans_by_position:
                scans_by_position[pos] = {}
            for station in scan['stations']:
                sid = (station['bssid'], station['ssid'])
                if sid not in scans_by_position[pos]:
                    scans_by_position[pos][sid] = []
                scans_by_position[pos][sid].append(station['level'])

        # average of each station that was always available at this position
        self.sids_count = {}
        for pos, stations in scans_by_position.items():
            count = max(len(s) for s in stations.values())
            for sid in tuple(stations.keys()):
                if sid not in self.sids_count:
                    self.sids_count[sid] = 0
                self.sids_count[sid] += 1
                stations[sid] = (sum(stations[sid])+(-100*(count-len(stations[sid]))))/count

        # sids to id
        self.sids = [sid for sid, values in self.sids_count.items() if values >= 3]
        self.sid_ids = {sid: i for i, sid in enumerate(self.sids)}

        self.matrix = np.empty((len(self.graph.levels), self.graph.width//2, self.graph.height//2, len(self.sids)))
        self.matrix[:, :, :, :] = -100

        # group scans by sid
        levelmatrixes = []
        for level in range(len(self.graph.levels)):
            sidmatrixes = []
            positions = tuple(i[1:] for i in scans_by_position.keys() if i[0] == level)
            np_positions = np.array(positions)
            for sid in self.sids:
                print(sid)
                values = np.array(tuple(scans_by_position[(level,)+pos].get(sid, -100) for pos in positions))
                print(values)
                center = np_positions[np.argmax(values)]

                polar = np.dstack((np.arctan2(*(np_positions-center).transpose())/np.pi/2*360,
                                   cdist([center], np_positions)[0]))[0]

                polar = np.concatenate((polar-np.array((360, 0)), polar, polar+np.array((360, 0))))
                values = np.concatenate((values, values, values))
                f = LinearNDInterpolator(polar, self.dbm_to_linear(values, 2400),
                                         fill_value=self.dbm_to_linear(-100, 2400))

                cartesian = np.vstack(np.dstack(np.mgrid[0:self.graph.width:self.divide_by,
                                                         0:self.graph.height:self.divide_by]))
                polar = np.array((np.arctan2(*(cartesian-center).transpose())/np.pi/2*360,
                                  cdist([center], cartesian)[0]))
                sidmatrixes.append(f(*polar).reshape((self.graph.width//self.divide_by,
                                                      self.graph.height//self.divide_by)))

            levelmatrixes.append(np.dstack(sidmatrixes))
            print(levelmatrixes)

        if len(levelmatrixes) > 1:
            self.matrix = np.dstack(levelmatrixes)
        else:
            self.matrix = levelmatrixes[0].reshape((1, )+levelmatrixes[0].shape)
        print(time.time()-starttime)

    def dbm_to_linear(self, value, frequency=2400):
        return value
        return 10**((27.55-(20*math.log10(frequency))+value)/20)

    def locate(self, scan):
        scan = {(s['bssid'], s['ssid']): s['level'] for s in scan}
        np_scan = np.ones((len(self.sid_ids), ))*-100
        known_spots = 0
        for sid, level in scan.items():
            if sid in self.sid_ids:
                known_spots += 1
                np_scan[self.sid_ids[sid]] = level
        print(self.dbm_to_linear(np_scan))

        # best_station = np.argmax(scan)
        # best_sid = self.sids[best_station]

        matches = ((self.matrix-self.dbm_to_linear(np_scan))**2).sum(axis=3)
        print(matches)
        best_match = np.unravel_index(np.argmin(matches), matches.shape)
        return [int(i*self.divide_by) for i in best_match], '%.12f' % np.min(matches), known_spots

    def locate_old(self, scan):
        scan = {(s['bssid'], s['ssid']): s['level'] for s in scan}
        scan = {sid: level for sid, level in scan.items() if sid in self.sids}

        print('')
        print(scan)

        best_station, best_signal = max(scan.items(), key=lambda s: s[1])
        print(best_station, best_signal)

        possible_positions = self.stations[best_station].keys()
        rated_positions = []
        for pos in possible_positions:
            posscan = self.scans_by_position[pos]
            squaresum = [(posscan[sid]-scan[sid])**2 for sid in (set(posscan) & set(scan))]
            print((pos, len(squaresum), sum(squaresum)/len(squaresum)))
            rated_positions.append((pos, len(squaresum), sum(squaresum)/len(squaresum)))
        best_position = min(rated_positions, key=lambda p: p[2])
        print('best:', best_position)
        return best_position
