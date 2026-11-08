# expect: cannot use Rock as Pet
interface Pet:
    def speak(self) -> str
class Rock:
    pass
class Main:
    static def main():
        p: Pet = new Rock()
