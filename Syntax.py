import AliasesRules as al_rules
import Scanner
from Aliases import LexNames as al_names
from Aliases import LexTypes as al_lexems
from AliasesSemFuncs import AliasesSemFuncs as al_funcs
from SemTree import SemTree, SemError


class SyntaxAnalyzer:
    """ синтаксический анализатор с использованием магазина и LL(1) грамматики """

    def __init__(self):
        self.__stack = []  # магазин
        self.__triplets = []  # триады
        self.__unresolved_triplet = None
        self.__lexems = []
        self.__tree_pointer = None
        self.__current_types = []  # прочитанные типы (short int и т д)
        self.__kept_type = None
        self.__kept_func = None
        self.__current_identifier = None  # текущий прочитанный идентификатор
        self.__current_identifier2 = None
        self.__current_identifier_type = None
        self.__current_node = None
        self.__current_const = None
        self.__current_val = None
        self.__current_func = None  # текущая функция
        self.__current_func_memory = 0  # количество байт, выделяемое для лок. пер. функции
        self.__results = []  # результаты арифметических операций

        self.__salt = 1
        self.__address1 = []
        self.__address2 = []
        self.__address3 = []
        self.__address4 = []

        self.__jzaddress3 = []

        self.__sem_tree = SemTree()
        # self.__create_table()

    def get_var_new_name(self, var_name):
        s = str(var_name) + "_" + str(self.__salt)
        self.__salt += 1
        return s

    def feed_text(self, text):
        self.__lexems = []
        sc = Scanner.Scanner()
        for lexem in sc.feed_text(text):
            if lexem['mistake']:
                raise SyntaxError("В работе сканера обнаружены ошибки. \n"
                                  "Ошибка в {0} строке и {1} столбце: {2}"
                                  .format(lexem['row'], lexem['column'], lexem['text']))
            else:
                self.__lexems.append(lexem)
        # добавляем лексему окончания файла
        self.__lexems.append({'type': al_lexems.T_EOF})
        return self

    def __init_pointer(self):
        self.__current_pointer = 0

    def __get_lexem(self):
        if self.__current_pointer < len(self.__lexems):
            self.__current_pointer += 1
            return self.__lexems[self.__current_pointer - 1]
        else:
            raise EOFError()

    def __get_current_pointer(self):
        return self.__current_pointer

    def __set_saved_pointer(self, pointer):
        self.__current_pointer = pointer

    def analyze(self):
        try:
            return self.__analyze()
        except SemError as err:
            print('Семантическая ошибка')
            print('Строка: {0}, столбцец: {1}'.format(self.__lexems[self.__get_current_pointer()]['row'],
                                                      self.__lexems[self.__get_current_pointer()]['column']))
            print(err)
            exit(1)

    def __analyze(self):
        self.__init_pointer()
        self.__stack = []
        self.__stack.append(Element('term', al_lexems.T_EOF))
        self.__stack.append(Element('rule', al_rules.PROGRAMM))

        cur_lexem = self.__get_lexem()
        prev_lexem = None
        while len(self.__stack):
            cur_element = self.__stack.pop()

            # нетерминалы
            if cur_element.element_type == 'rule':

                # <программа>
                if cur_element.type == al_rules.PROGRAMM:
                    if cur_lexem['type'] == al_lexems.T_LONG or \
                            cur_lexem['type'] == al_lexems.T_SHORT or \
                            cur_lexem['type'] == al_lexems.T_INT:
                        self.__stack.append(Element('rule', al_rules.PROGRAMM))
                        self.__stack.append(Element('rule', al_rules.DESR_OR_FUNC))
                    elif cur_lexem['type'] == al_lexems.T_EOF:
                        self.__stack.append(Element('term', al_lexems.T_EOF))
                    else:
                        raise SyntaxError(self.__get_error_text(
                            cur_lexem,
                            "Ожидалось: short, long, int. Прочитали: {0}".format(cur_lexem['str'])))

                # <описание д-х или ф-ия>
                elif cur_element.type == al_rules.DESR_OR_FUNC:
                    if cur_lexem['type'] == al_lexems.T_LONG or \
                            cur_lexem['type'] == al_lexems.T_SHORT:
                        self.__stack.append(Element('rule', al_rules.D))
                    elif cur_lexem['type'] == al_lexems.T_INT:
                        self.__stack.append(Element('rule', al_rules.FUNC))
                        self.__stack.append(Element('func', al_funcs.keep_var))
                        self.__stack.append(Element('term', al_lexems.T_MAIN))
                        self.__stack.append(Element('func', al_funcs.keep_type))
                        self.__stack.append(Element('term', al_lexems.T_INT))
                    else:
                        raise SyntaxError(self.__get_error_text(
                            cur_lexem, "Ожидалось: short, long, int. Прочитали: {0}"
                                .format(cur_lexem['str'])))

                # <D>
                elif cur_element.type == al_rules.D:
                    if cur_lexem['type'] == al_lexems.T_SHORT or \
                            cur_lexem['type'] == al_lexems.T_LONG:
                        self.__stack.append(Element('rule', al_rules.D2))
                        self.__stack.append(Element('rule', al_rules.TYPE))
                    else:
                        raise SyntaxError(self.__get_error_text(
                            cur_lexem, "Ожидалось: short, long. Прочитали: {0}"
                                .format(cur_lexem['str'])))

                # <тип>
                elif cur_element.type == al_rules.TYPE:
                    if cur_lexem['type'] == al_lexems.T_SHORT:
                        self.__stack.append(Element('rule', al_rules.D3))
                        self.__stack.append(Element('term', al_lexems.T_SHORT))

                    elif cur_lexem['type'] == al_lexems.T_LONG:
                        self.__stack.append(Element('rule', al_rules.D4))
                        self.__stack.append(Element('term', al_lexems.T_LONG))

                    else:
                        raise SyntaxError(self.__get_error_text(
                            cur_lexem,
                            'Ожидалось long или short. Прочитали {}'
                                .format(cur_lexem['str'])))

                # <D3>
                elif cur_element.type == al_rules.D3:
                    # если прочитали int
                    if cur_lexem['type'] == al_lexems.T_INT:
                        self.__stack.append(Element('func', al_funcs.keep_type))
                        self.__stack.append(Element('term', al_lexems.T_INT))
                    else:
                        self.__stack.append(Element('func', al_funcs.keep_type))

                # <D4>
                elif cur_element.type == al_rules.D4:
                    # если прочитали long
                    if cur_lexem['type'] == al_lexems.T_LONG:
                        self.__stack.append(Element('func', al_funcs.keep_type))
                        self.__stack.append(Element('term', al_lexems.T_LONG))
                    else:
                        self.__stack.append(Element('func', al_funcs.keep_type))

                # <D2>
                elif cur_element.type == al_rules.D2:
                    if cur_lexem['type'] == al_lexems.T_IDENT:
                        self.__stack.append(Element('rule', al_rules.D5))
                        self.__stack.append(Element('func', al_funcs.keep_var))
                        self.__stack.append(Element('term', al_lexems.T_IDENT))
                    else:
                        raise SyntaxError(self.__get_error_text(
                            cur_lexem,
                            'Ожидался идентификатор. Прочитали {}'
                                .format(cur_lexem['str'])))

                # <D5>
                elif cur_element.type == al_rules.D5:
                    if cur_lexem['type'] == al_lexems.T_LEFT_BRACKET:
                        self.__stack.append(Element('rule', al_rules.FUNC))
                    else:
                        self.__stack.append(Element('term', al_lexems.T_SEMICOLON))
                        self.__stack.append(Element('rule', al_rules.IDENT_INTERPET))
                        self.__stack.append(Element('func', al_funcs.add_var))

                # <ф-ия>
                elif cur_element.type == al_rules.FUNC:
                    if cur_lexem['type'] == al_lexems.T_LEFT_BRACKET:
                        self.__stack.append(Element('func', al_funcs.generate_end_func))
                        self.__stack.append(Element('func', al_funcs.generate_end_memory_func))
                        self.__stack.append(Element('rule', al_rules.BLOCK))
                        self.__stack.append(Element('func', al_funcs.generate_memory_func))
                        self.__stack.append(Element('func', al_funcs.generate_func))
                        self.__stack.append(Element('func', al_funcs.add_func))
                        self.__stack.append(Element('term', al_lexems.T_RIGHT_BRACKET))
                        self.__stack.append(Element('term', al_lexems.T_LEFT_BRACKET))
                    else:
                        raise SyntaxError(self.__get_error_text(
                            cur_lexem,
                            "Ожидали '('. Прочитали '{}'".format(cur_lexem['str'])))

                # <опр. идентификатора>
                elif cur_element.type == al_rules.IDENT_INTERPET:
                    self.__stack.append(Element('rule', al_rules.DU))
                    self.__stack.append(Element('rule', al_rules.ASSIGNMENT_Q))

                # <DU>
                elif cur_element.type == al_rules.DU:
                    if cur_lexem['type'] == al_lexems.T_COMMA:
                        self.__stack.append(Element('rule', al_rules.IDENT_INTERPET))
                        self.__stack.append(Element('func', al_funcs.add_var))
                        self.__stack.append(Element('func', al_funcs.keep_var))
                        self.__stack.append(Element('term', al_lexems.T_IDENT))
                        self.__stack.append(Element('term', al_lexems.T_COMMA))
                    else:
                        self.__stack.append(Element('term', al_lexems.T_EPS))

                # <присваивание?>
                elif cur_element.type == al_rules.ASSIGNMENT_Q:
                    if cur_lexem['type'] == al_lexems.T_ASSIGNMENT:
                        self.__stack.append(Element('func', al_funcs.generate_assignment_triplet))
                        self.__stack.append(Element('func', al_funcs.check_type))
                        self.__stack.append(Element('rule', al_rules.EQUATION))
                        self.__stack.append(Element('term', al_lexems.T_ASSIGNMENT))
                    else:
                        self.__stack.append(Element('term', al_lexems.T_EPS))

                # <блок>
                elif cur_element.type == al_rules.BLOCK:
                    if cur_lexem['type'] == al_lexems.T_LEFT_CURLY_BRACKET:
                        self.__stack.append(Element('func', al_funcs.end_block))
                        self.__stack.append(Element('term', al_lexems.T_RIGHT_CURLY_BRACKET))
                        self.__stack.append(Element('rule', al_rules.OPERATORS))
                        self.__stack.append(Element('func', al_funcs.begin_block))
                        self.__stack.append(Element('term', al_lexems.T_LEFT_CURLY_BRACKET))
                    else:
                        raise SyntaxError(self.__get_error_text(
                            cur_lexem,
                            "Ожидалось '{'. Прочитали: {}".format(cur_lexem['str'])))

                # <операторы>
                elif cur_element.type == al_rules.OPERATORS:
                    if cur_lexem['type'] == al_lexems.T_IDENT \
                            or cur_lexem['type'] == al_lexems.T_LEFT_CURLY_BRACKET \
                            or cur_lexem['type'] == al_lexems.T_RETURN \
                            or cur_lexem['type'] == al_lexems.T_FOR:
                        self.__stack.append(Element('rule', al_rules.OPERATORS))
                        self.__stack.append(Element('rule', al_rules.OPERATOR))
                    elif cur_lexem['type'] == al_lexems.T_SHORT \
                            or cur_lexem['type'] == al_lexems.T_LONG:
                        self.__stack.append(Element('rule', al_rules.OPERATORS))
                        self.__stack.append(Element('term', al_lexems.T_SEMICOLON))
                        self.__stack.append(Element('rule', al_rules.IDENT_INTERPET))
                        self.__stack.append(Element('func', al_funcs.add_var))
                        self.__stack.append(Element('func', al_funcs.keep_var))
                        self.__stack.append(Element('term', al_lexems.T_IDENT))
                        self.__stack.append(Element('rule', al_rules.TYPE))
                    else:
                        self.__stack.append(Element('term', al_lexems.T_EPS))

                # <оператор>
                elif cur_element.type == al_rules.OPERATOR:
                    if cur_lexem['type'] == al_lexems.T_IDENT:
                        self.__stack.append(Element('term', al_lexems.T_SEMICOLON))
                        self.__stack.append(Element('func', al_funcs.generate_assignment_triplet))
                        self.__stack.append(Element('func', al_funcs.check_type))
                        self.__stack.append(Element('rule', al_rules.EQUATION))
                        self.__stack.append(Element('term', al_lexems.T_ASSIGNMENT))
                        self.__stack.append(Element('func', al_funcs.find_type))
                        self.__stack.append(Element('func', al_funcs.keep_var))
                        self.__stack.append(Element('term', al_lexems.T_IDENT))
                    elif cur_lexem['type'] == al_lexems.T_LEFT_CURLY_BRACKET:
                        self.__stack.append(Element('rule', al_rules.BLOCK))
                    elif cur_lexem['type'] == al_lexems.T_FOR:
                        self.__stack.append(Element('rule', al_rules.FOR))
                    elif cur_lexem['type'] == al_lexems.T_SEMICOLON:
                        self.__stack.append(Element('term', al_lexems.T_SEMICOLON))
                    elif cur_lexem['type'] == al_lexems.T_RETURN:
                        self.__stack.append(Element('term', al_lexems.T_SEMICOLON))
                        self.__stack.append(Element('func', al_funcs.generate_triad_return))
                        self.__stack.append(Element('func', al_funcs.check_func_type))
                        self.__stack.append(Element('rule', al_rules.EQUATION))
                        self.__stack.append(Element('term', al_lexems.T_RETURN))
                    elif cur_lexem['type'] == al_lexems.T_LONG or cur_lexem['type'] == al_lexems.T_SHORT:
                        self.__stack.append(Element('term', al_lexems.T_SEMICOLON))
                        self.__stack.append(Element('rule', al_rules.IDENT_INTERPET))
                        self.__stack.append(Element('func', al_funcs.add_var))
                        self.__stack.append(Element('func', al_funcs.keep_var))
                        self.__stack.append(Element('term', al_lexems.T_IDENT))
                        self.__stack.append(Element('rule', al_rules.TYPE))

                    else:
                        raise SyntaxError(self.__get_error_text(
                            cur_lexem,
                            "Ожидалось: 'for', '{', ';', 'return', 'short', 'long' или идентификатор.\n"
                            "Прочитали: {}".format(cur_lexem['str'])
                        ))

                # <for>
                elif cur_element.type == al_rules.FOR:
                    self.__stack.append(Element('func', al_funcs.save_address4))
                    self.__stack.append(Element('func', al_funcs.jmp_address2))
                    self.__stack.append(Element('rule', al_rules.OPERATOR))
                    self.__stack.append(Element('func', al_funcs.save_address3))
                    self.__stack.append(Element('term', al_lexems.T_RIGHT_BRACKET))
                    self.__stack.append(Element('func', al_funcs.jmp_address1))
                    self.__stack.append(Element('rule', al_rules.ASSIGNMENT))
                    self.__stack.append(Element('func', al_funcs.save_address2))
                    self.__stack.append(Element('term', al_lexems.T_SEMICOLON))
                    self.__stack.append(Element('func', al_funcs.jz_address3))
                    self.__stack.append(Element('rule', al_rules.EQUATION))
                    self.__stack.append(Element('func', al_funcs.save_address1))
                    self.__stack.append(Element('term', al_lexems.T_SEMICOLON))
                    self.__stack.append(Element('rule', al_rules.ASSIGNMENT))
                    self.__stack.append(Element('term', al_lexems.T_LEFT_BRACKET))
                    self.__stack.append(Element('term', al_lexems.T_FOR))

                # <присваивание>
                elif cur_element.type == al_rules.ASSIGNMENT:
                    if cur_lexem['type'] == al_lexems.T_IDENT:
                        self.__stack.append(Element('func', al_funcs.generate_assignment_triplet))
                        self.__stack.append(Element('func', al_funcs.check_type))
                        self.__stack.append(Element('rule', al_rules.EQUATION))
                        self.__stack.append(Element('term', al_lexems.T_ASSIGNMENT))
                        self.__stack.append(Element('func', al_funcs.find_type))
                        self.__stack.append(Element('func', al_funcs.keep_var))
                        self.__stack.append(Element('term', al_lexems.T_IDENT))
                    else:
                        self.__stack.append(Element('term', al_lexems.T_EPS))

                # <выражение>
                elif cur_element.type == al_rules.EQUATION:
                    self.__stack.append(Element('rule', al_rules.M))

                # <M>
                elif cur_element.type == al_rules.M:
                    self.__stack.append(Element('rule', al_rules.M2))
                    self.__stack.append(Element('rule', al_rules.B))

                # <M2>
                elif cur_element.type == al_rules.M2:
                    if cur_lexem['type'] == al_lexems.T_NOT_EQUAL:
                        self.__stack.append(Element('rule', al_rules.M2))
                        self.__stack.append(Element('func', al_funcs.make_not_equal))
                        # self.__stack.append(Element('func', al_funcs.check_type))
                        self.__stack.append(Element('rule', al_rules.B))
                        self.__stack.append(Element('term', al_lexems.T_NOT_EQUAL))
                    elif cur_lexem['type'] == al_lexems.T_EQUAL:
                        self.__stack.append(Element('rule', al_rules.M2))
                        self.__stack.append(Element('func', al_funcs.make_equal))
                        # self.__stack.append(Element('func', al_funcs.check_type))
                        self.__stack.append(Element('rule', al_rules.B))
                        self.__stack.append(Element('term', al_lexems.T_EQUAL))
                    else:
                        self.__stack.append(Element('term', al_lexems.T_EPS))

                # <B>
                elif cur_element.type == al_rules.B:
                    self.__stack.append(Element('rule', al_rules.B2))
                    self.__stack.append(Element('rule', al_rules.N))

                # <B2>
                elif cur_element.type == al_rules.B2:
                    if cur_lexem['type'] == al_lexems.T_LESS:
                        self.__stack.append(Element('rule', al_rules.B2))
                        self.__stack.append(Element('func', al_funcs.make_less))
                        # self.__stack.append(Element('func', al_funcs.check_type))
                        self.__stack.append(Element('rule', al_rules.N))
                        self.__stack.append(Element('term', al_lexems.T_LESS))
                    elif cur_lexem['type'] == al_lexems.T_BIGGER:
                        self.__stack.append(Element('rule', al_rules.B2))
                        self.__stack.append(Element('func', al_funcs.make_bigger))
                        # self.__stack.append(Element('func', al_funcs.check_type))
                        self.__stack.append(Element('rule', al_rules.N))
                        self.__stack.append(Element('term', al_lexems.T_BIGGER))
                    elif cur_lexem['type'] == al_lexems.T_BIGGER_OR_EQUAL:
                        self.__stack.append(Element('rule', al_rules.B2))
                        self.__stack.append(Element('func', al_funcs.make_bigger_or_equal))
                        # self.__stack.append(Element('func', al_funcs.check_type))
                        self.__stack.append(Element('rule', al_rules.N))
                        self.__stack.append(Element('term', al_lexems.T_BIGGER_OR_EQUAL))
                    elif cur_lexem['type'] == al_lexems.T_LESS_OR_EQUAL:
                        self.__stack.append(Element('rule', al_rules.B2))
                        self.__stack.append(Element('func', al_funcs.make_less_or_equal))
                        # self.__stack.append(Element('func', al_funcs.check_type))
                        self.__stack.append(Element('rule', al_rules.N))
                        self.__stack.append(Element('term', al_lexems.T_LESS_OR_EQUAL))
                    else:
                        self.__stack.append(Element('term', al_lexems.T_EPS))

                # <N>
                elif cur_element.type == al_rules.N:
                    self.__stack.append(Element('rule', al_rules.N2))
                    self.__stack.append(Element('rule', al_rules.A))

                # <N2>
                elif cur_element.type == al_rules.N2:
                    if cur_lexem['type'] == al_lexems.T_PLUS:
                        self.__stack.append(Element('rule', al_rules.N2))
                        self.__stack.append(Element('func', al_funcs.make_add))
                        # self.__stack.append(Element('func', al_funcs.check_type))
                        self.__stack.append(Element('rule', al_rules.A))
                        self.__stack.append(Element('term', al_lexems.T_PLUS))
                    elif cur_lexem['type'] == al_lexems.T_MINUS:
                        self.__stack.append(Element('rule', al_rules.N2))
                        self.__stack.append(Element('func', al_funcs.make_sub))
                        # self.__stack.append(Element('func', al_funcs.check_type))
                        self.__stack.append(Element('rule', al_rules.A))
                        self.__stack.append(Element('term', al_lexems.T_MINUS))
                    else:
                        self.__stack.append(Element('term', al_lexems.T_EPS))

                # <A>
                elif cur_element.type == al_rules.A:
                    self.__stack.append(Element('rule', al_rules.A2))
                    self.__stack.append(Element('rule', al_rules.T))

                # <A2>
                elif cur_element.type == al_rules.A2:
                    if cur_lexem['type'] == al_lexems.T_MULTIPLY:
                        self.__stack.append(Element('rule', al_rules.A2))
                        self.__stack.append(Element('func', al_funcs.make_multiply))
                        # self.__stack.append(Element('func', al_funcs.check_type))
                        self.__stack.append(Element('rule', al_rules.T))
                        self.__stack.append(Element('term', al_lexems.T_MULTIPLY))
                    elif cur_lexem['type'] == al_lexems.T_DIVIDER:
                        self.__stack.append(Element('rule', al_rules.A2))
                        self.__stack.append(Element('func', al_funcs.make_division))
                        # self.__stack.append(Element('func', al_funcs.check_type))
                        self.__stack.append(Element('rule', al_rules.T))
                        self.__stack.append(Element('term', al_lexems.T_DIVIDER))
                    elif cur_lexem['type'] == al_lexems.T_REMAINDER:
                        self.__stack.append(Element('rule', al_rules.A2))
                        self.__stack.append(Element('func', al_funcs.make_division_remainder))
                        # self.__stack.append(Element('func', al_funcs.check_type))
                        self.__stack.append(Element('rule', al_rules.T))
                        self.__stack.append(Element('term', al_lexems.T_REMAINDER))
                    else:
                        self.__stack.append(Element('term', al_lexems.T_EPS))

                # <T>
                elif cur_element.type == al_rules.T:
                    if cur_lexem['type'] == al_lexems.T_CONST_10 \
                            or cur_lexem['type'] == al_lexems.T_CONST_16:
                        self.__stack.append(Element('func', al_funcs.save_r))
                        self.__stack.append(Element('func', al_funcs.check_const))
                        if cur_lexem['type'] == al_lexems.T_CONST_16:
                            self.__stack.append(Element('term', al_lexems.T_CONST_16))
                        else:
                            self.__stack.append(Element('term', al_lexems.T_CONST_10))
                    elif cur_lexem['type'] == al_lexems.T_IDENT:
                        self.__stack.append(Element('rule', al_rules.FUNC_CALL_OR_IDENT))
                    elif cur_lexem['type'] == al_lexems.T_LEFT_BRACKET:
                        self.__stack.append(Element('term', al_lexems.T_RIGHT_BRACKET))
                        self.__stack.append(Element('rule', al_rules.M))
                        self.__stack.append(Element('term', al_lexems.T_LEFT_BRACKET))
                    else:
                        raise SyntaxError(self.__get_error_text(
                            cur_lexem,
                            "Ожидали: '(', константу или идентификатор. Прочитали: {}".format(cur_lexem['str'])
                        ))

                # <вызов ф-ии или идент>
                elif cur_element.type == al_rules.FUNC_CALL_OR_IDENT:
                    self.__stack.append(Element('rule', al_rules.BRACKETS))
                    self.__stack.append(Element('func', al_funcs.find_node))
                    self.__stack.append(Element('func', al_funcs.keep_var2))
                    self.__stack.append(Element('term', al_lexems.T_IDENT))

                # <скобки>
                elif cur_element.type == al_rules.BRACKETS:
                    if cur_lexem['type'] == al_lexems.T_LEFT_BRACKET:
                        self.__stack.append(Element('func', al_funcs.generate_call_function))
                        self.__stack.append(Element('term', al_lexems.T_RIGHT_BRACKET))
                        self.__stack.append(Element('term', al_lexems.T_LEFT_BRACKET))
                    else:
                        self.__stack.append(Element('func', al_funcs.save_r))

            # терминалы
            elif cur_element.element_type == 'term':
                if cur_element.type == al_lexems.T_EOF or cur_element.type == al_lexems.T_EPS:
                    pass

                elif cur_lexem['type'] != cur_element.type:
                    raise SyntaxError(self.__get_error_text(
                        cur_lexem,
                        "Ожидали {0}. Прочитали {1}".format(
                            al_names.get(cur_element.type), cur_lexem['str'])
                    ))
                else:
                    # если прочитали типы, запомним их
                    if cur_element.type == al_lexems.T_SHORT \
                            or cur_element.type == al_lexems.T_INT \
                            or cur_element.type == al_lexems.T_LONG:
                        self.__current_types.append(cur_element.type)

                    # запомним идентификатор
                    # elif cur_element.type == al_lexems.T_IDENT:
                    #    self.__current_identifier = cur_lexem['str']

                    # запомним константу
                    elif cur_element.type == al_lexems.T_CONST_10 \
                            or cur_element.type == al_lexems.T_CONST_16:
                        self.__current_const = cur_lexem['str']
                    prev_lexem = cur_lexem
                    cur_lexem = self.__get_lexem()

            # семантические функции
            elif cur_element.element_type == 'func':

                # KeepType
                if cur_element.type == al_funcs.keep_type:
                    self.__kept_type = \
                        self.__sem_tree \
                            .lex_type_to_semtype(self.__current_types)
                    self.__current_types.clear()

                # AddVar
                elif cur_element.type == al_funcs.add_var:
                    alter = self.get_var_new_name(self.__current_identifier)
                    self.__current_func_memory += \
                        self.__sem_tree.add_variable(self.__current_identifier,
                                                     self.__kept_type,
                                                     self.get_var_new_name(self.__current_identifier))

                    self.__results.append({'value': alter,
                                           'type': self.__kept_type,
                                           'triplet_type': 'value'})

                # AddFunc
                elif cur_element.type == al_funcs.add_func:
                    alter = self.get_var_new_name(self.__current_identifier)
                    func = self.__sem_tree.add_func(self.__current_identifier,
                                                    self.__kept_type, alter)
                    self.__current_func = func.node

                # GenerateFunc
                elif cur_element.type == al_funcs.generate_func:
                    self.__current_func_memory = 0
                    self.__triplets.append(self.__sem_tree.generate_func_triple(self.__current_func.alternate_name))

                # GenerateMemoryFunc
                elif cur_element.type == al_funcs.generate_memory_func:
                    self.__unresolved_triplet = self.__sem_tree.generate_memory_func_triple()
                    self.__triplets.append(self.__unresolved_triplet)

                # GenerateEndMemoryFunc
                elif cur_element.type == al_funcs.generate_end_memory_func:
                    self.__sem_tree.resolve_triplet(self.__unresolved_triplet,
                                                    self.__current_func_memory,
                                                    'value')
                    self.__triplets.append(self.__sem_tree.generate_memory_end_func_triple(
                        self.__current_func_memory))
                    self.__current_func_memory = 0

                # GenerateEndFunc
                elif cur_element.type == al_funcs.generate_end_func:
                    triplet = self.__sem_tree.generate_func_end_triple(self.__current_func.alternate_name)
                    self.__triplets.append(triplet)

                # GenerateTriadReturn
                elif cur_element.type == al_funcs.generate_triad_return:
                    val = self.__results.pop()
                    self.__triplets.append(self.__sem_tree.generate_return_triple(val))

                # CheckFuncType
                elif cur_element.type == al_funcs.check_func_type:
                    self.__sem_tree.return_check(self.__current_func.sem_type,
                                                 self.__results[-1]['type'])

                # FindType
                elif cur_element.type == al_funcs.find_type:
                    var = self.__sem_tree.find_variable(self.__current_identifier)
                    self.__results.append({'value': var.alternate_name,
                                           'type': var.sem_type,
                                           'triplet_type': 'value'})

                # KeepVar
                elif cur_element.type == al_funcs.keep_var:
                    self.__current_identifier = prev_lexem['str']

                # KeepVar2
                elif cur_element.type == al_funcs.keep_var2:
                    self.__current_identifier2 = prev_lexem['str']

                # CheckType
                elif cur_element.type == al_funcs.check_type:
                    val2 = self.__results[-1]
                    val1 = self.__results[-2]
                    self.__sem_tree.assignment_check(val1['type'], val2['type'])

                # CheckConst
                elif cur_element.type == al_funcs.check_const:
                    self.__current_val = self.__sem_tree.check_const(self.__current_const)

                # SaveR
                elif cur_element.type == al_funcs.save_r:
                    self.__results.append(self.__sem_tree.save_r(self.__current_val))
                    self.__current_val = None

                # FindNode
                elif cur_element.type == al_funcs.find_node:
                    self.__current_node = self.__sem_tree.find_node(self.__current_identifier2)
                    self.__current_val = self.__sem_tree.get_variable_val(self.__current_node)

                # BeginBlock
                elif cur_element.type == al_funcs.begin_block:
                    self.__tree_pointer = self.__sem_tree.add_block()

                # EndBlock
                elif cur_element.type == al_funcs.end_block:
                    self.__sem_tree.pointer = self.__tree_pointer

                # GenerateCallFunction
                elif cur_element.type == al_funcs.generate_call_function:
                    triplet = self.__sem_tree.generate_func_call_triple(
                        self.__current_node
                    )
                    self.__triplets.append(triplet)
                    self.__results.append({'type': self.__current_node.sem_type,
                                           'value': triplet.number,
                                           'triplet_type': 'link'})

                # GenerateTriadAssign
                elif cur_element.type == al_funcs.generate_assignment_triplet:
                    val = self.__results.pop()
                    self.__results.pop()
                    node = self.__sem_tree.find_variable(self.__current_identifier)
                    self.__triplets.append(self.__sem_tree.generate_assignment_triple(
                        node.alternate_name,
                        val['value'],
                        val['triplet_type']))

                # цикл for
                # SaveAddress1
                elif cur_element.type == al_funcs.save_address1:
                    self.__address1.append(self.__sem_tree.generate_nop())
                    self.__triplets.append(self.__address1[-1])

                # JzAddress3
                elif cur_element.type == al_funcs.jz_address3:
                    self.__jzaddress3.append(self.__sem_tree.generate_jz())
                    self.__triplets.append(self.__jzaddress3[-1])

                # SaveAddress2
                elif cur_element.type == al_funcs.save_address2:
                    self.__address2.append(self.__sem_tree.generate_nop())
                    self.__triplets.append(self.__address2[-1])

                # JmpAddress1
                elif cur_element.type == al_funcs.jmp_address1:
                    self.__triplets.append(self.__sem_tree.generate_jmp(self.__address1.pop().number))

                # SaveAddress3
                elif cur_element.type == al_funcs.save_address3:
                    address3 = self.__sem_tree.generate_nop()
                    self.__triplets.append(address3)
                    self.__sem_tree.resolve_triplet(self.__jzaddress3[-1], address3.number, 'link')

                # JmpAddress2
                elif cur_element.type == al_funcs.jmp_address2:
                    self.__triplets.append(self.__sem_tree.generate_jmp(self.__address2.pop().number))

                # SaveAddress4
                elif cur_element.type == al_funcs.save_address4:
                    address4 = self.__sem_tree.generate_nop()
                    self.__triplets.append(address4)
                    self.__sem_tree.resolve_triplet(self.__jzaddress3.pop(), address4.number, 'link')

                # арифметические операции
                # %
                elif cur_element.type == al_funcs.make_division_remainder:
                    val2 = self.__results.pop()
                    val1 = self.__results.pop()
                    triplet, sem_type = self.__sem_tree.eq_operation(val1, val2, '%')
                    self.__triplets.append(triplet)
                    self.__results.append({'value': triplet.number,
                                           'type': sem_type,
                                           'triplet_type': 'link'})

                # /
                elif cur_element.type == al_funcs.make_division:
                    val2 = self.__results.pop()
                    val1 = self.__results.pop()
                    triplet, sem_type = self.__sem_tree.eq_operation(val1, val2, '/')
                    self.__triplets.append(triplet)
                    self.__results.append({'value': triplet.number,
                                           'type': sem_type,
                                           'triplet_type': 'link'})

                # *
                elif cur_element.type == al_funcs.make_multiply:
                    val2 = self.__results.pop()
                    val1 = self.__results.pop()
                    triplet, sem_type = self.__sem_tree.eq_operation(val1, val2, '*')
                    self.__triplets.append(triplet)
                    self.__results.append({'value': triplet.number,
                                           'type': sem_type,
                                           'triplet_type': 'link'})

                # >
                elif cur_element.type == al_funcs.make_bigger:
                    val2 = self.__results.pop()
                    val1 = self.__results.pop()
                    triplet, sem_type = self.__sem_tree.eq_operation(val1, val2, '>')
                    self.__triplets.append(triplet)
                    self.__results.append({'value': triplet.number,
                                           'type': sem_type,
                                           'triplet_type': 'link'})

                # <
                elif cur_element.type == al_funcs.make_less:
                    val2 = self.__results.pop()
                    val1 = self.__results.pop()
                    triplet, sem_type = self.__sem_tree.eq_operation(val1, val2, '<')
                    self.__triplets.append(triplet)
                    self.__results.append({'value': triplet.number,
                                           'type': sem_type,
                                           'triplet_type': 'link'})

                # >=
                elif cur_element.type == al_funcs.make_bigger_or_equal:
                    val2 = self.__results.pop()
                    val1 = self.__results.pop()
                    triplet, sem_type = self.__sem_tree.eq_operation(val1, val2, '>=')
                    self.__triplets.append(triplet)
                    self.__results.append({'value': triplet.number,
                                           'type': sem_type,
                                           'triplet_type': 'link'})

                # <=
                elif cur_element.type == al_funcs.make_less_or_equal:
                    val2 = self.__results.pop()
                    val1 = self.__results.pop()
                    triplet, sem_type = self.__sem_tree.eq_operation(val1, val2, '<=')
                    self.__triplets.append(triplet)
                    self.__results.append({'value': triplet.number,
                                           'type': sem_type,
                                           'triplet_type': 'link'})
                # !=
                elif cur_element.type == al_funcs.make_not_equal:
                    val2 = self.__results.pop()
                    val1 = self.__results.pop()
                    triplet, sem_type = self.__sem_tree.eq_operation(val1, val2, '!=')
                    self.__triplets.append(triplet)
                    self.__results.append({'value': triplet.number,
                                           'type': sem_type,
                                           'triplet_type': 'link'})

                # ==
                elif cur_element.type == al_funcs.make_equal:
                    val2 = self.__results.pop()
                    val1 = self.__results.pop()
                    triplet, sem_type = self.__sem_tree.eq_operation(val1, val2, '==')
                    self.__triplets.append(triplet)
                    self.__results.append({'value': triplet.number,
                                           'type': sem_type,
                                           'triplet_type': 'link'})

                # +
                elif cur_element.type == al_funcs.make_add:
                    val2 = self.__results.pop()
                    val1 = self.__results.pop()
                    triplet, sem_type = self.__sem_tree.eq_operation(val1, val2, '+')
                    self.__triplets.append(triplet)
                    self.__results.append({'value': triplet.number,
                                           'type': sem_type,
                                           'triplet_type': 'link'})

                # -
                elif cur_element.type == al_funcs.make_sub:
                    val2 = self.__results.pop()
                    val1 = self.__results.pop()
                    triplet, sem_type = self.__sem_tree.eq_operation(val1, val2, '-')
                    self.__triplets.append(triplet)
                    self.__results.append({'value': triplet.number,
                                           'type': sem_type,
                                           'triplet_type': 'link'})

        return self.__triplets, self.__sem_tree

    def __get_error_text(self, lexem, additional_text=''):
        return 'Ошибка в {0} строке и {1} столбце: {2}' \
            .format(lexem['row'], lexem['column'], additional_text)


class Element:
    """
        элемент магазина (терминал или нетерминал)
    """

    # term_type: 'rule' - нетерминал, 'term' - терминал, 'func' - сем функция
    # type_lex: тип лексемы/правила
    def __init__(self, el_type, type_lex):
        self.__term_type = el_type
        self.__lex_type = type_lex

    @property
    def element_type(self):
        """ правило или терминал """
        return self.__term_type

    @property
    def type(self):
        """ тип конкретного правила или терминала """
        return self.__lex_type

    def __str__(self):
        return str({'element': self.element_type, 'type': self.type})
