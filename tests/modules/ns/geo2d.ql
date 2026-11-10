class Point:
    x: int
    y: int
    def init(self, x: int, y: int):
        self.x = x
        self.y = y
    def describe(self) -> str:
        return "2d(" + str(self.x) + "," + str(self.y) + ")"
    static def origin() -> Point:
        return new Point(0, 0)

class Shape < Point:
    def init(self):
        super.init(1, 1)

class Oops < Error:
    pass

class Box[T]:
    item: T
    def init(self, item: T):
        self.item = item
