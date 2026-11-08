# Inheritance, virtual dispatch, fields, constructors, static entry point.

class Animal:
    name: str
    legs: int

    def init(self, name: str, legs: int):
        self.name = name
        self.legs = legs

    def speak(self) -> str:
        return "..."

    def describe(self) -> str:
        return self.name + " says " + self.speak()

class Dog < Animal:
    def init(self, name: str):
        self.name = name
        self.legs = 4

    def speak(self) -> str:
        return "Woof"

class Bird < Animal:
    def init(self, name: str):
        self.name = name
        self.legs = 2

    def speak(self) -> str:
        return "Tweet"

class Counter:
    count: int

    def add(self, n: int):
        self.count += n

    static def fib(n: int) -> int:
        if n < 2:
            return n
        return Counter.fib(n - 1) + Counter.fib(n - 2)

class Main:
    static def main():
        zoo1: Animal = new Dog("Rex")
        zoo2: Animal = new Bird("Tweety")
        zoo3: Animal = new Animal("Thing", 0)

        print(zoo1.describe())
        print(zoo2.describe())
        print(zoo3.describe())
        print("legs:", zoo1.legs + zoo2.legs)

        c = new Counter()
        for i in range(1, 6):
            c.add(i)
        print("sum 1..5 =", c.count)
        print("fib(20) =", Counter.fib(20))
        print("avg:", float(c.count) / 4, "big?", c.count > 10 and not (c.count == 99))
