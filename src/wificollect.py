#!/usr/bin/env python3
import datetime
import json
import os
import sys
import time

from flask import Flask, render_template, request

from classes import Graph

app = Flask('c3nav-wificollect')


if 'C3NAVCONF' in os.environ:
    filename = os.environ['C3NAVCONF']
elif len(sys.argv) > 1:
    filename = sys.argv[1]
else:
    print('Please specify filename: run.py <filename> or environment variable C3NAVCONF')
    sys.exit(1)

starttime = time.time()


@app.route('/')
def map():
    f = open(filename)
    graph = Graph(json.load(f), auto_connect=False)
    return render_template('wificollect.html', graph=graph)


@app.route('/add', methods=['POST'])
def addroom():
    data = json.load(open(filename))
    position = [int(i) for i in request.form.get('position').split('.')]
    stations = json.loads(request.form.get('stations'))
    data['wifidata'].append({
        'level': position[0],
        'x': position[1],
        'y': position[2],
        'time': str(datetime.datetime.now()),
        'stations': stations
    })
    json.dump(data, open(filename, 'w'), indent=4, sort_keys=True)
    return 'ok'

app.run(threaded=True, debug=True)
