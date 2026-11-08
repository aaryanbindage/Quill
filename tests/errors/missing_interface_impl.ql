# expect: class Dog does not implement Pet.speak
interface Pet:
    def speak(self) -> str
class Dog < Pet:
    pass
class Main:
    static def main():
        pass
