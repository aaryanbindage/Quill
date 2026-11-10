# Quill Language Guide

## Program structure

Quill is class-only: there are no top-level functions or variables. A program
is a list of classes, and execution starts at `static def main()` in a class
named `Main`. `main` takes no arguments and returns nothing or an `int`
(used as the process exit code).

```python
class Main:
    static def main():
        print("hello")
```

## Lexical rules

- Blocks are defined by indentation (spaces only; tabs are an error).
- A block header ends with `:`. A one-line body may follow on the same line.
- `#` starts a comment. Newlines inside `( )` are ignored.
- Strings use double quotes with escapes `\n \t \r \0 \\ \"`.
- Keywords: `class def static return if elif else while for in new self true
  false null and or not break continue pass weak
  public private abstract interface super instanceof as try catch throw`.

## Types

| Type    | Meaning                          | LLVM     |
|---------|----------------------------------|----------|
| `int`   | 64-bit signed integer            | `i64`    |
| `float` | 64-bit float                     | `double` |
| `bool`  | `true` / `false`                 | `i1`     |
| `str`   | immutable UTF-8 C string         | `ptr`    |
| `void`  | no value (return type only)      | `void`   |
| `Name`  | reference to an instance of a class | `ptr` |

`null` is assignable to `str` and to any class type.

Implicit conversions: `int` to `float`, and subclass to superclass. Everything
else needs an explicit `int(x)` or `float(x)`.

## Variables

```python
x: int = 5          # annotated
y = 2.5             # type inferred from the first assignment
z: str              # declared, zero-initialised (0, 0.0, false, null)
x += 1              # += -= *= /= %=
```

Variables are block scoped. Redeclaring a name that is already visible in an
enclosing scope is an error (no shadowing).

## Operators

Lowest to highest precedence:

1. `or`
2. `and` (both short-circuit)
3. `not`
4. `==  !=  <  <=  >  >=`
5. `+  -`
6. `*  /  %`
7. unary `-`
8. `.field`, `.method(...)`, calls

Notes:

- `/` and `%` on two `int`s are integer operations (truncating division).
  If either side is `float`, the operation is done in floating point.
- `+` on two `str` values concatenates.
- `==` and `!=` on `str` compare contents. On class types they compare
  identity.
- Conditions must be `bool`; there is no truthiness.

## Control flow

```python
if a < b:
    ...
elif a == b:
    ...
else:
    ...

while n > 0:
    n -= 1

for i in range(10):        # 0..9
    ...
for i in range(2, 8):      # 2..7, bounds evaluated once
    ...
```

`break` and `continue` work in both loop forms. `pass` is a no-op.

## Classes

```python
class Name:
    field: type               # fields have no initialisers; they start zeroed
    def init(self, args...):  # optional constructor
        ...
    def method(self, p: int) -> str:
        ...
    static def util(n: int) -> int:
        ...
```

- **Fields** are declared as `name: type` at the top level of the class.
- **Constructor:** a method called `init`. `new Name(args)` allocates a zeroed
  object and then calls the nearest `init` in the class chain. If no class in
  the chain defines `init`, `new Name()` takes no arguments.
- **Instance methods** take `self` first. Fields and other methods are
  reached only through `self.` (no implicit `this`).
- **Static methods** have no `self`; call them as `ClassName.method(...)`.
- Methods and constructors are not overloaded; a name can be defined once per
  class.

### Inheritance

Single inheritance, written with `<`:

```python
class Dog < Animal:
    def speak(self) -> str:      # overrides Animal.speak
        return "Woof"
```

- A subclass inherits all fields and methods.
- An override must have exactly the same parameter types and return type.
- Instance method calls are **virtual**: the method that runs depends on the
  object's actual class, not the variable's declared type.
- `init` is not virtual and is not inherited by signature: a subclass `init`
  may have different parameters. It does not call the parent `init`
  automatically; call `super.init(...)` yourself (see `super` below).

## Access control: `public` and `private`

Fields and methods (including `init`) are `public` unless marked `private`.
Put the modifier first:

```python
class Account:
    private balance: int
    private def audit(self): ...
    public def deposit(self, n: int):
        self.balance += n
        self.audit()
```

- A private member can be used only inside the class that declares it. Code in
  other classes, **including subclasses**, gets a compile error.
- A private `init` makes `new` available only inside that class (singletons,
  factories).
- Private methods are **not virtual**: a subclass method with the same name is
  a separate method and does not override. A subclass cannot give a public
  method the same name with `private` (that would reduce visibility).

## Abstract classes

