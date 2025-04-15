# ruff: noqa: E303,I001
from typing import Any


class Lexer:
    code_start: int
    lexpos: int
    lineno: int
    lexdata: Any

    def begin(self, name: str) -> None:
        ...

    def skip(self, n: int) -> None:
        ...


class LexToken:
    lexer: Lexer
    type: Any
    value: Any


def lex(debug: bool = ...) -> Lexer:
    ...
