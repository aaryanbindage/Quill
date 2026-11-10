# expect: native methods must be static
class Main:
    native def f(self) -> int = "f() -> int"
    static def main():
        pass
