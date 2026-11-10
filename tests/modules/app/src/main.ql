bring util.text
bring shapes

class Main:
    static def main():
        print(Text.shout("hello"))
        c = new Circle(2.0)
        print("area", c.area())
