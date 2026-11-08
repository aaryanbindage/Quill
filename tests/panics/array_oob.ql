# expect: index 3 out of range (length 2)
class Main:
    static def main():
        a = new Array[int](2)
        a[3] = 1
