from enum import auto, Enum

from Aliases import LexTypes
from Triplet import Triplet, TripletOperandType, TripletOperation


class SemError(BaseException):
    """
        Выбрасывается при семантической ошибке
    """


class SemTypes(Enum):
    long_long = auto()
    long = auto()
    short = auto()


def convert_sem_type_to_string(sem_type):
    """ Преобразует семантический тип в строку """
    if sem_type == SemTypes.long_long:
        return 'long long'
    elif sem_type == SemTypes.long:
        return 'long'
    elif sem_type == SemTypes.short:
        return 'short'
    else:
        raise AttributeError("Нет семантического типа с номером: {}".format(sem_type))


class ObjectTypes(Enum):
    variable = auto()
    func = auto()


class Node:

    def __init__(self, name, obj_type, sem_type, value=0, text_position=None):
        self.__name = name
        self.__obj_type = obj_type
        self.__sem_type = sem_type
        self.__value = value
        self.__text_position = text_position
        self.alternate_name = None

    @property
    def name(self):
        return self.__name

    @property
    def obj_type(self):
        return self.__obj_type

    @property
    def sem_type(self):
        return self.__sem_type

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, other):
        self.__value = other

    @property
    def text_position(self):
        return self.__text_position

    def __str__(self):
        text = "name: {0}\n" \
               "obj_type: {1}\n" \
               "sem_type: {2}\n" \
               "value: {3}\n" \
               "text_position: {4}".format(self.name,
                                           self.obj_type,
                                           self.sem_type,
                                           self.value,
                                           self.text_position)
        return text


