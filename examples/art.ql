# Text art in the terminal: a canvas, big letters and colours.  quill run examples/art.ql
bring std.art
bring std.console

class Main:
    static def main():
        Console.init()
        Banner.show("Quill", Console.cyan())
        c = new Canvas(44, 15)
        c.frame(0, 0, 44, 15, 8)
        c.fillEllipse(14, 7, 10, 5, "#", Console.rgb(255, 120, 0))
        c.ellipse(30, 7, 10, 5, "o", Console.green())
        c.line(2, 13, 41, 1, "*", Console.yellow())
        c.text(17, 7, "hello", Console.white())
        c.show()
        print(Art.rainbow("drawn with std.art"))
        name = Console.ask("your name? ")
        if name != null:
            Console.writeln(Console.bold("hi " + name))
