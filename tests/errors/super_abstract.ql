# expect: cannot call abstract method
abstract class A:
    abstract def f(self)
class B < A:
    def f(self):
        super.f()
class Main:
    static def main():
        pass
