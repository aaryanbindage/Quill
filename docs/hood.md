# Under the hood

`quill hood` explains what the compiler does with a program. It changes nothing; it just
shows the internals that normally stay out of sight.

```
quill hood [file.ql]                  the whole story, briefly
quill hood file.ql --only classes     chosen sections
quill hood file.ql --class Point      the memory layout of one class
quill hood file.ql --ir Main.main     the LLVM IR of one function, annotated
quill hood file.ql --all              every function and class, not only the largest
quill hood file.ql --no-build         do not run clang
```

Without a file it uses the project's start module, like `quill run`.

## Sections (`--only a,b`)

| Section | Shows |
|---|---|
| `overview` | the pipeline in numbers: modules read, classes, functions and instructions generated, reference count and exception-check sites, native bindings |
| `modules` | each file that was loaded, its package, the name it was brought under, and whether it contains native code |
| `classes` | each class: kind (yours, std library, generic instance, interface), parent, field count, heap size, vtable slots |
| `generics` | which generic classes were instantiated and how much code each produced |
| `functions` | the largest functions with their instruction count, calls, retains, releases, allocations, exception checks and cleanup paths |
| `native` | every native binding: the C signature and the conversion of each argument and result, plus what is linked |
| `build` | the exact clang/gcc commands, how long each took, and the size of the result |

## One class: `--class NAME`

```
== Layout of Point ====================================
  offset  field     Quill type  LLVM type  bytes
  0       (vtable)  ptr         ptr        8
  8       x         int         i64        8
  16      y         float       double     8

  payload 24 bytes, heap block 40 bytes
```

Every object lives in a heap block with a 16 byte header (strong and weak reference
count) before the pointer you hold, then a pointer to its vtable, then its fields.

## One function: `--ir Class.method`

Prints the function's LLVM IR with notes where Quill's runtime machinery appears:

- `+1 reference` / `-1 reference`: reference counting. A value is freed when its count
  reaches zero.
- `heap allocation`: a `new`, a string concatenation, a list growing.
- `has an exception been thrown?`: the check after every call that makes `try`/`catch`
  work without unwinding tables.
- `cleanup that runs when an exception passes through`: the code that releases locals
  when a `throw` leaves a function.
- `an address kept as an int becomes a pointer again`: a native call, where an address
  that Quill code only ever held as an `int` is handed to C.

## Why it exists

Quill hides a lot on purpose: reference counting, exceptions, generics, native
pointers. `quill hood` is the way to check what that costs and what really runs, for
example whether a generic method was compiled five times, how many retains a loop does,
or exactly which `-l` flags a wrapper added.
