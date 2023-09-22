from typing import Any, Literal

from django.db.models import Q
from ply import yacc
from ply.lex import LexToken

from minchoc.filterlex import tokens  # noqa: F401

__all__ = ('parser',)

FIELD_MAPPING = {'Description': 'description', 'Id': 'nuget_id', 'Tags': 'tags__name'}


def setup_p0(p: yacc.YaccProduction) -> None:
    if not isinstance(p[0], Q):  # pragma no cover
        p[0] = Q()


def p_expression_expr(p: yacc.YaccProduction) -> None:
    """expression : LPAREN expression RPAREN"""
    setup_p0(p)
    p[0] = p[2]


def p_substringof(p: yacc.YaccProduction) -> None:
    """substringof : SUBSTRINGOF LPAREN STRING COMMA expression RPAREN"""
    setup_p0(p)
    a: str
    b: Q
    _, __, ___, a, ____, b, _____ = p
    db_field = b.children[0][0]
    prefix = ''
    if '__iexact' in db_field:
        prefix = 'i'
        db_field = db_field.replace('__iexact', '')
    p[0] &= Q(**{f'{db_field}__{prefix}contains': a})


def p_tolower(p: yacc.YaccProduction) -> None:
    """tolower : TOLOWER LPAREN FIELD RPAREN"""
    setup_p0(p)
    field: Literal['Description', 'Id', 'Tags']
    _, __, ___, field, ____ = p
    p[0] &= Q(**{f'{FIELD_MAPPING[field]}__iexact': None})


def p_expression_field(p: yacc.YaccProduction) -> None:
    """expression : FIELD"""
    setup_p0(p)
    field: Literal['Description', 'Id', 'Tags']
    _, field = p
    p[0] &= Q(**{FIELD_MAPPING[field]: None})


def p_expression_op(p: yacc.YaccProduction) -> None:
    """expression : expression OR expression
                  | expression AND expression
                  | expression NE expression
                  | expression EQ expression"""
    setup_p0(p)
    a: Q
    b: Q | str
    op: Literal['and', 'eq', 'ne', 'or']
    _, a, op, b = p
    if op == 'and':
        p[0] &= a & b
    elif op == 'or':
        p[0] &= a | b
    else:
        db_field: str = a.children[0][0]
        rhs = b.children[0][0] if isinstance(b, Q) else None
        if b == 'null' or rhs == 'rhs__isnull':
            p[0] &= Q(**{f'{db_field}__isnull': False if op == 'ne' else True})
        else:  # eq
            if not isinstance(b, (int, str)):
                raise ValueError('Only numbers and strings can be used with eq.')
            p[0] &= Q(**{db_field: b})


def p_expression_str(p: yacc.YaccProduction) -> None:
    """expression : STRING"""
    setup_p0(p)
    s: str
    _, s = p
    p[0] = s


def p_expression(p: yacc.YaccProduction) -> None:
    """expression : NULL
                  | substringof
                  | tolower
                  | ISLATESTVERSION"""
    setup_p0(p)
    expr: Any
    _, expr = p
    if expr == 'IsLatestVersion':
        p[0] &= Q(is_latest_version=True)
    elif expr == 'null':
        p[0] &= Q(rhs__isnull=True)
    else:
        p[0] &= expr


def p_error(p: LexToken) -> None:
    raise SyntaxError(f'Syntax error (index: {p.lexer.lexpos}, token: "{p.value}")')


parser = yacc.yacc(debug=False)
"""An extremely basic parser for parsing ``$filter`` strings. Returns a ``Q`` instance."""
