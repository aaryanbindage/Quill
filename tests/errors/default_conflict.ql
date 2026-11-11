# expect: inherits two default versions of hello
interface A:
    def hello(self) -> str:
        return "a"

interface B:
    def hello(self) -> str:
        return "b"

class C < A, B:
    pass

class Main:
    static def main():
        print(1)
