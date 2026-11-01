# -*- coding: utf-8 -*-
import os
import xbmcaddon

from bottle import run, route, post, template, request, static_file, TEMPLATE_PATH
import json

from libs.session import save_session
from libs.api import set_domain

addon = xbmcaddon.Addon()
template_dir = os.path.join(addon.getAddonInfo('path'), 'resources','templates')
image_dir = os.path.join(addon.getAddonInfo('path'), 'resources','images')
addon = None

@route('/img/<image>')
def add_image(image):
    return static_file(image, root = image_dir)


@route('/')
@post('/')
def page():
    message = ''
    if request.params.get('jsessionid') is not None:
        jsessionid = request.params.get('jsessionid').strip()
        if len(jsessionid) == 0:
            message = 'Nezadaná žádná hodnota JSESSIONID!'
        elif 'p-wt' not in jsessionid:
            message = 'Chybná hodnota JSESSIONID! Přesvědčte se, že jste vložily celou hodnotu!'
        else:
            cookie = [{'domain' : set_domain('.tipsport.cz'), 'name' : 'JSESSIONID', 'value' : str(jsessionid)}]
            save_session(json.dumps(cookie))
            message = 'Hodnota JSESSIONID uložena do doplňku.'
    TEMPLATE_PATH.append(template_dir)
    return template('form.tpl', message = message)

def start_server():
    run(host = '127.0.0.1', port = 8089)

