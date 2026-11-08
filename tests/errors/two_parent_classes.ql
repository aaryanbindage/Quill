# expect: can extend only one class
class A:
    pass
class B:
    pass
class C < A, B:
    pass
class Main:
    static def main():
        pass
