import sys

def main():
    return

if __name__ == '__main__':
    assert len(sys.argv) == 3, f'expected 2 arguments, received {len(sys.argv)-1}'

    arg1, arg2 = sys.argv[1:2]

    main(arg1, arg2)
    main()