# 13. Generics

You have already used generic classes: `List[int]`, `Map[str, int]`. The part in square
brackets is a **type parameter**, a blank filled in when you use the class. You can
write your own.

## A box for anything

```python
# course: runs
class Box[T]:
    value: T

    def init(self, value: T):
        self.value = value

    def get(self) -> T:
        return self.value

    def set(self, value: T):
        self.value = value

class Main:
    static def main():
        a = new Box[int](5)
        b = new Box[str]("hello")
        a.set(a.get() + 1)
        print(a.get(), b.get())
        # a.set("text") would not compile: a holds ints
```

```text
6 hello
```

`Box[int]` and `Box[str]` are two separate classes, made by the compiler from the one
you wrote. Each is fully type-checked, so mistakes are caught before the program runs.

## A stack

A stack gives things back in the reverse of the order you put them in, like a pile of
plates. We can build it on `List`:

```python
# course: runs
class Stack[T]:
    private items: List[T]

    def init(self):
        self.items = new List[T]()

    def push(self, x: T):
        self.items.add(x)

    def pop(self) -> T:
        if self.items.isEmpty():
            throw new Error("the stack is empty")
        return self.items.pop()

    def size(self) -> int:
        return self.items.size()

class Main:
    static def main():
        s = new Stack[str]()
        s.push("first")
        s.push("second")
        s.push("third")
        print(s.pop(), s.pop(), s.size())

        numbers = new Stack[int]()
        for i in range(1, 5):
            numbers.push(i * i)
        total = 0
        while numbers.size() > 0:
            total = total + numbers.pop()
        print("sum of squares:", total)
```

```text
third second 1
sum of squares: 30
```

## More than one parameter

```python
# course: runs
class Pair[A, B]:
    first: A
    second: B

    def init(self, first: A, second: B):
        self.first = first
        self.second = second

    def swapped(self) -> Pair[B, A]:
        return new Pair[B, A](self.second, self.first)

    def toString(self) -> str:
        return "(" + str(self.first) + ", " + str(self.second) + ")"

class Main:
    static def main():
        p = new Pair[str, int]("age", 12)
        print(p, p.swapped())
```

```text
(age, 12) (12, age)
```

## Limits to know about

- A generic class is checked for each type you use. If a method uses `<` on a `T`, it only
  works for types that support `<`.
- There are no generic *methods* on ordinary classes yet, and `new Box(5)` needs the type
  spelled out: `new Box[int](5)`.

## Exercises

1. Write a `Queue[T]` (first in, first out) with `enqueue`, `dequeue` and `size`.
2. Add a `peek()` to `Stack[T]` that looks at the top without removing it.
3. Make a `Triple[A, B, C]` and print one.
4. What error do you get if you write `new Stack[int]()` and then `push("x")`?

Next: [Threads](14-threads.md).
