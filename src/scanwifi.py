#!/usr/bin/env python3
import json
import time
from subprocess import PIPE, Popen

while True:
    p = Popen(['iwlist', 'scan'], stdout=PIPE, stderr=PIPE)
    output = p.communicate()[0].decode().split('Cell')[1:]
    if not output:
        print('scan failed, try again…')
        time.sleep(0.2)
        continue

    def get_from_lines(lines, keyword):
        return [l for l in lines if l.startswith(keyword)][0].split(keyword)[1].strip()

    stations = []
    for data in output:
        lines = [l.strip() for l in data[5:].split('\n')]
        stations.append({
            'bssid': get_from_lines(lines, 'Address:'),
            'ssid': get_from_lines(lines, 'ESSID:')[1:-1],
            'level': int(get_from_lines(lines, 'Quality=').split('=')[-1][:-4]),
            'frequency': int(float(get_from_lines(lines, 'Frequency:').split(' ')[0])*1000)
        })

    result = json.dumps(stations)
    print('\a', end='')
    try:
        p = Popen(['xclip', '-selection', 'c'], stdin=PIPE)
        p.communicate(("mobileclient.setNearbyStations('"+result+"');").encode())
        failed = p.returncode
    except:
        raise
        failed = 1

    if failed:
        print('clipboard failed. install xclip')
    print('%d stations. JSON copied to clipboard' % len(stations))
