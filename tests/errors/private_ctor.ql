# expect: constructor of Single is private
class Single:
    private def init(self):
        pass
class Main:
    static def main():
        s = new Single()
