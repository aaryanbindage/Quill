# expect: cannot reduce the visibility
class A:
    def f(self) -> int:
        return 1

class B < A:
    protected def f(self) -> int:
        return 2

class Main:
    static def main():
        print(1)
