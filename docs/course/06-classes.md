# 6. Classes and objects

So far all the code lived in `Main`. A **class** lets you design your own kind of thing:
what it remembers (**fields**) and what it can do (**methods**). An **object** is one
particular thing made from the class.

```python
# course: runs
class Dog:
    name: str
    age: int

    def init(self, name: str, age: int):
        self.name = name
        self.age = age

    def bark(self) -> str:
        return self.name + " says woof"

    def birthday(self):
        self.age = self.age + 1

class Main:
    static def main():
        rex = new Dog("Rex", 3)
        fido = new Dog("Fido", 7)
        print(rex.bark())
        rex.birthday()
        print(rex.name, "is now", rex.age)
        print(fido.name, "is still", fido.age)
```

```text
Rex says woof
Rex is now 4
Fido is still 7
```

- `new Dog("Rex", 3)` makes an object and runs `init`, the **constructor**, which sets it up.
- `self` is the object a method is working on. `self.age` is that object's own `age`.
- Two objects of the same class have separate fields: `rex` getting older does nothing to `fido`.

## Keeping things private

Mark a field `private` and only the class's own methods can touch it. That lets the class
protect its own rules:

```python
# course: runs
class Account:
    private balance: int

    def init(self):
        self.balance = 0

    def deposit(self, amount: int):
        if amount > 0:
            self.balance = self.balance + amount

    def withdraw(self, amount: int) -> bool:
        if amount > self.balance:
            return false
        self.balance = self.balance - amount
        return true

    def getBalance(self) -> int:
        return self.balance

class Main:
    static def main():
        acct = new Account()
        acct.deposit(100)
        print(acct.withdraw(30), acct.getBalance())
        print(acct.withdraw(500), acct.getBalance())
        # acct.balance = 1000000     <- would be a compile error: balance is private
```

```text
true 70
false 70
```

## Printing objects: toString

Give a class a `toString` method and `print` uses it:

```python
# course: runs
class Point:
    x: int
    y: int

    def init(self, x: int, y: int):
        self.x = x
        self.y = y

    def toString(self) -> str:
        return "(" + str(self.x) + ", " + str(self.y) + ")"

class Main:
    static def main():
        p = new Point(3, 4)
        print("p is", p)
```

```text
p is (3, 4)
```

## Objects are shared, and cleaned up for you

Assigning an object to another variable does not copy it; both names refer to the same
object. Quill counts the references and frees an object when the last one goes away, so
you never free memory yourself.

```python
# course: runs
class Box:
    value: int
    def init(self, value: int):
        self.value = value

class Main:
    static def main():
        a = new Box(1)
        b = a              # b is the same box, not a copy
        b.value = 99
        print(a.value)
```

```text
99
```

## Exercises

1. Make a `Rectangle` class with width and height, a method `area()` and a `toString`.
2. Add a `scale(factor)` method that multiplies both sides. Print before and after.
3. Make a `Counter` with a private count, `increment()` and `value()`.
4. Make a `Temperature` class that stores degrees Celsius and has `toFahrenheit()`.

Next: [Lists and maps](07-collections.md).
