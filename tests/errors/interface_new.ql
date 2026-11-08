# expect: cannot instantiate interface Named
interface Named:
    def name(self) -> str
class Main:
    static def main():
        s = new Named()