```python
abstract class Shape:
    label: str
    abstract def area(self) -> float        # no body, no colon

    def describe(self) -> str:              # normal methods are fine too
        return self.label
```

- An `abstract class` cannot be instantiated with `new`.
- An `abstract def` declares a method with no body. Only abstract classes may
  contain one. It cannot be `static` or `private`.
- Every non-abstract subclass must implement all inherited abstract methods
  with the same parameter and return types, or the class is a compile error.

## Interfaces

```python
interface Named:
    def name(self) -> str

interface Greeter < Named:                  # interfaces can extend interfaces
    def greet(self) -> str

class Circle < Shape, Greeter:              # one class, any number of interfaces
    def name(self) -> str: ...
    def greet(self) -> str: ...
```

- An interface has only public, non-static method signatures: no fields,
  bodies, `init` or `deinit`.
- After `<`, a class lists at most one superclass and any number of
  interfaces, in any order.
- A concrete class must implement every method of every interface it
  promises (directly or inherited). Signatures must match exactly, and the
  implementing method cannot be private.
- An interface name is a type. A `Circle` can be stored in a `Named`
  variable, passed as a `Named` parameter, and so on. Through that type you
  can call only the interface's methods.
- The same method name in two interfaces must have the same signature.
- There is no downcasting yet: you cannot turn a `Named` back into a `Circle`.

## `super`

```python
class Square < Rect:
    def init(self, s: float):
        super.init(s, s)               # run the parent constructor

    def name(self) -> str:
        return "Square(" + super.name() + ")"   # call the parent's version
```

`super.method(args)` calls the parent class's implementation directly,
bypassing overrides. It works only in instance methods of a class that has a
parent. `super.init()` with no arguments is allowed (and does nothing) when the
parent has no constructor. You cannot call an abstract method through `super`.

## Generics

A class can take type parameters in square brackets. Use the class by naming
the types you want:

```python
class Box[T]:
    value: T
    def init(self, v: T):
        self.value = v
    def get(self) -> T:
        return self.value

class Pair[A, B]:
    first: A
    second: B
    ...

b = new Box[int](5)
p: Pair[str, Box[int]] = new Pair[str, Box[int]]("k", b)
```

- Type arguments can be any type, including other generic types
  (`Map[str, List[int]]`).
- Each distinct instantiation (`Box[int]`, `Box[str]`) is its own class,
  generated at compile time. Values of different instantiations are not
  interchangeable (`Box[Dog]` is not a `Box[Animal]`).
- A generic class is type-checked per instantiation, as if you had written
  the class out by hand with `T` replaced. So a method that uses `<` on a `T`
  only compiles for instantiations where that works. All methods of an
  instantiated class are checked, whether or not they are called.
- Generic interfaces and abstract classes work the same way. Type arguments
  cannot be `weak`.
- Not supported yet: generic methods on non-generic classes, static calls on
  a generic class (`Box[int].make()`), and type inference for `new Box(5)`.

## Arrays

`Array[T]` is the built-in fixed-size array that the collections are built on.

```python
a = new Array[int](10)     # 10 zeroed elements
a[0] = 5
print(a[0], a.length)
```

- Elements start as `0`, `0.0`, `false` or `null`.
- Indexing is bounds checked. A bad index stops the program with
  `error: index 3 out of range (length 2)` and exit status 1.
- `a.length` is read-only. An array cannot be resized; use a `List`.
- Arrays are reference counted like objects. Releasing one releases its
  elements.

## Lists

`List[T]` is a growable array.

```python
xs = new List[int]()
xs.add(10)
xs.add(20)
xs.insert(0, 5)            # [5, 10, 20]
xs[1] = 11                 # same as xs.set(1, 11)
print(xs[2], xs.size())    # 20 3
for x in xs:
    print(x)
```

| Method | Meaning |
|--------|---------|
| `add(x)` | append |
| `get(i)` / `xs[i]` | read element `i` |
| `set(i, x)` / `xs[i] = x` | replace element `i` |
| `insert(i, x)` | insert before position `i` (`i == size()` appends) |
| `removeAt(i)` | remove and return element `i` |
| `pop()` | remove and return the last element |
| `size()` / `len(xs)` | number of elements |
| `isEmpty()` | `size() == 0` |
| `contains(x)` / `indexOf(x)` | search with `==` (`indexOf` gives `-1` if absent) |
| `clear()` | remove everything |

An out-of-range index stops the program with `error: list index out of range`.
`==` compares `str` by contents and objects by identity.

## Maps

`Map[K, V]` is a hash map.

