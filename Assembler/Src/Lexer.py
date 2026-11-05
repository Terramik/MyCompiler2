from ..Defines.Base import *
from ..Defines.Tokens import *
import re
from typing import TextIO


__all__ = ('lex',)


PARSE_ORDER = (
    TokenLiteral,
    TokenWord,
    TokenDivider,
)

REGEXP_COMMENT = re.compile(r'\s*#')


def lex(file: TextIO) -> list[TokenABC]:
    res = []

    for row_i, row in enumerate(file):
        col_i = 0

        # обрабатываем линию
        while True:

            # если это просто куча пробелов - заканчиваем
            if not row[col_i:].strip():
                break

            # если остался комментарий - тоже заканчиваем
            if REGEXP_COMMENT.match(row, col_i):
                break

            # проходимся по всем возможным токенам и их regexp
            for token in PARSE_ORDER:
                match = token.REGEXP.match(row, col_i)  # ищём от прошлого конца

                # если совпадение есть
                if match is not None:
                    # этот конец - теперь новый конец
                    col_i = match.span()[1]
                    # и собственно что мы нашли
                    string = match.group(1)
                    # происхождение токена
                    origin = TextRange(
                        TextPosition(row_i, col_i - len(string)),
                        TextPosition(row_i, col_i)
                    )

                    # делаем токен и добавляем в ряд
                    if token is TokenLiteral:
                        res.append(TokenLiteral(string, origin))
                    elif token is TokenWord:
                        res.append(TokenWord(string, origin))
                    elif token is TokenDivider:
                        res.append(TokenDivider(origin))
                    break

            else:
                # если ни один из токенов не подошёл - кидаем ошибку
                raise ValueError(f'Unreadable line: {row[col_i:]}')

        # '\n' тоже могут служить разделителями, так что если его уже нет, добавим
        if res and not isinstance(res[-1], TokenDivider):
            res.append(TokenDivider(TextRange(
                TextPosition(row_i, 0), TextPosition(row_i, 0)
            )))

        ...

    return res


