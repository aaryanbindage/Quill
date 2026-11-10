# expect: operator | needs two ints (or two bools), not str and str
class Main:
    static def main():
        x = "a" | "b"
