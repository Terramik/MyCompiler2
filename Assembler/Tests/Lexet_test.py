from abc import ABC, abstractmethod
from dataclasses import dataclass
from ..Defines.Tokens import *
from ..Src.Lexer import lex
from io import StringIO
import pytest


class CheckTokenABC(ABC):
    @abstractmethod
    def check(self, token: TokenABC):
        ...


@dataclass
class CheckTokenWord(CheckTokenABC):
    word: str

    def check(self, token: TokenWord):
        assert isinstance(token, TokenWord)
        assert self.word == token.word


@dataclass
class CheckTokenLiteral(CheckTokenABC):
    literal: str

    def check(self, token: TokenLiteral):
        assert isinstance(token, TokenLiteral)
        assert self.literal == token.literal


@dataclass
class CheckTokenDivider(CheckTokenABC):
    def check(self, token: TokenDivider):
        assert isinstance(token, TokenDivider)


def test_1():
    src = StringIO('''
    conST r1 100; python
    # commentary
    
    c 42
    ''')
    need = [
        CheckTokenWord('conST'),
        CheckTokenLiteral('r1'),
        CheckTokenLiteral('100'),
        CheckTokenDivider(),
        CheckTokenWord('python'),
        CheckTokenDivider(),
        CheckTokenWord('c'),
        CheckTokenLiteral('42'),
        CheckTokenDivider(),
    ]
    have = lex(src)

    assert len(need) == len(have)
    for n, h in zip(need, have):
        n.check(h)

