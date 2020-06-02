from Triplet import Triplet
from Triplet import TripletOperation, TripletOperandType


class TripletList(list):

    def __init__(self, triplets: list = None):
        super().__init__()
        if triplets is not None:
            for triplet in triplets:
                self.append(triplet)

    def append(self, obj):
        if not isinstance(obj, Triplet):
            raise ValueError("Список может хранить только триады")
        super().append(obj)

    def get_index_by_triplet_number(self, triplet_number):
        for i, obj in enumerate(self):
            if obj.number == triplet_number:
                return i
        return None

    def delete_by_triplet_number(self, triplet_number):
        remove_item = None
        for item in self:
            if item.number == triplet_number:
                remove_item = item
                break
        self.remove(remove_item)


class VisitedTripletsList(list):

    def delete_last(self):
        return VisitedTripletsList(self[:-1])

    def get_base_element(self, triplet_number):
        """
            возврщает базовый элемент.
            То есть, в массиве [[1, 2, 3], [4, 5, 6]] при triplet_number = 6
            =>return 4;
            Если triplet_number равен базовому элементу, если triplet_number нет в массиве вообще,
            выбрасывается исключение
        """
        if triplet_number not in self.ravel():
            raise ValueError("Триады с таким номером нет в списке")
        for arr in self:
            if arr[0] == triplet_number:
                raise ValueError("Триада с таким номером равна базовой")
            if triplet_number in arr[1:]:
                return arr[0]

    def ravel(self, except_elements=0):
        """
            привести массив к одномерному.
            except_elements - количество элементов,
            которые нужно пропустить в начале вложенных массивов.
            Например, если массив = [[1, 2, 3], [4, 5, 6]], то при except_elements = 1
            => [2, 3, 5, 6]
            Если число отрицательное, то, наоборот, берем это количество элементов с начала
            Например, если массив = [[1, 2, 3], [4, 5, 6]], то при except_elements = -2
            => [1, 2, 4, 5]
        """
        res = []
        self.__ravel_array(res, self, except_elements)
        return res

    def is_ravel(self, l):
        for item in l:
            if isinstance(item, list) or isinstance(item, tuple):
                return False
        return True

    def __ravel_array(self, res: list, go_through, except_elements=0):
        if self.is_ravel(go_through):
            if except_elements >= 0:
                arr = go_through[except_elements:]
            else:
                arr = go_through[:abs(except_elements)]
            for obj in arr:
                res.append(obj)
        else:
            for obj in go_through:
                self.__ravel_array(res, obj, except_elements)


