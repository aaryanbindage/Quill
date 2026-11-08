class Counter:
    n: int

class Adder < Thread:
    counter: Counter
    lock: Mutex
    times: int

    def init(self, c: Counter, l: Mutex, times: int):
        self.counter = c
        self.lock = l
        self.times = times

    def run(self):
        for i in range(self.times):
            self.lock.lock()
            self.counter.n += 1
            self.lock.unlock()

# Hammers the reference counts of one shared object from many threads.
class Sharer < Thread:
    shared: Counter

    def init(self, c: Counter):
        self.shared = c

    def run(self):
        for i in range(300000):
            x = self.shared
            y = x
            z: Counter = y
            s = "a" + "b"

class Napper < Thread:
    ms: int
    def init(self, ms: int):
        self.ms = ms
    def run(self):
        Thread.sleep(self.ms)

class Main:
    static def check(name: str, live: int):
        if live == 0:
            print("ok  ", name)
        else:
            print("LEAK", name, live)

    static def main():
        # 1. mutex-protected counter: 4 threads x 50000 = 200000 exactly
        c = new Counter()
        m = new Mutex()
        t1 = new Adder(c, m, 50000)
        t2 = new Adder(c, m, 50000)
        t3 = new Adder(c, m, 50000)
        t4 = new Adder(c, m, 50000)
        t1.start()
        t2.start()
        t3.start()
        t4.start()
        t1.join()
        t2.join()
        t3.join()
        t4.join()
        print("count:", c.n, "expected 200000")
        t1 = null
        t2 = null
        t3 = null
        t4 = null
        m = null
        c = null
        Main.check("mutex counter", heap_live())

        # 2. shared refcounts under contention
        shared = new Counter()
        s1 = new Sharer(shared)
        s2 = new Sharer(shared)
        s3 = new Sharer(shared)
        s1.start()
        s2.start()
        s3.start()
        s1.join()
        s2.join()
        s3.join()
        s1 = null
        s2 = null
        s3 = null
        shared = null
        Main.check("shared refcounts", heap_live())

        # 3. a thread keeps its object alive after the starter drops it
        nap = new Napper(50)
        nap.start()
        h = nap.handle
        nap = null
        __thread_join(h)
        Main.check("thread outlives handle", heap_live())
