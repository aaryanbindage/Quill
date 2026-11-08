# expect: field id is private to Base
class Base:
    private id: int
class Sub < Base:
    def get(self) -> int:
        return self.id
class Main:
    static def main():
        pass
