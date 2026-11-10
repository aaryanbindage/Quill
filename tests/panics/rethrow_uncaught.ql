# expect: uncaught exception: bad
class Main:
    static def main():
        try:
            throw new Error("first")
        catch Error as e:
            throw new Error("bad")
