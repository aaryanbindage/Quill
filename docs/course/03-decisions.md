# 3. Making decisions

## if, elif, else

```python
# course: runs
class Main:
    static def main():
        temperature = 18
        if temperature < 10:
            print("Wear a coat")
        elif temperature < 20:
            print("Wear a jumper")
        else:
            print("T-shirt weather")
```

```text
Wear a jumper
```

Quill checks the conditions from top to bottom and runs the first block whose
condition is true. `elif` means "else, if"; `else` catches everything left over. Both
are optional.

## Comparisons

`==` equal, `!=` not equal, `<` `<=` `>` `>=`. Note the double `==`: a single `=`
assigns, `==` asks a question. They work on numbers and strings.

```python
# course: runs
class Main:
    static def main():
        print(3 == 3, 3 != 3, 2 < 5, 5 <= 5)
        print("apple" == "apple", "apple" == "pear")
```

```text
true false true true
true false
```

## and, or, not

```python
# course: runs
class Main:
    static def main():
        age = 15
        hasTicket = true
        if age >= 13 and hasTicket:
            print("Welcome in")
        if age < 5 or age > 65:
            print("Free entry")
        if not hasTicket:
            print("Please buy a ticket")
        print(true xor false, true xor true)
```

```text
Welcome in
true false
```

`and` is true when both sides are; `or` when at least one is; `not` flips; `xor` when
exactly one is. `and` and `or` stop early: in `a and b`, if `a` is false, `b` is not
looked at.

## Decisions inside a method

A method can answer a question with `return`:

```python
# course: runs
class Main:
    static def describe(n: int) -> str:
        if n < 0:
            return "negative"
        if n == 0:
            return "zero"
        return "positive"

    static def main():
        print(Main.describe(-4), Main.describe(0), Main.describe(9))
```

```text
negative zero positive
```

(Lesson 5 explains methods properly.)

## Exercises

1. Write a program that prints `"even"` or `"odd"` for a number you pick. Hint: `%`.
2. Given a score from 0 to 100, print a grade: 90 or more is `A`, 80 or more `B`, 70 or more `C`, otherwise `D`.
3. Print `true` if a year is a leap year: divisible by 4, except years divisible by 100, unless also divisible by 400.
4. What does `true or (1 / 0 == 1)` do, and why?

Next: [Repeating things](04-loops.md).
