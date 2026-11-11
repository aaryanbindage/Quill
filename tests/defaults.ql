# default methods in interfaces
interface Shape:
    def area(self) -> int
    def name(self) -> str:
        return "shape"
    def describe(self) -> str:
        return self.name() + " with area " + str(self.area())
    def double(self) -> int:
        return self.area() * 2

interface Loud:
    def shout(self) -> str:
        return "LOUD"

class Square < Shape:
    side: int
    def init(self, side: int):
        self.side = side
    def area(self) -> int:
        return self.side * self.side

class Circle < Shape:
    def area(self) -> int:
        return 3
    def name(self) -> str:
        return "circle"

class Both < Shape, Loud:
    def area(self) -> int:
        return 1

class Child < Square:
    def init(self):
        super.init(5)
    def name(self) -> str:
        return "child"

class Main:
    static def check(name: str, ok: bool):
        if ok:
            print("ok  ", name)
        else:
            print("FAIL", name)

    static def main():
        base: int = heap_live()
        a: Shape = new Square(3)
        b: Shape = new Circle()
        c = new Both()
        d: Shape = new Child()
        Main.check("default used", a.name() == "shape")
        Main.check("default calls required", a.describe() == "shape with area 9")
        Main.check("override wins", b.name() == "circle" and b.describe() == "circle with area 3")
        Main.check("second default", a.double() == 18)
        Main.check("two interfaces", c.shout() == "LOUD" and c.describe() == "shape with area 1")
        Main.check("inherited override", d.describe() == "child with area 25")
        a = null
        b = null
        c = null
        d = null
        if heap_live() != base:
            print("LEAK", heap_live() - base)
