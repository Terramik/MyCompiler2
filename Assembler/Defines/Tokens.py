from abc import ABC
from dataclasses import dataclass
from .Base import *
import re


__all__ = ('TokenABC', 'TokenWord', 'TokenLiteral', 'TokenDivider')


class TokenABC(ABC):
    origin: TextRange


@dataclass
class TokenWord(TokenABC):
    word: str
    origin: TextRange

    REGEXP = re.compile(r'\s*([a-z_][a-z_0-9]*)', re.IGNORECASE)


@dataclass
class TokenLiteral(TokenABC):
    literal: str
    origin: TextRange

    REGEXP_REG = re.compile(r'\s*r(\d+)', re.IGNORECASE)
    REGEXP_INT = re.compile(r'\s*(-?(0b[01]+|0x[0-9a-f]+|\d+))', re.IGNORECASE)
    REGEXP = re.compile(r'\s*(-?(0b[01]+|0x[0-9a-f]+|\d+)|r\d+)', re.IGNORECASE)


@dataclass
class TokenDivider(TokenABC):
    origin: TextRange

    REGEXP = re.compile(r'\s*(;)', re.IGNORECASE)

