from .Transfer import transfer
from .Commands import *
from io import BytesIO
import pytest


def assemble(code: list[CommandABC]) -> bytes:
    dest = BytesIO()
    transfer(code, dest)
    return dest.getvalue()


@pytest.mark.parametrize(['code', 'expected'], [
    ([CommandSTOP()], b'\x10'),
    ([CommandPASS()], b'\x11'),
    ([CommandSTOP(), CommandSTOP(), CommandSTOP()], b'\x10\x10\x10'),
])
def test_simple(code, expected):
    assert assemble(code) == expected


@pytest.mark.parametrize(['dest_reg', 'src_reg', 'expected'], [
    (0, 0, b'\x20\x00'),
    (1, 2, b'\x20\x21'),
    (15, 15, b'\x20\xff'),
])
def test_move(dest_reg, src_reg, expected):
    code = [CommandMOVE(Register(dest_reg), Register(src_reg))]
    assert assemble(code) == expected


@pytest.mark.parametrize(['src_reg', 'expected'], [
    (0, b'\x21\x00'),
    (3, b'\x21\x03'),
    (15, b'\x21\x0f'),
])
def test_comp(src_reg, expected):
    code = [CommandCOMP(Register(src_reg))]
    assert assemble(code) == expected


op_cases = [
    (TypeOP.Add, b'\x22'),
    (TypeOP.Add_m, b'\x23'),
    (TypeOP.Sub, b'\x24'),
    (TypeOP.Neg, b'\x25'),
    (TypeOP.And, b'\x26'),
    (TypeOP.Or, b'\x27'),
    (TypeOP.Xor, b'\x28'),
    (TypeOP.Not, b'\x29'),
    (TypeOP.Shl, b'\x2a'),
    (TypeOP.Shr, b'\x2b'),
]

@pytest.mark.parametrize(['op_type', 'opcode'], op_cases)
def test_op(op_type, opcode):
    code = [CommandOP(op_type, Register(1), Register(2))]
    expected = opcode + b'\x21'
    assert assemble(code) == expected


@pytest.mark.parametrize(['dest_reg', 'val', 'expected'], [
    (1, 0x12345678, b'\x2c\x01\x00\x00\x78\x56\x34\x12'),
    (2, 0, b'\x2c\x02\x00\x00\x00\x00\x00\x00'),
    (3, -1, b'\x2c\x03\x00\x00\xff\xff\xff\xff'),
    (4, -0x12345678, b'\x2c\x04\x00\x00' + (-0x12345678).to_bytes(4, 'little', signed=True)),
])
def test_const_word(dest_reg, val, expected):
    code = [CommandCONSTWORD(Register(dest_reg), val)]
    assert assemble(code) == expected


@pytest.mark.parametrize(['dest_reg', 'val', 'expected'], [
    (1, 0x1234, b'\x2d\x01\x34\x12'),
    (2, 0, b'\x2d\x02\x00\x00'),
    (3, -1, b'\x2d\x03\xff\xff'),
])
def test_const_half(dest_reg, val, expected):
    code = [CommandCONSTHALF(Register(dest_reg), val)]
    assert assemble(code) == expected


@pytest.mark.parametrize(['dest_reg', 'val', 'expected'], [
    (1, 0x12, b'\x2d\x01\x12\x00'),
    (2, 0x1234, b'\x2d\x02\x34\x12'),
    (3, 0x10000, b'\x2c\x03\x00\x00\x00\x00\x01\x00'),
    (4, -1, b'\x2c\x04\x00\x00\xff\xff\xff\xff'),
])
def test_const_auto(dest_reg, val, expected):
    code = [CommandCONST(Register(dest_reg), val)]
    assert assemble(code) == expected


load_cases = [
    (TypeSAVELOAD.Byte, b'\x30'),
    (TypeSAVELOAD.Half, b'\x31'),
    (TypeSAVELOAD.Word, b'\x32'),
]

@pytest.mark.parametrize(['load_type', 'opcode'], load_cases)
def test_load(load_type, opcode):
    code = [CommandLOAD(load_type, Register(1), Register(2))]
    expected = opcode + b'\x21'
    assert assemble(code) == expected


save_cases = [
    (TypeSAVELOAD.Byte, b'\x33'),
    (TypeSAVELOAD.Half, b'\x34'),
    (TypeSAVELOAD.Word, b'\x35'),
]

@pytest.mark.parametrize(['save_type', 'opcode'], save_cases)
def test_save(save_type, opcode):
    code = [CommandSAVE(save_type, Register(1), Register(2))]
    expected = opcode + b'\x21'
    assert assemble(code) == expected


def test_alias_no_output():
    code = [CommandALIAS('x', Register(1)), CommandSTOP()]
    assert assemble(code) == b'\x10'


def test_label_no_output():
    code = [CommandLABEL('start'), CommandSTOP()]
    assert assemble(code) == b'\x10'


def test_alignment_move():
    code = [CommandSTOP(), CommandMOVE(Register(1), Register(2))]
    expected = b'\x10' + b'\x11' + b'\x20\x21'
    assert assemble(code) == expected


def test_alignment_consthalf():
    code = [CommandPASS(), CommandCONSTHALF(Register(1), 0x1234)]
    expected = b'\x11' + b'\x11' * 3 + b'\x2d\x01\x34\x12'
    assert assemble(code) == expected


def test_alignment_constword():
    code = [CommandPASS(), CommandCONSTWORD(Register(1), 0x12345678)]
    expected = b'\x11' + b'\x11' * 3 + b'\x2c\x01\x00\x00\x78\x56\x34\x12'
    assert assemble(code) == expected


def test_jump_forward():
    code = [
        CommandJUMP(TypeJUMP.NO, 'label'),
        CommandLABEL('label'),
        CommandSTOP(),
    ]
    expected = b'\x40\x00\x00\x00' + (8).to_bytes(4, 'little') + b'\x10'
    assert assemble(code) == expected


def test_jump_backward():
    code = [
        CommandLABEL('start'),
        CommandSTOP(),
        CommandJUMP(TypeJUMP.NO, 'start'),
    ]
    expected = b'\x10' + b'\x11' * 3 + b'\x40\x00\x00\x00' + \
               (-4).to_bytes(4, 'little', signed=True)
    assert assemble(code) == expected


jump_cases = [
    (TypeJUMP.NO, b'\x40'),
    (TypeJUMP.CR, b'\x41'),
    (TypeJUMP.NC, b'\x42'),
    (TypeJUMP.ZR, b'\x43'),
    (TypeJUMP.NZ, b'\x44'),
    (TypeJUMP.GT, b'\x45'),
    (TypeJUMP.GE, b'\x46'),
    (TypeJUMP.LT, b'\x47'),
    (TypeJUMP.LE, b'\x48'),
    (TypeJUMP.IF, b'\x49'),
]

@pytest.mark.parametrize(['jump_type', 'opcode'], jump_cases)
def test_jump_types(jump_type, opcode):
    code = [
        CommandJUMP(jump_type, 'label'),
        CommandLABEL('label'),
        CommandSTOP(),
    ]
    expected = opcode + b'\x00\x00\x00' + (8).to_bytes(4, 'little') + b'\x10'
    assert assemble(code) == expected