from typing import Any

from .lex import LexToken, Lexer


class YaccProduction:
    lexer: Lexer | None

    def __getitem__(self, indices: tuple[int, ...] | int) -> Any:
        ...

    def __setitem__(self, index: int, value: Any) -> None:
        ...

    def __len__(self) -> int:
        ...

    def __getslice__(self, i: int, j: int) -> LexToken:
        ...

    def lineno(self, n: int) -> int:
        ...

    def set_lineno(self, n: int, lineno: int) -> None:
        ...

    def linespan(self, n: int) -> tuple[int, int]:
        ...

    def lexpos(self, n: int) -> int:
        ...

    def set_lexpos(self, n: int, lexpos: int) -> None:
        ...

    def lexspan(self, n: int) -> tuple[int, int]:
        ...

    def error(self) -> None:
        ...


class Parser:
    def parse(self, input: str, debug: bool = ...) -> Any:
        ...


def yacc(debug: bool = ...) -> Parser:
    ...
