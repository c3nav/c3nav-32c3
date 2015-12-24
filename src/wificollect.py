#!/usr/bin/env python3
import datetime
import json
import os
import sys
import time

from flask import Flask, render_template, request

from classes import Graph

app = Flask('c3nav-wificollect')


if 'C3NAVPROJECT' in os.environ:
    project = os.environ['C3NAVPROJECT']
elif len(sys.argv) > 1:
    project = sys.argv[1]
else:
    print('Please specify project: run.py <project> or environment variable C3NAVPROJECT')
    sys.exit(1)

starttime = time.time()

graph = Graph(project, auto_connect=False, load_wifi=True)


@app.route('/')
def map():
    graph = Graph(project, auto_connect=False, load_wifi=True)
    return render_template('wificollect.html', fakemobile=('fakemobile' in request.args), graph=graph)


@app.route('/add', methods=['POST'])
def addroom():
    data = json.load(open('projects/'+project+'/wifiscans.json'))
    position = [int(i) for i in request.form.get('position').split('.')]
    stations = json.loads(request.form.get('stations'))
    data['wifiscans'].append({
        'level': position[0],
        'x': position[1],
        'y': position[2],
        'time': str(datetime.datetime.now()),
        'stations': stations
    })
    json.dump(data, open('projects/'+project+'/wifiscans.json', 'w'), indent=4, sort_keys=True)
    return 'ok'


@app.route('/locate', methods=['POST'])
def locate():
    result = list(graph.wifi.locate(json.loads(request.form.get('stations'))))
    result[0] = (result[0].level, result[0].x, result[0].y)
    return json.dumps(result)


app.run(threaded=True, debug=True)
