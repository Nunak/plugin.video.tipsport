"""Run with: python -m unittest discover -s tests"""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch


class ListStreamsTests(unittest.TestCase):
    def test_optional_scores_do_not_hide_playable_matches(self):
        matches = []
        for score in ({}, {'score': None}, {'score': {}},
                      {'score': {'statusOffer': None}},
                      {'score': {'statusOffer': '1:0'}}):
            matches.append(dict(id=len(matches), name='Player A - Player B',
                                live=True, sport='Tennis', competition='Test',
                                **score))
        data = {'program': [{'id': 43, 'matchesByTimespans': [matches]}]}
        gui = types.ModuleType('xbmcgui')
        gui.ListItem = Mock(side_effect=lambda **kwargs: Mock(**{
            'label': kwargs['label']}))
        plugin = types.ModuleType('xbmcplugin')
        plugin.setPluginCategory = Mock()
        plugin.addDirectoryItem = Mock()
        plugin.endOfDirectory = Mock()
        api = types.ModuleType('libs.api')
        api.api_call = Mock(return_value=data)
        api.set_domain = lambda url: url
        session = types.ModuleType('libs.session')
        session.login = Mock()
        blacklist = types.ModuleType('libs.blacklist')
        blacklist.load_blacklist = lambda: {'competitions': [], 'sports': []}
        utils = types.ModuleType('libs.utils')
        utils.get_url = lambda **kwargs: 'play/' + str(kwargs['id'])
        utils.plugin_id = 'plugin.video.tipsport'
        modules = {'xbmc': types.ModuleType('xbmc'), 'xbmcgui': gui,
                   'xbmcplugin': plugin, 'xbmcaddon': types.ModuleType('xbmcaddon'),
                   'libs.api': api, 'libs.session': session,
                   'libs.blacklist': blacklist, 'libs.utils': utils}
        source = Path(__file__).resolve().parents[1] / 'libs' / 'lists.py'
        spec = importlib.util.spec_from_file_location('tipsport_lists', source)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, modules), patch.object(sys, 'argv', ['addon', '1']):
            spec.loader.exec_module(module)
            module.list_streams('43', 'Tennis')

        self.assertEqual(plugin.addDirectoryItem.call_count, len(matches))
        for index, call in enumerate(plugin.addDirectoryItem.call_args_list):
            handle, url, item, folder = call.args
            self.assertEqual((handle, url, folder), (1, 'play/' + str(index), False))
            item.setProperty.assert_called_once_with('IsPlayable', 'true')
            self.assertIn('Player A - Player B', item.label)
            self.assertNotIn('None', item.label)
        self.assertIn('1:0', plugin.addDirectoryItem.call_args.args[2].label)
        plugin.endOfDirectory.assert_called_once_with(1, cacheToDisc=False)


if __name__ == '__main__':
    unittest.main()
