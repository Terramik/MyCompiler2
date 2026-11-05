from .Commands import *
from typing import BinaryIO
from typing import Callable


__all__ = ('transfer',)


class TransferContext:

    def __init__(self, code: list[CommandABC]):
        self.code = code
        # Для прыжков
        # сдвиги(от начало программы) до i-той инструкции
        self.offsets: list[int] = []
        # сколько нужно добавить после каждой i-той команды
        self.paddings: list[int] = []
        # метки и их сдвиги
        self.labels: dict[str, int] = {}

        # костыль
        self.current_i: int = -1

        self.calc_offsets()
        self.calc_labels()

    @staticmethod
    def calc_offset(current_offset: int, size: int) -> int:
        """
        Считает необходимый сдвиг для команды указанной длинны
        """
        # для больших самый большой
        if size == 8:
            size = 4
        elif size == 0:
            return 0

        if current_offset % size == 0:
            return 0

        return (current_offset // size + 1) * size - current_offset

    def calc_offsets(self):
        """
        Считает сдвиги команд он начала и друг от друга
        """
        current_offset = 0

        for cmd in self.code:
            size = cmd.size
            offset = self.calc_offset(current_offset, size)

            # расстояние между командами
            self.paddings.append(offset)
            # расстояние от начала
            current_offset += offset
            self.offsets.append(current_offset)
            # для новой итерации, конец текущей команды
            current_offset += size

    def calc_labels(self):
        """
        Считает расстояние от начала до указанных меток и засовывает в удобный словарь
        """
        for i, cmd in enumerate(self.code):
            if isinstance(cmd, CommandLABEL):
                self.labels[cmd.name] = self.offsets[i]

    def calc_jump_dist(self, src: CommandJUMP) -> int:
        """Считает, сколько нужно прыгнуть от команды до её метки"""
        # self.current_i это ужасный костыль, но мне немного лень.

        return self.labels[src.dest] - self.offsets[self.current_i]


class Registrator:
    """Для регистрации обработчиков инструкций, исходя из её класса"""

    def __init__(self):
        self.funcs: dict[type, Callable[[CommandABC, TransferContext], bytes]] = {}

    def register(self, cls: type):

        def dec(f: Callable[[CommandABC, TransferContext], bytes]):
            self.funcs[cls] = f
            return f

        return dec

    def for_cls(self, cls: type) -> Callable[[CommandABC, TransferContext], bytes]:
        assert cls in self.funcs
        return self.funcs[cls]


register = Registrator()


def two_4_bit_to_byte(n1: int | Register, n2: int | Register):
    if isinstance(n1, Register):
        n1 = n1.i
    if isinstance(n2, Register):
        n2 = n2.i
    return bytes([n1 + (n2 << 4)])  # наоборот из-за всяких little-приколов


@register.register(CommandSTOP)
def _(node: CommandSTOP, context: TransferContext):
    return b'\x10'


@register.register(CommandPASS)
def _(node: CommandPASS, context: TransferContext):
    return b'\x11'


@register.register(CommandALIAS)
def _(node: CommandALIAS, context: TransferContext):
    return b''


@register.register(CommandMOVE)
def _(node: CommandMOVE, context: TransferContext):
    return b'\x20' + two_4_bit_to_byte(node.dest, node.src)


@register.register(CommandCOMP)
def _(node: CommandCOMP, context: TransferContext):
    return b'\x21' + two_4_bit_to_byte(node.src, 0)


@register.register(CommandOP)
def _(node: CommandOP, context: TransferContext):
    op: bytes
    match node.type:
        case TypeOP.Add: op = b'\x22'
        case TypeOP.Add_m: op = b'\x23'
        case TypeOP.Sub: op = b'\x24'
        case TypeOP.Neg: op = b'\x25'
        case TypeOP.And: op = b'\x26'
        case TypeOP.Or: op = b'\x27'
        case TypeOP.Xor: op = b'\x28'
        case TypeOP.Not: op = b'\x29'
        case TypeOP.Shl: op = b'\x2a'
        case TypeOP.Shr: op = b'\x2b'
        case _: raise ValueError('Что-то пошло не так')

    return op + two_4_bit_to_byte(node.r1, node.r2)


@register.register(CommandCONSTWORD)
def transfer_const_word(node: CommandCONSTWORD, context: TransferContext):
    return b'\x2c' + two_4_bit_to_byte(node.dest, 0) + b'\x00\x00' + \
        node.val.to_bytes(4, byteorder='little', signed=node.val < 0)


@register.register(CommandCONSTHALF)
def transfer_const_half(node: CommandCONSTHALF, context: TransferContext):
    return b'\x2d' + two_4_bit_to_byte(node.dest, 0) + \
        node.val.to_bytes(2, byteorder='little', signed=node.val < 0)


@register.register(CommandCONST)
def transfer_const(node: CommandCONST, context: TransferContext):
    if node.size == 8:
        return transfer_const_word(node.to_word(), context)
    return transfer_const_half(node.to_half(), context)


@register.register(CommandLOAD)
def _(node: CommandLOAD, context: TransferContext):
    op: bytes
    match node.type:
        case TypeSAVELOAD.Byte: op = b'\x30'
        case TypeSAVELOAD.Half: op = b'\x31'
        case TypeSAVELOAD.Word: op = b'\x32'
        case _: raise ValueError('Что-то пошло не так')
    return op + two_4_bit_to_byte(node.dest, node.src_ptr)


@register.register(CommandSAVE)
def _(node: CommandSAVE, context: TransferContext):
    op: bytes
    match node.type:
        case TypeSAVELOAD.Byte: op = b'\x33'
        case TypeSAVELOAD.Half: op = b'\x34'
        case TypeSAVELOAD.Word: op = b'\x35'
        case _: raise ValueError('Что-то пошло не так')
    return op + two_4_bit_to_byte(node.dest_ptr, node.src)


@register.register(CommandJUMP)
def _(node: CommandJUMP, context: TransferContext):
    match node.type:
        case TypeJUMP.NO: op = b'\x40'
        case TypeJUMP.CR: op = b'\x41'
        case TypeJUMP.NC: op = b'\x42'
        case TypeJUMP.ZR: op = b'\x43'
        case TypeJUMP.NZ: op = b'\x44'
        case TypeJUMP.GT: op = b'\x45'
        case TypeJUMP.GE: op = b'\x46'
        case TypeJUMP.LT: op = b'\x47'
        case TypeJUMP.LE: op = b'\x48'
        case TypeJUMP.IF: op = b'\x49'
        case _: raise ValueError('Что-то пошло не так')

    return op + b'\x00\x00\x00' + \
        context.calc_jump_dist(node).to_bytes(4, byteorder='little', signed=True)


@register.register(CommandLABEL)
def _(node: CommandLABEL, context: TransferContext):
    return b''


def transfer(code: list[CommandABC], dest: BinaryIO):
    context = TransferContext(code)

    for i, cmd in enumerate(code):
        context.current_i = i  # костылизация
        dest.write(
            b'\x11' * context.paddings[i] +  # выравнивание для команды(заполняем PASS)
            register.for_cls(type(cmd))(cmd, context)  # сама команда
        )


