class Point:
    x: int
    y: int
    z: int
    def init(self, x: int, y: int, z: int):
        self.x = x
        self.y = y
        self.z = z
    def describe(self) -> str:
        return "3d(" + str(self.x) + "," + str(self.y) + "," + str(self.z) + ")"
