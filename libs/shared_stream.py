"""One local MPEG-TS acquisition for Jellyfin's SharedHttpStream tuner."""
import os
import subprocess
import threading

from libs.live_tv import StreamUnavailable, resolve_channel

FFMPEG = r'C:\Program Files\Jellyfin\Server\ffmpeg.exe'


class SingleInput:
    def __init__(self):
        self._lock = threading.Lock()
        self._process = None
        self._channel = None
        self._starts = 0
        self._busy = False

    def status(self):
        with self._lock:
            return {'active': self._busy, 'channel': self._channel,
                    'acquisitions': self._starts}

    def open(self, channel):
        # Reserve before resolving: even concurrent requests cannot open two inputs.
        with self._lock:
            if self._busy:
                raise StreamUnavailable('Jeden vstup už běží; další divák musí použít sdílení v Jellyfinu.')
            self._busy = True
            self._channel = channel
        process = None
        try:
            if not os.path.isfile(FFMPEG):
                raise StreamUnavailable('Nenalezen FFmpeg z instalace Jellyfinu.')
            url = resolve_channel(channel)
            from libs.utils import user_agent
            command = [FFMPEG, '-nostdin', '-hide_banner', '-loglevel', 'error',
                       '-rw_timeout', '15000000', '-user_agent', user_agent,
                       '-i', url, '-map', '0:v:0', '-map', '0:a:0?',
                       '-c', 'copy', '-mpegts_flags', '+resend_headers',
                       '-f', 'mpegts', 'pipe:1']
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            with self._lock:
                self._process = process
                self._starts += 1
            # Prime output so failures return a sanitized 503, not a successful empty body.
            first = process.stdout.read(188 * 32)
            if not first:
                raise StreamUnavailable('Přenos neposkytl video data.')
            return self._body(process, first)
        except BaseException:
            self._release(process)
            raise

    def _body(self, process, first):
        try:
            yield first
            while True:
                chunk = process.stdout.read(188 * 128)
                if not chunk:
                    break
                yield chunk
        finally:
            self._release(process)

    def _release(self, process):
        if process is not None:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)
            if process.stdout:
                process.stdout.close()
        with self._lock:
            if self._process is process:
                self._process = None
                self._channel = None
                self._busy = False

    def stop(self):
        with self._lock:
            process = self._process
        if process is not None:
            self._release(process)


shared_input = SingleInput()
