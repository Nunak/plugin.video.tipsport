# -*- coding: utf-8 -*-
import os
import xbmcaddon
import xbmc
from socketserver import ThreadingMixIn
from wsgiref.simple_server import make_server, WSGIServer

from bottle import run, route, post, template, request, static_file, TEMPLATE_PATH, response, redirect, abort, default_app
import json

from libs.session import save_session
from libs.api import set_domain
from libs.live_tv import playlist, resolve_channel, StreamUnavailable
from libs.shared_stream import shared_input

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

@route('/jellyfin/channels.m3u')
def jellyfin_channels():
    response.content_type = 'audio/x-mpegurl; charset=utf-8'
    response.set_header('Cache-Control', 'no-store')
    return playlist()


@route('/jellyfin/<channel>.m3u8')
def jellyfin_stream(channel):
    if channel not in ('kometa', 'test-tennis'):
        abort(404, 'Unknown channel')
    try:
        url = resolve_channel(channel)
    except StreamUnavailable as error:
        abort(503, str(error))
    except Exception as error:
        # Never return cookies, signed stream URLs, or remote error details.
        abort(503, 'Stream unavailable (' + type(error).__name__ + '); check the local Tipsport session.')
    response.set_header('Cache-Control', 'no-store')
    return redirect(url, 302)


@route('/jellyfin/status')
def jellyfin_status():
    response.set_header('Cache-Control', 'no-store')
    return shared_input.status()


@route('/jellyfin/<channel>.ts')
def jellyfin_shared_stream(channel):
    if channel not in ('kometa', 'test-tennis'):
        abort(404, 'Unknown channel')
    if request.method == 'HEAD':
        response.content_type = 'video/MP2T'
        return ''
    try:
        body = shared_input.open(channel)
    except StreamUnavailable as error:
        abort(503, str(error))
    except Exception:
        abort(503, 'Local media input unavailable.')
    response.content_type = 'video/MP2T'
    response.set_header('Cache-Control', 'no-store')
    return body


class ThreadedServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True


def start_server():
    monitor = xbmc.Monitor()
    server = make_server('127.0.0.1', 8089, default_app(), server_class=ThreadedServer)
    server.timeout = 0.5
    try:
        while not monitor.abortRequested():
            server.handle_request()
    finally:
        shared_input.stop()
        server.server_close()

