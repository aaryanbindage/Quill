# 4. Repeating things

## for and range

`for i in range(n)` repeats a block `n` times, with `i` counting from 0:

```python
# course: runs
class Main:
    static def main():
        for i in range(5):
            print("round", i)
```

```text
round 0
round 1
round 2
round 3
round 4
```

`range(2, 8)` counts 2 up to 7. The end is never included.

```python
# course: runs
class Main:
    static def main():
        total = 0
        for n in range(1, 11):
            total = total + n
        print("1 + 2 + ... + 10 =", total)
```

```text
1 + 2 + ... + 10 = 55
```

## while

`while` repeats as long as a condition is true. Use it when you do not know in advance
how many rounds you need:

```python
# course: runs
class Main:
    static def main():
        n = 27
        steps = 0
        while n != 1:
            if n % 2 == 0:
                n = n / 2
            else:
                n = 3 * n + 1
            steps = steps + 1
        print("reached 1 after", steps, "steps")
```

```text
reached 1 after 111 steps
```

If the condition never becomes false the loop never ends. Press Ctrl+C to stop it.

## break and continue

`break` leaves the loop at once. `continue` skips to the next round.

```python
# course: runs
class Main:
    static def main():
        for i in range(1, 20):
            if i % 3 == 0:
                continue          # skip multiples of 3
            if i > 10:
                break             # stop after 10
            print(i)
```

```text
1
2
4
5
7
8
10
```

## Loops inside loops

```python
# course: runs
class Main:
    static def main():
        for row in range(1, 4):
            line = ""
            for col in range(1, 5):
                line = line + str(row * col).padLeft(3, " ")
            print(line)
```

```text
  1  2  3  4
  2  4  6  8
  3  6  9 12
```

## Exercises

1. Print the numbers from 10 down to 1. (Hint: count up and print `11 - i`, or use `while`.)
2. Print the first 10 square numbers: 1, 4, 9, ...
3. Find the first number above 100 that is divisible by both 7 and 9, using `while` and `break`.
4. Draw a triangle of stars: one star on the first line, two on the second, up to five.
5. Print a times-table for a number you choose.

Next: [Functions](05-functions.md).
