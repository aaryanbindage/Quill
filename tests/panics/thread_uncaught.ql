# expect: uncaught exception: from thread
class Worker < Thread:
    def run(self):
        throw new Error("from thread")

class Main:
    static def main():
        w = new Worker()
        w.start()
        w.join()
