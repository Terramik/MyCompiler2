from ..Src.Lexer import lex
from ..Src.Parser import parse
from ...MachineCode.Commands import *
from io import StringIO
import pytest


def r(i: int): return Register(i)


@pytest.mark.parametrize(['code', 'expected'], [
    pytest.param('''
            STOP; STOP
            STOP
        ''', [
            CommandSTOP(),
            CommandSTOP(),
            CommandSTOP(),
        ],
        id='STOP'
    ),
    pytest.param('''
            PASS
        ''', [
            CommandPASS(),
        ],
        id='PASS'
    ),
    pytest.param('''
            ALIAS answer_to_question_of_life_and_everything 42
        ''', [
            CommandALIAS('answer_to_question_of_life_and_everything', 42),
        ],
        id='ALIAS'
    ),
    pytest.param('''
            MOVE r1 r9
        ''', [
            CommandMOVE(r(1), r(9)),
        ],
        id='MOVE'
    ),
    pytest.param('''
            COMP r4
        ''', [
            CommandCOMP(r(4)),
        ],
        id='COMP'
    ),
    pytest.param('''
            OP ADD r1 r3
            OP ADD_M r5 r0
            OP SUB r7 r5
            OP NEG r1 r13
            OP AND r5 r15
            OP OR r7 r1
            OP XOR r1 r10
            OP NOT r4 r3
            OP SHL r6 r14
            OP SHR r2 r6
        ''', [
            CommandOP(TypeOP.Add, r(1), r(3)),
            CommandOP(TypeOP.Add_m, r(5), r(0)),
            CommandOP(TypeOP.Sub, r(7), r(5)),
            CommandOP(TypeOP.Neg, r(1), r(13)),
            CommandOP(TypeOP.And, r(5), r(15)),
            CommandOP(TypeOP.Or, r(7), r(1)),
            CommandOP(TypeOP.Xor, r(1), r(10)),
            CommandOP(TypeOP.Not, r(4), r(3)),
            CommandOP(TypeOP.Shl, r(6), r(14)),
            CommandOP(TypeOP.Shr, r(2), r(6)),
        ],
        id='OP'
    ),
    pytest.param('''
            CONST r0 0xff
        ''', [
            CommandCONST(r(0), 0xff),
        ],
        id='CONST'
    ),
    pytest.param('''
            ALIAS answer 42
            CONST_HALF r1 answer
        ''', [
            CommandALIAS('answer', 42),
            CommandCONSTHALF(r(1), 42),
        ],
        id='CONST_HALF'
    ),
    pytest.param('''
            CONST_WORD r2 -1
        ''', [
            CommandCONSTWORD(r(2), -1),
        ],
        id='CONST_WORD'
    ),
    pytest.param('''
            LOAD BYTE r1 r2
            LOAD HALF r5 r9
            LOAD WORD r5 r6
        ''', [
            CommandLOAD(TypeSAVELOAD.Byte, r(1), r(2)),
            CommandLOAD(TypeSAVELOAD.Half, r(5), r(9)),
            CommandLOAD(TypeSAVELOAD.Word, r(5), r(6)),
        ],
        id='LOAD'
    ),
    pytest.param('''
            SAVE BYTE r2 r1 
            SAVE HALF r9 r5 
            SAVE WORD r6 r5 
        ''', [
            CommandSAVE(TypeSAVELOAD.Byte, r(2), r(1)),
            CommandSAVE(TypeSAVELOAD.Half, r(9), r(5)),
            CommandSAVE(TypeSAVELOAD.Word, r(6), r(5)),
        ],
        id='SAVE'
    ),
    pytest.param('''
            LABEL lol
        ''', [
            CommandLABEL('lol')
        ],
        id='LABEL'
    ),
    pytest.param('''
            LABEL start
            JUMP NO end
            JUMP CR start
            JUMP NC start
            JUMP ZR end
            JUMP NZ end
            JUMP GT start
            JUMP GE end
            JUMP LT start
            JUMP LE end
            JUMP IF start
            LABEL end
        ''', [
            CommandLABEL('start'),
            CommandJUMP(TypeJUMP.NO, 'end'),
            CommandJUMP(TypeJUMP.CR, 'start'),
            CommandJUMP(TypeJUMP.NC, 'start'),
            CommandJUMP(TypeJUMP.ZR, 'end'),
            CommandJUMP(TypeJUMP.NZ, 'end'),
            CommandJUMP(TypeJUMP.GT, 'start'),
            CommandJUMP(TypeJUMP.GE, 'end'),
            CommandJUMP(TypeJUMP.LT, 'start'),
            CommandJUMP(TypeJUMP.LE, 'end'),
            CommandJUMP(TypeJUMP.IF, 'start'),
            CommandLABEL('end'),
        ],
        id='JUMP'
    ),
])
def test_1(code: str, expected: list[CommandABC]):
    have = parse(lex(StringIO(code)))
    assert have == expected

