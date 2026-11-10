# Standard library

Quill ships a few modules in the `std/` folder. Bring them in like any other
module; no `quill.pkg` entry is needed:

```python
bring std.math
bring std.random
bring std.stats
```

Errors (bad arguments, empty lists) are thrown as `Error`, so they can be caught
with `try`/`catch`. The built-in `List`, `Map` and `Set` need no `bring`; see the
language guide.

## std.math: `Math`

All static methods. Float functions also accept ints. Functions that work on ints
only start with `i`.

| Group | Methods |
|---|---|
| Constants | `pi()`, `e()`, `tau()` |
| Sign and extremes | `abs`, `iabs`, `sign`, `isign`, `min`, `max`, `imin`, `imax`, `clamp`, `iclamp`, `lerp` |
| Rounding | `floor`, `ceil`, `round`, `trunc` (results stay `float`; use `int(x)`) |
| Powers and logs | `sqrt`, `cbrt`, `pow`, `hypot`, `exp`, `ln`, `log10`, `log2`, `logBase` |
| Trigonometry | `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `atan2`, `sinh`, `cosh`, `tanh`, `toRadians`, `toDegrees` |
| Float checks | `isNaN`, `isInfinite` |
| Integers | `ipow`, `mod` (sign of the divisor), `gcd`, `lcm`, `isqrt`, `isPrime`, `factorial` (0 to 20), `fib` (0 to 92) |

```python
print(Math.sqrt(2.0), Math.gcd(12, 18), Math.mod(-1, 5))
```

## std.random: `Random`

A seedable generator: the same seed gives the same sequence on every platform.
Not for security.

```python
r = new Random(42)
r.next()            # 0 .. 2147483647
r.nextInt(10)       # 0 <= n < 10
r.between(-3, 3)    # -3 <= n <= 3
r.nextFloat()       # 0.0 <= f < 1.0
r.nextBool()
r.index(list.size())
```

## std.stats: `Stats`

Population statistics. The float versions take `List[float]`; the `i` versions
take `List[int]`. An empty list throws an `Error`. Inputs are never modified.

`sum`, `mean`, `median`, `variance`, `stddev`, `range`, `isum`, `imean`, `imedian`

## Notes

- `Math`, `Random` and `Stats` are plain class names. If your own code uses the
  same names, bring the module under an alias (`bring std.math as m`, then
  `m.Math`).
- A local module or a package named `std` takes precedence over the bundled one.
