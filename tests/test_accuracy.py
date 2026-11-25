"""Regression tests for arithmetic routing and conservative Wikipedia selection."""
import unittest
from unittest.mock import patch
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

    def test_invalid_math_no_eval_or_wikipedia(self):
        for q in ('calculate 5 / 0', 'calculate 2 ** 100', 'calculate 9 + __import__("os")', 'calculate 10 % 3'):
            with self.subTest(q=q), patch.object(skills, 'wiki', side_effect=AssertionError('wrong route')):
                r = skills.answer(q, 'en')
                self.assertEqual(r['source'], 'Calculator')
                self.assertIn('could not calculate', r['text'])

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

    def test_title_matching_hindi_and_capital(self):
        self.assertTrue(skills.wiki_title_matches('चंद्रयान', 'चंद्रयान'))
        self.assertTrue(skills.wiki_title_matches('capital of japan', 'Capital of Japan'))
        self.assertFalse(skills.wiki_title_matches('albert einstein', 'Einstein family'))

if __name__ == '__main__': unittest.main()
