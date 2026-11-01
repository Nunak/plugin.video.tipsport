# -*- coding: utf-8 -*-
import sys
import xbmc
import xbmcaddon
import xbmcgui

from urllib.request import urlopen, Request
from urllib.error import HTTPError
import json

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.driver_utils import get_driver_path

from libs.session import login, load_session
from libs.utils import user_agent, check_chromedriver

def set_domain(url):
    addon = xbmcaddon.Addon()
    if addon.getSetting('tipsport_version') == 'SK':
        return url.replace('.cz', '.sk')
    else:
        return url

def init_driver():
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    addon = xbmcaddon.Addon()
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--start-maximized')
    options.add_argument('--window-size=1200,800')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-proxy-server')
    options.add_argument('--user-agent=' + user_agent)
    caps = DesiredCapabilities().CHROME
    options.page_load_strategy = 'none'
    caps['pageLoadStrategy'] = 'none'
    try:
        if addon.getSetting('browser') == 'lokální Google Chrome':
            driverPath = str(get_driver_path('chromedriver'))
            check_chromedriver(driverPath)
            driver = webdriver.Chrome(driverPath, options=options, desired_capabilities=caps)
        elif addon.getSetting('browser') == 'Selenium Grid':
            driver = webdriver.Remote(command_executor=addon.getSetting('docker_url'), desired_capabilities=options.to_capabilities())
    except Exception as e:
        xbmcgui.Dialog().notification('Tipsport.cz', 'Problém při volaní prohlížeče. Pokud doplněk předtím fungoval, zkuste restartovat zařízení', xbmcgui.NOTIFICATION_ERROR, 10000)        
        sys.exit()
    return driver

def make_request(url, method):
    cookies = load_session()
    jsessionid = ''
    if cookies is not None:
        for cookie in cookies:
            if cookie['name'] in ['JSESSIONID'] and cookie['value'] is not None:
                jsessionid = cookie['value']
    else:
        login()
        cookies = load_session()
        jsessionid = ''
        if cookies is not None:
            for cookie in cookies:
                if cookie['name'] in ['JSESSIONID'] and cookie['value'] is not None:
                    jsessionid = cookie['value']
    headers = {'User-Agent' : user_agent, 'Accept': 'application/json', 'Content-Type' : 'application/json', 'Cookie' : 'JSESSIONID=' + jsessionid}
    if method == 'GET':
        request = Request(url = url, headers = headers, method = 'GET')
    elif method == 'PUT':
        request = Request(url = url, headers = headers, method = 'PUT')
    try:
        response = urlopen(request).read()
        data = json.loads(response)
    except HTTPError as e:
        xbmc.log('Tipsport.cz > ' 'Chyba při volání '+ str(url) + ': ' + e.reason)
        return { 'err' : e.reason }  
    return data

def api_call(url, method = 'GET', nolog = False, novalidate = False):
    data = {}
    data = make_request(url = url, method = method)
    xbmc.log('Tipsport.cz > ' + str(url))
    if nolog == False or 'errorCode' in data:
        xbmc.log('Tipsport.cz > ' + str(data))
    if 'errorCode' in data and novalidate == False:
        login()
        data = make_request(url = url, method = method)
        xbmc.log('Tipsport.cz > ' + str(url))
        if nolog == False or 'errorCode' in data:
            xbmc.log('Tipsport.cz > ' + str(data))
    return data
