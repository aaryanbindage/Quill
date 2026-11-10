# expect: operator << needs two ints (or two bools), not int and bool
class Main:
    static def main():
        x = 1 << true
