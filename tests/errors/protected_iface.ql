# expect: cannot be protected
interface Shape:
    def area(self) -> int

class Sq < Shape:
    protected def area(self) -> int:
        return 4

class Main:
    static def main():
        print(1)
