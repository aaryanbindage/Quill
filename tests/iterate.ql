# for loops directly over a Map (keys, or key and value) and a Set
class Main:
    static def check(name: str, ok: bool):
        if ok:
            print("ok  ", name)
        else:
            print("FAIL", name)

    static def makeMap() -> Map[str, int]:
        m = new Map[str, int]()
        m.set("x", 1)
        m.set("y", 2)
        return m

    static def makeSet() -> Set[int]:
        s = new Set[int]()
        s.add(4)
        s.add(5)
        return s

    static def nested() -> int:
        lists = new Map[str, List[int]]()
        lists.set("a", [1, 2])
        lists.set("b", [3])
        items = 0
        for key, vals in lists:
            for item in vals:
                items = items + item
        return items

    static def main():
        base: int = heap_live()
        m = new Map[str, int]()
        m.set("a", 1)
        m.set("b", 2)
        m.set("c", 3)

        total = 0
        names = ""
        for k in m:
            total = total + m.get(k)
            names = names + k
        Main.check("map keys", total == 6 and len(names) == 3 and names.contains("b"))

        sum = 0
        count = 0
        for k, v in m:
            sum = sum + v
            if m.get(k) == v:
                count = count + 1
        Main.check("map pairs", sum == 6 and count == 3)

        s = new Set[int]()
        for n in [3, 1, 3, 2]:
            s.add(n)
        acc = 0
        seen = 0
        for x in s:
            acc = acc + x
            seen = seen + 1
        Main.check("set items", acc == 6 and seen == 3)

        # the loop works on a snapshot, so changing the map inside it is safe
        removed = 0
        for k in m:
            m.remove(k)
            removed = removed + 1
        Main.check("remove while looping", removed == 3 and m.size() == 0)

        # an owned temporary is cleaned up, break and continue work
        n = 0
        for k in Main.makeMap():
            n = n + 1
        Main.check("temporary map", n == 2)
        n = 0
        for x in Main.makeSet():
            if x == 4:
                continue
            n = n + x
        Main.check("temporary set", n == 5)
        for k, v in Main.makeMap():
            break

        items = Main.nested()
        Main.check("nested", items == 6)

        e = new Map[int, int]()
        none = 0
        for k in e:
            none = none + 1
        Main.check("empty", none == 0)

        k = ""
        names = ""
        m = null
        s = null
        e = null
        if heap_live() != base:
            print("LEAK", heap_live() - base)
