# expect: field balance is protected in Account
class Account:
    protected balance: int

class Main:
    static def main():
        a = new Account()
        print(a.balance)
