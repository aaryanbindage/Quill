# 14. Threads

A **thread** is a second line of execution running at the same time as the first.
Programs use threads to do several things at once, such as downloading while the user
keeps typing. In Quill, a thread is a class that extends `Thread` and overrides `run`.

```python
# course: runs
class Worker < Thread:
    id: int
    result: int

    def init(self, id: int):
        self.id = id
        self.result = 0

    def run(self):
        total = 0
        for i in range(1, 1001):
            total = total + i * self.id
        self.result = total

class Main:
    static def main():
        workers = new List[Worker]()
        for id in range(1, 5):
            w = new Worker(id)
            workers.add(w)
            w.start()                 # begins running at once
        for w in workers:
            w.join()                  # wait for it to finish
            print("worker", w.id, "->", w.result)
```

```text
worker 1 -> 500500
worker 2 -> 1001000
worker 3 -> 1501500
worker 4 -> 2002000
```

- `start()` launches the thread; `join()` waits for it. If you do not join, the program
  may end before the thread does.
- Each worker here only touches its **own** fields, so the threads cannot interfere.

## The danger: shared data

If threads change the *same* variable, updates can be lost, because "read, add one,
write back" is three steps and another thread can slip in between. The fix is a
`Mutex`, a lock only one thread can hold at a time:

```python
# course: runs
class Counter:
    n: int

class Adder < Thread:
    counter: Counter
    lock: Mutex

    def init(self, counter: Counter, lock: Mutex):
        self.counter = counter
        self.lock = lock

    def run(self):
        for i in range(20000):
            self.lock.lock()
            self.counter.n = self.counter.n + 1
            self.lock.unlock()

class Main:
    static def main():
        counter = new Counter()
        lock = new Mutex()
        threads = new List[Adder]()
        for i in range(4):
            t = new Adder(counter, lock)
            threads.add(t)
            t.start()
        for t in threads:
            t.join()
        print("total:", counter.n)
```

```text
total: 80000
```

Remove the `lock()` and `unlock()` lines and run it a few times: the total will usually
come out smaller than 80000. Quill protects its own reference counts, but not your fields.

## Limits

Quill's toolkit is small for now: `Thread` and `Mutex`. There are no channels, condition
variables or atomic integers yet (they are on the [roadmap](../roadmap.md)). On Linux
and macOS you can check a program for data races with `quill run --sanitize thread`.

## Exercises

1. Make four threads each add up a quarter of 1 to 1,000,000 and combine their answers.
2. Write a program where two threads append to one `List` using a `Mutex`.
3. Remove the lock from the counter example. How far off is the total? Why?
4. Use `Thread.sleep(100)` inside `run` to simulate slow work and watch the order change.

Next: the [language guide](../language-guide.md) covers modules, packages and calling C
libraries; more lessons on those are planned.
