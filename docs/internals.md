# Compiler Internals

Everything is in `quill.py`, in the order the pipeline runs.

## Pipeline

```
source.ql -> lex -> parse -> Module (class table) -> FuncGen per method -> .ll text -> clang -> binary
```

1. **Lexer (`lex`)** turns text into tokens and synthesises `INDENT`,
   `DEDENT` and `NEWLINE` tokens from indentation. Newlines inside
   parentheses are suppressed.
2. **Parser (`Parser`)** is recursive descent and produces the dataclass AST
   (`ClassDecl`, `MethodDecl`, statement and expression nodes).
3. **`Module`** builds the class table: resolves parents (detecting unknown
   parents and cycles), computes each class's full field list and vtable,
   and checks override signatures.
4. **`FuncGen`** generates one LLVM function per method. Expression
   generators return `(operand, quill_type)`, and type checking happens
   during generation.
5. **`build`** writes the textual IR to a `.ll` file and calls
   `clang -O1`. The compiler does not link against LLVM libraries, which keeps
   it dependency-free.

## Object layout

Every heap value (object or string) is preceded by a 16-byte **header**,
`[strong count i64][weak count i64]`: `quill_alloc` allocates `size + 16`
zeroed bytes, writes strong = 1 and weak = 1, and returns the pointer just
past the header. Each class becomes a named
struct whose first slot is the vtable pointer:

```
%Animal = type { ptr, ptr /*name*/, i64 /*legs*/ }
%Dog    = type { ptr, ptr, i64 }          ; parent fields first, then own
```

Because a subclass's fields start with its parent's, a `Dog*` can be used
wherever an `Animal*` is expected and field offsets stay valid.

`new C(...)` computes `sizeof` with the `getelementptr null, 1` idiom,
allocates with `quill_alloc` (so fields start zeroed), stores the vtable
pointer, and calls the nearest `init` directly.

## Virtual dispatch

Each class has a constant array of function pointers:

```
@"vtable.Dog" = constant [4 x ptr] [ptr @"drop.Dog", ptr @"itable.Dog",
                                    ptr @"Dog.speak", ptr @"Animal.describe"]
```

Slot 0 is the class's **drop function** (see Reference counting) and slot 1 is
its **interface table** (below), so method slot numbers are offset by two.
Private methods, static methods, `init` and `deinit` have no slot and are
called directly. Only concrete classes get a vtable; abstract classes and
interfaces cannot be instantiated.

- A subclass starts with a copy of its parent's slot list.
- An override reuses the parent's slot index; a new method appends a slot.
- The slot's function is the nearest definition walking up from the class.

An instance call loads the vtable from slot 0 of the object, indexes the
method slot (the index comes from the receiver's static type), loads the
function pointer, and makes an indirect call. `init` and static methods
bypass the vtable and call the symbol directly.

## Interfaces, abstract classes and access control

**Interface dispatch.** A class's method slots are chosen by its own
inheritance chain, so two unrelated classes implementing the same interface
place the method at different slots. Calls through an interface type therefore
cannot use a fixed slot. Instead:

- Every interface method *name* gets a program-wide integer id.
- Each concrete class has an `itable`: an array of `{ id, function }` entries
  for every interface method it must implement, ending with `{ -1, null }`.
- A call whose resolved method was declared in an interface calls
  `@quill_find_method(obj, id)`, which scans the object's itable (reached via
  vtable slot 1) and returns the function pointer.

This is a linear scan, which is fine for small interfaces. Caching the result
at the call site, or hashing, are possible later optimisations.

When the receiver's static type is a class, normal vtable dispatch is used
even for methods that also implement an interface, because the class method is
found first. `find_method` searches the superclass chain and only then the
interfaces (`ClassInfo.required`); `find_class_method` searches only the chain.

**Abstract methods** are ordinary vtable entries, but no function is
generated for them. `Module.collect` checks that every concrete class
overrides all of them and implements all of `required`, with matching
signatures, so a vtable slot never points at nothing. Abstract classes and
interfaces get no vtable or drop function, and `new` rejects them.

