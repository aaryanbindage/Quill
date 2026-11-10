bring geo2d as flat
bring geo3d as solid

class Point:
    def describe(self) -> str:
        return "my own Point"

class Main:
    static def show(p: flat.Point):
        print(p.describe())

    static def main():
        a = new flat.Point(1, 2)
        b = new solid.Point(3, 4, 5)
        c = new Point()
        print(a.describe(), b.describe(), c.describe())
        Main.show(flat.Point.origin())
        pts: List[flat.Point] = [a, new flat.Shape()]
        print(len(pts), pts[1].describe())
        print(a instanceof flat.Point, pts[1] instanceof flat.Shape, a instanceof flat.Shape)
        s: flat.Shape = pts[1] as flat.Shape
        print(s.x)
        box = new flat.Box[int](42)
        print(box.item)
        try:
            throw new flat.Oops("custom")
        catch flat.Oops as e:
            print("caught", e.message)
