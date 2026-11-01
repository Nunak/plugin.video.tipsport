# -*- coding: utf-8 -*-
import os
import sys
import xbmcaddon
import xbmcgui
from xbmcvfs import translatePath

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import json
import socket

LOGIN_URL = {'CZ' : 'https://www.tipsport.cz/', 'SK' : 'https://www.tipsport.sk/'}

def login():
    addon = xbmcaddon.Addon()
    if addon.getSetting('browser') not in ['zadání přes web', 'načíst ze souboru']:
        from libs.api import init_driver
        driver = init_driver()
        LOGIN_BUTTON1 = {'CZ' : 'Přihlásit', 'SK' : 'Prihlásiť'}
        LOGIN_BUTTON2 = {'CZ' : 'Přihlásit se', 'SK' : 'Prihlásiť sa'}
        LOGIN_VERIFICATION = {'CZ' : 'Vložit peníze', 'SK' : 'Vložiť peniaze'}

        addon = xbmcaddon.Addon()
        try:
            driver.get(LOGIN_URL[addon.getSetting('tipsport_version')])
            WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, '//button[text()="' + LOGIN_BUTTON1[addon.getSetting('tipsport_version')] + '"]')))
            login_button = driver.find_element(By.XPATH, '//button[text()="' + LOGIN_BUTTON1[addon.getSetting('tipsport_version')] + '"]')
            login_button.click()
            WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.NAME, 'username')))
            username = driver.find_element(By.NAME, 'username')
            username.send_keys(addon.getSetting('username'))
            password = driver.find_element(By.NAME, 'password')
            password.send_keys(addon.getSetting('password'))

            login_button = driver.find_element(By.XPATH, '//button[text()="' + LOGIN_BUTTON2[addon.getSetting('tipsport_version')] + '"]')
            login_button.click()
            WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, '//a[text()="' + LOGIN_VERIFICATION[addon.getSetting('tipsport_version')] + '"]')))
            save_session(json.dumps(driver.get_cookies()))
            return True
        except Exception:
            xbmcgui.Dialog().notification('Tipsport.cz', 'Došlo k chybě při přihlášení', xbmcgui.NOTIFICATION_ERROR, 5000)
            return False
        finally:
            try:
                driver.quit()
            except Exception:
                xbmcgui.Dialog().notification('Tipsport.cz', 'Došlo k chybě při volání prohlížeče', xbmcgui.NOTIFICATION_ERROR, 5000)
    elif addon.getSetting('browser') == 'zadání přes web':
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        xbmcgui.Dialog().textviewer('Tipsport.cz', 'Připojte se z prohlížeče na http://' + ip + ':8089/ a zadejte do formuláře platné JSESSIONID podle návodu.')
        sys.exit()
    else:
        jsession_file_folder = addon.getSetting('jsession_file_folder')
        jsessionid = ''
        if len(jsession_file_folder) > 0:
            filename = os.path.join(jsession_file_folder, 'jsessionid.txt')
            try:
                with open(filename, "r") as f:
                    for row in f:
                        jsessionid = row[:-1]
            except IOError as error:
                if error.errno != 2:
                    xbmcgui.Dialog().notification('Tipsport.cz', 'Chyba načtení JSESSIONID', xbmcgui.NOTIFICATION_ERROR, 5000)
                    return False
            if len(jsessionid) > 0:
                from libs.api import set_domain
                cookie = [{'domain' : set_domain('.tipsport.cz'), 'name' : 'JSESSIONID', 'value' : str(jsessionid)}]
                save_session(json.dumps(cookie))
                return True
            else:
                xbmcgui.Dialog().notification('Tipsport.cz', 'JSESSIONID se ze souboru nepodařilo načíst', xbmcgui.NOTIFICATION_ERROR, 5000)
                sys.exit()
        else:
            xbmcgui.Dialog().notification('Tipsport.cz', 'Není zadaný adresář se souborem s JSESSIONID', xbmcgui.NOTIFICATION_ERROR, 5000)        
        

def save_session(data):
    addon = xbmcaddon.Addon()
    addon_userdata_dir = translatePath(addon.getAddonInfo('profile'))
    filename = os.path.join(addon_userdata_dir, 'session.txt')
    try:
        with open(filename, "w") as f:
            f.write('%s\n' % data)
    except IOError:
        xbmcgui.Dialog().notification('Tipsport.cz', 'Chyba uložení session', xbmcgui.NOTIFICATION_ERROR, 5000)

def load_session():
    data = None
    addon = xbmcaddon.Addon()
    addon_userdata_dir = translatePath(addon.getAddonInfo('profile'))
    filename = os.path.join(addon_userdata_dir, 'session.txt')
    try:
        with open(filename, "r") as f:
            for row in f:
                session_data = row[:-1]
        data = json.loads(session_data)
    except IOError as error:
        if error.errno != 2:
            xbmcgui.Dialog().notification('Tipsport.cz', 'Chyba načtení session', xbmcgui.NOTIFICATION_ERROR, 5000)
    return data

def export_jsessionid():
    addon = xbmcaddon.Addon()
    jsessionid = ''
    jsession_file_folder = addon.getSetting('jsession_file_folder')
    if len(jsession_file_folder) > 0:
        session = load_session()
        if len(session) > 0:
            for cookie in session:
                if 'name' in cookie and cookie['name'] == 'JSESSIONID':
                    jsessionid = cookie['value']
                    filename = os.path.join(jsession_file_folder, 'jsessionid.txt')
                    try:
                        with open(filename, "w") as f:
                            f.write('%s\n' % jsessionid)
                        xbmcgui.Dialog().notification('Tipsport.cz', 'JSESSIONID bylo uloženo do souboru', xbmcgui.NOTIFICATION_INFO, 5000)    
                    except IOError:
                        xbmcgui.Dialog().notification('Tipsport.cz', 'Chyba uložení JSESSIONID', xbmcgui.NOTIFICATION_ERROR, 5000)
            if len(jsessionid) == 0:
                xbmcgui.Dialog().notification('Tipsport.cz', 'Chyba získání JSESSIONID', xbmcgui.NOTIFICATION_ERROR, 5000)
        else:
            xbmcgui.Dialog().notification('Tipsport.cz', 'Chyba získání JSESSIONID', xbmcgui.NOTIFICATION_ERROR, 5000)
    else:
        xbmcgui.Dialog().notification('Tipsport.cz', 'Není zadaný adresář pro export JSESSIONID', xbmcgui.NOTIFICATION_ERROR, 5000)