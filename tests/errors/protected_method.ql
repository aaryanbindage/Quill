# expect: method fee is protected in Account
class Account:
    protected def fee(self) -> int:
        return 1

class Main:
    static def main():
        a = new Account()
        print(a.fee())
