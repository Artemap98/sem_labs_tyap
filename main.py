from Syntax import SyntaxAnalyzer
from TripletsOptimization import TripletOptimization


def main():
    syntax = SyntaxAnalyzer().feed_text(open('input2.txt').read())
    try:
        triplets = syntax.analyze()
        with open('triplets.txt', 'w') as file:
            for triplet in triplets:
                file.write(str(triplet) + '\n')
        opt = TripletOptimization(triplets)
        res, triplets = opt.optimize()
        with open('multiply_triplets.txt', 'w') as file:
            for r in res:
                file.write(str(r) + '\n')
        with open('opt_triplets.txt', 'w') as file:
            for r in triplets:
                file.write(str(r) + '\n')

    except SyntaxError as err:
        print('Синтаксическая ошибка:')
        print(err)


if __name__ == '__main__':
    main()
