# expect: give the class a toString method
class A:
    pass

class Main:
    static def main():
        a: A = new A()
        s: str = str(a)
