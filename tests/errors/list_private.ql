# expect: field items is private to List[int]
class Main:
    static def main():
        xs = new List[int]()
        print(xs.items)