class TripletOptimization:
    def __init__(self, triplets):
        self.__triplets = TripletList(triplets)

    def optimize(self):
        graph = self.make_graph()
        res = []
        for node in graph.nodes():
            # сначала выделим все повторяющиеся арифметические триады
            first = self.__triplets.get_index_by_triplet_number(node.first)
            last = self.__triplets.get_index_by_triplet_number(node.last)
            multiple_triplets = VisitedTripletsList()

            for i in range(first, last + 1):
                triplet1 = self.__triplets[i]
                if triplet1.number in multiple_triplets.ravel():
                    continue
                check_func = None
                if triplet1.operation == TripletOperation.plus \
                        or triplet1.operation == TripletOperation.multiply:
                    check_func = lambda x, y: x.shallow_equal(y)
                elif triplet1.operation == TripletOperation.minus \
                        or triplet1.operation == TripletOperation.divide:
                    check_func = lambda x, y: x.deep_equal(y)
                else:
                    continue

                multiple_triplets.append([triplet1.number])
                is_assignment = False

                for j in range(i + 1, last + 1):
                    triplet2 = self.__triplets[j]
                    # если произошло изменения значения одного из операндов
                    # triplet1, дальнейшая оптимизация невозможна.
                    # удаляем ее вместе с базой
                    if triplet2.operation == TripletOperation.assignment:
                        if triplet2.first_arg == triplet1.first_arg \
                                or triplet2.first_arg == triplet1.second_arg:
                            is_assignment = True
                            break

                    if triplet2.number in multiple_triplets.ravel():
                        continue

                    if triplet1.operation == triplet2.operation and check_func(triplet1, triplet2) \
                            and is_assignment:
                        break
                    if triplet1.operation == triplet2.operation \
                            and check_func(triplet1, triplet2):
                        multiple_triplets[-1].append(triplet2.number)

            # теперь имеем двумерный массив повторяющихся триад
            # например, [[1, 2, 3], [6, 8, 10]] означает, что
            # триады 1, 2 и 3 равны между собой. Также и триады 6, 8, 10.
            # Однако 1 != 6 и. т. д.
            # Теперь заменим все все ссылки на повторяющиеся триады на базовые.
            # В данном случае все ссылки на 2 и 3 заменим на 1. А 8 и 10 на 6.
            # после этого триады 2, 3, 8 и 10 можно удалить

            for i in range(first, last + 1):
                triplet1 = self.__triplets[i]
                if triplet1.first_arg_type == TripletOperandType.link:
                    try:
                        new_link = multiple_triplets.get_base_element(triplet1.first_arg)
                        triplet1.first_arg = new_link
                    except ValueError:
                        pass
                if triplet1.second_arg_type == TripletOperandType.link:
                    try:
                        new_link = multiple_triplets.get_base_element(triplet1.second_arg)
                        triplet1.second_arg = new_link
                    except ValueError:
                        pass

            # теперь удалим повторяющиеся триады
            for number in multiple_triplets.ravel(1):
                self.__triplets.delete_by_triplet_number(number)

            first = self.__triplets.get_index_by_triplet_number(node.first)
            last = self.__triplets.get_index_by_triplet_number(node.last)

            # далее произведем вычисление элементарных выражений на этапе компиляции
            equations = {}
            delete_numbers = set()
            actions = {
                TripletOperation.plus: lambda x, y: x + y,
                TripletOperation.minus: lambda x, y: x - y,
                TripletOperation.multiply: lambda x, y: x * y,
                TripletOperation.divide: lambda x, y: x // y,
            }
            for i in range(first, last + 1):
                triplet1 = self.__triplets[i]

                if triplet1.first_arg_type == TripletOperandType.link:
                    if triplet1.first_arg in equations.keys():
                        triplet1.first_arg_type = TripletOperandType.value
                        delete_numbers.add(triplet1.first_arg)
                        triplet1.first_arg = equations[triplet1.first_arg]
                if triplet1.second_arg_type == TripletOperandType.link:
                    if triplet1.second_arg in equations.keys():
                        triplet1.second_arg_type = TripletOperandType.value
                        delete_numbers.add(triplet1.second_arg)
                        triplet1.second_arg = equations[triplet1.second_arg]

                if triplet1.operation in actions.keys():
                    if triplet1.first_arg_type == TripletOperandType.value \
                            and triplet1.second_arg_type == TripletOperandType.value:
                        try:
                            equations[triplet1.number] = actions[triplet1.operation](
                                int(triplet1.first_arg),
                                int(triplet1.second_arg))
                        except ZeroDivisionError:
                            raise ZeroDivisionError("Деление на ноль")
                        except ValueError:
                            pass

            # удалим лишние триады
            for number in delete_numbers:
                self.__triplets.delete_by_triplet_number(number)

            res.append(multiple_triplets)
        return res, self.__triplets

    def make_graph(self):
        graph = Graph(self.__triplets[0].number, self.__triplets[-1].number)
        for i, triplet in enumerate(self.__triplets):
            if triplet.operation == TripletOperation.generate_func \
                    or triplet.operation == TripletOperation.generate_end_func \
                    or triplet.operation == TripletOperation.jz \
                    or triplet.operation == TripletOperation.jmp:
                graph.split(i)
            elif triplet.operation == TripletOperation.generate_func_call:
                graph.split(triplet.number, 1)
        return graph


class Graph:
    def __init__(self, first, last):
        self.__nodes = list()
        node = Graph.Node(first, last)
        self.__nodes.append(node)

    def nodes(self):
        return self.__nodes

    def split(self, pos, split_size=None):
        node = self.__nodes[-1]
        nodes = node.split(pos, split_size)
        self.__nodes.remove(node)
        for a in nodes:
            if a.first == a.last:
                continue
            self.__nodes.append(a)

    class Node:
        def __init__(self, first, last):
            self.__first = first
            self.__last = last

        def __str__(self):
            return "({0} : {1})" \
                .format(self.__first, self.__last)

        @property
        def first(self):
            return self.__first

        @property
        def last(self):
            return self.__last

        def split(self, pos, split_size=None):
            if pos < self.__first:
                raise ValueError("Позиция pos = {0} меньше первой позиции first = {1}"
                                 .format(pos, self.first))
            nodes = list()
            if split_size is not None:
                node_mid = Graph.Node(pos, pos + split_size - 1)
                if pos != self.first:
                    node_first = Graph.Node(self.first, pos - 1)
                    nodes.append(node_first)
                nodes.append(node_mid)
                if pos != self.last:
                    node_last = Graph.Node(pos + 1, self.last)
                    nodes.append(node_last)
            else:
                if pos != self.first:
                    node_first = Graph.Node(self.first, pos - 1)
                    node_last = Graph.Node(pos, self.last)
                    nodes.append(node_first)
                    nodes.append(node_last)
                else:
                    nodes.append(Graph.Node(self.first, self.last))
            return nodes
