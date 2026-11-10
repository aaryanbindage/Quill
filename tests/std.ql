# the bundled standard library: std.math, std.random, std.stats
bring std.math
bring std.random
bring std.stats

class Main:
    static def check(name: str, ok: bool):
        if ok:
            print("ok  ", name)
        else:
            print("FAIL", name)

    static def near(a: float, b: float) -> bool:
        return Math.abs(a - b) < 0.000001

    static def main():
        base: int = heap_live()

        Main.check("sqrt", Main.near(Math.sqrt(2.0), 1.4142135623730951) and Main.near(Math.sqrt(16.0), 4.0))
        Main.check("pow", Main.near(Math.pow(2.0, 10.0), 1024.0))
        Main.check("rounding", Math.floor(-2.5) == -3.0 and Math.ceil(2.1) == 3.0 and Math.round(2.5) == 3.0 and Math.trunc(-2.9) == -2.0)
        Main.check("abs sign", Math.abs(-3.5) == 3.5 and Math.iabs(-4) == 4 and Math.sign(-2.0) == -1 and Math.isign(0) == 0)
        Main.check("min max", Math.min(1.5, 2.5) == 1.5 and Math.imax(3, 9) == 9 and Math.imin(3, 9) == 3)
        Main.check("clamp", Math.clamp(5.0, 0.0, 1.0) == 1.0 and Math.iclamp(-5, 0, 10) == 0 and Math.iclamp(4, 0, 10) == 4)
        Main.check("lerp", Math.lerp(0.0, 10.0, 0.25) == 2.5)
        Main.check("trig", Main.near(Math.sin(Math.pi() / 2.0), 1.0) and Main.near(Math.cos(0.0), 1.0) and Main.near(Math.atan2(1.0, 1.0), Math.pi() / 4.0))
        Main.check("angles", Main.near(Math.toDegrees(Math.pi()), 180.0) and Main.near(Math.toRadians(90.0), Math.pi() / 2.0))
        Main.check("logs", Main.near(Math.ln(Math.e()), 1.0) and Main.near(Math.log10(1000.0), 3.0) and Main.near(Math.log2(8.0), 3.0) and Main.near(Math.exp(0.0), 1.0))
        Main.check("hypot cbrt", Math.hypot(3.0, 4.0) == 5.0 and Main.near(Math.cbrt(27.0), 3.0) and Main.near(Math.cbrt(-8.0), -2.0))
        Main.check("nan", Math.isNaN(Math.sqrt(-1.0)) and not Math.isNaN(1.0))

        Main.check("gcd lcm", Math.gcd(12, 18) == 6 and Math.gcd(-12, 18) == 6 and Math.lcm(4, 6) == 12 and Math.lcm(0, 5) == 0)
        Main.check("ipow", Math.ipow(3, 4) == 81 and Math.ipow(2, 62) == 4611686018427387904 and Math.ipow(5, 0) == 1)
        Main.check("mod", Math.mod(-1, 5) == 4 and Math.mod(7, 5) == 2)
        Main.check("isqrt", Math.isqrt(99) == 9 and Math.isqrt(100) == 10 and Math.isqrt(0) == 0)
        Main.check("primes", Math.isPrime(97) and not Math.isPrime(91) and not Math.isPrime(1) and Math.isPrime(2))
        Main.check("factorial", Math.factorial(10) == 3628800 and Math.factorial(0) == 1 and Math.factorial(20) == 2432902008176640000)
        Main.check("fib", Math.fib(10) == 55 and Math.fib(50) == 12586269025)

        msg = ""
        try:
            Math.factorial(21)
        catch Error as e:
            msg = e.message
        Main.check("domain error", msg == "factorial: n must be between 0 and 20")

        r1 = new Random(7)
        r2 = new Random(7)
        same = true
        for i in range(20):
            if r1.next() != r2.next():
                same = false
        Main.check("same seed, same numbers", same)
        ok = true
        r = new Random(1)
        for i in range(2000):
            n = r.nextInt(10)
            d = r.between(-3, 3)
            f = r.nextFloat()
            if n < 0 or n >= 10 or d < -3 or d > 3 or f < 0.0 or f >= 1.0:
                ok = false
        Main.check("ranges", ok)
        seen: Set[int] = {}
        r = new Random(5)
        for i in range(500):
            seen.add(r.nextInt(6))
        Main.check("covers the range", seen.size() == 6)

        xs: List[float] = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
        Main.check("mean", Stats.mean(xs) == 5.0 and Stats.sum(xs) == 40.0)
        Main.check("median", Stats.median(xs) == 4.5 and Stats.median([3.0, 1.0, 2.0]) == 2.0)
        Main.check("stddev", Stats.stddev(xs) == 2.0 and Stats.variance(xs) == 4.0)
        Main.check("range", Stats.range(xs) == 7.0)
        Main.check("int stats", Stats.isum([1, 2, 3]) == 6 and Stats.imean([1, 2]) == 1.5 and Stats.imedian([3, 1, 2]) == 2.0)
        Main.check("xs unchanged", xs.get(0) == 2.0 and xs.get(7) == 9.0)
        empty: List[float] = []
        msg = ""
        try:
            Stats.mean(empty)
        catch Error as e:
            msg = e.message
        Main.check("empty mean", msg == "mean of an empty list")

        r1 = null
        r2 = null
        r = null
        xs = null
        empty = null
        seen = null
        if heap_live() - base == 0:
            print("ok   no leaks")
        else:
            print("LEAK", heap_live() - base)
