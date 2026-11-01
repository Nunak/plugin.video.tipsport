import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('libs.live_tv', root/'libs/live_tv.py')
live_tv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(live_tv)
spec = importlib.util.spec_from_file_location('shared_stream', root/'libs/shared_stream.py')
shared = importlib.util.module_from_spec(spec)
with patch.dict(sys.modules, {'libs.live_tv': live_tv}):
    spec.loader.exec_module(shared)


class SingleInputTests(unittest.TestCase):
    def test_one_acquisition_rejects_second_and_releases_on_disconnect(self):
        utils = types.ModuleType('libs.utils')
        utils.user_agent = 'test'
        process = Mock()
        process.stdout.read.side_effect = [b'packet', b'next']
        process.poll.return_value = None
        relay = shared.SingleInput()
        with patch.dict(sys.modules, {'libs.utils': utils}), \
                patch.object(shared.os.path, 'isfile', return_value=True), \
                patch.object(shared, 'resolve_channel', return_value='https://example.test/live') as resolve, \
                patch.object(shared.subprocess, 'Popen', return_value=process) as spawn:
            body = relay.open('kometa')
            self.assertEqual(next(body), b'packet')
            with self.assertRaises(live_tv.StreamUnavailable):
                relay.open('test-tennis')
            self.assertEqual(resolve.call_count, 1)
            self.assertEqual(spawn.call_count, 1)
            self.assertIn('copy', spawn.call_args.args[0])
            self.assertNotIn('shell', spawn.call_args.kwargs)
            self.assertEqual(relay.status(), {'active': True, 'channel': 'kometa', 'acquisitions': 1})
            body.close()
            process.terminate.assert_called_once()
            process.stdout.close.assert_called_once()
            self.assertFalse(relay.status()['active'])

    def test_resolution_failure_releases_reservation(self):
        relay = shared.SingleInput()
        with patch.object(shared.os.path, 'isfile', return_value=True), \
                patch.object(shared, 'resolve_channel', side_effect=live_tv.StreamUnavailable('offline')):
            for _ in range(2):
                with self.assertRaises(live_tv.StreamUnavailable):
                    relay.open('kometa')
                self.assertFalse(relay.status()['active'])
                self.assertEqual(relay.status()['acquisitions'], 0)

    def test_missing_ffmpeg_does_not_contact_provider(self):
        relay = shared.SingleInput()
        with patch.object(shared.os.path, 'isfile', return_value=False), \
                patch.object(shared, 'resolve_channel') as resolve:
            with self.assertRaises(live_tv.StreamUnavailable):
                relay.open('kometa')
            resolve.assert_not_called()
            self.assertFalse(relay.status()['active'])
