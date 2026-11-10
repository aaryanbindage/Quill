native link "m"

class Fast:
    native static def twice_(x: float) -> float = "sqrt(double) -> double"
    static def twice(x: int) -> int:
        return x * 2
