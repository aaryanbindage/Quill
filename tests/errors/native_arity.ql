# expect: native signature has 2 parameter(s) but the method declares 1
class Main:
    native static def f(x: int) -> int = "f(int, int) -> int"
    static def main():
        pass
