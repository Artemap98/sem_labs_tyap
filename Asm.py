from collections import defaultdict

from Triplet import TripletOperation, TripletOperandType


class AsmGenerator:
    def __init__(self):
        self.__triplets = []
        self.__asm_code = []
        self.__registers = Register()
        self.__stack_pointer = 0
        self.__stack_elements = []

    def generate(self, triplets, sem_tree):
        asm_code = []
        current_level = 0
        self.__triplets = triplets
        self.__asm_code.clear()
        self.__registers.reset()
        self.__stack_pointer = 0
        nodes = sem_tree.find_all_nodes_in_all_tree()

        # сначала пробежимся по всем триадам, выделим арифметические и посчитаем кол-во
        # раз, которые они используются (это нужно для того, чтобы знать, когда можно
        # освобождать регистр)
        used_arithm_triplets = defaultdict(lambda: 0)

        for triplet in triplets:
            if triplet.first_arg_type == TripletOperandType.link:
                used_arithm_triplets[triplet.first_arg] += 1
            if triplet.second_arg_type == TripletOperandType.link:
                used_arithm_triplets[triplet.second_arg] += 1

        # объявим данные
        asm_code.append(AsmLine('.data'))
        for node in nodes['var']:
            asm_code.append(AsmLine('{0} dd 0'.format(node.alternate_name), level=1))

        asm_code.append(AsmLine(''))
        asm_code.append(AsmLine('.code'))

        triplets_values = {}

        current_level += 1
        for triplet in self.__triplets:
            if triplet.operation == TripletOperation.generate_func:
                asm_code.append(AsmLine('', level=current_level))
                asm_code.append(AsmLine('proc {}'.format(triplet.first_arg), level=current_level))
                current_level += 1
                asm_code.append(AsmLine('push ebp', level=current_level))
                asm_code.append(AsmLine('push esp', level=current_level))
                asm_code.append(AsmLine('push eax', level=current_level))
                asm_code.append(AsmLine('push ebx', level=current_level))
                asm_code.append(AsmLine('push ecx', level=current_level))
                asm_code.append(AsmLine('push edx', level=current_level))
                asm_code.append(AsmLine('push esi', level=current_level))
                asm_code.append(AsmLine('push edi', level=current_level))

            elif triplet.operation == TripletOperation.generate_end_func:
                asm_code.append(AsmLine('pop edi', level=current_level))
                asm_code.append(AsmLine('pop esi', level=current_level))
                asm_code.append(AsmLine('pop edx', level=current_level))
                asm_code.append(AsmLine('pop ecx', level=current_level))
                asm_code.append(AsmLine('pop ebx', level=current_level))
                asm_code.append(AsmLine('pop eax', level=current_level))
                asm_code.append(AsmLine('pop esp', level=current_level))
                asm_code.append(AsmLine('pop ebp', level=current_level))
                current_level -= 1
                asm_code.append(AsmLine('endp {}'.format(triplet.first_arg), level=current_level))

            elif triplet.operation == TripletOperation.plus:
                try:
                    register = self.get_free_register_or_stack()
                except LookupError:
                    print('err')
                    return asm_code
                code = self.make_operation(triplet.operation,
                                           triplet,
                                           register,
                                           used_arithm_triplets,
                                           triplets_values)
                for line in code:
                    asm_code.append(AsmLine(line, level=current_level))

            elif triplet.operation == TripletOperation.minus:
                try:
                    register = self.get_free_register_or_stack()
                except LookupError:
                    print('err')
                    return asm_code
                code = self.make_operation(triplet.operation,
                                           triplet,
                                           register,
                                           used_arithm_triplets,
                                           triplets_values)
                for line in code:
                    asm_code.append(AsmLine(line, level=current_level))
            elif triplet.operation == TripletOperation.assignment:
                code = 'mov [{}], '.format(triplet.first_arg)
                if triplet.second_arg_type == TripletOperandType.value:
                    try:
                        a = str(int(triplet.second_arg))
                        code += a
                    except:
                        reg = self.get_free_register_or_stack()
                        asm_code.append(AsmLine('mov {0}, [{1}]'.format(reg, triplet.second_arg)))
                        code += reg
                        self.free_register_or_stack({'value': reg, 'type': 'register'})
                else:
                    used_arithm_triplets[triplet.second_arg] -= 1
                    if used_arithm_triplets[triplet.second_arg] == 0:
                        self.free_register_or_stack(triplets_values[triplet.second_arg])
                    code += triplets_values[triplet.second_arg]['value']
                asm_code.append(AsmLine(code, level=current_level))

            elif triplet.operation == TripletOperation.generate_return:
                code = 'mov eax, '
                if triplet.first_arg_type == TripletOperandType.value:
                    try:
                        a = str(int(triplet.first_arg))
                        code += a
                    except:
                        code += '[{}]'.format(triplet.first_arg)
                else:
                    used_arithm_triplets[triplet.first_arg] -= 1
                    if used_arithm_triplets[triplet.first_arg] == 0:
                        self.free_register_or_stack(triplets_values[triplet.first_arg])
                    code += triplets_values[triplet.first_arg]['value']
                asm_code.append(AsmLine(code, level=current_level))

        return asm_code

    def make_operation(self, operation, triplet, register, used_arithm_triplets, triplets_values):
        code = []
        if operation == TripletOperation.plus:
            oper = 'add'
        else:
            oper = 'sub'

        first_arg = None

        if triplet.first_arg_type == TripletOperandType.link:
            used_arithm_triplets[triplet.first_arg] -= 1
            first_arg = triplets_values[triplet.first_arg]['value']
            if used_arithm_triplets[triplet.first_arg] == 0:
                self.free_register_or_stack(triplets_values[triplet.first_arg])

        else:
            try:
                a = int(triplet.first_arg)
                first_arg = triplet.first_arg
            except:
                first_arg = '[{}]'.format(triplet.first_arg)

        second_arg = None
        if triplet.second_arg_type == TripletOperandType.link:
            used_arithm_triplets[triplet.second_arg] -= 1
            second_arg = triplets_values[triplet.second_arg]['value']
            if used_arithm_triplets[triplet.second_arg] == 0:
                self.free_register_or_stack(triplets_values[triplet.second_arg])

        else:
            try:
                a = int(triplet.second_arg)
                second_arg = triplet.second_arg
            except:
                second_arg = '[{}]'.format(triplet.second_arg)

        code.append('mov {0}, {1}'.format(register, first_arg))
        code.append('{0} {1}, {2}'.format(oper, register, second_arg))
        triplets_values[triplet.number] = {'value': register, 'type': 'register'}
        return code

    def get_free_register_or_stack(self):
        return self.__registers.get_free_register()

    def free_register_or_stack(self, val_info):
        self.__registers.free_register(val_info['value'])


class AsmLine:
    def __init__(self, s, level=0):
        self.__s = '  ' * level + s

    def __str__(self):
        return self.__s


class Register:
    def __init__(self):
        self.__registers = [['eax', True],
                            ['ebx', True],
                            ['ecx', True],
                            ['edx', True],
                            ['esi', True],
                            ['edi', True],
                            ['ebp', True]]

    def reset(self):
        for reg in self.__registers:
            reg[1] = True

    def free_register(self, register_name):
        for reg in self.__registers:
            if reg[0] == register_name:
                reg[1] = True
                break

    def get_free_register(self):
        reg = None
        for i in range(len(self.__registers)):
            if self.__registers[i][1]:
                self.__registers[i][1] = False
                reg = self.__registers[i][0]
                break
        if reg is None:
            raise LookupError("Нет свободных регистров")
        return reg
