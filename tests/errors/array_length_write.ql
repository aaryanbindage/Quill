# expect: array length is read-only
class Main:
    static def main():
        a = new Array[int](3)
        a.length = 5
