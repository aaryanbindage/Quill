# expect: cannot use str as int (array element)
class Main:
    static def main():
        a = new Array[int](3)
        a[0] = "x"
