# Set[T]: operations, literals, element types
class Item:
    id: int
    def init(self, id: int):
        self.id = id

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

    static def join(s: Set[int]) -> str:
        out = ""
        for x in s.sortedItems():
            out = out + str(x) + " "
        return out

    static def main():
        base: int = heap_live()

        a = {1, 2, 3, 4}
        b = {3, 4, 5}
        Main.check("literal", a.size() == 4 and a.has(1) and not a.has(9))
        Main.check("duplicates", {1, 1, 2, 2}.size() == 2)
        Main.check("add", a.add(10) and not a.add(10) and a.size() == 5)
        Main.check("remove", a.remove(10) and not a.remove(10) and a.size() == 4)
        Main.check("union", Main.join(a.union(b)) == "1 2 3 4 5 ")
        Main.check("intersect", Main.join(a.intersect(b)) == "3 4 ")
        Main.check("difference", Main.join(a.difference(b)) == "1 2 ")
        Main.check("other difference", Main.join(b.difference(a)) == "5 ")
        Main.check("symDiff", Main.join(a.symDiff(b)) == "1 2 5 ")
        Main.check("operands unchanged", Main.join(a) == "1 2 3 4 " and Main.join(b) == "3 4 5 ")
        Main.check("subset", {3, 4}.isSubsetOf(a) and not b.isSubsetOf(a))
        Main.check("superset", a.isSupersetOf({1, 2}) and not a.isSupersetOf(b))
        Main.check("disjoint", a.isDisjoint({8, 9}) and not a.isDisjoint(b))
        Main.check("equals", {1, 2}.equals({2, 1}) and not {1, 2}.equals({1, 2, 3}))

        c = a.copy()
        c.add(99)
        Main.check("copy is separate", c.size() == 5 and a.size() == 4)
        c.removeAll(b)
        Main.check("removeAll", Main.join(c) == "1 2 99 ")
        c.retainAll({1, 99, 100})
        Main.check("retainAll", Main.join(c) == "1 99 ")
        c.addAll(b)
        Main.check("addAll", c.size() == 5)
        c.clear()
        Main.check("clear", c.isEmpty())

        names: Set[str] = {}
        names.add("ann")
        names.add("bo")
        names.add("ann")
        Main.check("strings by value", names.size() == 2 and names.has("b" + "o"))
        Main.check("sorted strings", names.sortedItems().get(0) == "ann")

        m = {"k" -> 1}
        Main.check("map literal still works", m.get("k") == 1)
        em: Map[str, int] = {}
        Main.check("empty map by type", em.size() == 0)

        i1 = new Item(1)
        i2 = new Item(2)
        objs = {i1, i2}
        Main.check("objects by identity", objs.has(i1) and objs.size() == 2)

        a = null
        b = null
        c = null
        names = null
        m = null
        em = null
        i1 = null
        i2 = null
        objs = null
        Main.leak("sets", heap_live() - base)
