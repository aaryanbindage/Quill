# expect: cannot order Plain
class Plain:
    pass

class Main:
    static def main():
        xs = [new Plain()]
        xs.sort()
