# toString, str(), instanceof, casts and null-safe printing
interface Named:
    def name(self) -> str

class Animal:
    label: str
    def init(self, label: str):
        self.label = label
    def toString(self) -> str:
        return "Animal(" + self.label + ")"

class Dog < Animal, Named:
    def init(self, label: str):
        super.init(label)
    def name(self) -> str:
        return "dog " + self.label
    def bark(self) -> str:
        return "Woof " + self.label

class Cat < Animal:
    def init(self, label: str):
        super.init(label)

class Plain:
    x: int

class Main:
    static def check(name: str, ok: bool):
        if ok:
            print("ok  ", name)
        else:
            print("FAIL", name)

    static def leak(name: str, live: int):
        if live == 0:
            print("ok  ", name)
        else:
            print("LEAK", name, live)

    static def make() -> Animal:
        return new Dog("tmp")

    static def main():
        base: int = heap_live()
        a: Animal = new Dog("Rex")
        b: Animal = new Cat("Tom")
        n: Animal = null
        Main.check("print toString", str(a) == "Animal(Rex)")
        Main.check("str(null)", str(n) == "null")
        Main.check("str int", str(42) == "42")
        Main.check("str float", str(2.5) == "2.5")
        Main.check("str bool", str(true) == "true")
        Main.check("temp toString", str(new Cat("t")) == "Animal(t)")
        Main.check("call toString", str(Main.make()) == "Animal(tmp)")
        print(a, b, n)
        print(new Plain() instanceof Plain)
        Main.check("instanceof self", a instanceof Dog)
        Main.check("instanceof parent", a instanceof Animal)
        Main.check("instanceof sibling", not (b instanceof Dog))
        Main.check("instanceof interface", a instanceof Named)
        Main.check("not interface", not (b instanceof Named))
        Main.check("null instanceof", not (n instanceof Animal))
        d: Dog = a as Dog
        Main.check("downcast", d.bark() == "Woof Rex")
        nm: Named = a as Named
        Main.check("cast to interface", nm.name() == "dog Rex")
        Main.check("null cast", (n as Dog) == null)
        up: Animal = d as Animal
        Main.check("upcast", up == a)
        Main.check("temp cast", (Main.make() as Dog).bark() == "Woof tmp")
        d = null
        nm = null
        up = null
        a = null
        b = null
        Main.leak("features", heap_live() - base)
