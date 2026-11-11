# 11. The standard library

Quill ships with extra code you can pull into your program with `bring`. The line goes
at the very top of the file and names the module:

```python
# course: runs
bring std.math
bring std.random
bring std.stats

class Main:
    static def main():
        print(Math.sqrt(2.0))
        print(Math.gcd(12, 18), Math.isPrime(97), Math.factorial(10))

        rng = new Random(42)          # the same seed always gives the same numbers
        dice = new List[int]()
        for i in range(5):
            dice.add(rng.between(1, 6))
        print("five dice:", dice.size(), "rolls, all between 1 and 6")

        scores = [70.0, 85.5, 92.0, 61.5]
        print("mean", Stats.mean(scores))
        print("median", Stats.median(scores))
```

```text
1.41421
6 true 3628800
five dice: 5 rolls, all between 1 and 6
mean 77.25
median 77.75
```

`bring std.math` makes the class `Math` available; nothing is loaded that you did not
ask for. The modules are:

| Module | Gives you |
|---|---|
| `std.math` | `Math`: roots, powers, trigonometry, `gcd`, primes |
| `std.random` | `Random`: repeatable random numbers |
| `std.stats` | `Stats`: mean, median, standard deviation |
| `std.text`, `std.encoding` | bytes, hex and base64 |
| `std.hash`, `std.cipher`, `std.crypto` | hashes, encryption, secure random bytes |
| `std.console`, `std.art` | colours, input, drawing (next lesson) |

The [standard library reference](../stdlib.md) lists every method.

## Hashing

A hash turns any text into a short fixed fingerprint. The same text always gives the
same fingerprint; a different text almost certainly gives a different one.

```python
# course: runs
bring std.hash

class Main:
    static def main():
        print(Hash.sha256Hex("hello"))
        print(Hash.sha256Hex("hellp"))
```

```text
2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824
fdd7585e08c4e2afd71dcabdb4636c89d557a3f42db9e2040c8bbd1708aa4ce7
```

One letter changed and the whole fingerprint changed.

> The crypto modules are written in Quill, are not audited, and are slow. Use them to
> learn and for small jobs, not to protect something that matters.

## Exercises

1. Roll a die 600 times with `Random` and count how many of each face came up.
2. Find the mean and the standard deviation of ten numbers you invent.
3. Use `Math.sqrt` to write a method that tells whether a number is a perfect square.
4. Hash your name, then your name with a space added at the end. Compare them.

Next: [Drawing in the terminal](12-art.md).
