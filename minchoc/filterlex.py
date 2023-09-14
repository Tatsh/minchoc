from typing import Any

from ply import lex

__all__ = ('tokens',)

states = (('string', 'exclusive'),)
tokens = ('AND', 'EQ', 'ISLATESTVERSION', 'LPAREN', 'RPAREN', 'STRING', 'TOLOWER_ID')

t_AND = r'and'
t_EQ = r'eq'
t_ISLATESTVERSION = r'IsLatestVersion'
t_TOLOWER_ID = r'tolower\(Id\)'
t_LPAREN = r'\('
t_RPAREN = r'\)'

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
    t.type = "STRING"
    t.lexer.lineno += t.value.count('\n')
    t.lexer.begin('INITIAL')
    return t


def t_string_error(t: lex.LexToken) -> None:
    # print("illegal character '%s'" % t.value[0])
    t.lexer.skip(1)


lexer = lex.lex()
