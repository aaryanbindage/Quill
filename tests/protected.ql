# protected members: visible in the declaring class and its subclasses, hidden elsewhere
class Account:
    protected balance: int
    def init(self, start: int):
        self.balance = start
    protected def fee(self) -> int:
        return 2
    def net(self) -> int:
        return self.balance - self.fee()

class Savings < Account:
    def init(self, start: int):
        super.init(start)
    protected def fee(self) -> int:
        return 5
    def bonus(self) -> int:
        self.balance = self.balance + 10
        return self.balance - self.fee()
    def peek(self, other: Account) -> int:
        return other.balance

class Main:
    static def check(name: str, ok: bool):
        if ok:
            print("ok  ", name)
        else:
            print("FAIL", name)

    static def main():
        base: int = heap_live()
        a = new Account(100)
        s = new Savings(100)
        Main.check("base uses its own", a.net() == 98)
        Main.check("override is virtual", s.net() == 95)
        Main.check("subclass uses field", s.bonus() == 105)
        Main.check("subclass reads other", s.peek(a) == 100)
        a = null
        s = null
        if heap_live() != base:
            print("LEAK", heap_live() - base)
