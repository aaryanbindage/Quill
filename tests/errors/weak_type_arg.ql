# expect: type arguments cannot be weak
class Node:
    pass
class Main:
    static def main():
        xs = new List[weak Node]()
