# expect: unknown class Nope
class Main:
    static def main():
        try:
            print(1)
        catch Nope as e:
            print(2)
