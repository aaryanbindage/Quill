# expect: index -1 out of range
class Main:
    static def main():
        a = new Array[int](2)
        i = 0 - 1
        print(a[i])
