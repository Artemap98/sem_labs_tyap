from enum import Enum, auto


class AliasesSemFuncs(Enum):
    """ семантические подпрограммы для триад """
    keep_var = auto()  # запомнить идентификатор
    keep_var2 = auto()
    keep_type = auto()  # запомнить тип
    add_var = auto()  # добавить переменную в семантическое дерево
    add_func = auto()  # добавить функция в семантическое дерево
    generate_func = auto()  # генерация заголовка функции
    generate_memory_func = auto()  # выделение памяти для локальных переменных функции
    save_func_type = auto()  # запомнить имя функции и тип
    generate_end_func = auto()  # генерация заголовка конца функции
    generate_end_memory_func = auto()  # освобождение памяти, выделявшейся для локаьных данных ф-ии
    generate_assignment_triplet = auto()
    check_type = auto()     # проверяет совместимость типов
    begin_block = auto()
    end_block = auto()
    generate_triad_return = auto()
    check_func_type = auto()
    find_type = auto()      # находит идентификатор в сем дереве
    # арифметические операции
    make_not_equal = auto()
    make_equal = auto()
    make_less = auto()
    make_bigger = auto()
    make_bigger_or_equal = auto()
    make_less_or_equal = auto()
    make_add = auto()
    make_sub = auto()
    make_multiply = auto()
    make_division = auto()
    make_division_remainder = auto()
    check_const = auto()
    save_r = auto()
    find_node = auto()
    generate_call_function = auto()
    generate_nop = auto()
    save_address1 = auto()
    save_address2 = auto()
    save_address3 = auto()
    save_address4 = auto()
    jmp_address1 = auto()
    jmp_address2 = auto()
    jz_address3 = auto()