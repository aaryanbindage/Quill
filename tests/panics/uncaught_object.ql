# expect: uncaught exception
class Thing:
    pass

class Main:
    static def main():
        throw new Thing()
