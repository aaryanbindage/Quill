# expect: bad native signature
class Main:
    native static def f(x: int) -> int = "this is not a signature"
    static def main():
        pass
