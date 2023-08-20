from typing import Any

class YaccProduction:
    def __getitem__(self, indices: tuple[int, ...] | int) -> Any:
        ...

    def __setitem__(self, index: int, value: Any) -> None:
        ...


class Parser:
    def parse(self, input: str) -> Any:
        ...


def yacc(debug: bool = ...) -> Parser:
    ...
