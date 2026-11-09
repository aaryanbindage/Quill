# expect: invalid cast to Dog
class Animal:
    pass

class Dog < Animal:
    pass

class Cat < Animal:
    pass

class Main:
    static def main():
        a: Animal = new Cat()
        d: Dog = a as Dog
        print("unreachable")
