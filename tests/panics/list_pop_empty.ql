# expect: list index out of range
class Main:
    static def main():
        xs = new List[int]()
        xs.pop()
