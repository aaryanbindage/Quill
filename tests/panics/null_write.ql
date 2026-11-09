# expect: null pointer dereference
class Node:
    v: int

class Main:
    static def main():
        n: Node = null
        n.v = 3
