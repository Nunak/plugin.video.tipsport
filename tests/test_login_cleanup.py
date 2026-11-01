"""Exercise login cleanup without a browser, account, or network access."""
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch


class LoginCleanupTests(unittest.TestCase):
    def setUp(self):
        self.driver = Mock()
        self.cookies = [{'name': 'JSESSIONID', 'value': 'synthetic-test-session'}]
        self.driver.get_cookies.return_value = self.cookies
        addon = types.ModuleType('xbmcaddon')
        addon.Addon = Mock(return_value=Mock(getSetting=lambda key: {
            'browser': 'lokální Google Chrome', 'tipsport_version': 'CZ',
            'username': 'example', 'password': 'synthetic-test-password'}[key]))
        gui = types.ModuleType('xbmcgui')
        gui.Dialog = Mock()
        gui.NOTIFICATION_ERROR = 'error'
        vfs = types.ModuleType('xbmcvfs')
        vfs.translatePath = lambda path: path
        by = types.ModuleType('selenium.webdriver.common.by')
        by.By = types.SimpleNamespace(XPATH='xpath', NAME='name')
        ec = types.ModuleType('selenium.webdriver.support.expected_conditions')
        ec.visibility_of_element_located = lambda locator: locator
        ui = types.ModuleType('selenium.webdriver.support.ui')
        self.wait = Mock()
        ui.WebDriverWait = Mock(return_value=self.wait)
        api = types.ModuleType('libs.api')
        api.init_driver = Mock(return_value=self.driver)
        modules = {'xbmcaddon': addon, 'xbmcgui': gui, 'xbmcvfs': vfs,
                   'selenium': types.ModuleType('selenium'),
                   'selenium.webdriver': types.ModuleType('selenium.webdriver'),
                   'selenium.webdriver.common': types.ModuleType('selenium.webdriver.common'),
                   'selenium.webdriver.common.by': by,
                   'selenium.webdriver.support': types.ModuleType('selenium.webdriver.support'),
                   'selenium.webdriver.support.expected_conditions': ec,
                   'selenium.webdriver.support.ui': ui, 'libs.api': api}
        self.module_patch = patch.dict(sys.modules, modules)
        self.module_patch.start()
        self.addCleanup(self.module_patch.stop)
        path = Path(__file__).resolve().parents[1] / 'libs' / 'session.py'
        spec = importlib.util.spec_from_file_location('tipsport_session', path)
        self.session = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.session)
        self.session.save_session = Mock()

    def test_success_saves_verified_session_and_closes_browser(self):
        self.assertTrue(self.session.login())
        self.session.save_session.assert_called_once_with(json.dumps(self.cookies))
        self.driver.quit.assert_called_once_with()

    def test_failed_verification_preserves_session_and_closes_browser(self):
        self.wait.until.side_effect = [True, True, RuntimeError('verification failed')]
        self.assertFalse(self.session.login())
        self.session.save_session.assert_not_called()
        self.driver.quit.assert_called_once_with()

    def test_navigation_error_preserves_session_and_closes_browser(self):
        self.driver.get.side_effect = RuntimeError('navigation failed')
        self.assertFalse(self.session.login())
        self.session.save_session.assert_not_called()
        self.driver.quit.assert_called_once_with()

    def test_click_error_preserves_session_and_closes_browser(self):
        self.driver.find_element.return_value.click.side_effect = RuntimeError('intercepted')
        self.assertFalse(self.session.login())
        self.session.save_session.assert_not_called()
        self.driver.quit.assert_called_once_with()

    def test_cookie_error_preserves_session_and_closes_browser(self):
        self.driver.get_cookies.side_effect = RuntimeError('browser disconnected')
        self.assertFalse(self.session.login())
        self.session.save_session.assert_not_called()
        self.driver.quit.assert_called_once_with()

    def test_cleanup_error_does_not_hide_success(self):
        self.driver.quit.side_effect = RuntimeError('already closed')
        self.assertTrue(self.session.login())
        self.session.save_session.assert_called_once()


if __name__ == '__main__':
    unittest.main()
