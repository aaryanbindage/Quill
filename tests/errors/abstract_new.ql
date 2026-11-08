# expect: cannot instantiate abstract class Shape
abstract class Shape:
    abstract def area(self) -> float
class Main:
    static def main():
        s = new Shape()
