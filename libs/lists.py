# -*- coding: utf-8 -*-
import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

from libs.api import api_call, set_domain
from libs.session import login
from libs.blacklist import load_blacklist
from libs.utils import get_url, plugin_id

if len(sys.argv) > 1:
    _handle = int(sys.argv[1])

def list_streams(id, label):
    xbmcplugin.setPluginCategory(_handle, label)
    blacklist = load_blacklist()
    api_call(set_domain('https://www.tipsport.cz/rest/client/restrictions/v1/login/duration'), method = 'PUT')
    data = api_call(url = set_domain('https://www.tipsport.cz/rest/articles/v1/tv/program?day=0&articleId='), nolog = True)
    if 'program' in data:
        for sport in data['program']:
            if sport['id'] == int(id):
                for item in sport['matchesByTimespans']:
                    if len(item) > 0:
                        for i in range(len(item)):
                            if item[i]['live'] == True and item[i]['competition'] not in blacklist['competitions'] and item[i]['sport'] not in blacklist['sports']:
                                list_item = xbmcgui.ListItem(label = item[i]['name'] + ' [COLOR=gray] / ' + str((item[i].get('score') or {}).get('statusOffer') or '') +'[/COLOR]\n' + '[COLOR=gray]' + item[i]['sport'] + ' / ' + item[i]['competition'] + '[/COLOR]')
                                list_item.setInfo('video', {'mediatype':'movie', 'title': item[i]['name']})
                                menus = [('Ignorovat: ' + item[i]['sport'], 'RunPlugin(plugin://' + plugin_id + '?action=add_to_blacklist&type=sports&name=' + item[i]['sport'] + ')'), 
                                        ('Ignorovat: ' + item[i]['competition'], 'Container.Update(plugin://' + plugin_id + '?action=add_to_blacklist&type=competitions&name=' + item[i]['competition'] + ')')]
                                list_item.addContextMenuItems(menus)                                    
                                list_item.setContentLookup(False)
                                list_item.setProperty('IsPlayable', 'true')
                                url = get_url(action = 'play_stream', id = item[i]['id'], title = item[i]['name'])
                                xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
    else:
        addon = xbmcaddon.Addon()
        if 'err' in data and data['err'] == 'Unauthorized':
            if addon.getSetting('browser') in ['zadání přes web', 'načíst ze souboru']:
                xbmcgui.Dialog().notification('Tipsport.cz', 'Neplatná session, zkuste zadat nové JSESSIONID', xbmcgui.NOTIFICATION_ERROR, 5000)                
            else:
                success = login()
                if success == True:
                    list_streams(id, label)
                else:
                    xbmcgui.Dialog().notification('Tipsport.cz', 'Neplatná session', xbmcgui.NOTIFICATION_ERROR, 5000)
        else:
            xbmcgui.Dialog().notification('Tipsport.cz', 'Chyba při načtení streamů', xbmcgui.NOTIFICATION_ERROR, 5000)
    xbmcplugin.endOfDirectory(_handle, cacheToDisc = False)

def list_sports():
    blacklist = load_blacklist()
    data = api_call(url = set_domain('https://www.tipsport.cz/rest/articles/v1/tv/program?day=0&articleId='), nolog = True)
    if 'program' in data:
        for sport in data['program']:
            cnt = 0
            for item in sport['matchesByTimespans']:
                for i in range(len(item)):
                    if item[i]['live'] == True and item[i]['competition'] not in blacklist['competitions'] and item[i]['sport'] not in blacklist['sports']:
                        cnt += 1
            if cnt > 0:
                list_item = xbmcgui.ListItem(label = sport['title'])
                url = get_url(action = 'list_streams', id = sport['id'], label = sport['title'])
                xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    else:
        addon = xbmcaddon.Addon()
        if 'err' in data and data['err'] == 'Unauthorized':
            if addon.getSetting('browser') in ['zadání přes web', 'načíst ze souboru']:
                xbmcgui.Dialog().notification('Tipsport.cz', 'Neplatná session, zkuste zadat nové JSESSIONID', xbmcgui.NOTIFICATION_ERROR, 5000)                
            else:
                success = login()
                if success == True:
                    list_sports()
                else:
                    xbmcgui.Dialog().notification('Tipsport.cz', 'Neplatná session', xbmcgui.NOTIFICATION_ERROR, 5000)
        else:
            xbmcgui.Dialog().notification('Tipsport.cz', 'Chyba při načtení streamů', xbmcgui.NOTIFICATION_ERROR, 5000)

def list_blacklist(label):
    xbmcplugin.setPluginCategory(_handle, label)
    blacklist = load_blacklist()
    for sport in blacklist['sports']:
        list_item = xbmcgui.ListItem(label = sport)
        url = get_url(action = 'remove_from_blacklist', type = 'sports', name = sport)
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    for competition in blacklist['competitions']:
        list_item = xbmcgui.ListItem(label = competition)
        url = get_url(action = 'remove_from_blacklist', type = 'competitions', name = competition)
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(_handle, cacheToDisc = False)

def list_settings(label):
    xbmcplugin.setPluginCategory(_handle, label)

    list_item = xbmcgui.ListItem(label='Blacklist')
    url = get_url(action='list_blacklist', label = 'Blacklist')  
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    list_item = xbmcgui.ListItem(label='Nastavení doplňku')
    url = get_url(action='addon_settings', label = 'Nastavení doplňku')  
    xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
    xbmcplugin.endOfDirectory(_handle)        


