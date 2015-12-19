
class WifiLocator():
    connection_types = ('default', 'steps-up', 'steps-down', 'stairs-up', 'stairs-down',
                        'escalator-up', 'escalator-down', 'elevator-up', 'elevator-down')
    diag = 2**0.5

    def __init__(self, graph, data):
        self.graph = graph

        # group multiple scans at the same position
        self.scans_by_position = {}
        for scan in data:
            pos = (scan['level'], scan['x'], scan['y'])
            if pos not in self.scans_by_position:
                self.scans_by_position[pos] = {}
            for station in scan['stations']:
                sid = (station['bssid'], station['ssid'])
                if station['ssid'] in ('codingcatgirl', 'mesh.ffe'):
                    continue
                if sid not in self.scans_by_position[pos]:
                    self.scans_by_position[pos][sid] = []
                self.scans_by_position[pos][sid].append(station['level'])

        # average of each station that was always available at this position
        for pos, stations in self.scans_by_position.items():
            count = max(len(s) for s in stations.values())
            for sid in tuple(stations.keys()):
                if len(stations[sid]) < count:
                    del stations[sid]
                else:
                    stations[sid] = sum(stations[sid])/count

        # group scans by position
        self.stations = {}
        for pos, values in self.scans_by_position.items():
            for sid, level in values.items():
                if sid not in self.stations:
                    self.stations[sid] = {}
                self.stations[sid][pos] = level
        self.sids = set(self.stations.keys())

    def locate(self, scan):
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
