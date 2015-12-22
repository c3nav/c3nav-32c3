import math

import matplotlib.cm as cm
import numpy as np
from matplotlib import pyplot as plt
from scipy.interpolate import LinearNDInterpolator
from scipy.misc import imread
from scipy.spatial.distance import cdist


class WifiLocator():
    diag = 2**0.5

    divide_by = 2
    no_signal = -90

    def __init__(self, graph):
        self.graph = graph
        import time
        starttime = time.time()

        data = graph.data['wifiscans']
        sid_positions = graph.data['wifipositions']

        # group multiple scans at the same position
        scans_by_position = {}
        for scan in data:
            pos = (scan['level'], scan['x'], scan['y'])
            if pos not in scans_by_position:
                scans_by_position[pos] = {}
            for station in scan['stations']:
                sid = (station['bssid'], station['ssid'])
                if sid[0] in sid_positions and sid_positions[sid[0]] is None:
                    print(sid)
                    continue
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
                stations[sid] = (sum(stations[sid])+(self.no_signal*(count-len(stations[sid]))))/count

        # sids to id
        self.sids = [sid for sid, values in self.sids_count.items() if values >= 6]
        self.sid_ids = {sid: i for i, sid in enumerate(self.sids)}
        # print('\n'.join(str(a) for a in self.sid_ids.keys()))

        self.matrix = np.empty((self.graph.levels, self.graph.width//2, self.graph.height//2, len(self.sids)))
        self.matrix.fill(self.no_signal)

        # group scans by sid
        levelmatrixes = []
        for level in range(self.graph.levels):
            sidmatrixes = []
            positions = tuple(i[1:] for i in scans_by_position.keys() if i[0] == level)
            np_positions = np.array(positions)
            cartesian = np.vstack(np.dstack(np.mgrid[0:self.graph.width:self.divide_by,
                                                     0:self.graph.height:self.divide_by]))

            distances = np.amin(
                cdist(cartesian, np_positions, 'euclidean')*self.graph.cm_per_px, 1
            ).reshape((self.graph.width//self.divide_by, self.graph.height//self.divide_by))

            if False:
                # Enable this to show distances
                plt.imshow(imread('static/img/levels/dev/level0.jpg')[::self.divide_by, ::self.divide_by])
                plt.imshow(0-(np.clip(distances, 0, 5000).transpose()/250).astype(int)*5,
                           alpha=0.3, cmap=cm.prism, origin='upper')
                plt.show()

            max_distance = 1500

            cartesian = cartesian[distances.flatten() <= max_distance]
            cartesian_div = cartesian//self.divide_by
            print(cartesian.shape)

            if False:
                # Enable this to show allowed positionss based on max_distance
                plt.imshow(imread('static/img/levels/dev/level0.jpg')[::self.divide_by, ::self.divide_by])
                plt.imshow(np.where(distances <= max_distance, 1, 0).transpose(),
                           alpha=0.3, cmap=cm.gray, origin='upper')
                plt.plot(*np_positions.transpose()//self.divide_by, marker='o')
                plt.show()

            for sid in self.sids:
                values = np.array(tuple(scans_by_position[(level,)+pos].get(sid, self.no_signal) for pos in positions))

                if sid[0] in sid_positions:
                    center = np.array(sid_positions[sid[0]])[1:]
                else:
                    center = np_positions[np.argmax(values)]

                polar = np.dstack((np.arctan2(*(np_positions-center).transpose())/np.pi/2*360,
                                   cdist([center], np_positions)[0]))[0]
                values = self.dbm_to_w_linear(values, polar[:, 1])

                polar = np.concatenate((polar-np.array((360, 0)), polar, polar+np.array((360, 0))))
                f = LinearNDInterpolator(polar, np.tile(values, 3),
                                         fill_value=np.nan)

                polar = np.array((np.arctan2(*(cartesian-center).transpose())/np.pi/2*360,
                                  cdist([center], cartesian)[0]))
                newmatrix = np.ones((self.graph.width//self.divide_by,
                                     self.graph.height//self.divide_by))*self.dbm_to_w(self.no_signal)

                # idea bei codefetch
                interpolated_values = self.w_linear_to_w(f(*polar), polar[1])
                interpolated_values[np.isnan(interpolated_values)] = self.dbm_to_w(self.no_signal)

                # 10*log(1/r²*b)
                newmatrix[cartesian_div[:, 0], cartesian_div[:, 1]] = interpolated_values
                sidmatrixes.append(newmatrix)

                if False:
                    # Enable this show interpolated ap data
                    print(sid, np.max(values))
                    plt.imshow(imread('static/img/levels/dev/level0.jpg')[::self.divide_by, ::self.divide_by])
                    plt.imshow(self.w_to_dbm(newmatrix).transpose(), alpha=0.5, cmap=cm.jet, origin='upper')
                    plt.plot(*np_positions.transpose()//self.divide_by, marker=',w')
                    plt.show()

            levelmatrixes.append(np.dstack(sidmatrixes))
            # print(levelmatrixes)

        if len(levelmatrixes) > 1:
            self.matrix = np.dstack(levelmatrixes)
        else:
            self.matrix = levelmatrixes[0].reshape((1, )+levelmatrixes[0].shape)
        print(time.time()-starttime)

    def dbm_to_linear(self, value, frequency=2400):
        # return value
        return 10**((27.55-(20*math.log10(frequency))+value)/20)

    def dbm_to_w(self, value):
        return 10**(value/10)

    def dbm_to_w_linear(self, value, distance):
        return 10**(value/10)*(distance*self.graph.cm_per_px)**2

    def w_linear_to_dbm(self, value, distance):
        return 10*np.log10(1/(distance*self.graph.cm_per_px)**2*value)

    def w_to_dbm(self, value):
        return 10*np.log10(value)

    def w_linear_to_w(self, value, distance):
        return 1/(np.clip(distance, 1, 10000000)*self.graph.cm_per_px)**2*value

    def locate(self, scan):
        scan = {(s['bssid'], s['ssid']): s['level'] for s in scan}
        np_scan = np.ones((len(self.sid_ids), ))*self.no_signal
        my_sids = []
        for sid, level in scan.items():
            if sid in self.sid_ids:
                np_scan[self.sid_ids[sid]] = level
                my_sids.append(self.sid_ids[sid])
        # print(self.dbm_to_linear(np_scan))

        my_sids = np.array(my_sids)
        known_spots = len(my_sids)

        # best_station = np.argmax(scan)
        # best_sid = self.sids[best_station]

        diffs = ((self.matrix[:, :, :, my_sids]-self.dbm_to_w(np_scan[my_sids]))**2)
        matches = diffs.sum(axis=3)
        # print(matches)
        best_match = np.unravel_index(np.argmin(matches), matches.shape)
        print(diffs[best_match])
        return [int(i*self.divide_by) for i in best_match], round(self.w_to_dbm(np.min(matches)), 2), known_spots

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
