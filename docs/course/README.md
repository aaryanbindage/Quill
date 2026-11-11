# Learn Quill

A hands-on course for people who have never programmed, and for programmers who want
to see how Quill works. Each lesson is short, every program in it runs, and each ends
with exercises.

## Before you start

You need Python 3 and `clang` (on Windows also `gcc`); see the [README](../../README.md).
Check that this works from the folder where you downloaded Quill:

```
python quill.py run examples/animals.ql
```

To run a lesson's program, copy it into a file such as `try.ql` and run
`python quill.py run try.ql`. Change things and run it again. Breaking a program on
purpose is the fastest way to learn what the error messages mean.

## The lessons

1. [Hello, Quill](01-hello.md): your first program, `print`, comments
2. [Values and variables](02-values.md): numbers, text, true and false, and what you can do with them
3. [Making decisions](03-decisions.md): `if`, `elif`, `else`, and, or, not
4. [Repeating things](04-loops.md): `while`, `for`, `break`, `continue`
5. [Functions](05-functions.md): naming a piece of work and reusing it
6. [Classes and objects](06-classes.md): bundling data with the code that uses it
7. [Lists and maps](07-collections.md): holding many values
8. [Sharing behaviour](08-inheritance.md): inheritance, interfaces, `protected`
9. [When things go wrong](09-errors.md): `try`, `catch`, `throw`
10. [A small project](10-project.md): putting it all together
11. [The standard library](11-stdlib.md): `bring`, math, random, statistics, hashing
12. [Drawing in the terminal](12-art.md): colours, a canvas, big letters
13. [Generics](13-generics.md): writing classes like `List[T]` yourself
14. [Threads](14-threads.md): doing two things at once, and `Mutex`

More lessons (your own modules and packages, calling C libraries, the memory checker)
are planned; until they are written, the [language guide](../language-guide.md) covers them.

## How the course is checked

Every program in these lessons is run by `tests/run_all.sh`, and the output shown under
it is compared with the real output, so the lessons cannot drift out of date. If you
find one that does not work, that is a bug: please report it.
