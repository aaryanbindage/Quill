# 8. Sharing behaviour

## Inheritance

A class can build on another with `<`. The new class (the *subclass*) gets the fields and
methods of the old one (the *superclass*), and can add to them or replace them:

```python
# course: runs
class Animal:
    name: str

    def init(self, name: str):
        self.name = name

    def speak(self) -> str:
        return "..."

    def intro(self) -> str:
        return self.name + " says " + self.speak()

class Dog < Animal:
    def speak(self) -> str:
        return "Woof"

class Cat < Animal:
    def init(self, name: str):
        super.init(name)          # run the superclass constructor yourself
    def speak(self) -> str:
        return "Meow"

class Main:
    static def main():
        pets = new List[Animal]()
        pets.add(new Dog("Rex"))
        pets.add(new Cat("Tom"))
        pets.add(new Animal("Thing"))
        for p in pets:
            print(p.intro())
```

```text
Rex says Woof
Tom says Meow
Thing says ...
```

Notice `intro` is written once, in `Animal`, yet it prints the *right* sound for each
animal: calling `self.speak()` runs the subclass's version. This is the heart of
object-oriented programming. A `Dog` can be used anywhere an `Animal` is expected.

A subclass constructor must call `super.init(...)` itself; Quill does not do it for you.

## Abstract classes

Sometimes the superclass is only a template. Mark it `abstract` and its abstract methods
have no body; every concrete subclass must supply one.

```python
# course: runs
abstract class Shape:
    abstract def area(self) -> float

    def describe(self) -> str:
        return "a shape with area " + str(self.area())

class Square < Shape:
    side: float
    def init(self, side: float):
        self.side = side
    def area(self) -> float:
        return self.side * self.side

class Main:
    static def main():
        s = new Square(3.0)
        print(s.describe())
        # new Shape() would be a compile error: Shape is abstract
```

```text
a shape with area 9
```

## Interfaces

An **interface** lists what a class can do, without saying how. A class can promise
several interfaces. A method with a body inside an interface is a **default**: classes
that do not write their own get it for free.

```python
# course: runs
interface Named:
    def name(self) -> str
    def greet(self) -> str:
        return "Hello, " + self.name()

interface Aged:
    def age(self) -> int

class Person < Named, Aged:
    n: str
    a: int
    def init(self, n: str, a: int):
        self.n = n
        self.a = a
    def name(self) -> str:
        return self.n
    def age(self) -> int:
        return self.a

class Robot < Named:
    def name(self) -> str:
        return "unit 7"
    def greet(self) -> str:
        return "BEEP " + self.name()

class Main:
    static def welcome(x: Named):
        print(x.greet())

    static def main():
        Main.welcome(new Person("Sam", 30))
        Main.welcome(new Robot())
```

```text
Hello, Sam
BEEP unit 7
```

`welcome` accepts anything that is `Named`, whatever its class. Through the interface
type you can only call the interface's methods.

## Three levels of privacy

| Modifier | Who can use the member |
|---|---|
| `public` (the default) | anyone |
| `protected` | the class itself and its subclasses |
| `private` | the class itself only |

```python
# course: runs
class Vehicle:
    protected speed: int
    private serial: int

    def init(self, serial: int):
        self.serial = serial
        self.speed = 0

    def serialNumber(self) -> int:
        return self.serial

class Car < Vehicle:
    def init(self):
        super.init(1234)
    def accelerate(self):
        self.speed = self.speed + 10       # allowed: speed is protected
        # self.serial would not compile: private to Vehicle
    def current(self) -> int:
        return self.speed

class Main:
    static def main():
        c = new Car()
        c.accelerate()
        c.accelerate()
        print(c.current(), c.serialNumber())
        # c.speed would not compile outside the class family
```

```text
20 1234
```

## Exercises

1. Add a `Bird` to the animals program with its own sound.
2. Make an abstract `Employee` with `pay()`; add `Salaried` and `Hourly` subclasses and print total pay for a mixed list.
3. Write an interface `Drawable` with `draw() -> str` and two classes that implement it.
4. Why can't `new Shape()` work? Try it and read the message.

Next: [When things go wrong](09-errors.md).
