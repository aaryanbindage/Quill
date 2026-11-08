# expect: list index out of range
class Main:
    static def main():
        xs = new List[str]()
        xs.add("a")
        print(xs[1])
