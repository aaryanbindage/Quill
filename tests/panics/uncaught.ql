# expect: uncaught exception: boom
class Main:
    static def f():
        throw new Error("boom")

    static def main():
        Main.f()
