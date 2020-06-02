from enum import Enum, auto


class TripletError(BaseException):
    pass


class TripletOperation(Enum):
    """ тип операции триады """
    assignment = '='
    generate_func = 'proc'
    generate_memory_func = 'memory'  # выделение памяти
    generate_end_func = 'endproc'
    generate_memory_end_func = 'free'  # освобождение памяти
    generate_func_call = 'call'
    generate_return = 'return'
    generate_nop = 'nop'
    jz = 'jnz'
    jmp = 'jmp'
    less = '<'
    bigger = '>'
    bigger_or_equal = '>='
    less_or_equal = '<='
    not_equal = '!='
    equal = '=='
    plus = '+'
    minus = '-'
    multiply = '*'
    divide = '/'
    remainder = '%'


class TripletOperandType(Enum):
    """ типы операндов (ссылка на триаду или значение) """
    value = auto()
    link = auto()


class Triplet:
    """ класс триады """

    def __init__(self, number: int, operation: TripletOperation,
                 first_arg_type: TripletOperandType = None,
                 first_arg: str = None,
                 second_arg_type: TripletOperandType = None,
                 second_arg: str = None):
        self.__number = number
        self.__operation = operation
        self.__first_arg_type = first_arg_type
        self.__first_arg = first_arg
        self.__second_arg_type = second_arg_type
        self.__second_arg = second_arg

    @property
    def number(self):
        return self.__number

    @property
    def operation(self):
        return self.__operation

    @property
    def first_arg(self):
        return self.__first_arg

    @property
    def first_arg_type(self):
        return self.__first_arg_type

    @property
    def second_arg(self):
        return self.__second_arg

    @property
    def second_arg_type(self):
        return self.__second_arg_type

    def __str__(self):
        s = "{0}) {1} {2} {3}"
        first_arg = str(self.first_arg) \
            if self.first_arg_type == TripletOperandType.value \
            else '({})'.format(self.first_arg)
        second_arg = ''
        if self.second_arg is not None:
            second_arg = str(self.second_arg) \
                if self.second_arg_type == TripletOperandType.value \
                else '({})'.format(self.second_arg)
        return s.format(self.number, self.operation.value, first_arg, second_arg)

    def resolve_triplet(self, arg, arg_type: TripletOperandType):
        """
            Доформировать триаду
            :param arg: значение
            :param arg_type: тип аргумента
            :return: None
        """
        if self.first_arg is None:
            self.__first_arg = arg
            self.__first_arg_type = arg_type
        elif self.second_arg is None:
            self.__second_arg = arg
            self.__second_arg_type = arg_type
        else:
            raise TripletError("Невозможно доформировать триаду, "
                               "так как она уже является полной")
