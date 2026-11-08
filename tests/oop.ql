interface Named:
    def name(self) -> str

interface Greeter < Named:
    def greet(self) -> str

abstract class Shape:
    private id: int
    label: str

    def init(self, label: str):
        self.label = label
        self.id = 7

    abstract def area(self) -> float

    def getId(self) -> int:
        return self.id

    private def secret(self) -> int:
        return 41

    def reveal(self) -> int:
        return self.secret() + 1

class Rect < Shape, Named:
    w: float
    h: float

    def init(self, w: float, h: float):
        super.init("rect")
        self.w = w
        self.h = h

    def area(self) -> float:
        return self.w * self.h

    def name(self) -> str:
        return "Rect"

class Square < Rect:
    def init(self, s: float):
        super.init(s, s)
        self.label = "square"

    def area(self) -> float:
        return super.area()              # parent's implementation

    def name(self) -> str:
        return "Square(" + super.name() + ")"

class Circle < Shape, Greeter:
    r: float

    def init(self, r: float):
        super.init("circle")
        self.r = r

    def area(self) -> float:
        return 3.0 * self.r * self.r

    def name(self) -> str:
        return "Circle"

    def greet(self) -> str:
        return "hello from " + self.name()

# private methods are not virtual: A.callHelper always uses A.helper
class A:
    private def helper(self) -> int:
        return 1
    def callHelper(self) -> int:
        return self.helper()

class B < A:
    private def helper(self) -> int:
        return 2
    def callOwn(self) -> int:
        return self.helper()

class Main:
    static def show(s: Shape):
        print(s.label, s.area())

    static def intro(n: Named):
        print(n.name())

    static def hello(g: Greeter):
        print(g.greet(), "/", g.name())     # name() comes from the super-interface

    static def check(name: str, live: int):
        if live == 0:
            print("ok  ", name)
        else:
            print("LEAK", name, live)

    static def main():
        Main.show(new Rect(2.0, 3.0))       # abstract type, virtual area()
        Main.show(new Square(4.0))
        Main.show(new Circle(1.0))

        Main.intro(new Rect(1.0, 1.0))      # interface dispatch
        Main.intro(new Square(1.0))
        Main.intro(new Circle(1.0))
        Main.hello(new Circle(1.0))

        n: Named = new Square(2.0)
        print("via interface:", n.name())
        g: Greeter = new Circle(2.0)
        n = g                               # Greeter is a Named
        print("after reassign:", n.name())

        s: Shape = new Circle(1.0)
        print("id:", s.getId(), "reveal:", s.reveal())

        a = new A()
        b = new B()
        print("private non-virtual:", a.callHelper(), b.callHelper(), b.callOwn())

        a = null
        b = null
        s = null
        n = null
        g = null
        Main.check("oop leaks", heap_live())
