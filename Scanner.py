from Aliases import LexTypes as al


class ScannerError(BaseException):
    def __init__(self, row, col, text):
        self.row = row
        self.col = col
        self.text = text


class Scanner:

    def __init__(self):
        # игнорируемые символы
        self.__ignore = [' ', '\n', '\t', '\r']
        # символы
        self.__symbols = list(map(chr, [x for x in range(ord('a'), ord('z') + 1)]))
        self.__symbols += list(map(chr, [x for x in range(ord('A'), ord('Z') + 1)]))
        self.__symbols += ['_']
        # 10x цифры
        self.__digits10 = list(map(str, [x for x in range(10)]))
        # 16x цифры
        self.__digits16 = self.__digits10 + \
                          list(map(chr, [x for x in range(ord('a'), ord('f') + 1)])) + \
                          list(map(chr, [x for x in range(ord('A'), ord('F') + 1)]))
        # ключевые слова:
        self.__key_words = {
            'for': al.T_FOR,
            'long': al.T_LONG,
            'main': al.T_MAIN,
            'return': al.T_RETURN,
            'int': al.T_INT,
            'short': al.T_SHORT
        }

        self.__one_symbol_lexems = {
            '+': al.T_PLUS,
            '-': al.T_MINUS,
            '*': al.T_MULTIPLY,
            '%': al.T_REMAINDER,
            ';': al.T_SEMICOLON,
            ',': al.T_COMMA,
            '(': al.T_LEFT_BRACKET,
            ')': al.T_RIGHT_BRACKET,
            '{': al.T_LEFT_CURLY_BRACKET,
            '}': al.T_RIGHT_CURLY_BRACKET
        }

    def __get_lexem_info(self, row, col, lex_type, lex_str):
        return {
            'mistake': False,
            'row': row + 1,
            'column': col + 1,
            'type': lex_type,
            'str': lex_str
        }

    def __get_lexem_error(self, row, col, text):
        return {
            'mistake': True,
            'row': row + 1,
            'column': col + 1,
            'text': text
        }

    def feed_text(self, text):
        if text[-1] != '\n':
            text += '\n'
        uk = 0
        row, uk_before = 0, 0
        # try:
        while uk < len(text) - 1:
            # пропуск игнорируемых символов
            while text[uk] in self.__ignore:
                # нужно для определения текущей строки и столбца
                if text[uk] == '\n':
                    row += 1
                    uk_before = uk + 1

                uk += 1
                if uk >= len(text):
                    return

            if text[uk] == '/':
                uk += 1
                if text[uk] != '/':
                    yield self.__get_lexem_info(row, uk - uk_before, al.T_DIVIDER, '/')
                    uk += 1
                else:
                    uk += 1
                    while text[uk] != '\n':
                        if uk >= len(text):
                            return
                        uk += 1

                    row += 1
                    uk += 1
                    uk_before = uk

            # идентификатор
            elif text[uk] in self.__symbols:
                lexem_begin = uk
                lexem_str = text[uk]

                uk += 1
                while text[uk] in self.__symbols + self.__digits10:
                    lexem_str += text[uk]
                    uk += 1

                # проверяем, является ли идентификатор ключевым словом
                try:
                    lex_type = self.__key_words[lexem_str]
                except KeyError:
                    lex_type = al.T_IDENT

                yield self.__get_lexem_info(row, lexem_begin - uk_before, lex_type, lexem_str)

            # 10x и 16x числа
            elif text[uk] in self.__digits10[1:]:  # все, кроме нуля
                lexem_begin = uk
                lexem_str = text[uk]

                uk += 1
                while text[uk] in self.__digits10:
                    lexem_str += text[uk]
                    uk += 1

                yield self.__get_lexem_info(row, lexem_begin - uk_before, al.T_CONST_10, lexem_str)

            elif text[uk] == '0':
                lexem_begin = uk
                lexem_str = text[uk]

                uk += 1
                # если после нуля не идет 'x' или 'X',
                # значит, это десятичный 0, вернем его
                if text[uk] != 'x' and text[uk] != 'X':
                    while text[uk] in self.__digits10:
                        lexem_str += text[uk]
                        uk += 1
                    yield self.__get_lexem_info(row, lexem_begin - uk_before, al.T_CONST_10, lexem_str)
                else:
                    lexem_str += text[uk]
                    uk += 1
                    # если лексема обрывается на '0x' или '0X'
                    if text[uk] not in self.__digits16:
                        raise ScannerError(row, uk - uk_before,
                                           'Незавершенная '
                                           'шестнадцатеричная '
                                           'константа')
                    lexem_str += text[uk]

                    uk += 1
                    while text[uk] in self.__digits16:
                        lexem_str += text[uk]
                        uk += 1

                    yield self.__get_lexem_info(row, lexem_begin - uk_before, al.T_CONST_16, lexem_str)

            # + - * % ; , ( ) { }
            elif text[uk] in self.__one_symbol_lexems:
                yield self.__get_lexem_info(
                    row,
                    uk - uk_before,
                    self.__one_symbol_lexems[text[uk]],
                    text[uk]
                )
                uk += 1

            elif text[uk] == '!':
                uk += 1
                if text[uk] == '=':
                    uk += 1
                    yield self.__get_lexem_info(row, uk - uk_before, al.T_NOT_EQUAL, '!=')
                else:
                    raise ScannerError(row, uk - uk_before, "Ожидался символ '='")

            elif text[uk] == '=':
                uk += 1
                # ==
                if text[uk] == '=':
                    uk += 1
                    yield self.__get_lexem_info(row, uk - uk_before, al.T_EQUAL, '==')
                else:
                    yield self.__get_lexem_info(row, uk - uk_before, al.T_ASSIGNMENT, '=')

            elif text[uk] == '>':
                uk += 1
                # ==
                if text[uk] == '=':
                    uk += 1
                    yield self.__get_lexem_info(row, uk - uk_before, al.T_BIGGER_OR_EQUAL, '>=')
                else:
                    yield self.__get_lexem_info(row, uk - uk_before, al.T_BIGGER, '>')

            elif text[uk] == '<':
                uk += 1
                # ==
                if text[uk] == '=':
                    uk += 1
                    yield self.__get_lexem_info(row, uk - uk_before, al.T_LESS_OR_EQUAL, '<=')
                else:
                    yield self.__get_lexem_info(row, uk - uk_before, al.T_LESS, '<')

# except ScannerError as err:
# yield self.__get_lexem_error(err.row, err.col, err.text)
