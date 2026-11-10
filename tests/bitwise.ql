# bitwise operators, shifts, hex/binary literals, logical xor
class Main:
    static def check(name: str, ok: bool):
        if ok:
            print("ok  ", name)
        else:
            print("FAIL", name)

    static def side(box: List[int]) -> bool:
        box.add(1)
        return true

    static def main():
        Main.check("and or xor", (12 & 10) == 8 and (12 | 10) == 14 and (12 ^ 10) == 6)
        Main.check("not", ~0 == -1 and ~5 == -6 and ~~7 == 7)
        Main.check("shift left", (1 << 10) == 1024 and (3 << 0) == 3)
        Main.check("shift right is arithmetic", (-8 >> 1) == -4 and (8 >> 2) == 2)
        Main.check("logical shift right", (-1 >>> 63) == 1 and (-8 >>> 1) == 9223372036854775804)
        Main.check("big shifts", (1 << 63) < 0 and (1 << 64) == 0 and (1 << 100) == 0 and (5 >> 70) == 0 and (-5 >> 70) == -1 and (-1 >>> 64) == 0)
        Main.check("negative count", (1 << -1) == 0)
        Main.check("hex", 0xFF == 255 and 0x1f == 31 and 0xDEAD_BEEF == 3735928559)
        Main.check("binary", 0b1010 == 10 and 0b1111_0000 == 240)
        Main.check("hex wraps like two's complement", 0xFFFFFFFFFFFFFFFF == -1 and 0x8000000000000000 < 0)
        Main.check("mask to 32 bits", (0xFFFFFFFF + 1) & 0xFFFFFFFF == 0)
        Main.check("rotate", ((0x80000001 << 1) | (0x80000001 >>> 31)) & 0xFFFFFFFF == 3)

        Main.check("precedence", (1 | 2 & 3) == 3 and (1 + 2 << 1) == 6 and (6 & 3 == 2) == true)
        Main.check("xor binds tighter than |", (1 | 3 ^ 1) == 3)

        x = 0b1100
        x &= 0b1010
        Main.check("&=", x == 8)
        x |= 1
        Main.check("|=", x == 9)
        x ^= 0xF
        Main.check("^=", x == 6)
        x <<= 4
        Main.check("<<=", x == 96)
        x >>= 1
        Main.check(">>=", x == 48)
        x = -1
        x >>>= 60
        Main.check(">>>=", x == 15)

        Main.check("bool xor", (true xor false) and not (true xor true) and not (false xor false))
        Main.check("bool ops", (true & false) == false and (true | false) == true and (true ^ true) == false)
        Main.check("xor precedence", (true or false xor true) == true and (false and true xor true) == true)
        box: List[int] = []
        r = false and Main.side(box)
        Main.check("and still short-circuits", box.size() == 0)
        r = false xor Main.side(box)
        r = true & Main.side(box)
        Main.check("xor and & evaluate both sides", box.size() == 2)
        box = null
