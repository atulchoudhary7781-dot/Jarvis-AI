"""OpenWeather backup and fail-closed shared quota; all provider/Redis calls mocked."""
import concurrent.futures
import http.client
import json
import os
import threading
import unittest
from datetime import datetime, timezone
from unittest.mock import patch
from urllib.error import HTTPError

from hologram import quota, skills
from hologram.server import make_server
from test_public_quota import FakeRedisTransport, URL, TOKEN, fakeredis

TEST_KEY = '0123456789abcdef0123456789abcdef'
NOW = datetime(2026, 11, 18, 10, 0, tzinfo=timezone.utc)
LOC = skills.ALIASES['delhi']

class WeatherAnswer(unittest.TestCase):
    def test_valid_data_and_attribution(self):
        data = {'main': {'temp': 26.5}, 'dt': NOW.timestamp(), 'weather': [{'id': 800, 'description': 'ignored user content'}]}
        with patch.object(skills, 'fetch_json', return_value=data) as request:
            result = skills.openweather_conditions(LOC, 'hi-IN', TEST_KEY, NOW)
        self.assertEqual(result['source'], 'OpenWeather')
        self.assertIn('26', result['text'])
        self.assertIn('ओपन वेदर', result['text'])
        self.assertIn('साफ़', result['text'])
        self.assertNotIn('ignored user content', result['text'])
        self.assertEqual(request.call_args.args[0], 'https://api.openweathermap.org/data/2.5/weather')
        self.assertEqual(request.call_args.args[1]['units'], 'metric')
        self.assertNotIn(TEST_KEY, json.dumps(result))

    def test_stale_and_future_never_presented_as_current(self):
        for seconds, expect in [(-5*3600, 'fresh'), (301, None)]:
            with self.subTest(seconds=seconds), patch.object(skills, 'fetch_json', return_value={'main': {'temp': 10}, 'dt': NOW.timestamp()+seconds}):
                if expect:
                    result = skills.openweather_conditions(LOC, 'en', TEST_KEY, NOW)
                    self.assertIn('do not have a fresh reading', result['text'])
                else:
                    with self.assertRaises(ValueError): skills.openweather_conditions(LOC, 'en', TEST_KEY, NOW)

    def test_invalid_provider_data_and_key_fail_closed(self):
        for data in [{'main': {'temp': 'nan'}, 'dt': NOW.timestamp()}, {'main': {'temp': 95}, 'dt': NOW.timestamp()}]:
            with patch.object(skills, 'fetch_json', return_value=data):
                with self.assertRaises(ValueError): skills.openweather_conditions(LOC, 'en', TEST_KEY, NOW)
        with patch.object(skills, 'fetch_json') as network:
            with self.assertRaises(ValueError): skills.openweather_conditions(LOC, 'en', 'secret&bad', NOW)
            network.assert_not_called()

    def test_only_429_triggers_fallback(self):
        error = HTTPError('https://example.invalid', 429, 'limit', None, None)
        with patch.object(skills, '_observation', side_effect=error):
            calls=[]
            def backup(loc, lang, now):
                calls.append(loc); return {'text':'backup', 'source':'OpenWeather'}
            result=skills.answer('weather in Delhi', 'en', weather_fallback=backup)
            self.assertEqual(result['source'], 'OpenWeather'); self.assertEqual(len(calls), 1)
        error = HTTPError('https://example.invalid', 401, 'bad auth', None, None)
        with patch.object(skills, '_observation', side_effect=error):
            with self.assertLogs('jarvis.weather', level='WARNING'):
                result=skills.answer('weather in Delhi', 'en', weather_fallback=lambda *x: self.fail('must not call'))
            self.assertEqual(result['source'], 'unavailable')

@unittest.skipUnless(fakeredis, 'Install fakeredis[lua] for atomic script tests')
class WeatherQuota(unittest.TestCase):
    def test_shared_limits_concurrency_and_ip_privacy(self):
        t=FakeRedisTransport()
        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as pool:
            result=list(pool.map(lambda i:quota.reserve_weather(URL,TOKEN,f'10.0.0.{i+1}',opener=t),range(40)))
        self.assertEqual(sum(result),quota.WEATHER_MINUTE)
        self.assertNotIn('10.0.0.1', json.dumps(t.commands))
        t=FakeRedisTransport()
        for i in range(quota.WEATHER_CLIENT_MINUTE):self.assertTrue(quota.reserve_weather(URL,TOKEN,'1.2.3.4',opener=t))
        self.assertFalse(quota.reserve_weather(URL,TOKEN,'1.2.3.4',opener=t))
        self.assertFalse(quota.reserve_weather(URL,TOKEN,'invalid',opener=t))
        self.assertFalse(quota.reserve_weather('https://evil.invalid',TOKEN,'1.2.3.4',opener=t))

class WeatherHttp(unittest.TestCase):
    def test_public_guard_and_secret_not_in_response(self):
        error=HTTPError('https://example.invalid/?secret='+TEST_KEY, 429, 'too many', None, None)
        for with_redis, permitted, calls in [(False,True,0),(True,False,0),(True,True,1)]:
            env={'VERCEL_ENV':'production','OPENWEATHER_API_KEY':TEST_KEY}
            if with_redis: env.update(UPSTASH_REDIS_REST_URL=URL,UPSTASH_REDIS_REST_TOKEN=TOKEN)
            with self.subTest(with_redis=with_redis,permitted=permitted), patch.dict(os.environ,env,clear=True), patch.object(skills, '_observation', side_effect=error), patch('hologram.quota.reserve_weather',return_value=permitted) as reserve, patch('hologram.server.openweather_conditions',return_value={'text':'safe weather','lang':'en-IN','source':'OpenWeather'}) as provider:
                server=make_server(0,preview=True); t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
                try:
                    c=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=6)
                    body=json.dumps({'query':'weather in Delhi','lang':'en-IN','zone':'Asia/Kolkata'})
                    c.request('POST','/api/command',body,{'Content-Type':'application/json','Origin':f'http://127.0.0.1:{server.server_port}','x-vercel-forwarded-for':'1.2.3.4'})
                    response=c.getresponse(); raw=response.read().decode(); c.close();r=json.loads(raw)
                    self.assertEqual(response.status,200)
                    self.assertEqual(provider.call_count,calls)
                    self.assertEqual(r['source'],'OpenWeather' if calls else 'unavailable')
                    self.assertNotIn(TEST_KEY,raw)
                    if not with_redis: self.assertIn('backup is temporarily unavailable', r['text'])
                    self.assertEqual(reserve.call_count,1 if with_redis else 0)
                finally: server.shutdown();server.server_close();t.join()

if __name__ == '__main__': unittest.main()
