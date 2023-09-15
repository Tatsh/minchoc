from typing import Any, cast

from ply import yacc
from ply.lex import LexToken

from minchoc.filterlex import tokens  # noqa: F401

__all__ = ('parser',)


def dict_if_not_dict(p: yacc.YaccProduction, index: int) -> dict[Any, Any]:
    try:
        if not isinstance(p[index], dict):
            return {}
        return cast(dict[Any, Any], p[index])
    except IndexError:
        return {}


def p_expression(p: yacc.YaccProduction) -> None:
    """
    expression : expression AND expression
               | LPAREN expression RPAREN
    """
    p[0] = {
        **dict_if_not_dict(p, 0),
        **dict_if_not_dict(p, 1),
        **dict_if_not_dict(p, 2),
        **dict_if_not_dict(p, 3)
    }


def p_islatestversion(p: yacc.YaccProduction) -> None:
    """expression : ISLATESTVERSION"""
    p[0] = {
        **dict_if_not_dict(p, 0),
        **dict_if_not_dict(p, 1),
        **dict_if_not_dict(p, 2), 'is_latest_version': True
    }


def p_tolower_id_eq_package(p: yacc.YaccProduction) -> None:
    """expression : TOLOWER_ID EQ STRING"""
    p[0] = {
        **dict_if_not_dict(p, 0),
        **dict_if_not_dict(p, 1),
        **dict_if_not_dict(p, 2), 'nuget_id__iexact': p[3]
    }


def p_error(p: LexToken) -> None:
    raise SyntaxError('Syntax error in input')


#: An extremely basic parser for parsing ``$filter`` strings.
parser = yacc.yacc(debug=False)
