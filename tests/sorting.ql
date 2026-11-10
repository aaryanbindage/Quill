# List.sort and friends, string ordering, compareTo
class Person:
    name: str
    age: int
    def init(self, name: str, age: int):
        self.name = name
        self.age = age
    def compareTo(self, other: Person) -> int:
        return self.age - other.age

class Student < Person:
    def init(self, name: str, age: int):
        super.init(name, age)

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

    static def join(xs: List[int]) -> str:
        out = ""
        for x in xs:
            out = out + str(x) + " "
        return out

    static def main():
        base: int = heap_live()

        xs = [5, 3, 9, 1, 7, 3, -4, 0]
        xs.sort()
        Main.check("ints", Main.join(xs) == "-4 0 1 3 3 5 7 9 ")
        Main.check("isSorted", xs.isSorted())
        xs.sortDesc()
        Main.check("descending", Main.join(xs) == "9 7 5 3 3 1 0 -4 ")
        Main.check("not sorted", not xs.isSorted())
        xs.reverse()
        Main.check("reverse", Main.join(xs) == "-4 0 1 3 3 5 7 9 ")
        Main.check("min max", xs.min() == -4 and xs.max() == 9)

        ys = [3, 1, 2]
        zs = ys.sorted()
        Main.check("sorted copy", Main.join(ys) == "3 1 2 " and Main.join(zs) == "1 2 3 ")

        e: List[int] = []
        e.sort()
        Main.check("empty", e.isSorted() and e.size() == 0)
        one = [42]
        one.sort()
        Main.check("single", one.get(0) == 42)

        fs = [2.5, -1.0, 3.0, 0.5]
        fs.sort()
        Main.check("floats", fs.get(0) == -1.0 and fs.get(3) == 3.0)

        ws = ["pear", "apple", "fig", "banana", ""]
        ws.sort()
        Main.check("strings", ws.get(0) == "" and ws.get(1) == "apple" and ws.get(4) == "pear")
        Main.check("string order", "a" < "b" and "b" > "a" and "a" <= "a" and "ab" >= "a" and not ("b" < "a"))

        bs = [true, false, true, false]
        bs.sort()
        Main.check("bools", not bs.get(0) and bs.get(3))

        ps = [new Person("ann", 30), new Person("bo", 20), new Person("cy", 25), new Person("di", 20)]
        ps.sort()
        Main.check("objects", ps.get(0).name == "bo" and ps.get(3).name == "ann")
        Main.check("stable", ps.get(0).name == "bo" and ps.get(1).name == "di")
        Main.check("object min max", ps.min().name == "bo" and ps.max().name == "ann")

        people: List[Person] = [new Student("s1", 22), new Person("p", 19)]
        people.sort()
        Main.check("subclasses", people.get(0).name == "p")

        big = new List[int]()
        for i in range(500):
            big.add((i * 7919) % 1009)
        big.sort()
        Main.check("500 elements", big.isSorted() and big.size() == 500)

        xs = null
        ys = null
        zs = null
        e = null
        one = null
        fs = null
        ws = null
        bs = null
        ps = null
        people = null
        big = null
        Main.leak("sorting", heap_live() - base)
