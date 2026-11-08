# expect: an interface can only extend interfaces
class A:
    pass
interface I < A:
    def f(self)
class Main:
    static def main():
        pass