**Class table.** `ClassInfo.supers` holds the class's own name plus every
ancestor class and interface, so assignability (`is_subclass`) is a set
lookup. A class with a parent and interfaces records the parent in `parent`
and the interfaces in `interfaces`.

**Access control** is checked at compile time only. Fields record
`(owner, access)` in `ClassInfo.field_info`, methods carry `access`, and the
check compares against the class currently being generated (`FuncGen.ci`).
Private methods get no vtable slot.

**`super`** (`SuperCall`) resolves the method on `self.ci.parent` with
`find_class_method` and emits a direct call with the current `self`, so no
vtable lookup happens.

## Generics and collections

**Monomorphization.** `class List[T]` is a template, stored in
`Module.templates` rather than `classes`. Types are written canonically
(`Map[str,List[int]]`, no spaces). After the plain classes are registered,
`collect` walks every AST for type mentions (`iter_types`) and calls `ensure`
for each. `ensure` instantiates a missing generic by deep-copying the
template and rewriting every type string in it with `subst_node` (type
parameter to argument), registering it as an ordinary class named
`List[int]` and queueing it so its own bodies are scanned too. Because
instantiation is a fixpoint over the AST, nested uses such as
`Map[str,List[int]]` pull in `List[int]`, `MapEntry[str,List[int]]` and
`Array[MapEntry[...]]` automatically. After that the instance is just another
class, so the rest of the compiler needs no generic-aware code.

This is C++-template-style: bodies are type-checked after substitution, which
is why every method of an instantiated class must compile for that type, and
why error messages mention the instantiated name (`List[int]`).

**`Array[T]`** is the one compiler-built primitive. Its `ClassInfo` has
`elem` set and an empty synthetic declaration. Layout is `{ vtable ptr,
length i64 }` followed by the elements (8 bytes each, 1 for `bool`), allocated
with `quill_alloc` so it has the usual refcount header and a vtable whose
drop function (`array_drop_fn`) releases each element if the element type is
a reference. Indexing is generated inline: an unsigned compare against the
length (which also rejects negative indexes) and a call to
`@quill_panic_index` on failure. Element writes follow the normal ownership
rules: consume the new value, store, release the old one. Reading an element
out of a temporary array retains it before the array is released.

**`List` and `Map`** are written in Quill in the `PRELUDE` (an `Array[T]`
plus a count; `Map` is a chained hash table of `MapEntry[K,V]`). A `blank`
one-element array supplies the zero value of `T` for clearing vacated list
slots. `hash(x)` is a compiler builtin that picks the right hash for the
static type (FNV-1a for strings, identity for objects).

**Indexing and for-each.** `x[i]` is `Index`: for arrays it is the inline
path above, otherwise it becomes a call to `get` (or `set` on assignment)
through `call_method`. `for x in xs:` is desugared by the parser into
`Block([$it = xs, for $i in range(LenOf($it)): x = $it[$i]; body])`. The
`Block` gives the hidden variable its own scope, so the reference to the
iterable is released as soon as the loop ends. `LenOf` picks `length` for
arrays and `size()` for classes.

**Panics.** `__panic(msg)` and the bounds checks print to stderr with
`dprintf` and call `exit(1)` (which flushes stdout). They are not catchable.

## Reference counting

Runtime functions: `quill_retain`, `quill_release_str`, `quill_release_obj`,
`quill_weak_retain`, `quill_weak_release`, `quill_weak_upgrade`,
`quill_free`. A negative strong count marks an immortal value; retain and
release skip it. String literals are emitted as constants with strong count
`-1`, so they are never written to or freed.

Releasing an object to zero calls its drop function through vtable slot 0.
Drop runs the class's `deinit` (if any), then releases each reference field
(`weak_release` for weak fields). It does not free the block: after drop the
runtime releases the **implicit weak reference** that all strong references
collectively hold, and the memory is freed only when the weak count also
reaches zero. Strings have no vtable, so `release_str` just frees.

**Atomicity.** All count updates use `atomicrmw` (increments `monotonic`,
decrements `acq_rel`). `weak_upgrade` is a `cmpxchg` loop that only raises the
strong count if it is currently positive, so it cannot race with the final
release. While drop runs, the strong count is set to a large sentinel
(2^40) so the retain/release pairs inside `deinit` (every callee retains
`self`) cannot re-trigger the drop; `weak_upgrade` treats the sentinel as
dead. After drop the count is 0.

