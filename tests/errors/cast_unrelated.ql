# expect: the types are unrelated
class A:
    pass

class B:
    pass

class Main:
    static def main():
        a: A = new A()
        b: B = a as B