class SemTree:
    def __init__(self, node=None, parent=None):
        self.__current_triple = 0
        self.__node = node
        self.__left = None
        self.__right = None
        self.__parent = parent
        self.__pointer = self
        self.id = None
        self.__func_returned = False  # True, если функция вернула значение

    @property
    def node(self):
        return self.__node

    @property
    def func_returned(self):
        return self.__func_returned

    @property
    def left(self):
        return self.__left

    @left.setter
    def left(self, other):
        self.__left = other

    @property
    def right(self):
        return self.__right

    @right.setter
    def right(self, other):
        self.__right = other

    @property
    def pointer(self):
        return self.__pointer

    @pointer.setter
    def pointer(self, other):
        self.__pointer = other

    @property
    def parent(self):
        return self.__parent

    @parent.setter
    def parent(self, other):
        self.__parent = other

    def add_block(self):
        """
            Добавляет блок в семантическое дерево
            :rtype: None
        """
        saved_pointer = self.__pointer
        self.__add_node(None, 'right')
        return saved_pointer

    def delete_current_block(self):
        """
            Удаляет блок, относительно текущего указателя в семантическом дереве
            :return: None
        """
        pointer = self.pointer.right
        self.__delete_block(pointer)

    def add_func(self, name, sem_type, alter):
        """
            Добавляет функцию в семантическое дерево, относительно текущего self.pointer
            :param name: Наименование функции
            :param sem_type: Семантический тип
            :type name: str
            :type lex_type: SemTypes
            :return: Указатель на ноду с именем ф-ии
            :rtype: SemTree
        """

        # Проверим, что функция еще не объявлена в программе
        pointer = self.__find_in_tree(name)

        # если Node не None, значит, объект с таким именем в глобальной
        # области видимости уже объявлен
        if pointer is not None:
            err_text = ''
            if pointer.node.obj_type == ObjectTypes.variable:
                err_text = "В глобальной области видимости " \
                           "уже объявлена переменная с именем {}".format(name)
            elif pointer.node.obj_type == ObjectTypes.func:
                err_text = "Функция с именем {} уже объявлена в программе".format(name)
            else:
                raise ValueError("Неверное значение obj_type для node:\n{}".format(str(pointer.node)))
            raise SemError(err_text)

        # добавляем в дерево ф-ию
        node = Node(name, ObjectTypes.func, sem_type)
        node.alternate_name = alter
        self.__add_node(node, 'left')
        pointer = self.pointer

        return pointer

    def add_returned_value_to_func(self, sem_type, value):
        """
            Фиксирует в текущей функции, относительно указателя в семантическом
            дереве, возвращаемое значение.
            :param sem_type: Семантический тип
            :param value: Значение
            :param pointer: Указатель
            :return: None
        """

        # теперь необходимо получить ссылку на функцию в семантическом дереве.
        # Так как при вызове создается копия, нужно записать значение в родительскую
        # ноду текущей функции
        pointer = self.pointer
        while not pointer.node or pointer.node.obj_type != ObjectTypes.func:
            pointer = pointer.parent
        if pointer.node.name == 'main':
            if not self.__assignment_sem_type(pointer.node.sem_type, sem_type):
                raise SemError(
                    "Невозможно вернуть тип {0} внутри ф-ии с типом {1}"
                        .format(convert_sem_type_to_string(pointer.node.sem_type),
                                convert_sem_type_to_string(sem_type))
                )
            pointer.node.value = value
            self.flag = False
            pointer.__func_returned = True
            return pointer
        pointer_delete = pointer
        pointer = pointer.parent

        if not self.__assignment_sem_type(pointer.node.sem_type, sem_type):
            raise SemError(
                "Невозможно вернуть тип {0} внутри ф-ии с типом {1}"
                    .format(convert_sem_type_to_string(pointer.node.sem_type),
                            convert_sem_type_to_string(sem_type))
            )
        pointer.node.value = value

        # удаляем копию функции из семантического дерева
        func_begin = pointer_delete.right

        if pointer_delete.parent:
            pointer_delete.parent.left = pointer_delete.left
        if pointer_delete.left:
            pointer_delete.left.parent = pointer_delete.parent
        pointer_delete.parent = None
        pointer_delete.left = None
        pointer_delete.right = None
        del pointer_delete

        self.__delete_block(func_begin)

        # после return никакие инструкции не выполняются
        self.flag = False
        pointer.__func_returned = True
        return pointer

    def add_variable(self, name, sem_type, alternate_name):
        """
            Добавляет переменную в семантическое дерево, относительно текущего self.pointer
            :param name: Наименование переменной
            :param sem_type: Семантический тип лексемы
            :type name: str
            :type lex_type: SemTypes
        """

        # Проверим, что переменная еще не объявлена в текущем блоке
        if self.__find_in_block(name) is not None:
            raise SemError("Переменная {} уже объявлена в этом блоке".format(name))

        # добавляем в дерево
        node = Node(name, ObjectTypes.variable, sem_type)
        node.alternate_name = alternate_name
        self.__add_node(node, 'left')
        return self.__get_bytes_size_sem_type(sem_type)

    def assignment(self, variable_name, value, sem_type):
        """
            Выполняет присваивание значения переменной
            :param variable_name: Наименование переменной
            :param value: Значение выражения
            :param sem_type: Семантический тип выражения
            :rtype: None
        """

        # проверим, есть ли переменная с таким именем в текущем блоке
        pointer = self.__find_in_tree(variable_name)
        if pointer is None or pointer.node.obj_type != ObjectTypes.variable:
            raise SemError("Переменная не объявлена в блоке")

        if not self.__assignment_sem_type(pointer.node.sem_type, sem_type):
            raise SemError("Невозможно присвоить типу {0} тип {1}"
                           .format(convert_sem_type_to_string(pointer.node.sem_type),
                                   convert_sem_type_to_string(sem_type)))
        pointer.node.value = value

    def assignment_check(self, sem_type_var, sem_type_result):
        """
            Проверка, можно ли переменной сем типу sem_type_var присвоить sem_type_result
        :param sem_type_var: Семантический типа переменной
        :param sem_type_result: Семантический тип выраженной
        :return: None
        """
        if not self.__assignment_sem_type(sem_type_var, sem_type_result):
            raise SemError("Невозможно присвоить типу {0} тип {1}"
                           .format(convert_sem_type_to_string(sem_type_var),
                                   convert_sem_type_to_string(sem_type_result)))

    def return_check(self, sem_type_func, sem_type_return):
        if not self.__assignment_sem_type(sem_type_func, sem_type_return):
            raise SemError("Невозможно вернуть тип {1} внутри функции с типом {0}"
                           .format(convert_sem_type_to_string(sem_type_func),
                                   convert_sem_type_to_string(sem_type_return)))

    def convert_types(self, sem_type1, sem_type2):
        return self.__convert_sem_type(sem_type1, sem_type2)

    def find_variable(self, variable_name):
        """
            Находит переменную в дереве
            :param variable_name: имя переменной
            :return: Node
        """
        pointer = self.__find_in_tree(variable_name)
        if pointer is None or pointer.node.obj_type != ObjectTypes.variable:
            raise SemError("Переменная с именем {} не объявлена".format(variable_name))

        return pointer.node

    def sem_type_by_value(self, value):
        """
            Возвращает кортеж: семантический тип и преобразованное значение
            :param value: Строка со значением
            :return: Семантический тип
            :type value: str
            :rtype: SemTypes or None
        """
        if not self.flag:
            return None, None

        try:
            value = int(value, 10)
        except ValueError:
            try:
                value = int(value, 16)
            except ValueError:
                raise SemError("Неправильная запись числа")

        if -2 ** 31 <= value <= 2 ** 31 - 1:
            return SemTypes.long, value
        else:
            raise SemError("Константа превышает допустимое значение для типа long")

    def call_function(self, func_name):
        """
            Находит в семантическом дереве функцию.
            Возвращает кортеж из двух значений:
            указатель на ноду функции в сем. дереве
        :param func_name: Имя функции
        :return:
        """

        pointer = self.__find_in_tree(func_name)
        if pointer is None or pointer.node.obj_type != ObjectTypes.func:
            raise SemError(
                "Невозможно вызвать функцию с именем {}".format(func_name)
            )

        # вернем указатель на изначальную ссылку на ноду функции в сем дереве
        return pointer.node

    def find_node(self, name) -> Node:
        pointer = self.__find_in_tree(name)
        if pointer is None:
            raise SemError("Не найден идентификатор с именем {}".format(name))
        return pointer.node

    def get_variable_val(self, var: Node):
        if var.obj_type != ObjectTypes.variable:
            return None
        return var.alternate_name, var.sem_type

    def variable_value(self, variable_name):
        """
            Возвращает ссылку на переменную с именем name в семантическом дереве
            :param variable_name: имя переменной
            :return: Node or None
        """
        pointer = self.__find_in_tree(variable_name)
        if pointer is None or pointer.node.obj_type != ObjectTypes.variable:
            raise SemError(
                "Переменная {} не объявлена".format(variable_name)
            )
        return pointer.node

    def equation(self, operation, value1, value2, sem_type1, sem_type2):
        """
            Выполняет необходимую операцию над двумя значениями
            :param operation: Тип операции
            :param value1: Первое значение
            :param value2: Второе значение
            :param sem_type1: Семантический тип первого значения
            :param sem_type2: Семантический тип второго значения
            :return: Кортеж из двух элементов - семантический тип и значение
            :type operation: LexTypes
        """
        bool_operations = {
            LexTypes.T_EQUAL: lambda x, y: int(x == y),
            LexTypes.T_NOT_EQUAL: lambda x, y: int(x != y),
            LexTypes.T_BIGGER: lambda x, y: int(x > y),
            LexTypes.T_BIGGER_OR_EQUAL: lambda x, y: int(x >= y),
            LexTypes.T_LESS: lambda x, y: int(x < y),
            LexTypes.T_LESS_OR_EQUAL: lambda x, y: int(x <= y),
        }

        arithmetic_operations = {
            LexTypes.T_PLUS: lambda x, y: x + y,
            LexTypes.T_MINUS: lambda x, y: x - y,
            LexTypes.T_DIVIDER: lambda x, y: x // y,
            LexTypes.T_MULTIPLY: lambda x, y: x * y,
            LexTypes.T_REMAINDER: lambda x, y: x % y
        }

        if operation in bool_operations.keys():
            return SemTypes.long, bool_operations[operation](value1, value2)

        elif operation in arithmetic_operations:
            new_sem_type = self.__convert_sem_type(sem_type1, sem_type2)
            new_value = arithmetic_operations[operation](value1, value2)
            if not self.__check_value_and_sem_type(new_sem_type, new_value):
                raise SemError("Значение {0} выходит за пределы типа {1}"
                               .format(new_value,
                                       convert_sem_type_to_string(new_sem_type)))
            return new_sem_type, new_value

    def generate_func_triple(self, func_name):
        """
            Генерирование триады "Начало функции"
            :param func_name: Имя функции
            :return: триада
        """
        triplet = Triplet(self.__current_triple,
                          TripletOperation.generate_func,
                          TripletOperandType.value,
                          func_name)
        self.__current_triple += 1
        return triplet

    def generate_memory_func_triple(self):
        """
            Генерирование триады для выделения памяти для локальных
            данных функций
            :return: Triplet
        """
        triplet = Triplet(self.__current_triple,
                          TripletOperation.generate_memory_func)
        self.__current_triple += 1
        return triplet

    def generate_memory_end_func_triple(self, free_bytes):
        """
            Гененирование триады освобождения памяти локальных
            данных функции
            :param free_bytes: Количество освобождаемых байт
            :return: Triplet
        """
        triplet = Triplet(self.__current_triple,
                          TripletOperation.generate_memory_end_func,
                          TripletOperandType.value,
                          free_bytes)
        self.__current_triple += 1
        return triplet

    def generate_return_triple(self, val):
        value = val['value']
        triplet_type = TripletOperandType.value
        if val['triplet_type'] == 'link':
            triplet_type = TripletOperandType.link
        triplet = Triplet(self.__current_triple,
                          TripletOperation.generate_return,
                          triplet_type,
                          value)
        self.__current_triple += 1
        return triplet

    def generate_func_end_triple(self, func_name):
        """
            Генерирование триады окончание функции
            :return:
        """
        triplet = Triplet(self.__current_triple,
                          TripletOperation.generate_end_func,
                          TripletOperandType.value,
                          func_name)
        self.__current_triple += 1
        return triplet

    def generate_nop(self):
        triplet = Triplet(self.__current_triple,
                          TripletOperation.generate_nop,
                          TripletOperandType.value,
                          'null')
        self.__current_triple += 1
        return triplet

    def generate_jz(self):
        triplet = Triplet(self.__current_triple,
                          TripletOperation.jz)
        self.__current_triple += 1
        return triplet

    def generate_jmp(self, triplet_number):
        triplet = Triplet(self.__current_triple,
                          TripletOperation.jmp,
                          TripletOperandType.link,
                          triplet_number)
        self.__current_triple += 1
        return triplet

    def generate_func_call_triple(self, node: Node):
        if node is None or node.obj_type != ObjectTypes.func:
            raise SemError("Не найдена функция с именем {}".format(node.name))
        triplet = Triplet(self.__current_triple,
                          TripletOperation.generate_func_call,
                          TripletOperandType.value,
                          node.alternate_name)
        self.__current_triple += 1
        return triplet

    def generate_assignment_triple(self, identifier, value, val_type):
        """
            Генерирование триады присваивания
            :param identifier: чему присваиваем
            :param value: что присваиваем
            :param val_type: 'value' если значение, 'link', если ссылка на триаду
            :return: None
        """
        t = None
        if val_type == 'link':
            t = TripletOperandType.link
        elif val_type == 'value':
            t = TripletOperandType.value

        triplet = Triplet(self.__current_triple,
                          TripletOperation.assignment,
                          TripletOperandType.value,
                          identifier,
                          t,
                          value)
        self.__current_triple += 1
        return triplet

    def eq_operation(self, val1, val2, operation):
        oper = {
            '>': TripletOperation.bigger,
            '<': TripletOperation.less,
            '!=': TripletOperation.not_equal,
            '==': TripletOperation.equal,
            '>=': TripletOperation.bigger_or_equal,
            '<=': TripletOperation.less_or_equal,
            '*': TripletOperation.multiply,
            '/': TripletOperation.divide,
            '%': TripletOperation.remainder,
            '+': TripletOperation.plus,
            '-': TripletOperation.minus,
        }
        sem_type = self.__convert_sem_type(val1['type'], val2['type'])
        first_arg_type = TripletOperandType.value if val1['triplet_type'] == 'value' \
            else TripletOperandType.link
        second_arg_type = TripletOperandType.value if val2['triplet_type'] == 'value' \
            else TripletOperandType.link
        triplet = Triplet(self.__current_triple,
                          oper[operation],
                          first_arg_type,
                          val1['value'],
                          second_arg_type,
                          val2['value'])
        self.__current_triple += 1
        return triplet, sem_type

    def check_const(self, const: str):
        a = None
        try:
            a = int(const, 10)
        except ValueError:
            try:
                a = int(const, 16)
            except ValueError:
                raise SemError("Невозможно привести к числовому значению строку: '{}'".format(const))

        sem_type = None

        if -2 ** 15 <= a <= 2 ** 15 - 1:
            sem_type = SemTypes.short
        elif -2 ** 31 <= a <= 2 ** 31 - 1:
            sem_type = SemTypes.long
        else:
            raise SemError("Число {} превышает допустимый диапазон для типов long и short".format(const))

        return a, sem_type

    def save_r(self, current_val):
        if current_val is None:
            raise SemError("Попытка обращения к необъявленной функции")
        return {'value': current_val[0], 'type': current_val[1], 'triplet_type': 'value'}

    def resolve_triplet(self, triplet: Triplet, value, val_type):
        """
            Доформировать незаконченную триаду
            :param triplet: триада
            :param value: значение
            :param val_type: 'link', если значение ссылка, 'value' - иначе
            :return: None
        """
        t = None
        if val_type == 'link':
            t = TripletOperandType.link
        elif val_type == 'value':
            t = TripletOperandType.value
        else:
            raise SemError("Неправильное значение для операнда триады. "
                           "Допустимо 'link', 'value'. Получили '{}'".format(val_type))
        triplet.resolve_triplet(value, t)

    def find_all_nodes_in_all_tree(self):
        res = dict()
        res['var'] = list()
        res['func'] = list()
        pointer = self
        self.__find_node_in_all_tree(pointer, res)
        return res

    def __find_node_in_all_tree(self, pointer, res):
        if pointer.left is not None:
            self.__find_node_in_all_tree(pointer.left, res)
        if pointer.right is not None:
            self.__find_node_in_all_tree(pointer.right, res)

        if pointer.node is not None:
            if pointer.node.obj_type == ObjectTypes.variable:
                res['var'].append(pointer.node)
            else:
                res['func'].append(pointer.node)

    def __add_node(self, node, direction):
        """
            Добавляет новую ноду в дерево
            :param node: Нода, которая будет добавлена
            :param direction: Направление, куда будет добавлена нода (лево или право)
            :type node: Node or None
            :type direction: str
        """
        tree = SemTree(node, self.pointer)
        if direction == 'left':
            self.pointer.left = tree
            self.pointer = self.pointer.left
        elif direction == 'right':
            self.pointer.right = tree
            self.pointer = self.pointer.right
        else:
            raise AttributeError("Допустимые значения для direction: 'left' или 'right'")

    def __get_bytes_size_sem_type(self, sem_type: SemTypes):
        size = 0
        if sem_type == SemTypes.short:
            size = 2
        elif sem_type == SemTypes.long:
            size = 4
        elif sem_type == SemTypes.long_long:
            size = 8
        return size

    def __delete_node(self, pointer):
        """
            Удалить в дереву ноду по заданному указателю
            :param pointer: Указатель на ноду
            :return: None
        """
        if pointer is None:
            return
        parent = pointer.parent
        left = pointer.left
        right = pointer.right
        pointer.parent = None
        pointer.left = None
        pointer.right = None
        if parent is not None:
            if parent.right.node is pointer.node:
                parent.right = right
            else:
                parent.left = left
        del pointer

    def __delete_block(self, pointer):
        """
            Удаляет блок и все вложенные блоки из семантического дерева
            :param pointer: Указатель на начало блока
            :return: None
        """
        if pointer is None:
            return

        if pointer.parent:
            pointer.parent.right = None
        pointer.parent = None
        stack = list()
        stack.append(pointer)
        while len(stack):
            pointer = stack[-1]
            if pointer.left or pointer.right:
                if pointer.left:
                    stack.append(pointer.left)
                if pointer.right:
                    stack.append(pointer.right)
            else:
                stack.pop()
                if pointer.parent:
                    if pointer.parent.left == pointer:
                        pointer.parent.left = None
                    else:
                        pointer.parent.right = None
                pointer.parent = None
                del pointer

    def __find_in_block(self, name):
        """
            Ищет объект по имени до конца текущего блока вверх
            :param name: Имя объекта, которое нужно найти в блоке
            :return: Найденная ноду
            :rtype: SemTree or None
        """
        result = None
        cur_pointer = self.pointer
        while cur_pointer.parent is not None and cur_pointer.parent.right is None:
            # Продолжаем цикл до тех пор, пока родитель не равен None и текущая
            # нода не является правым потомком родителя
            if cur_pointer.node and cur_pointer.node.name == name:
                result = cur_pointer
                break
            else:
                cur_pointer = cur_pointer.parent
        return result

    def __get_current_func(self):
        """
            Возвращает указатель на текущую функцию или None
            :return: SemTree or None
        """
        prev_uk = self.pointer
        next_uk = self.pointer.parent
        while next_uk:
            if next_uk.node and next_uk.node.obj_type == ObjectTypes.func:
                if prev_uk == next_uk.right:
                    return next_uk
                else:
                    break
            else:
                prev_uk = next_uk
                next_uk = next_uk.parent
        return None

    def __find_in_tree(self, name):
        """
            Ищет объект по имени до конца дерева вверх
            :param name: Имя объекта, которое нужно найти в блоке
            :return: Найденная ноду
            :rtype: SemTree or None
        """
        result = None
        cur_pointer = self.pointer
        while cur_pointer.parent is not None:
            # Продолжаем цикл до тех пор, пока родитель не равен None и текущая
            if cur_pointer.node and cur_pointer.node.name == name:
                result = cur_pointer
                break
            else:
                cur_pointer = cur_pointer.parent
        return result

    def lex_type_to_semtype(self, lex_type):
        """
            Преобразовывает список лексем в семантический тип
            :param lex_type: Список лексических типов
            :type lex_type: list of LexTypes
            :return: Семантический тип
            :rtype: SemTypes
        """
        if not hasattr(lex_type, '__iter__'):
            raise AttributeError("lex_type должен быть итерируемым")
        err = "Ошибка в преобразовании лексем в семантический тип: {0}".format(lex_type)
        semtype = None

        if len(lex_type) == 1:
            if lex_type[0] == LexTypes.T_SHORT:
                semtype = SemTypes.short
            elif lex_type[0] == LexTypes.T_LONG:
                semtype = SemTypes.long
            elif lex_type[0] == LexTypes.T_INT:
                semtype = SemTypes.long
            else:
                raise SemError(err)
        elif len(lex_type) == 2:
            if lex_type[0] == LexTypes.T_SHORT and lex_type[1] == LexTypes.T_INT:
                semtype = SemTypes.short
            elif lex_type[0] == LexTypes.T_LONG and lex_type[1] == LexTypes.T_LONG:
                semtype = SemTypes.long_long
            else:
                raise SemError(err)
        else:
            raise SemError(err)

        return semtype

    def __convert_sem_type(self, sem_type1, sem_type2):
        """
            Выполняет преобразование двух семантических типов
            при выполнение арифметической операции
        """
        convert_rules = {
            SemTypes.short:
                {
                    SemTypes.long_long: SemTypes.long_long,
                    SemTypes.long: SemTypes.long,
                    SemTypes.short: SemTypes.short
                },
            SemTypes.long_long:
                {
                    SemTypes.long_long: SemTypes.long_long,
                    SemTypes.long: SemTypes.long_long,
                    SemTypes.short: SemTypes.long_long
                },
            SemTypes.long:
                {
                    SemTypes.long_long: SemTypes.long_long,
                    SemTypes.long: SemTypes.long,
                    SemTypes.short: SemTypes.long
                }
        }
        return convert_rules[sem_type1][sem_type2]

    def __assignment_sem_type(self, sem_type1, sem_type2):
        """
            Проверяет, можно ли первому семантическому типу присвоить второй
            :param sem_type1: Первый семантический тип
            :param sem_type2: Второй семантический тип
            :return: True или False
            :rtype: bool
        """
        result = None
        if sem_type1 == SemTypes.long_long:
            result = True
        elif sem_type1 == SemTypes.long:
            if sem_type2 == SemTypes.long:
                result = True
            elif sem_type2 == SemTypes.short:
                result = True
            elif sem_type2 == SemTypes.long_long:
                result = False
            else:
                raise AttributeError("Нет семантического типа sem_type2 со значением {}".format(sem_type2))
        elif sem_type1 == SemTypes.short:
            if sem_type2 == SemTypes.short:
                result = True
            elif sem_type2 == SemTypes.long:
                result = False
            elif sem_type2 == SemTypes.long_long:
                result = False
            else:
                raise AttributeError("Нет семантического типа sem_type2 со значением {}".format(sem_type2))
        else:
            raise AttributeError("Нет семантического типа sem_type1 со значением {}".format(sem_type1))
        return result

    def __convert_sem_type_to_string(self, sem_type):
        if sem_type == SemTypes.long_long:
            return 'long long'
        elif sem_type == SemTypes.short:
            return 'short'
        elif sem_type == SemTypes.long:
            return 'long'
        else:
            raise AttributeError("Нет семантического типа с номером: {}".format(sem_type))

    def __check_value_and_sem_type(self, sem_type, value):
        """
            Функция проверяет, находится ли значение в пределах данного типа
        """
        if sem_type == SemTypes.long_long:
            return -2 ** 63 <= value <= 2 ** 63 - 1
        elif sem_type == SemTypes.long:
            return -2 ** 31 <= value <= 2 ** 31 - 1
        elif sem_type == SemTypes.short:
            return -2 ** 15 <= value <= 2 ** 15 - 1
        else:
            raise AttributeError("Нет семантического типа с номером: {}".format(sem_type))
