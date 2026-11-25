"""Small, deterministic arithmetic parser; never evaluates user-supplied code."""

import ast
import re
import unicodedata
from decimal import Decimal, DivisionByZero, InvalidOperation, localcontext

_LIMIT = Decimal('1000000000000')


def calculate(query):
    """Return (handled, text). Unsupported input is never passed to eval()."""
    q = ''.join(str(unicodedata.decimal(c)) if c.isdecimal() else c for c in query.casefold())
    q = ' '.join(q.strip(' ?!.।').split())
    # A deliberately narrow, predictable word problem; don't guess at other stories.
    dozen = re.fullmatch(r'(?:अगर )?एक दर्जन में 12 अंडे हैं,? तो (\d{1,7}) दर्जन में कितने अंडे होंगे', q)
    if dozen:
        n = int(dozen.group(1))
        return True, str(n * 12)
    s = re.sub(r'^(?:please\s+)?(?:what is|what\'s|calculate|compute|solve|कितना है|गणना करो)\s+', '', q)
    s = re.sub(r'\s+(?:कितना है|कितने हैं|क्या है|बताओ|calculate)$', '', s)
    for pattern, replacement in [
        (r'\bmultiplied by\b|\btimes\b|\bmultiply by\b|गुणा', '*'),
        (r'\bdivided by\b|भाग', '/'),
        (r'\bplus\b|जोड़', '+'),
        (r'\bminus\b|घटाओ', '-'),
        (r'(?<=\d)\s*[x×]\s*(?=\d)', '*'),
    ]:
        s = re.sub(pattern, replacement, s)
    s = s.replace('÷', '/').strip()
    intent = bool(re.search(r'\d', q) and re.search(
        r'\b(?:calculate|compute|solve|multiplied|multiply|times|divided|plus|minus)\b|[+*/×÷%]|गुणा|भाग|जोड़|घटाओ', q))
    if not re.fullmatch(r'[0-9.()+*/\s-]+', s) or not re.search(r'[+*/-]', s) or len(s) > 120:
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
            elif isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
                a, b = evaluate(node.left), evaluate(node.right)
                if isinstance(node.op, ast.Add): value = a + b
                elif isinstance(node.op, ast.Sub): value = a - b
                elif isinstance(node.op, ast.Mult): value = a * b
                else: value = a / b
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
