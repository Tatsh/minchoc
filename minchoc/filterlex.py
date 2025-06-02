"""Lexer."""
# ruff: noqa: D300,D400,N816
from __future__ import annotations

from typing import Any

from ply import lex

__all__ = ('tokens',)

states = (('string', 'exclusive'),)
tokens = ('AND', 'COMMA', 'EQ', 'FIELD', 'ISLATESTVERSION', 'LPAREN', 'NE', 'NULL', 'OR', 'RPAREN',
          'STRING', 'SUBSTRINGOF', 'TOLOWER')

t_AND = r'and'
t_COMMA = r','
t_EQ = r'eq'
t_FIELD = r'Description|Id|Tags'
t_ISLATESTVERSION = r'IsLatestVersion'
t_LPAREN = r'\('
t_NE = r'ne'
t_NULL = r'null'
t_OR = r'or'
t_RPAREN = r'\)'
t_SUBSTRINGOF = r'substringof'
t_TOLOWER = r'tolower'

t_ignore = ' '
t_string_ignore = ' '


def t_error(t: Any) -> None:
    t.lexer.skip(1)


def t_string(t: lex.LexToken) -> None:
    r"'"
    t.lexer.code_start = t.lexer.lexpos
    t.lexer.begin('string')


def t_string_escapedquote(_t: lex.LexToken) -> None:
    r"\\'"
    # Do nothing


def t_string_quote(t: lex.LexToken) -> lex.LexToken:
    r"'"
    t.value = t.lexer.lexdata[t.lexer.code_start:t.lexer.lexpos - 1]
    t.type = 'STRING'
    t.lexer.lineno += t.value.count('\n')
    t.lexer.begin('INITIAL')
    return t


def t_string_error(t: lex.LexToken) -> None:
    # print("illegal character '%s'" % t.value[0])  # noqa: ERA001
    t.lexer.skip(1)


lexer = lex.lex()
