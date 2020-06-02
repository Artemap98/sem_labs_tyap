from enum import Enum, auto


class LexTypes(Enum):
    T_IDENT = auto()
    T_FOR = auto()
    T_INT = auto()
    T_SHORT = auto()
    T_LONG = auto()
    T_MAIN = auto()
    T_RETURN = auto()
    T_SEMICOLON = auto()
    T_COMMA = auto()
    T_LEFT_BRACKET = auto()
    T_RIGHT_BRACKET = auto()
    T_LEFT_CURLY_BRACKET = auto()
    T_RIGHT_CURLY_BRACKET = auto()
    T_PLUS = auto()
    T_MINUS = auto()
    T_MULTIPLY = auto()
    T_DIVIDER = auto()
    T_REMAINDER = auto()
    T_NOT_EQUAL = auto()
    T_EQUAL = auto()
    T_BIGGER = auto()
    T_BIGGER_OR_EQUAL = auto()
    T_LESS = auto()
    T_LESS_OR_EQUAL = auto()
    T_ASSIGNMENT = auto()
    T_CONST_10 = auto()
    T_CONST_16 = auto()
    T_EOF = auto()
    T_EPS = auto()
    SKIP = auto()


class LexNames:
    @staticmethod
    def get(lex_type: LexTypes):
        lex_names = {
            int(LexTypes.T_IDENT.value): 'Идентификатор',
            int(LexTypes.T_FOR.value): 'Ключевое слово for',
            int(LexTypes.T_INT.value): 'Ключевое слово int',
            int(LexTypes.T_SHORT.value): 'Ключевое слово short',
            int(LexTypes.T_LONG.value): 'Ключевое слово long',
            int(LexTypes.T_MAIN.value): 'Ключевое слово main',
            int(LexTypes.T_RETURN.value): 'Ключевое слово return',
            int(LexTypes.T_SEMICOLON.value): ';',
            int(LexTypes.T_COMMA.value): ',',
            int(LexTypes.T_LEFT_BRACKET.value): '(',
            int(LexTypes.T_RIGHT_BRACKET.value): ')',
            int(LexTypes.T_LEFT_CURLY_BRACKET.value): '{',
            int(LexTypes.T_RIGHT_CURLY_BRACKET.value): '}',
            int(LexTypes.T_PLUS.value): '+',
            int(LexTypes.T_MINUS.value): '-',
            int(LexTypes.T_MULTIPLY.value): '*',
            int(LexTypes.T_DIVIDER.value): '/',
            int(LexTypes.T_REMAINDER.value): '%',
            int(LexTypes.T_NOT_EQUAL.value): '!=',
            int(LexTypes.T_EQUAL.value): '==',
            int(LexTypes.T_BIGGER.value): '>',
            int(LexTypes.T_BIGGER_OR_EQUAL.value): '>=',
            int(LexTypes.T_LESS.value): '<',
            int(LexTypes.T_LESS_OR_EQUAL.value): '<=',
            int(LexTypes.T_ASSIGNMENT.value): '=',
            int(LexTypes.T_CONST_10.value): 'Десятичная константа',
            int(LexTypes.T_CONST_16.value): 'Шестнадцатеричная константа',
        }
        return lex_names[int(lex_type.value)]