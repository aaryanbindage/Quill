# expect: cannot use str as int (argument x)
class Main:
    static def main():
        xs = new List[int]()
        xs.add("nope")
