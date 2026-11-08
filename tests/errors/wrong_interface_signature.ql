# expect: different signature than interface method
interface Pet:
    def speak(self) -> str
class Dog < Pet:
    def speak(self) -> int:
        return 1
class Main:
    static def main():
        pass
