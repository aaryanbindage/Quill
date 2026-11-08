# expect: cannot reduce the visibility
class A:
    def f(self):
        pass
class B < A:
    private def f(self):
        pass
class Main:
    static def main():
        pass
