#!/usr/bin/env python3
import io
import json
import os
import sys
import time
from collections import Iterable
from datetime import datetime, timedelta

import qrcode
from flask import Flask, make_response, render_template, request, send_file
from flask.ext.assets import Environment

from classes import Graph, Router

app = Flask('congress-route-planner')
assets = Environment(app)

default_settings = {
    'steps': 'yes',
    'stairs': 'yes',
    'escalators': 'yes',
    'elevators': 'yes',
    'h': '0',
    'e': [],
    's-default': 160,
    's-elevator': 20,
    's-stairs-up': 130,
    's-stairs-down': 160,
    's-escalator-up': 160,
    's-escalator-down': 160,
}
short_base = 'c3nav.de/'

if 'C3NAVCONF' in os.environ:
    filename = os.environ['C3NAVCONF']
elif len(sys.argv) > 1:
    filename = sys.argv[1]
else:
    print('Please specify filename: run.py <filename> or environment variable C3NAVCONF')
    sys.exit(1)

starttime = time.time()
f = open(filename)
graph = Graph(json.load(f), auto_connect=True)
print('Graph loaded in %.3fs' % (time.time()-starttime))


@app.route('/', methods=['GET', 'POST'])
def main(origin=None, destination=None):
    src = request.args if request.method == 'GET' else request.form

    ctx = {
        'location_select': sorted(graph.selectable_locations.values(), key=lambda l: (0-l.priority, l.title)),
        'titles': {name: room.titles.get('en', name) for name, room in graph.rooms.items()},
        'mobile_client': request.headers.get('User-Agent').startswith('c3navClient'),
        'graph': graph
    }

    # Select origins

    origin = graph.selectable_locations.get(src.get('o', origin))
    destination = graph.selectable_locations.get(src.get('d', destination))
    ctx.update({'origin': origin, 'destination': destination})
    if request.method == 'POST':
        if origin is None:
            return 'missing origin'

        if destination is None:
            return 'missing destination'

    # Load Settings
    settingscookie = request.cookies.get('settings')
    cookie_settings = {}
    if settingscookie is not None:
        try:
            cookie_settings = json.loads(settingscookie)
        except:
            pass
        else:
            ctx['had_settings_cookie'] = True

    setsettings = {}
    for name, default_value in Router.default_settings.items():
        if not isinstance(default_value, str) and isinstance(default_value, Iterable):
            value = src.getlist(name)
            cookie_value = cookie_settings.get(name)
            if value or ('force-'+name) in src:
                setsettings[name] = value
            elif isinstance(cookie_value, list):
                setsettings[name] = cookie_value
        elif name in src:
            setsettings[name] = src.get(name)
        elif name in cookie_settings:
            cookie_value = cookie_settings.get(name)
            if not isinstance(cookie_value, Iterable):
                setsettings[name] = cookie_value

    router = Router(graph, setsettings)
    ctx['settings'] = router.settings

    settings_flat = sum([(sum([[(n, vv)] for vv in v], []) if isinstance(v, Iterable) else [(n, v)])
                         for n, v in router.settings.items()], [])
    ctx['settings_fields'] = [(n, v) for n, v in settings_flat if n in src]

    # parse what is avoided
    avoid = []
    for ctype in ('steps', 'stairs', 'escalators', 'elevators'):
        s = router.settings[ctype]
        if s == 'yes':
            continue
        else:
            avoid.append(ctype+{'no': '↕', 'up': '↓', 'down': '↑'}[s])
    for e in router.settings['e']:
        avoid.append(graph.titles.get(e, {}).get('en', e))
    ctx['avoid'] = avoid

    if request.method == 'GET':
        return make_response(render_template('main.html', **ctx))

    """
    Now lets route!
    """
    messages, route = router.get_route(origin, destination)
    if route is not None:
        route_description, has_avoided_ctypes = route.describe()
        if has_avoided_ctypes:
            messages.append(('warn', 'This route contains way types that you wanted to avoid '
                                     'because otherwise there would route would be possible.'))
        total_duration = sum(rp['duration'] for rp in route_description)
        ctx.update({
            'routeparts': route_description,
            'total_distance': round(sum(rp['distance'] for rp in route_description)/100, 1),
            'total_duration': (int(total_duration/60), int(total_duration % 60)),
            'jsonfoo': json.dumps(route_description, indent=4)
        })

    ctx.update({
        'messages': messages,
        'isresult': True,
        'resultsonly': src.get('ajax') == '1'
    })

    resp = make_response(render_template('main.html', **ctx))
    if src.get('savesettings') == '1':
        resp.set_cookie('settings', json.dumps(router.settings),
                        expires=datetime.now()+timedelta(days=30))
    return resp


@app.route('/qr/<path:path>')
def qr_code(path):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(short_base+path)
    qr.make(fit=True)
    img = io.BytesIO()
    qr.make_image().save(img, 'PNG')
    img.seek(0)
    return send_file(img, mimetype='image/png')


@app.route('/link/<path:path>')
def link_for_noscript(path):
    return render_template('link.html', path=path, short_base=short_base)


@app.route('/o<location>')
def short_origin(location):
    return main(origin=location)


@app.route('/d<location>')
def short_destination(location):
    return main(destination=location)


if 'gunicorn' not in os.environ.get('SERVER_SOFTWARE', ''):
    app.run(threaded=True, debug=('debug' in sys.argv))
