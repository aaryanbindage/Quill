# expect: cannot use str as int (map value)
class Main:
    static def main():
        m: Map[str, int] = {"a" -> "b"}
