# expect: native parameter x is int in Quill but cstr in the C signature
class Main:
    native static def f(x: int) -> int = "f(cstr) -> int"
    static def main():
        pass
