import importlib.util
from pathlib import Path
import unittest
import sys
import types
from io import BytesIO
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location(
    'live_tv', Path(__file__).resolve().parents[1] / 'libs' / 'live_tv.py')
live_tv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(live_tv)


class LiveTVTests(unittest.TestCase):
    def test_api_request_preserves_required_headers_and_method(self):
        utils = types.ModuleType('libs.utils')
        utils.user_agent = 'test-agent'
        for method in ('GET', 'PUT'):
            response = BytesIO(b'{"ok": true}')
            with patch.dict(sys.modules, {'libs.utils': utils}), \
                    patch.object(live_tv, 'urlopen', return_value=response) as request:
                self.assertEqual(live_tv.fetch_json('https://api.example.test/program',
                    [{'name': 'JSESSIONID', 'value': 'synthetic-session'}], method), {'ok': True})
                sent = request.call_args.args[0]
                self.assertEqual(sent.get_method(), method)
                self.assertEqual(sent.get_header('Content-type'), 'application/json')
                self.assertEqual(sent.get_header('Cookie'), 'JSESSIONID=synthetic-session')

    def test_playlist_uses_only_loopback_resolvers(self):
        result = live_tv.playlist()
        self.assertTrue(result.startswith('#EXTM3U\n'))
        self.assertEqual([line for line in result.splitlines() if line.startswith('http')], [
            'http://127.0.0.1:8089/jellyfin/kometa.m3u8',
            'http://127.0.0.1:8089/jellyfin/test-tennis.m3u8'])

    def test_kometa_selects_only_live_matching_game(self):
        program = {'program': [{'matchesByTimespans': [[
            {'id': 1, 'name': 'Kometa - Example', 'live': False},
            {'id': 2, 'name': 'Example - Other', 'live': True},
            {'id': 3, 'name': 'Example - KOMETA Brno', 'live': True}]]}]}
        self.assertEqual(live_tv.choose_match(program, 'kometa'), '3')

    def test_tennis_uses_tennis_sport(self):
        program = {'program': [
            {'id': 1, 'matchesByTimespans': [[{'id': 1, 'live': True}]]},
            {'id': 43, 'matchesByTimespans': [[{'id': 2, 'live': True}]]}]}
        self.assertEqual(live_tv.choose_match(program, 'test-tennis'), '2')

    def test_offline_and_unknown_channels_do_not_select_other_games(self):
        for channel in ('kometa', 'test-tennis', 'unknown'):
            with self.subTest(channel=channel), self.assertRaises(live_tv.StreamUnavailable):
                live_tv.choose_match({'program': []}, channel)

    def test_img_resolver(self):
        fetch = Mock(return_value={'hlsUrl': 'https://media.example.test/live.m3u8'})
        self.assertEqual(live_tv.resolve_payload({
            'type': 'URL_IMG', 'data': 'https://api.example.test/stream'}, fetch),
            'https://media.example.test/live.m3u8')
        fetch.assert_called_once_with('https://api.example.test/stream')

    def test_tvcom_resolver(self):
        fetch = Mock(return_value={'url': {'hls': {'url': 'https://media.example.test/live.m3u8'}}})
        self.assertEqual(live_tv.resolve_payload({
            'type': 'URL_TVCOM', 'data': 'https://api.example.test/stream'}, fetch),
            'https://media.example.test/live.m3u8')

    def test_unsupported_types_and_invalid_urls_fail_closed(self):
        for payload in ({'type': 'URL_UNKNOWN', 'data': 'https://example.test/video'},
                        {'type': 'DIRECT', 'data': 'file:///private/data'},
                        {'type': 'DIRECT', 'data': 'http://example.test/video'},
                        {'type': 'DIRECT'},
                        {'type': 'DIRECT', 'data': 'https://user:pass@example.test/video'}):
            with self.subTest(payload=payload), self.assertRaises(live_tv.StreamUnavailable):
                live_tv.resolve_payload(payload, Mock())


if __name__ == '__main__':
    unittest.main()
