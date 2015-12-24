#!/usr/bin/env python3
from flask import Flask, make_response
from subprocess import Popen, PIPE
import json
import time

app = Flask('c3nav-wificollect')


def get_from_lines(lines, keyword):
    return [l for l in lines if l.startswith(keyword)][0].split(keyword)[1].strip()


@app.route('/scan')
def map():
    while True:
        p = Popen(['iwlist', 'scan'], stdout=PIPE, stderr=PIPE)
        output = p.communicate()[0].decode().split('Cell')[1:]
        if not output:
            print('scan failed, try again…')
            time.sleep(0.2)
            continue

        stations = []
        for data in output:
            lines = [l.strip() for l in data[5:].split('\n')]
            stations.append({
                'bssid': get_from_lines(lines, 'Address:'),
                'ssid': get_from_lines(lines, 'ESSID:')[1:-1],
                'level': int(get_from_lines(lines, 'Quality=').split('=')[-1][:-4]),
                'frequency': int(float(get_from_lines(lines, 'Frequency:').split(' ')[0])*1000)
            })

        if not stations:
            continue

        result = json.dumps(stations)
        resp = make_response(json.dumps({'data': result}))
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

app.run(threaded=True, debug=True, port=4999)
