# 2. Values and variables

## Four kinds of value

| Type | What it holds | Examples |
|---|---|---|
| `int` | whole numbers | `0`, `42`, `-7` |
| `float` | numbers with a decimal point | `3.14`, `-0.5` |
| `str` | text (a "string") | `"hello"`, `""` |
| `bool` | yes or no | `true`, `false` |

## Variables

A **variable** is a name for a value. You create one by assigning to it:

```python
# course: runs
class Main:
    static def main():
        age = 12
        name = "Sam"
        height = 1.52
        likesTea = true
        print(name, "is", age, "and", height, "m tall")
        print("Likes tea:", likesTea)

        age = age + 1          # a variable can change
        print("Next year:", age)
```

```text
Sam is 12 and 1.52 m tall
Likes tea: true
Next year: 13
```

Quill works out the type from the value, and the type of a variable never changes:
once `age` holds an `int`, you cannot put text in it. That is what "statically typed"
means, and it is why Quill can tell you about mistakes before the program runs.

You can also write the type yourself: `age: int = 12`.

## Arithmetic

`+ - * /` and `%` (the remainder). Dividing two `int`s gives an `int` and drops the
remainder; use a `float` on either side for a fractional answer.

```python
# course: runs
class Main:
    static def main():
        print(7 + 2, 7 - 2, 7 * 2)
        print(7 / 2, 7 % 2)
        print(7 / 2.0)
        print(2 + 3 * 4, (2 + 3) * 4)   # * happens before +; brackets override
```

```text
9 5 14
3 1
3.5
14 20
```

## Text

`+` joins strings. To put a number in a sentence, convert it with `str(...)`:

```python
# course: runs
class Main:
    static def main():
        first = "Ada"
        last = "Lovelace"
        full = first + " " + last
        print(full)
        print("Letters in the name:", len(full))
        print("Born in " + str(1815))
```

```text
Ada Lovelace
Letters in the name: 12
Born in 1815
```

## Methods on values

Every value can be asked to do things with a **method**, written `value.method()`:

```python
# course: runs
class Main:
    static def main():
        shout = "quiet please".upper()
        print(shout)
        print("  padded  ".trim() + "|")
        print("banana".contains("nan"), "banana".indexOf("nan"))
        print("a,b,c".split(",").size(), "parts")
        print("42".toInt() + 1)
        print(255.toHex(), 5.toBinary())
        print(2.7.floor(), 2.7.round(), (0 - 3).abs())
        print(7.isEven(), 7.isOdd())
```

```text
QUIET PLEASE
padded|
true 2
3 parts
43
ff 101
2 3 3
false true
```

Strings never change: `upper()` gives you a new string and leaves the original alone.
The full list is in the [language guide](../language-guide.md#methods-on-basic-types).

## Exercises

1. Store your birth year in a variable and print how old you will be in 2050.
2. What does `10 / 4` print? And `10 % 4`? And `10 / 4.0`? Guess first, then check.
3. Make a string with your full name and print it in capitals, followed by its length.
4. Turn the text `"2.5"` into a number, double it and print the result.

Next: [Making decisions](03-decisions.md).
