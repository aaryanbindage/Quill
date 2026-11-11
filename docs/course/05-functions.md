# 5. Functions

A **function** (Quill calls it a *method*, because it lives in a class) is a named piece
of work. You define it once and use it as often as you like.

```python
# course: runs
class Main:
    static def greet(name: str):
        print("Hello, " + name + "!")

    static def main():
        Main.greet("Ada")
        Main.greet("Grace")
```

```text
Hello, Ada!
Hello, Grace!
```

- `static def` makes a method that belongs to the class itself, so you call it as
  `Main.greet(...)`. (Lesson 6 shows methods that belong to *objects*.)
- Each **parameter** has a name and a type: `name: str`.
- The values you pass in are called **arguments**.

## Returning a value

`-> type` says what the method gives back, and `return` hands the value over:

```python
# course: runs
class Main:
    static def square(n: int) -> int:
        return n * n

    static def average(a: float, b: float) -> float:
        return (a + b) / 2.0

    static def main():
        print(Main.square(9))
        print(Main.average(3.0, 4.0))
        print(Main.square(Main.square(3)))   # results can be arguments
```

```text
81
3.5
81
```

A method with no `->` returns nothing. `return` also ends the method early.

## Putting methods to work

Break a problem into small methods with good names:

```python
# course: runs
class Main:
    static def isPrime(n: int) -> bool:
        if n < 2:
            return false
        for d in range(2, n):
            if n % d == 0:
                return false
        return true

    static def countPrimes(limit: int) -> int:
        count = 0
        for n in range(2, limit + 1):
            if Main.isPrime(n):
                count = count + 1
        return count

    static def main():
        print("primes up to 100:", Main.countPrimes(100))
        print("is 97 prime?", Main.isPrime(97))
```

```text
primes up to 100: 25
is 97 prime? true
```

## Methods calling themselves

A method can call itself. This is **recursion**; every recursive method needs a case
that stops:

```python
# course: runs
class Main:
    static def factorial(n: int) -> int:
        if n <= 1:
            return 1
        return n * Main.factorial(n - 1)

    static def main():
        for n in range(1, 8):
            print(n, "! =", Main.factorial(n))
```

```text
1 ! = 1
2 ! = 2
3 ! = 6
4 ! = 24
5 ! = 120
6 ! = 720
7 ! = 5040
```

## Exercises

1. Write `max3(a, b, c)` returning the largest of three ints.
2. Write `repeat(text, times)` that prints `text` that many times. (A string has `.repeat(n)` too; write your own anyway.)
3. Write `fib(n)` returning the n-th Fibonacci number (0, 1, 1, 2, 3, 5, ...) with recursion. Try `fib(35)` and notice it is slow. Why?
4. Write `gcd(a, b)`, the greatest common divisor, using `while`.

Next: [Classes and objects](06-classes.md).