```python
ages = new Map[str, int]()
ages["ann"] = 31                  # same as ages.put("ann", 31)
print(ages["ann"])                # 31
print(ages.getOr("bob", -1))      # -1
if ages.has("ann"):
    ages.remove("ann")
for name in ages.keys():
    print(name, ages[name])
```

| Method | Meaning |
|--------|---------|
| `put(k, v)` / `m[k] = v` | insert or replace |
| `get(k)` / `m[k]` | the value; **stops the program** with `error: key not found in map` if absent |
| `getOr(k, fallback)` | the value, or `fallback` if absent |
| `has(k)` | is the key present |
| `remove(k)` | remove it; returns whether it was there |
| `keys()` / `values()` | a new `List` of the keys or values |
| `size()` / `len(m)` | number of entries |
| `isEmpty()`, `clear()` | as expected |

- Keys can be `int`, `str`, `float`, `bool`, or any class. `str` keys hash by
  contents; objects hash and compare **by identity**.
- **Iteration order is unspecified.** Sort or look up by key if you need order.
- `keys()` and `values()` return copies, so changing the map while looping
  over them is safe; the loop just won't see the changes.
- You cannot loop over a `Map` directly; loop over `m.keys()` or `m.values()`.

## Indexing and `for` loops

- `x[i]` on an `Array` reads an element. On any other class it calls
  `x.get(i)`.
- `x[i] = v` on an `Array` writes an element. On any other class it calls
  `x.set(i, v)`. So your own classes can support indexing by defining `get`
  and `set`.
- `for item in xs:` works on an `Array`, or any class with `size()` and
  `get(i)` (so `List` works, and so do your own). The collection is evaluated
  once, and its length is fixed when the loop starts. `break`, `continue` and
  `return` work normally. `range` loops are unchanged.

## Built-in functions

| Call           | Result                                              |
|----------------|-----------------------------------------------------|
| `print(a, b)`  | Prints arguments separated by spaces, then a newline. Works on `int`, `float`, `bool`, `str`; objects print through their `toString()` if they define a public one, otherwise as `<Class object at 0x...>`. A `null` object or `str` prints as `null`. |
| `str(x)`       | converts an `int`, `float`, `bool` or object (via `toString()`) to `str`; `null` becomes `"null"` |
| `int(x)`       | `float` truncated, `bool` to 0/1, or `int` unchanged |
| `float(x)`     | `int` or `float` to `float`                          |
| `len(x)`       | length of a `str` in bytes; number of elements of an `Array`, or of a class with `size()` |
| `hash(x)`      | integer hash of an `int`, `float`, `bool` or `str` (by contents), or object identity |
| `heap_live()`  | number of live heap allocations (debugging aid)      |

## Memory management

Quill uses automatic **reference counting**. You never free anything. An
object or string is released the moment the last variable or field that
refers to it goes away, and its own fields are released in turn.

```python
a = new Node(1)
b = a            # same object, count is now 2
a = null
b = null         # count hits 0: the object is freed here
```

Because release is immediate, memory use stays flat in loops that create
many temporary objects or strings.

**Strong reference cycles leak.** If `a.other = b` and `b.other = a`, neither
count reaches zero. Make one direction `weak` (next section), or break the
cycle by hand by setting a link to `null`.

`heap_live()` returns the number of live heap allocations (objects and
heap strings). It is meant for tests and debugging; string literals are not
counted.

## Weak references

A `weak` variable or field refers to an object without keeping it alive. Use
it for back-pointers, the usual source of cycles.

```python
class Parent:
    child: Child

class Child:
    parent: weak Parent       # does not keep the parent alive
```

- Write to it like any other variable: `c.parent = p`.
- **Reading it gives the object or `null`.** The read produces a normal strong
  reference if the target is still alive and `null` once it has died, so check
  before use: `if c.parent != null:`.
- `weak` applies only to class types, and only to fields and local variables.
  Parameters and return types cannot be weak.
- Weak references to an object keep its memory block allocated but not its
  contents: when the last strong reference goes, the fields are released and
  the object is "dead" while weak readers see `null`.

## Threads

`Thread` and `Mutex` are built-in classes.

```python
class Worker < Thread:
    lock: Mutex
    total: Counter

    def run(self):                  # override run(); it executes on the new thread
        self.lock.lock()
        self.total.n += 1
        self.lock.unlock()

w = new Worker(...)
w.start()                           # begins running run() concurrently
w.join()                            # waits for it to finish
```

