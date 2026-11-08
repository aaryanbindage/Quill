# expect: method secret is private to Shape
class Shape:
    private def secret(self) -> int:
        return 1
class Main:
    static def main():
        s = new Shape()
        print(s.secret())
