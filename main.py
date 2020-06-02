from Syntax import SyntaxAnalyzer
from TripletsOptimization import TripletOptimization
from Asm import AsmGenerator

def main():
    syntax = SyntaxAnalyzer().feed_text(open('input2.txt').read())
    try:
        triplets, sem_tree = syntax.analyze()
        with open('triplets.txt', 'w') as file:
            for triplet in triplets:
                file.write(str(triplet) + '\n')
        opt = TripletOptimization(triplets)
        res, triplets = opt.optimize()

        with open('opt_triplets.txt', 'w') as file:
            for r in triplets:
                file.write(str(r) + '\n')

        asm = AsmGenerator()
        asm_code = asm.generate(triplets, sem_tree)
        file = open('asm_code.asm', 'w')
        for line in asm_code:
            file.write(str(line) + '\n')
        file.close()

    except SyntaxError as err:
        print('Синтаксическая ошибка:')
        print(err)


if __name__ == '__main__':
    main()
