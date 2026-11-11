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
  false null and or xor not break continue pass weak
  public private protected abstract interface super instanceof as try catch finally throw bring`.

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
x += 1              # += -= *= /= %= &= |= ^= <<= >>= >>>=
```

Variables are block scoped. Redeclaring a name that is already visible in an
enclosing scope is an error (no shadowing).

## Operators

Lowest to highest precedence:

1. `or`
2. `xor`
3. `and` (`or` and `and` short-circuit)
4. `not`
5. `==  !=  <  <=  >  >=`
6. `|`
7. `^`
8. `&`
9. `<<  >>  >>>`
10. `+  -`
11. `*  /  %`
12. unary `-` and `~`
13. `.field`, `.method(...)`, calls

Notes:

- **Bitwise operators** work on `int`: `&` and, `|` or, `^` xor, `~` not,
  `<<` shift left, `>>` arithmetic shift right (keeps the sign), `>>>` logical
  shift right (fills with zeros). A shift by a count outside 0..63 is defined:
  the result is 0 (or the sign bits for `>>`). They bind tighter than
  comparisons, as in Python, so `x & 1 == 0` means `(x & 1) == 0`.
- **`xor`** is the logical exclusive or on `bool`. Unlike `and`/`or` it
  evaluates both sides. `&`, `|` and `^` also accept two `bool`s and likewise
  evaluate both sides. `1 xor 2` is an error; use `1 ^ 2`.
- Integer literals can be written `0xFF` or `0b1010`, with `_` as a separator
  (`0xDEAD_BEEF`). A hex or binary literal up to 64 bits is allowed and wraps as
  two's complement: `0xFFFFFFFFFFFFFFFF` is `-1`.
- `int` arithmetic wraps on overflow.

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

## Access control: `public`, `protected` and `private`

Fields and methods (including `init`) are `public` unless marked `private` or
`protected`. Put the modifier first:

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
- A `protected` member can be used in the declaring class and in its subclasses,
  and nowhere else. Protected methods are inherited and virtual, like public ones;
  an overriding method may stay protected or become public, but cannot turn a public
  method into a protected one. A protected `init` lets subclasses call `super.init`
  while `new` stays limited to the class and its subclasses.
- An interface method that a class implements must be public.

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

- An interface has only public, non-static methods: no fields, `init` or `deinit`.
  A method with a body is a **default method**: classes that do not define it
  inherit the default, and the body can call the interface's other methods through
  `self`. If a class gets two different defaults of one name from two interfaces it
  must define the method itself.
- After `<`, a class lists at most one superclass and any number of
  interfaces, in any order.
- A concrete class must implement every method of every interface it
  promises (directly or inherited). Signatures must match exactly, and the
  implementing method must be public.
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
- `for k in m:` loops over the keys and `for k, v in m:` over keys and values, both on a
  snapshot taken when the loop starts (so removing entries inside the loop is safe). The
  order is unspecified. To loop over the values alone use `m.values()`.

## List and map literals

```python
primes = [2, 3, 5, 7]                         # List[int]
ratios: List[float] = [1, 2.5]                # ints widen to float
pets: List[Animal] = [new Dog("Rex"), new Cat("Tom")]
ages = {"ann" -> 31, "bo" -> 27}              # Map[str,int]
index = {"evens" -> [2, 4], "odds" -> [1, 3]} # Map[str,List[int]]
none: Map[str, int] = {}
```

A map entry is written `key -> value`; the arrow is the same one used for
return types. Literals may span several lines and end with a trailing comma.

The element type is taken from the declared type when there is one (variable,
field assignment, parameter or return type), otherwise from the elements: all
the same type, `int` mixed with `float` (giving `float`), or a type every other
element can be assigned to. `null` elements are allowed for `str` and classes.
An empty `[]` or `{}` needs a declared type. A literal builds a new `List` or
`Map`, so a repeated map key keeps its last value.

## Sorting

```python
xs = [5, 3, 9, 1]
xs.sort()               # in place, ascending, stable
xs.sortDesc()           # in place, descending
ys = xs.sorted()        # a sorted copy; xs is untouched
xs.isSorted()   xs.reverse()   xs.min()   xs.max()   xs.copy()   xs.addAll(ys)
```

