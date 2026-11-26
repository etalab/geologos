"""HTTP requests with retries."""

import time

import requests

from .config import COMMONS_API, RETRY_STATUSES


def request(session, url, retries=5, **kwargs):
    """GET with retries on throttling, server and network errors."""
    kwargs.setdefault('timeout', 30)
    for attempt in range(1, retries + 1):
        try:
            resp = session.get(url, **kwargs)
        except requests.RequestException as exc:
            if attempt == retries:
                raise
            print(f'Erreur réseau ({exc}), tentative {attempt}/{retries}')
            time.sleep(2 ** attempt)
            continue
        if resp.status_code in RETRY_STATUSES and attempt < retries:
            wait = resp.headers.get('Retry-After', '')
            wait = int(wait) if wait.isdigit() else 2 ** attempt
            print(f'HTTP {resp.status_code}, pause de {wait}s '
                  f'(tentative {attempt}/{retries})')
            resp.close()
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp
    raise RuntimeError('unreachable')


def commons_api(session, params):
    """Query the Commons API, waiting when its servers are lagged."""
    params = dict(params, format='json', formatversion=2, maxlag=5)
    while True:
        data = request(session, COMMONS_API, params=params).json()
        error = data.get('error')
        if error and error.get('code') == 'maxlag':
            print('Serveurs Commons surchargés, pause de 5s...')
            time.sleep(5)
            continue
        if error:
            raise RuntimeError(f"Erreur API Commons : {error.get('info')}")
        return data
