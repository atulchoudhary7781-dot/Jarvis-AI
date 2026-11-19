"""Shared fail-closed quota for public Groq requests (Upstash Redis REST)."""
from __future__ import annotations

import hashlib
import hmac
import ipaddress
import json
import re
import urllib.request
from urllib.parse import urlsplit
from .groq_speech import NoRedirect

# Units are reserved before any outbound provider request. A transcription costs
# two units (it can also trigger a translation); a separate response translation
# costs one. Fixed windows start on the first admitted request, not midnight.
DAILY_UNITS = 100
MINUTE_UNITS = 20
CLIENT_MINUTE_UNITS = 8
LUA = r'''
local weight=tonumber(ARGV[1])
local d=tonumber(redis.call('GET',KEYS[1]) or '0')
local m=tonumber(redis.call('GET',KEYS[2]) or '0')
local i=tonumber(redis.call('GET',KEYS[3]) or '0')
if d+weight>tonumber(ARGV[2]) or m+weight>tonumber(ARGV[3]) or i+weight>tonumber(ARGV[4]) then return 0 end
local nd=redis.call('INCRBY',KEYS[1],weight)
local nm=redis.call('INCRBY',KEYS[2],weight)
local ni=redis.call('INCRBY',KEYS[3],weight)
if nd==weight then redis.call('EXPIRE',KEYS[1],86400) end
if nm==weight then redis.call('EXPIRE',KEYS[2],60) end
if ni==weight then redis.call('EXPIRE',KEYS[3],60) end
return 1
'''


def valid_config(url, token):
    if not isinstance(url, str) or not isinstance(token, str):
        return False
    try:
        p = urlsplit(url)
        return bool(p.scheme == 'https' and re.fullmatch(r'[a-z0-9-]+\.upstash\.io', p.netloc)
                    and p.path in ('', '/') and not p.query and not p.fragment
                    and token.isascii() and 16 <= len(token) <= 512
                    and all(33 <= ord(c) < 127 for c in token))
    except ValueError:
        return False


def reserve(url, token, client_ip, weight, *, opener=None):
    """Reserve weighted capacity atomically. False on missing IP or any failure."""
    if not valid_config(url, token) or weight not in (1, 2):
        return False
    try:
        address = str(ipaddress.ip_address(client_ip))
        digest = hmac.new(token.encode(), address.encode(), hashlib.sha256).hexdigest()
        keys = ['jarvis:voice:daily', 'jarvis:voice:minute', 'jarvis:voice:client:' + digest]
        command = ['EVAL', LUA, '3', *keys, str(weight), str(DAILY_UNITS),
                   str(MINUTE_UNITS), str(CLIENT_MINUTE_UNITS)]
        endpoint = url.rstrip('/')
        req = urllib.request.Request(endpoint, json.dumps(command).encode(),
                headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'}, method='POST')
        client = opener or urllib.request.build_opener(NoRedirect())
        with client.open(req, timeout=4) as response:
            if response.status != 200 or response.geturl().rstrip('/') != endpoint:
                return False
            data = response.read(4097)
        if len(data) > 4096:
            return False
        result = json.loads(data)
        return type(result.get('result')) is int and result['result'] == 1
    except (OSError, ValueError, TypeError, AttributeError, UnicodeError):
        return False
