# Roadmap and Known Limitations

## Known limitations (v0)

- **Strong reference cycles leak.** Use `weak` for back-pointers, or break
  the cycle by hand.
- **Deep structures free recursively.** Dropping a very long linked list
  recurses once per node and can overflow the C stack.
- **Borrowed values can dangle in rare cases.** In `x + f()` or `g(x, f())`, if
  `f` overwrites the variable or field `x` was read from, the earlier operand
  may already be freed. Callees retain their own parameters, so only the
  caller-side evaluation window is affected.
- **Threads share fields without protection.** Counts are atomic, but field
  reads and writes are not; guard shared mutable state with a `Mutex`.
  Overwriting a shared field while another thread reads it can free the old
  value under the reader.
- **Minimal concurrency toolkit.** Only `Thread` and `Mutex`: no condition
  variables, atomics, channels, thread-local state or thread results. The
  program exits when `main` returns even if threads are running.
- **`weak` is limited** to class-typed fields and locals.
- **No null checks.** Calling a method or reading a field on `null` crashes.
- **No implicit `super()`.** A subclass `init` must call `super.init(...)` itself; the parent constructor does not run automatically.
- **Missing return paths** in non-void methods silently return zero.
- **Single file programs only.** There are no imports or modules.
- **Objects print as addresses.** There is no `toString`.
- **Only `public` and `private`.** There is no `protected`, and no package or module level.
- **No downcasting.** There is no `instanceof` or cast, so an interface or superclass value cannot be turned back into its concrete class.
- **Interface calls scan a table.** Dispatch through an interface is a linear search per call.
- **Primitives are not objects.** `int`, `str` and the others have no methods.
- **Collections are basic.** `List` and `Map` have no literals (`[1, 2]`), sorting, slicing or `Set`. `Map` iteration order is unspecified, objects used as keys compare by identity, and you cannot loop over a `Map` directly.
- **Generics are template-style.** Every method of an instantiated generic is compiled for that type, there are no constraints on type parameters, no generic methods on ordinary classes, and no static calls on generic classes. Code size grows with the number of instantiations.
- **Errors are not catchable.** Index and missing-key errors stop the program with exit status 1.

## Planned, in priority order

1. `protected`, `instanceof` and casts, and default methods in interfaces.
2. Primitives as objects with methods (`"hi".upper()`, `x.toString()`), and a
   `toString` hook used by `print`.
3. List and map literals, `Set[T]`, sorting, direct `Map` iteration, and generic methods.
4. Exceptions (`try`/`catch`/`throw`).
5. An explicit-stack drop to avoid deep recursion, and weak parameters and
   returns.
6. Concurrency primitives: condition variables, atomic integers, channels,
   and thread results.
7. A standard library and multi-file imports.
8. Rewrite the compiler in Rust (or Quill itself) and link LLVM directly for
   better diagnostics and faster builds.
