from dataclasses import dataclass


__all__ = ('TextPosition', 'TextRange')


@dataclass
class TextPosition:
    row: int
    col: int


@dataclass
class TextRange:
    start: TextPosition
    end: TextPosition

