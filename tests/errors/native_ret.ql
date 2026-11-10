# expect: native method returns int in Quill but void in the C signature
class Main:
    native static def f(x: int) -> int = "f(int)"
    static def main():
        pass