**Weak slots** hold the same pointer as a strong slot but own a weak count
instead. The compiler turns every read of a weak variable or field into a
`weak_upgrade` call, so a weak read is a fresh strong reference (or `null`)
and the existing fresh/borrowed rules apply unchanged. Writing to a weak slot
does `weak_retain(new)`, store, `weak_release(old)`, then releases the
temporary strong reference.

The compiler (`FuncGen`) tracks ownership with these rules:

- **Locals and parameters own one reference.** A callee retains each
  parameter (including `self`) on entry and releases it on exit, so a method
  stays safe even if it overwrites the field it was called through.
- **Expression results are borrowed or fresh.** Loads from variables and
  fields are borrowed. `new`, string concatenation and call results are
  *fresh* (+1). The `fresh` set records which temps are owned.
- **Consuming a value** (assigning it, initialising a variable, returning it)
  retains it if it was borrowed, and just takes over a fresh one.
- **Unused fresh values are released**: expression statements, call
  arguments after the call, operands of `+`, comparisons, `print` arguments,
  and the receiver of a method call.
- **Assignment** retains the new value, stores it, then releases the old one,
  so `x = x` is safe. The value is evaluated before the target.
- **Scope exit, `return`, `break`, `continue`** release the variables of every
  scope being left (`release_from(depth)`); `return` retains its value first.
- A field read from a fresh temporary is retained before the temporary is
  released.

`heap_live()` reads a global counter that `quill_alloc` increments and
`quill_free` decrements; `tests/refcount.ql` uses it to assert that every
scenario ends with zero live allocations.

## Threads

`Thread` and `Mutex` are written in Quill in the `PRELUDE` string and compiled
with every program, on top of a few intrinsics (`__thread_start`,
`__thread_join`, `__mutex_*`, `__sleep_ms`, listed in `INTRINSICS`) that map
to small runtime functions over pthreads. Thread and mutex handles are
pointers stored in an `int` field.

`Thread.start()` passes `self` to `quill_thread_start`, which transfers one
strong reference to the new thread. The generated `@quill_thread_entry`
trampoline calls `run` through the vtable (slot index computed from
`Thread`'s vtable), then releases that reference. `Mutex` wraps a
`pthread_mutex_t` and frees it from `deinit`.

## Sanitizers

`quill.py run|build --sanitize address|thread` builds with
AddressSanitizer or ThreadSanitizer. Sanitizers only instrument functions
that carry a `sanitize_*` attribute, which clang adds for C input but not for
raw `.ll`, so `mark_sanitize` adds it to every generated `define`. Without it
the sanitizers run but instrument nothing. `tests/run_all.sh` runs every test
plain and under both sanitizers.

## Locals and control flow

Every local variable is an `alloca` hoisted into the function's entry block,
and reads and writes use `load`/`store`. This avoids building SSA by hand,
and clang's `mem2reg` pass cleans it up. `and`/`or` use a small `i1` slot
plus conditional branches for short-circuiting. Code after a `return`,
`break` or `continue` is placed in a fresh unreachable block so the IR stays
well formed.

## Naming

- Methods: `@"Class.method"`
- Vtables: `@"vtable.Class"`
- String literals: `@.str.N`, deduplicated
- Entry: a generated `@main` calls `Main.main` and returns its `int` result
  (or 0).

## Runtime

A small IR prelude declares libc and pthread functions, defines the reference
counting, thread and mutex functions above, and defines `@quill_concat` for
string concatenation. There is no separate
runtime library yet.

## Adding a language feature

1. Add keywords or tokens in the lexer if needed.
2. Add an AST dataclass and parse it in `Parser`.
3. Add a `s_<NodeName>` (statement) or `e_<NodeName>` (expression) method to
   `FuncGen`. Dispatch is by class name.
4. Raise `CompileError(msg, line)` for user errors.

Use `python3 quill.py emit file.ql` to inspect the IR while debugging.
