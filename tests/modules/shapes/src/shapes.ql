bring mathx

class Circle:
    r: float
    def init(self, r: float):
        self.r = r
    def area(self) -> float:
        return Maths.pi() * Maths.square(self.r)
