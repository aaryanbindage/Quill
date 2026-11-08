# expect: key not found in map
class Main:
    static def main():
        m = new Map[str, int]()
        m["a"] = 1
        print(m["b"])