| Member                   | Meaning |
|--------------------------|---------|
| `Thread.run()`           | Override this. Default does nothing. |
| `Thread.start()`         | Starts a new OS thread running `run()`. |
| `Thread.join()`          | Blocks until that thread's `run()` returns. |
| `Thread.sleep(ms)`       | Static; pauses the calling thread. |
| `Mutex()`                | A mutual-exclusion lock. |
| `Mutex.lock()` / `unlock()` | Acquire and release; not re-entrant. |

What is safe and what is not:

- **Reference counts are atomic.** Passing objects between threads, and
  retaining and releasing them from several threads, is memory safe. A
  started thread owns a reference to its `Thread` object, so it stays alive
  even if the starter drops it.
- **Field reads and writes are not protected.** Two threads writing the same
  field, or one writing while another reads it, is a data race. Guard shared
  mutable state with a `Mutex`, or do not mutate it after sharing it.
- Overwriting a field that another thread is reading can free the old value
  under that reader, so shared fields need the lock for reads too.
- The program exits when `Main.main` returns, even if threads are still
  running. `join` the threads you care about.
- There are no condition variables, atomics or channels yet.

## Destructors

A class may define `def deinit(self)`. It runs just before the object's fields
are released, when the last strong reference goes away. Only the nearest
`deinit` in the inheritance chain runs (a subclass does not call its parent's
automatically). `Mutex` uses this to free its lock.

## Type tests and casts, `toString`

`x instanceof T` is `true` when `x` is not `null` and its runtime class is `T`,
a subclass of `T`, or implements the interface `T`.

`x as T` narrows or widens the static type. It stops the program with
`error: invalid cast to T` if `x` is not a `T`; `null` casts to `null`. The
compiler rejects casts between unrelated classes (interfaces are always allowed,
since a subclass might implement them).

```python
if a instanceof Dog:
    d: Dog = a as Dog
    print(d.bark())
```

A class that defines `def toString(self) -> str` is printed through it by
`print`, and `str(obj)` calls it.

## Null checks

Reading or writing a field, calling a method, indexing, or taking `len` of a
`null` value stops the program with `error: null pointer dereference` and exit
status 1 instead of crashing. Concatenating a `null` string is checked the same way.

## Exceptions

`throw` raises any object. `try` runs a block, and the first `catch` clause
whose class matches the thrown object (the class itself, a subclass, or an
implementer of an interface) handles it. A bare `catch:` takes anything.

```python
class NotFound < Error:
    def init(self, what: str):
        super.init(what + " not found")

class Main:
    static def find(i: int) -> int:
        if i < 0:
            throw new NotFound("item")
        return i

    static def main():
        try:
            print(Main.find(-1))
        catch NotFound as e:
            print("caught:", e.message)
        catch Error as e:        # also receives runtime errors, see below
            print("other:", e.message)
```

- `Error` is a built-in class with a `message: str` field. Subclass it for your
  own exceptions; any other class can be thrown too.
- Runtime errors (list or array index out of range, missing map key, `null`
  dereference, bad cast, ...) are thrown as an `Error` whose message is the
  panic text, so `catch Error as e` handles them.
- A clause with no match passes the exception on to the enclosing `try`; a
  `throw` inside a `catch` block does the same. An exception nobody catches
  prints `error: uncaught exception: <message>` and exits with status 1 (runtime
  errors print `error: <message>` as before).
- `return`, `break` and `continue` may leave a `try` block.
- Locals owned by the frames an exception unwinds are not released (see the
  roadmap).

### `finally`

A `finally` block runs however the `try` ends: normal completion, after a
`catch` clause, when an exception propagates (unmatched, or thrown from a
`catch` block), and when `return`, `break` or `continue` leaves the block. A
`try` needs at least one `catch` or a `finally`.

```python
f: File = new File("data.txt")
try:
    f.process()
finally:
    f.close()          # runs even if process() throws or returns
```

When several `try` blocks are left at once, their `finally` blocks run
innermost first. A `return` or `throw` inside `finally` replaces whatever was
in flight.

## Errors

The compiler reports the first error as `file:line: error: message` and exits
with status 1. Checks include undefined names, wrong argument counts,
incompatible assignments, bad overrides, unknown types, missing `Main.main`,
`break` outside a loop, and inheritance cycles.

## Complete example

```python
class Counter:
    count: int

    def add(self, n: int):
        self.count += n

    static def fib(n: int) -> int:
        if n < 2:
            return n
        return Counter.fib(n - 1) + Counter.fib(n - 2)

class Main:
    static def main():
        c = new Counter()
        for i in range(1, 6):
            c.add(i)
        print("sum:", c.count, "fib(20):", Counter.fib(20))
```
