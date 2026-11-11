# 1. Hello, Quill

A Quill program is a list of **classes**. Every program has one special class called
`Main` with a method called `main`; that is where the program starts.

```python
# course: runs
class Main:
    static def main():
        print("Hello, Quill!")
```

```text
Hello, Quill!
```

Line by line:

- `class Main:` starts a class. The colon means "an indented block follows".
- `static def main():` defines the method where execution begins. For now treat
  `static def` as part of the spell; lesson 5 explains it.
- `print("Hello, Quill!")` shows text on the screen. Text in double quotes is a **string**.

Indentation matters. Everything inside `class Main:` is indented, and everything inside
`main` is indented a little more. Use four spaces.

## Printing several things

`print` accepts any number of values and puts a space between them:

```python
# course: runs
class Main:
    static def main():
        print("2 + 3 =", 2 + 3)
        print("Quill", "is", "fun")
        print()
        print("A blank line is above this one.")
```

```text
2 + 3 = 5
Quill is fun

A blank line is above this one.
```

## Comments

A `#` starts a **comment**: the rest of the line is for human readers and the
computer ignores it.

```python
# course: runs
# This whole line is a comment.
class Main:
    static def main():
        print("Visible")   # this part is a comment too
```

```text
Visible
```

## Reading error messages

Mistakes are normal. Quill tells you the file, the line and what it did not like:

```
try.ql:3: error: expected ':', found 'NEWLINE'
```

That means: on line 3 Quill expected a colon and found the end of the line instead.
Look at the line it names, and usually the line just before it.

## Exercises

1. Change the program to print your name.
2. Print three lines about your favourite food, one `print` per line.
3. Print `10 * 7 =` followed by the answer, letting Quill do the multiplication.
4. Remove the colon after `static def main()` and run it. Read the error. Put it back.

Next: [Values and variables](02-values.md).
