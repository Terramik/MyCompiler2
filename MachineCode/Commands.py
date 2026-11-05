from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


__all__ = ('Register', 'CommandABC', 'CommandSTOP', 'CommandPASS', 'CommandALIAS', 'CommandMOVE', 'CommandCOMP', 'TypeOP', 'CommandOP', 'CommandCONST',
           'CommandCONSTWORD', 'CommandCONSTHALF', 'TypeSAVELOAD', 'CommandLOAD', 'CommandSAVE', 'TypeJUMP', 'CommandJUMP', 'CommandLABEL')


@dataclass
class Register:
    i: int


class CommandABC(ABC):
    @property
    @abstractmethod
    def size(self) -> int:
        ...


@dataclass
class CommandSTOP(CommandABC):
    @property
    def size(self) -> int: return 1


@dataclass
class CommandPASS(CommandABC):
    @property
    def size(self) -> int: return 1


@dataclass
class CommandALIAS(CommandABC):
    name: str
    val: Register | int

    @property
    def size(self) -> int: return 0


@dataclass
class CommandMOVE(CommandABC):
    dest: Register
    src: Register

    @property
    def size(self) -> int: return 2


@dataclass
class CommandCOMP(CommandABC):
    src: Register

    @property
    def size(self) -> int: return 2


class TypeOP(Enum):
    Add = 'ADD'
    Add_m = 'ADD_M'
    Sub = 'SUB'
    Neg = 'NEG'
    And = 'AND'
    Or = 'OR'
    Xor = 'XOR'
    Not = 'NOT'
    Shl = 'SHL'
    Shr = 'SHR'


@dataclass
class CommandOP(CommandABC):
    type: TypeOP
    r1: Register
    r2: Register

    @property
    def size(self) -> int: return 2


@dataclass
class CommandCONST(CommandABC):
    dest: Register
    val: int

    def to_word(self):
        return CommandCONSTWORD(self.dest, self.val)

    def to_half(self):
        return CommandCONSTHALF(self.dest, self.val)

    @property
    def size(self) -> int:
        if self.val < 0 or self.val >= 2 ** 16:
            return 8
        return 4

@dataclass
class CommandCONSTWORD(CommandABC):
    dest: Register
    val: int

    @property
    def size(self) -> int: return 8


@dataclass
class CommandCONSTHALF(CommandABC):
    dest: Register
    val: int

    @property
    def size(self) -> int: return 4


class TypeSAVELOAD(Enum):
    Byte = 'BYTE'
    Half = 'HALF'
    Word = 'WORD'


@dataclass
class CommandLOAD(CommandABC):
    type: TypeSAVELOAD
    dest: Register
    src_ptr: Register

    @property
    def size(self) -> int: return 2


@dataclass
class CommandSAVE(CommandABC):
    type: TypeSAVELOAD
    dest_ptr: Register
    src: Register

    @property
    def size(self) -> int: return 2


class TypeJUMP(Enum):
    NO = 'NO'
    CR = 'CR'
    NC = 'NC'
    ZR = 'ZR'
    NZ = 'NZ'
    GT = 'GT'
    GE = 'GE'
    LT = 'LT'
    LE = 'LE'
    IF = 'IF'


@dataclass
class CommandJUMP(CommandABC):
    type: TypeJUMP
    dest: str

    @property
    def size(self) -> int: return 8


@dataclass
class CommandLABEL(CommandABC):
    name: str

    @property
    def size(self) -> int: return 0

