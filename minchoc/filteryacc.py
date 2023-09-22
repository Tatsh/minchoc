from typing import Any, Literal

from ply import yacc
from ply.lex import LexToken

from minchoc.filterlex import tokens  # noqa: F401

__all__ = ('parser',)

FIELD_MAPPING = {'Description': 'description', 'Id': 'nuget_id'}
FUNC_MAPPING = {'substringof': 'contains', 'tolower': 'iexact'}


def setup_p0(p: yacc.YaccProduction) -> None:
    if not isinstance(p[0], dict):
        p[0] = {}


def p_expression_expr(p: yacc.YaccProduction) -> None:
    """expression : LPAREN expression RPAREN"""
    setup_p0(p)
    p[0] = p[2]


def p_substringof(p: yacc.YaccProduction) -> None:
    """substringof : SUBSTRINGOF LPAREN expression COMMA expression RPAREN"""
    setup_p0(p)
    a: Any
    b: Any
    res: Any
    res, _, __, a, ___, b, ____ = p
    if 'substringof' not in res:
        res['substringof'] = []
    res['substringof'].extend([a, b])


def p_tolower(p: yacc.YaccProduction) -> None:
    """tolower : TOLOWER LPAREN expression RPAREN"""
    setup_p0(p)
    expr: Any
    res: Any
    res, _, __, expr, ___ = p
    if 'tolower' not in res:
        res['tolower'] = []
    res['tolower'].append(expr)


def p_expression_field(p: yacc.YaccProduction) -> None:
    """expression : FIELD"""
    setup_p0(p)
    field: Literal['Id', 'Description', 'Tags']
    res: Any
    res, field = p
    if 'fields' not in res:
        res['fields'] = []
    res['fields'].append(field)


def p_expression_op(p: yacc.YaccProduction) -> None:
    """expression : expression OR expression
                  | expression AND expression
                  | expression NE expression
                  | expression EQ expression"""
    setup_p0(p)
    a: Any
    b: Any
    op: Literal['and', 'eq', 'ne', 'or']
    res: Any
    res, a, op, b = p
    if op not in res:
        res[op] = []
    res[op].extend([a, b])


def p_expression_str(p: yacc.YaccProduction) -> None:
    """expression : STRING"""
    setup_p0(p)
    expr: Any
    res: Any
    res, expr = p
    if 'strings' not in res:
        res['strings'] = []
    res['strings'].append(f'"{expr}"')


def p_expression(p: yacc.YaccProduction) -> None:
    """expression : NULL
                  | substringof
                  | tolower
                  | ISLATESTVERSION"""
    setup_p0(p)
    expr: Any
    res: Any
    res, expr = p
    if 'expressions' not in res:
        res['expressions'] = []
    res['expressions'].append(None if expr == 'null' else expr)


def p_error(p: LexToken) -> None:
    raise SyntaxError(f'Syntax error (index: {p.lexer.lexpos}, token: "{p.value}")')


parser = yacc.yacc(debug=False)
"""An extremely basic parser for parsing ``$filter`` strings."""

# if __name__ == '__main__':
#     terms = 'cat'
#     filter_str = (f"((((Id ne null) and substringof('{terms}',tolower(Id))) or "
#                   f"((Description ne null) and substringof('{terms}',tolower(Description))))"
#                   f" or ((Tags ne null) and substringof(' {terms} ',tolower(Tags)))) "
#                   "and IsLatestVersion")
#     print(json.dumps({'$filter': filter_str, 'output': parser.parse(filter_str)}, sort_keys=True))
