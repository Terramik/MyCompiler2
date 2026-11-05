from __future__ import annotations
from ..Defines.Base import *
from ..Defines.Tokens import *
from ...MachineCode.Commands import *
from dataclasses import dataclass
from typing import Callable
from abc import ABC, abstractmethod
import re


__all__ = ('parse',)


class Processor:
    """
    Сам парсер, должен из ряда простых токенов делать ряд готовых к трансляции команд.
    """

    class ParseDataABC(ABC):
        """
        Для хранения информации о том, как обрабатывать аргументы той или иной команды
        """

        @abstractmethod
        def process(self, proc: Processor, data: list[TokenABC]) -> CommandABC:
            pass

    @dataclass
    class ParseDataUsual(ParseDataABC):
        class DataABC(ABC):
            """Содержатель информации того, что нужно"""

            @abstractmethod
            def process(self, proc: Processor, token: TokenABC):
                pass

        class DataReg(DataABC):
            def process(self, proc: Processor, token: TokenABC):
                return proc.get_reg(token)

        class DataInt(DataABC):
            def process(self, proc: Processor, token: TokenABC):
                return proc.get_int(token)

        class DataStr(DataABC):
            def process(self, proc: Processor, token: TokenABC):
                return proc.get_str(token)

        @dataclass
        class DataEnum(DataABC):
            enum_cls: type

            def process(self, proc: Processor, token: TokenABC):
                return proc.get_enum(token, self.enum_cls)

        cls: type
        data: list[DataABC]

        def process(self, proc: Processor, data: list[TokenABC]) -> CommandABC:
            if len(data) - 1 != len(self.data):
                raise ValueError(f'Ожидалось {len(self.data)} аргументов: {data[0].origin}')
            # применяем все это дело
            res = self.cls(
                *[exp.process(proc, tok) for exp, tok in zip(self.data, data[1:])]
            )
            # костыль для гаранта
            assert isinstance(res, CommandABC)
            return res


    @dataclass
    class ParseDataSpecial(ParseDataABC):
        cls: type
        data: Callable[[Processor, list[TokenABC]], CommandABC]

        def process(self, proc: Processor, data: list[TokenABC]) -> CommandABC:
            return self.data(proc, data)

    def add(self, name: str, data: ParseDataABC):
        self.processors[name] = data

    def __init__(self):
        # чтобы не писать много букв
        PDU = Processor.ParseDataUsual
        PDUI = PDU.DataInt()
        PDUR = PDU.DataReg()
        PDUS = PDU.DataStr()
        PDUE = PDU.DataEnum
        PDS = Processor.ParseDataSpecial

        self.processors: dict[str, Processor.ParseDataABC] = {}
        self.aliases: dict[str, Register | int] = {}
        # для проверок
        self.all_labels: set[str] = set()
        # костыль, для проверки того, что прыжки прыгают к меткам, что существуют,
        # и сделаем мы это в конце, чтобы все метки были обнаружены
        self.jump_dest_to_check: list[tuple[str, TextRange]] = []

        # регистрация процессоров для команд
        self.add('STOP', PDU(CommandSTOP, []))
        self.add('PASS', PDU(CommandPASS, []))
        self.add('ALIAS', PDS(CommandALIAS, Processor.spec_command_alias))
        self.add('MOVE', PDU(CommandMOVE, [PDUR, PDUR]))
        self.add('COMP', PDU(CommandCOMP, [PDUR]))
        self.add('OP', PDU(CommandOP, [PDUE(TypeOP), PDUR, PDUR]))
        self.add('CONST', PDS(CommandCONST, Processor.spec_command_const))
        self.add('CONST_WORD', PDS(CommandCONSTWORD, Processor.spec_command_const_word))
        self.add('CONST_HALF', PDS(CommandCONSTHALF, Processor.spec_command_const_half))
        self.add('LOAD', PDU(CommandLOAD, [PDUE(TypeSAVELOAD), PDUR, PDUR]))
        self.add('SAVE', PDU(CommandSAVE, [PDUE(TypeSAVELOAD), PDUR, PDUR]))
        self.add('JUMP', PDS(CommandJUMP, Processor.spec_command_jump))
        self.add('LABEL', PDS(CommandLABEL, Processor.spec_command_label))

    # функции для получения значений из токенов и проверки

    def get_str(self, token: TokenABC) -> str:
        if not isinstance(token, TokenWord):
            raise ValueError(f'Ожидалось слово: {token.origin}')
        if token.word is self.aliases:
            raise ValueError(f'Ожидалось слово: {token.origin}')
        return token.word

    def get_enum(self, token: TokenABC, enum: type):
        status = self.get_str(token)
        try:
            return enum(status.upper())
        except ValueError:
            raise ValueError(f'Состояния "{status}" не существует: {token.origin}')

    def get_alias(self, word: TokenWord) -> int | Register:
        if word.word not in self.aliases:
            raise ValueError(f'Псевдонима "{word.word}" не существует: {word.origin}')
        return self.aliases[word.word]

    def get_int(self, token: TokenABC) -> int:
        # если псевдоним
        if isinstance(token, TokenWord):
            thing = self.get_alias(token)
            if not isinstance(thing, int):
                raise ValueError(f'Ожидалось число: {token.origin}')
            return thing

        # проверки
        if not isinstance(token, TokenLiteral):
            raise ValueError(f'Ожидался литерал: {token.origin}')
        if TokenLiteral.REGEXP_INT.fullmatch(token.literal) is None:
            raise ValueError(f'Ожидалось число: {token.origin}')

        # определим базу
        if re.fullmatch(r'-?\d+', token.literal) is not None:
            return int(token.literal, base=10)
        elif re.fullmatch(r'-?0b[01]+', token.literal) is not None:
            return int(token.literal, base=2)
        else:
            return int(token.literal, base=16)

    def get_reg(self, token: TokenABC) -> Register:
        # всё в
        if isinstance(token, TokenWord):
            thing = self.get_alias(token)
            if not isinstance(thing, Register):
                raise ValueError(f'Ожидался регистр: {token.origin}')
            return thing

        if not isinstance(token, TokenLiteral):
            raise ValueError(f'Ожидался литерал: {token.origin}')
        reg = TokenLiteral.REGEXP_REG.fullmatch(token.literal)
        if reg is None:
            raise ValueError(f'Ожидался регистр: {token.origin}')

        # получаем номер регистра
        i = int(reg.group(1))
        if not 0 <= i < 16:
            raise ValueError(f'Существует только 16 регистров: {token.origin}')

        return Register(i)

    # функции для специальных команд

    @staticmethod
    def spec_command_alias(self: Processor, data: list[TokenABC]) -> CommandALIAS:
        if len(data) - 1 != 2:
            raise ValueError(f'Ожидалось 2 аргументов: {data[0].origin}')

        name = self.get_str(data[1])
        # проверка на уникальность
        if name in self.aliases:
            raise ValueError(f'Имя "{name}" для псевдонима уже занято литерал: {data[1].origin}')

        val = data[2]
        if not isinstance(val, TokenLiteral):
            raise ValueError(f'Ожидался литерал: {val.origin}')

        # число или регистр
        if TokenLiteral.REGEXP_INT.fullmatch(val.literal) is not None:
            val = self.get_int(val)
        else:
            val = self.get_reg(val)

        self.aliases[name] = val
        return CommandALIAS(name, val)

    @staticmethod
    def spec_command_const(self: Processor, data: list[TokenABC]) -> CommandCONST:
        if len(data) - 1 != 2:
            raise ValueError(f'Ожидалось 2 аргументов: {data[0].origin}')
        dest = self.get_reg(data[1])
        val = self.get_int(data[2])

        if not -2**31 <= val < 2**32:
            raise ValueError(f'Число "{val}" выходит за пределы 32 битного числа: {data[2].origin}')

        return CommandCONST(dest, val)

    @staticmethod
    def spec_command_const_word(self: Processor, data: list[TokenABC]) -> CommandABC:
        const = self.spec_command_const(self, data)
        return const.to_word()

    @staticmethod
    def spec_command_const_half(self: Processor, data: list[TokenABC]) -> CommandABC:
        const = self.spec_command_const(self, data)
        if not -2**15 <= const.val < 2**16:
            raise ValueError(f'Число "{const.val}" выходит за пределы 16 битного числа: {data[2].origin}')
        return const.to_half()

    @staticmethod
    def spec_command_jump(self: Processor, data: list[TokenABC]) -> CommandJUMP:
        if len(data) - 1 != 2:
            raise ValueError(f'Ожидалось 2 аргументов: {data[0].origin}')

        type_ = self.get_enum(data[1], TypeJUMP)
        dest = self.get_str(data[2])
        # добавим проверку
        self.jump_dest_to_check.append((dest, data[2].origin))

        return CommandJUMP(type_, dest)

    @staticmethod
    def spec_command_label(self: Processor, data: list[TokenABC]) -> CommandLABEL:
        if len(data) - 1 != 1:
            raise ValueError(f'Ожидалось 1 аргументов: {data[0].origin}')

        name = self.get_str(data[1])

        # добавим проверку
        if name in self.all_labels:
            raise ValueError(f'Имя для метки "{name}" уже занято: {data[1].origin}')
        self.all_labels.add(name)

        return CommandLABEL(name)

    # финальный обработчики
    def process(self, data: list[TokenABC]) -> list[CommandABC]:
        res = []

        # добавим в конец разделитель(если его нет) чтобы последние токены тоже были обработаны в цикле
        if not isinstance(data[-1], TokenDivider):
            data.append(TokenDivider(TextRange(TextPosition(0, 0), TextPosition(0, 0))))

        # нужно разделить токена на части между разделителями
        last_divider = 0

        for i, tok in enumerate(data):
            if isinstance(tok, TokenDivider):
                # токены между разделителями
                slise = data[last_divider:i]

                # ошибку за пустые кидать не будем
                if len(slise) != 0:
                    # получаем команду(первое слово)
                    name = slise[0]
                    if not isinstance(name, TokenWord):
                        raise ValueError(f'Ожидалось слово-имя команды: {slise[0].origin}')

                    # чтобы игнорировать регистр
                    name.word = name.word.upper()
                    if name.word not in self.processors:
                        raise ValueError(f'Команды "{name.word}" не существует: {name.origin}')

                    proc = self.processors[name.word]

                    # и запускаем обработчик
                    res.append(
                        proc.process(self, slise)
                    )

                # новый срез начнётся от следующего токена
                last_divider = i + 1

        # проверим назначения прыжков
        for dest, origin in self.jump_dest_to_check:
            if dest not in self.all_labels:
                raise ValueError(f'Метки с именем "{dest}" не существует: {origin}')

        return res


def parse(data: list[TokenABC]) -> list[CommandABC]:
    processor = Processor()
    return processor.process(data)


# from .Lexer import lex
# from ..MachineCode.Transfer import transfer
# from io import StringIO, BytesIO
# dadta = StringIO('''
# # label start
# # MOVE r1 R2
# # op add r2 r3
# const r0 -2
# const r1 42
# const r2 0xffffffff
# move r4 r2
# op xor r6 r6
# # jump no start
# STOP
# ''')
# resssss = BytesIO()
#
# lexed = lex(dadta)
# parsed = parse(lexed)
# transfer(parsed, resssss)
#
# print(*parsed, sep='\n')
# print('-'*30)
#
# ress = resssss.getvalue()
# print(ress.hex())
#
# with open(r'C:\Coding\Python\Two\Test\TheLanguage\TrueHardVersionV2\Processor\program.bin', 'wb') as f:
#     transfer(parsed, f)
#
# # for t in resss:
# #     print(t)


