# 9. When things go wrong

Programs meet trouble: a file is missing, a number cannot be read, a list is too short.
Quill reports trouble with **exceptions**.

## Catching an exception

Put risky code in `try`; if it fails, control jumps to `catch`:

```python
# course: runs
class Main:
    static def main():
        for text in ["42", "x7", "-3"]:
            try:
                n = text.toInt()
                print(text, "is the number", n)
            catch Error as e:
                print("could not read", text, "->", e.message)
```

```text
42 is the number 42
could not read x7 -> toInt: "x7" is not a number
-3 is the number -3
```

The loop carries on after the failure, which is the point: you decide what a failure
means instead of the whole program stopping.

## Throwing your own

Use `throw` when your code finds a problem it cannot solve itself:

```python
# course: runs
class Main:
    static def divide(a: int, b: int) -> int:
        if b == 0:
            throw new Error("cannot divide " + str(a) + " by zero")
        return a / b

    static def main():
        print(Main.divide(10, 2))
        try:
            print(Main.divide(1, 0))
        catch Error as e:
            print("oops:", e.message)
        print("still running")
```

```text
5
oops: cannot divide 1 by zero
still running
```

If nothing catches an exception, the program stops and prints it:
`error: uncaught exception: ...`.

## Your own kinds of error

A class that extends `Error` is its own kind, and `catch` can pick which kinds it handles:

```python
# course: runs
class OutOfStock < Error:
    def init(self, item: str):
        super.init(item + " is out of stock")

class Shop:
    stock: Map[str, int]

    def init(self):
        self.stock = new Map[str, int]()
        self.stock.set("apple", 2)

    def buy(self, item: str):
        left = self.stock.getOr(item, 0)
        if left == 0:
            throw new OutOfStock(item)
        self.stock.set(item, left - 1)

class Main:
    static def main():
        shop = new Shop()
        for item in ["apple", "apple", "apple"]:
            try:
                shop.buy(item)
                print("bought", item)
            catch OutOfStock as e:
                print(e.message)
```

```text
bought apple
bought apple
apple is out of stock
```

## finally

A `finally` block runs whether or not something failed. Use it to tidy up:

```python
# course: runs
class Main:
    static def main():
        try:
            print("working")
            throw new Error("boom")
        catch Error as e:
            print("caught", e.message)
        finally:
            print("cleanup always happens")
```

```text
working
caught boom
cleanup always happens
```

## Exercises

1. Write `parseAge(text)` that throws unless the text is a number from 0 to 150.
2. Call it for several inputs and print a friendly message for each failure.
3. Make `InsufficientFunds < Error` and use it in the `Account` from lesson 6.
4. What happens if you never catch an exception? Try it.

Next: [A small project](10-project.md).
