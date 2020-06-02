from Syntax import SyntaxAnalyzer


def main():
    syntax = SyntaxAnalyzer().feed_text(open('input2.txt').read())
    try:
        triplets = syntax.analyze()
        with open('triplets.txt', 'w') as file:
            for triplet in triplets:
                file.write(str(triplet) + '\n')
    except SyntaxError as err:
        print('Синтаксическая ошибка:')
        print(err)


if __name__ == '__main__':
    main()
