"""Local Jellyfin channel adapter using the add-on's existing Tipsport session."""
import json
from urllib.parse import urlsplit
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_URL = 'http://127.0.0.1:8089'
PROGRAM_PATH = '/rest/articles/v1/tv/program?day=0&articleId='


class StreamUnavailable(Exception):
    pass


def playlist(include_test=True):
    channels = [('kometa', 'Tipsport - Kometa')]
    if include_test:
        channels.append(('test-tennis', 'Tipsport - test tenisu'))
    rows = ['#EXTM3U']
    for channel_id, name in channels:
        rows.extend(['#EXTINF:-1 tvg-id="tipsport.' + channel_id +
                     '" group-title="Tipsport",' + name,
                     BASE_URL + '/jellyfin/' + channel_id + '.m3u8'])
    return '\n'.join(rows) + '\n'


def fetch_json(url, cookies=None, method='GET'):
    from libs.utils import user_agent
    headers = {'User-Agent': user_agent, 'Accept': 'application/json',
               'Content-Type': 'application/json'}
    if cookies is not None:
        session = next((cookie.get('value') for cookie in cookies
                        if cookie.get('name') == 'JSESSIONID'), None)
        if not session:
            raise StreamUnavailable('Relace není dostupná.')
        headers['Cookie'] = 'JSESSIONID=' + session
    try:
        with urlopen(Request(url, headers=headers, method=method), timeout=15) as result:
            return json.load(result)
    except HTTPError as error:
        raise StreamUnavailable('Poskytovatel vrátil HTTP ' + str(error.code)) from None
    except URLError:
        raise StreamUnavailable('Poskytovatele se nepodařilo kontaktovat.') from None


def choose_match(program, channel):
    if channel not in ('kometa', 'test-tennis'):
        raise StreamUnavailable('Neznámý kanál.')
    for sport in program.get('program', []):
        if channel == 'test-tennis' and str(sport.get('id')) != '43':
            continue
        candidates = [match for matches in sport.get('matchesByTimespans', []) for match in matches]
        if channel == 'test-tennis':
            candidates.sort(key=lambda match: not match.get('competition', '').startswith('ATP '))
        for match in candidates:
            if not match.get('live'):
                continue
            if channel == 'kometa' and 'kometa' not in match.get('name', '').casefold():
                continue
            if str(match.get('id', '')).isdigit():
                return str(match['id'])
    raise StreamUnavailable('Pro tento kanál právě neběží přenos.')


def checked_url(value):
    if not isinstance(value, str):
        raise StreamUnavailable('Chybí adresa přenosu.')
    parsed = urlsplit(value)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
        raise StreamUnavailable('Nepodporovaná adresa přenosu.')
    return value


def resolve_payload(payload, fetch):
    kind = payload.get('type', '')
    target = checked_url(payload.get('data'))
    if kind == 'URL_IMG':
        target = fetch(target).get('hlsUrl')
    elif kind == 'URL_TVCOM':
        target = fetch(target).get('url', {}).get('hls', {}).get('url')
    elif 'URL' in kind:
        raise StreamUnavailable('Tento typ přenosu doplněk nepodporuje.')
    return checked_url(target)


def resolve_channel(channel):
    from libs.api import set_domain
    from libs.session import load_session
    cookies = load_session()
    if not cookies:
        raise StreamUnavailable('Nejdřív předejte přihlášenou relaci doplňku.')
    base = set_domain('https://www.tipsport.cz')
    try:
        fetch_json(base + '/rest/client/restrictions/v1/login/duration', cookies, method='PUT')
    except StreamUnavailable:
        # This optional endpoint may be absent; the original add-on also continues.
        pass
    try:
        program = fetch_json(base + PROGRAM_PATH, cookies)
    except StreamUnavailable as error:
        raise StreamUnavailable('Načtení programu: ' + str(error)) from None
    match_id = choose_match(program, channel)
    try:
        payload = fetch_json(base + '/rest/offer/v2/live/matches/' + match_id +
                             '/stream?deviceType=DESKTOP', cookies)
    except StreamUnavailable as error:
        raise StreamUnavailable('Výběr přenosu: ' + str(error)) from None
    return resolve_payload(payload, fetch_json)
