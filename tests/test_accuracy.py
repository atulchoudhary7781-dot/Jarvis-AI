"""Regression tests for arithmetic routing and conservative Wikipedia selection."""
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from hologram import skills
from hologram.calculator import calculate

class Accuracy(unittest.TestCase):
    def test_live_failure_and_common_arithmetic(self):
        cases = {'What is 17 multiplied by 23?': '391', 'Calculate 17 times 23': '391',
                 '१७ गुणा २३ कितना है': '391', '12 / 4 + 2': '5',
                 '(2 + 3) * 4': '20', 'अगर एक दर्जन में 12 अंडे हैं, तो 3 दर्जन में कितने अंडे होंगे?': '36'}
        with patch.object(skills, 'fetch_json', side_effect=AssertionError('unexpected network')):
            for q, expected in cases.items():
                with self.subTest(q=q):
                    r = skills.answer(q, 'hi-IN' if 'अंडे' in q or 'गुणा' in q else 'en-IN')
                    self.assertEqual(r['source'], 'Calculator')
                    self.assertIn(expected, r['text'])

    def test_spoken_transcripts_reach_calculator(self):
        cases = (
            'सत्रह गुणा तेईस कितना है', 'सत्रह गुना तेइस कितना होता है',
            '17 guna 23 kitna hai', 'satrah guna teis kitna hai',
            '17 को 23 से गुणा करो', '१७ ko २३ se guna karo',
            'सत्रह को तेईस से गुणा कर दो', '17 को 23 से गुणा करो दो',
            'जार्विस सत्रह गुणा तेईस कितना है',
        )
        with patch.object(skills, 'fetch_json', side_effect=AssertionError('unexpected network')):
            for q in cases:
                with self.subTest(q=q):
                    r = skills.answer(q, 'hi-IN')
                    self.assertEqual(r['source'], 'Calculator')
                    self.assertIn('391', r['text'])

    def test_unsupported_spoken_expression_never_guesses(self):
        with patch.object(skills, 'wiki', side_effect=AssertionError('unexpected wiki')):
            r = skills.answer('17 guna unknown kitna hai', 'en')
            self.assertEqual(r['source'], 'Calculator')
            self.assertIn('could not calculate', r['text'])

    def test_invalid_math_no_eval_or_wikipedia(self):
        for q in ('calculate 5 / 0', 'calculate 2 ** 100', 'calculate 9 + __import__("os")', 'calculate 10 % 0', '1.5 modulo 1'):
            with self.subTest(q=q), patch.object(skills, 'wiki', side_effect=AssertionError('wrong route')):
                r = skills.answer(q, 'en')
                self.assertEqual(r['source'], 'Calculator')
                self.assertIn('could not calculate', r['text'])

    def test_modulo_integer_math_and_edges(self):
        cases = {'What is 17 modulo 5?': '2', '17 mod 5': '2', '17 % 5': '2',
                 'calculate 10 % 3': '1', '-17 modulo 5': '3', '17 mod -5': '-3',
                 '१७ modulo ५ कितना है': '2'}
        with patch.object(skills, 'fetch_json', side_effect=AssertionError('unexpected network')):
            for q, expected in cases.items():
                with self.subTest(q=q):
                    handled, result = calculate(q)
                    self.assertTrue(handled)
                    self.assertEqual(result, expected)
        self.assertEqual(calculate('17 modulo 0'), (True, None))
        self.assertEqual(calculate('1.5 mod 1'), (True, None))

    def test_india_independence_scoped_without_chat_consent(self):
        with patch.object(skills, 'fetch_json', side_effect=AssertionError('unexpected network')):
            for q in ('In what year did India become independent?', 'When did India become independent?',
                      'भारत को आजादी कब मिली?'):
                result = skills.answer(q, 'hi-IN')
                self.assertEqual(result['source'], 'local')
                self.assertIn('1947', result['text'])
            self.assertIsNone(skills.india_independence('when did nepal become independent', 'en'))

    def test_hindi_nepal_capital_uses_verified_wiki_city(self):
        data = {'query': {'pages': [
            {'index': 1, 'title': 'Capital punishment in Nepal', 'extract': 'Capital punishment in Nepal has been abolished.'},
            {'index': 2, 'title': 'Kathmandu', 'extract': 'Kathmandu is the capital and largest city of Nepal.'},
        ]}}
        with patch.object(skills, 'fetch_json', return_value=data) as fetch:
            result = skills.answer('नेपाल की राजधानी क्या है?', 'hi-IN')
            self.assertEqual(result['source'], 'Wikipedia')
            self.assertIn('काठमांडू', result['text'])
            self.assertEqual(result['article'], 'Kathmandu')
            self.assertEqual(fetch.call_args.args[1]['gsrsearch'], 'capital of Nepal')

    def test_hindi_capital_direct_title_is_translated_only_if_verified(self):
        data = {'query': {'pages': [{'index': 1, 'title': 'Capital of Japan',
                                    'extract': 'The capital of Japan is Tokyo.'}]}}
        with patch.object(skills, 'fetch_json', return_value=data):
            result = skills.answer('जापान की राजधानी क्या है?', 'hi-IN')
            self.assertIn('टोक्यो', result['text'])
            self.assertEqual(result['lang'], 'hi-IN')

    def test_hindi_capital_not_guessed_when_unverified(self):
        data = {'query': {'pages': [{'index': 1, 'title': 'Kathmandu', 'extract': 'Kathmandu is a city in Nepal.'}]}}
        with patch.object(skills, 'fetch_json', return_value=data):
            result = skills.answer('नेपाल की राजधानी क्या है?', 'hi-IN')
            self.assertNotIn('काठमांडू', result['text'])
            self.assertIn('पक्की जानकारी नहीं मिली', result['text'])
        self.assertIsNone(skills.hindi_capital('नेपाल की राजधानी पर कहानी सुनाओ', 'hi'))

    def test_weather_retry_is_bounded_and_does_not_guess(self):
        skills._observation.cache_clear()
        with patch.object(skills, 'fetch_json', side_effect=[URLError('timeout'), {'current': {'temperature_2m': 25}}]) as fetch:
            self.assertEqual(skills._observation(28.6, 77.2, 123)['current']['temperature_2m'], 25)
            self.assertEqual(fetch.call_count, 2)
        skills._observation.cache_clear()
        with patch.object(skills, 'fetch_json', side_effect=URLError('timeout')) as fetch:
            with self.assertRaises(URLError):
                skills._observation(28.6, 77.2, 123)
            self.assertEqual(fetch.call_count, 2)
        skills._observation.cache_clear()
        rate_limit = HTTPError('https://api.open-meteo.com', 429, 'limited', None, None)
        with patch.object(skills, 'fetch_json', side_effect=rate_limit) as fetch:
            with self.assertRaises(HTTPError):
                skills._observation(28.6, 77.2, 123)
            self.assertEqual(fetch.call_count, 1)
        skills._observation.cache_clear()

    def test_weather_error_diagnostic_has_no_query_location_or_secret(self):
        secret = 'private-secret'
        error = HTTPError('https://example.invalid/?key=' + secret, 429, 'error ' + secret, None, None)
        with patch.object(skills, '_observation', side_effect=error):
            with self.assertLogs('jarvis.weather', level='WARNING') as logs:
                result = skills.answer('weather in Delhi', 'en')
        self.assertEqual(result['source'], 'unavailable')
        text = ' '.join(logs.output)
        self.assertIn('stage=forecast category=http_429', text)
        for data in (secret, 'Delhi', '28.614', 'example.invalid'):
            self.assertNotIn(data, text)

    def test_fractional_results_are_not_presented_as_exact(self):
        self.assertIn('approximately', skills.answer('1 / 3', 'en')['text'])
        self.assertIn('0.000000000001', skills.answer('1 / 1000000000000', 'en')['text'])

    def test_no_false_math(self):
        self.assertEqual(calculate('what is iphone 17'), (False, None))
        self.assertEqual(calculate('time in Tokyo'), (False, None))

    def test_wikipedia_selects_relevant_entry(self):
        data = {'query': {'pages': [
            {'index': 1, 'title': 'Einstein family', 'extract': 'Wrong family article.'},
            {'index': 2, 'title': 'Albert Einstein', 'extract': 'Albert Einstein was a physicist.'}]}}
        with patch.object(skills, 'fetch_json', return_value=data):
            r = skills.answer('Wikipedia search Albert Einstein', 'en')
            self.assertEqual(r['article'], 'Albert Einstein')
            self.assertNotIn('family article', r['text'])

    def test_unrelated_article_is_not_spoken_as_answer(self):
        data = {'query': {'pages': [{'index': 1, 'title': 'Einstein family', 'extract': 'Irrelevant.'}]}}
        with patch.object(skills, 'fetch_json', return_value=data):
            r = skills.answer('Wikipedia search Albert Einstein', 'en')
            self.assertNotIn('Irrelevant', r['text'])
            self.assertIn('could not find', r['text'])

    def test_capital_punishment_never_mistaken_for_a_city(self):
        data = {'query': {'pages': [
            {'index': 1, 'title': 'Capital punishment in France', 'extract': 'Capital punishment in France is banned.'},
            {'index': 2, 'title': 'Paris', 'extract': 'Paris is the capital and largest city of France.'},
        ]}}
        with patch.object(skills, 'fetch_json', return_value=data):
            r = skills.answer('What is the capital of France?', 'en')
            self.assertEqual(r['article'], 'Paris')
            self.assertIn('Paris', r['text'])
            self.assertNotIn('punishment', r['text'])

    def test_capital_does_not_fabricate_when_no_safe_match(self):
        data = {'query': {'pages': [{'index': 1, 'title': 'Capital punishment in France',
                                     'extract': 'Capital punishment in France is banned.'}]}}
        with patch.object(skills, 'fetch_json', return_value=data):
            r = skills.answer('What is the capital of France?', 'en')
            self.assertNotIn('punishment', r['text'])
            self.assertIn('could not find', r['text'])

    def test_capital_other_direct_forms(self):
        match = skills.capital_article_matches
        self.assertTrue(match('capital of japan', 'Capital of Japan', 'The capital of Japan is Tokyo.'))
        self.assertTrue(match('capital of germany', 'Capital of Germany', 'The capital of Germany is the city of Berlin.'))
        self.assertTrue(match('capital of brazil', 'Brasília', 'Brasília (pronounced here) is the capital city of Brazil.'))
        self.assertTrue(match('capital of india', 'New Delhi', 'New Delhi is the capital and a city of India.'))
        self.assertFalse(match('capital of france', 'Capital punishment in France', 'Capital punishment in France is banned.'))
        self.assertFalse(match('capital of france', 'Capital of France', 'Capital punishment in France is banned.'))
        self.assertFalse(match('capital of france', 'Paris', 'Paris is the capital of Germany.'))
        self.assertIsNone(match('capital punishment in france', 'Capital punishment in France', 'Text'))

    def test_title_matching_hindi_and_capital(self):
        self.assertTrue(skills.wiki_title_matches('चंद्रयान', 'चंद्रयान'))
        self.assertTrue(skills.wiki_title_matches('capital of japan', 'Capital of Japan'))
        self.assertFalse(skills.wiki_title_matches('albert einstein', 'Einstein family'))

if __name__ == '__main__': unittest.main()
