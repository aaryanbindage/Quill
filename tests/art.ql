# std.art: canvas drawing, big letters and helpers, compared as plain text
bring std.art

class Main:
    static def check(name: str, ok: bool):
        if ok:
            print("ok  ", name)
        else:
            print("FAIL", name)

    static def main():
        base: int = heap_live()

        c = new Canvas(6, 3)
        c.plot(0, 0, "a", -1)
        c.plot(5, 2, "b", -1)
        c.plot(9, 9, "x", -1)
        Main.check("plot", c.toString() == "a\n\n     b\n")
        Main.check("get", c.get(0, 0) == "a" and c.get(1, 1) == " " and c.get(50, 50) == " ")

        c.clear()
        c.line(0, 0, 5, 0, "-", -1)
        Main.check("line", c.toString() == "------\n\n\n")
        c.clear()
        c.line(0, 0, 2, 2, "\\", -1)
        Main.check("diagonal", c.toString() == "\\\n \\\n  \\\n")

        c.clear()
        c.rect(0, 0, 4, 3, "#", -1)
        Main.check("rect", c.toString() == "####\n#  #\n####\n")

        c.clear()
        c.frame(0, 0, 5, 3, -1)
        Main.check("frame", c.toString() == "+---+\n|   |\n+---+\n")

        c.clear()
        c.fillRect(1, 1, 2, 2, "x", -1)
        Main.check("fillRect clipped", c.toString() == "\n xx\n xx\n")

        c.clear()
        c.text(1, 1, "hi", -1)
        Main.check("text", c.toString() == "\n hi\n\n")

        c.clear()
        c.rect(0, 0, 3, 3, "#", -1)
        c.floodFill(1, 1, "o", -1)
        Main.check("floodFill", c.get(1, 1) == "o" and c.get(4, 1) == " ")

        d = new Canvas(2, 1)
        d.plot(0, 0, "z", -1)
        c.clear()
        c.draw(d, 3, 2)
        Main.check("draw", c.get(3, 2) == "z" and c.get(4, 2) == " ")

        e = new Canvas(30, 15)
        e.fillEllipse(15, 7, 10, 5, "#", -1)
        e.ellipse(15, 7, 12, 6, "o", -1)
        Main.check("ellipse", e.get(15, 7) == "#" and e.get(15, 1) == "o" and e.get(3, 7) == "o" and e.get(0, 0) == " ")

        f = new Canvas(3, 3)
        v = new List[int]()
        v.add(1)
        v.add(3)
        f.bars(v, "|", -1)
        Main.check("bars", f.toString() == " |\n |\n||\n")

        col = new Canvas(2, 1)
        col.plot(0, 0, "a", 1)
        Main.check("colour render", len(col.render(true)) > len(col.render(false)))
        Main.check("plain render has no escapes", col.render(false) == "a\n")

        Main.check("banner", Banner.render("I") == "##### \n  #   \n  #   \n  #   \n##### \n")
        Main.check("banner rows", len(Banner.render("hello")) == 5 * (5 * 6 + 1))
        Main.check("banner unknown", Banner.render("@") == Banner.render("?"))
        Main.check("shade", Art.shade(0.0) == " " and Art.shade(1.0) == "@" and Art.shade(0.5) == "+")
        Main.check("isqrt", Art.isqrt(0) == 0 and Art.isqrt(99) == 9 and Art.isqrt(100) == 10)
        Main.check("rule", Art.rule(3, "=") == "===")
        lines = new List[str]()
        lines.add("ab")
        lines.add("c")
        Main.check("boxed", Art.boxed(lines) == "+----+\n| ab |\n| c  |\n+----+\n")
        Main.check("rainbow", len(Art.rainbow("a b")) > 3)

        c = null
        d = null
        e = null
        f = null
        col = null
        lines = null
        v = null
        if heap_live() != base:
            print("LEAK", heap_live() - base)