Lists of `int`, `float`, `str` and `bool` sort natively (strings by byte
order). A list of objects sorts when the class defines
`compareTo(self, other: X) -> int`, returning negative, zero or positive.
Subclasses use their parent's `compareTo`. Sorting a `List[X]` whose element type
cannot be ordered is a compile error. `min`/`max` of an empty list throw an
`Error`. `<`, `<=`, `>` and `>=` also work on strings.

## Sets

`Set[T]` holds each value once. Elements compare like `Map` keys: ints, floats,
strings and bools by value, objects by identity.

```python
a = {1, 2, 3}                     # Set[int]
none: Set[str] = {}               # an empty set needs a declared type
a.add(4)   a.remove(1)   a.has(2)   a.size()   a.isEmpty()   a.clear()
a.union(b)   a.intersect(b)   a.difference(b)   a.symDiff(b)   # new sets
a.addAll(b)  a.removeAll(b)   a.retainAll(b)                   # in place
a.isSubsetOf(b)   a.isSupersetOf(b)   a.isDisjoint(b)   a.equals(b)
a.items()   a.sortedItems()   a.copy()
```

`add` and `remove` return whether the set changed. Iteration order is
unspecified, so loop over `s.sortedItems()` when order matters. `for x in s:` also works (on a snapshot). `{a, b}` is a
set and `{k -> v}` is a map.

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

## Methods on basic types

`int`, `float`, `bool` and `str` values have methods, written `value.method(...)`. They
never change the value; they return a new one. Write a number literal in brackets before
the dot if the parser could mistake it for a decimal point: `(5).toHex()` also works as `5.toHex()`.
Calling a method on a `null` string stops with an error.

| Type | Methods |
|---|---|
| `str` | `length() isEmpty() upper() lower() capitalize() trim() indexOf(s) contains(s) startsWith(s) endsWith(s) count(s) substring(start, end) charAt(i) byteAt(i) replace(old, new) split(sep) lines() repeat(n) reverse() padLeft(width, ch) padRight(width, ch) toInt() toFloat() toString()` and `sep.join(list)` |
| `int` | `toString() toFloat() abs() sign() min(o) max(o) clamp(lo, hi) isEven() isOdd() pow(e) toHex() toBinary()` |
| `float` | `toString() toInt() floor() ceil() round() abs() sign() min(o) max(o) clamp(lo, hi) isNaN()` |
| `bool` | `toString()` |

Notes: `substring(start, end)` excludes `end`; `indexOf` gives -1 when not found;
`split("")` gives one piece per character; `float.floor/ceil/round` return an `int` (halves
round away from zero) and throw when the value does not fit; `toInt()` and `toFloat()` on
strings throw an `Error` for text that is not a number, and `toFloat()` is close to exact but
not always correctly rounded in the last digit. Strings are bytes, so `upper` and `lower` only
change the letters A to Z.

These are ordinary static methods of built-in classes named `__Str`, `__Int`, `__Float` and
`__Bool` (see `std/primitives.ql`); the compiler rewrites `s.upper()` to `__Str.upper(s)`.
You cannot add methods of your own to basic types.

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

## Splitting a program: `bring`

`bring util.text` at the top of a file loads `util/text.ql`, and `bring shapes`
loads a package you depend on. Classes from brought files are used by their plain
names. Details, and the package manager, are in [Modules and packages](packages.md).

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
- Unwinding is clean: every function an exception passes through releases its
  parameters, locals and in-flight temporaries as it goes, so nothing leaks.
  Resources that are not memory are not released automatically; a `Mutex` locked
  inside a `try` stays locked unless a `finally` unlocks it.

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

## Native code

A method can be bound to a C function, and `quill wrap` generates such bindings from a
header, so your code never handles a pointer:

```python
native link "m"                       # -lm
class Fast:
    native static def hypot(a: float, b: float) -> float = "hypot(double, double) -> double"
```

Native code is outside what the compiler can check and `bring`/`needs` cannot fetch
it. Read [native.md](native.md) for the caveats, the wrapper tool and `Buffer`, and use
`quill hood` ([hood.md](hood.md)) to see how each call is converted.

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
