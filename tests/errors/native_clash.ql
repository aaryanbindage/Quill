# expect: clashes with a runtime function of the same name
class Main:
    native static def f(x: int) -> int = "strlen(int) -> int"
    static def main():
        pass
