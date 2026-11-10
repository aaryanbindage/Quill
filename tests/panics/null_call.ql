# expect: null pointer dereference (calling size)
class Main:
    static def main():
        xs: List[int] = null
        print(xs.size())
