# uses the wrapper `quill wrap` generated from vec.h (see tests/run_all.sh)
bring std.native
bring std.text
bring vec

class Main:
    static def check(name: str, ok: bool):
        if ok:
            print("ok  ", name)
        else:
            print("FAIL", name)

    static def main():
        base: int = heap_live()

        v = Vec.new_()
        Main.check("handle", v != null)
        for i in range(5):
            Vec.push(v, i * 10)
        Main.check("len and get", Vec.len(v) == 5 and Vec.get(v, 3) == 30)
        Main.check("long long result", Vec.sum(v) == 100)
        Main.check("double result", Vec.mean(v) == 20.0)
        Main.check("bool result", Vec.contains(v, 40) and not Vec.contains(v, 41))
        Main.check("enum constants", Vec.VEC_OK() == 0 and Vec.VEC_FULL() == 2)
        Main.check("macro constants", Vec.VEC_MAX() == 8 and Vec.VEC_NAME() == "vec" and Vec.VEC_RATIO() == 3.25)
        Main.check("static string copied", Vec.describe(v) == "vec of 5")
        Main.check("malloc string freed", Vec.join(v, ", ") == "0, 10, 20, 30, 40")
        Main.check("string argument", Vec.count_char("banana", 97) == 3)
        Main.check("bytes become a list", Vec.checksum([1, 2, 3, 4]) == 1463068797)
        Main.check("checksum is stable", Vec.checksum(Text.bytes("hello")) == Vec.checksum(Text.bytes("hello")))
        Main.check("bytes values", Vec.first_byte([200, 1]) == 200)

        status = 0
        for i in range(10):
            status = Vec.push(v, i)
        Main.check("status code", status == Vec.VEC_FULL() and Vec.len(v) == 8)

        # the raw layer: output parameters through a Buffer, no pointer in sight
        out = new Buffer(8)
        VecRaw.vec_dims(v.handle, out.address(), out.address() + 4)
        Main.check("output parameters via Buffer", out.get(0) == 8 and out.get(4) == 1)
        out = null

        v.close()
        Main.check("closed", v.handle == 0)
        v.close()
        Main.check("close twice is safe", true)

        w = Vec.new_()
        w = null
        v = null
        if heap_live() - base == 0:
            print("ok   no leaks")
        else:
            print("LEAK", heap_live() - base)
