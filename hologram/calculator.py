"""Small, deterministic arithmetic parser; never evaluates user-supplied code."""

import ast
import re
import unicodedata
from decimal import Decimal, DivisionByZero, InvalidOperation, localcontext

_LIMIT = Decimal('1000000000000')

# Common short forms returned by Hindi/English speech recognition. Do not try
# to infer arbitrary long number phrases: unsupported input should fail closed.
_SPOKEN_NUMBERS = {
    'शून्य': 0, 'जीरो': 0, 'zero': 0,
    'एक': 1, 'दो': 2, 'तीन': 3, 'चार': 4, 'पांच': 5, 'पाँच': 5,
    'छह': 6, 'सात': 7, 'आठ': 8, 'नौ': 9, 'दस': 10,
    'ग्यारह': 11, 'बारह': 12, 'तेरह': 13, 'चौदह': 14, 'पंद्रह': 15,
    'पन्द्रह': 15, 'सोलह': 16, 'सत्रह': 17, 'सतरह': 17, 'अठारह': 18,
    'उन्नीस': 19, 'बीस': 20, 'इक्कीस': 21, 'बाईस': 22, 'तेईस': 23,
    'तेइस': 23, 'चौबीस': 24, 'पच्चीस': 25, 'छब्बीस': 26, 'सत्ताईस': 27,
    'अट्ठाईस': 28, 'उनतीस': 29, 'तीस': 30,
    'satrah': 17, 'satarah': 17, 'satra': 17, 'teis': 23, 'teees': 23,
    'teiss': 23,
}


def calculate(query):
    """Return (handled, text). Unsupported input is never passed to eval()."""
    q = ''.join(str(unicodedata.decimal(c)) if c.isdecimal() else c for c in query.casefold())
    q = ' '.join(q.strip(' ?!.।').split())
    # A deliberately narrow, predictable word problem; don't guess at other stories.
    dozen = re.fullmatch(r'(?:अगर )?एक दर्जन में 12 अंडे हैं,? तो (\d{1,7}) दर्जन में कितने अंडे होंगे', q)
    if dozen:
        n = int(dozen.group(1))
        return True, str(n * 12)
    math_words = re.search(r'(?<!\w)(?:गुणा|गुना|guna|gunaa|गुने|gunay|times|multiplied|divided|plus|minus|modulo|mod|भाग|जोड़|घटाओ)(?!\w)|[+*/×÷%]', q, re.I)
    if math_words:
        q = re.sub(r'((?:करो|कर|karo|kar))\s+(?:दो|do)$', r'\1', q)
        q = ' '.join(str(_SPOKEN_NUMBERS.get(word, word)) for word in q.split())
    # A common natural Hindi construction: 17 ko 23 se guna karo.
    natural = re.fullmatch(r'(\d+(?:\.\d+)?)\s+(?:को|ko)\s+(\d+(?:\.\d+)?)\s+(?:से|se)\s+(?:गुणा|गुना|guna|gunaa)\s+(?:करो|कर|karo|kar)(?:\s+(?:दो|do))?', q)
    if natural:
        q = natural.group(1) + ' * ' + natural.group(2)
    s = re.sub(r'^(?:please\s+)?(?:what is|what\'s|calculate|compute|solve|कितना है|गणना करो)\s+', '', q)
    s = re.sub(r'\s+(?:कितना है|कितना होता है|कितना होगा|कितने हैं|क्या है|क्या होगा|बताओ|kitna hai|kitna hota hai|kitna hoga|calculate)$', '', s)
    for pattern, replacement in [
        (r'\bmultiplied by\b|\btimes\b|\bmultiply by\b|\bguna\b|\bgunaa\b|\bgunay\b|गुणा|गुना|गुने', '*'),
        (r'\bdivided by\b|भाग', '/'),
        (r'\bplus\b|जोड़', '+'),
        (r'\bminus\b|घटाओ', '-'),
        (r'\bmodulo\b|\bmod\b', '%'),
        (r'(?<=\d)\s*[x×]\s*(?=\d)', '*'),
    ]:
        s = re.sub(pattern, replacement, s)
    s = s.replace('÷', '/').strip()
    intent = bool(re.search(r'\d', q) and re.search(
        r'\b(?:calculate|compute|solve|multiplied|multiply|times|divided|plus|minus|modulo|mod)\b|[+*/×÷%]|गुणा|गुना|गुने|\bguna\b|\bgunaa\b|\bgunay\b|भाग|जोड़|घटाओ', q))
    if not re.fullmatch(r'[0-9.()+*/%\s-]+', s) or not re.search(r'[+*/%\-]', s) or len(s) > 120:
        return (True, None) if intent else (False, None)
    try:
        tree = ast.parse(s, mode='eval')
        nodes = list(ast.walk(tree))
        if len(nodes) > 50:
            raise ValueError('expression too long')
        def evaluate(node):
            if isinstance(node, ast.Constant) and type(node.value) in (int, float):
                literal = ast.get_source_segment(s, node)
                if literal is None or not re.fullmatch(r'\d+(?:\.\d+)?', literal) or len(literal) > 16:
                    raise ValueError('invalid number')
                value = Decimal(literal)
            elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
                value = evaluate(node.operand)
                if isinstance(node.op, ast.USub):
                    value = -value
            elif isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod)):
                a, b = evaluate(node.left), evaluate(node.right)
                if isinstance(node.op, ast.Add): value = a + b
                elif isinstance(node.op, ast.Sub): value = a - b
                elif isinstance(node.op, ast.Mult): value = a * b
                elif isinstance(node.op, ast.Div): value = a / b
                else:
                    # Remainder follows Python floor-mod semantics, only for
                    # integers; decimal percentages are too ambiguous.
                    if a != a.to_integral_value() or b != b.to_integral_value():
                        raise ValueError('integer modulo only')
                    if not b:
                        raise ZeroDivisionError('modulo by zero')
                    value = Decimal(int(a) % int(b))
            else:
                raise ValueError('unsupported operation')
            if not value.is_finite() or abs(value) > _LIMIT:
                raise ValueError('out of range')
            return value
        with localcontext() as ctx:
            ctx.prec = 28
            result = evaluate(tree.body)
            with localcontext() as display:
                display.prec = 10
                shown = +result
            text = format(shown, 'f')
            if len(text) > 60:
                raise ValueError('result too small to display')
            return True, ('~' if shown != result else '') + text
    except (SyntaxError, ValueError, InvalidOperation, DivisionByZero, ZeroDivisionError, RecursionError):
        return True, None
