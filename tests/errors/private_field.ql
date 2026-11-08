# expect: field id is private to Shape
class Shape:
    private id: int
class Main:
    static def main():
        s = new Shape()
        print(s.id)
