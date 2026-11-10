# Using C and C++ libraries

Quill can call C and C++ libraries. This is optional: nothing changes for programs
that do not use it, and you never have to write a Makefile or a linker command.

```
quill wrap zlib.h --name Zlib --link z --strip ZEXTERN --strip ZEXPORT --yes
```

writes `zlib.ql`. Then, in your program:

```python
bring zlib

class Main:
    static def main():
        print(Zlib.crc32(0, [104, 101, 108, 108, 111]))
```

`quill run` compiles, links `-lz` and runs it. No pointer ever appears in your code.

## Read this first: the caveats

Quill's authors acknowledge that native code gives up guarantees Quill otherwise
provides. `quill wrap` prints these and will not continue until you pass `--yes` (or
type `yes`):

1. **The compiler cannot check C or C++.** A wrong declaration, a wrong size or a bad
   pointer crashes the program or corrupts memory, with no Quill error to explain it.
2. **Memory the library allocates is not reference counted.** A handle is freed only if
   you say how (`--owns`); otherwise it leaks, or dangles if you free it yourself too soon.
3. **C has no exceptions**, so error codes stay your job. C++ exceptions are caught in the
   generated shim and rethrown as Quill `Error`s.
4. **Callbacks, structs by value, output parameters and variadic functions** are not
   wrapped automatically. They stay in the raw class or are listed as skipped.
5. **`--sanitize` and `heap_live()` cannot see inside the native library.**
6. **Native code is platform specific.** The library must be installed on every machine
   that builds the program, and a wrapper made on one machine may need regenerating on
   another (C types such as `long` have different sizes on Windows and Unix).
7. **`bring` and `needs` do not support native code.** They only fetch Quill source. Use
   this with libraries you downloaded and installed yourself, and keep the wrapper in your
   own project. A package fetched with `needs` that contains native code is refused:
   `this module of package X contains native (C/C++) code`.

Building a program that links native code prints a one-line note about this. Set
`QUILL_QUIET_NATIVE=1` to silence it.

## What `quill wrap` produces

For `vec.h` with `--name Vec` you get `vec.ql` containing:

| Class | What it is |
|---|---|
| `VecRaw` | every function exactly as C sees it, as `native` methods. Pointers are plain `int` addresses. Use it for anything the friendly layer cannot express. |
| `Vec` | the friendly layer: static methods and constants. |
| `VecHandle` | one class per struct that is used through a pointer (the name gets `Handle` when it would clash). It holds the address privately and frees it. |

How C types become Quill types in the friendly layer:

| C | Quill |
|---|---|
| `int`, `long`, `size_t`, `uint8_t`, enums, ... | `int` |
| `float`, `double` | `float` |
| `bool` | `bool` |
| `const char *` | `str` (copied; C never keeps your string) |
| returned `const char *` | a new `str` copy |
| returned `char *` | a copy, then freed if you pass `--free-strings FN` |
| `const uint8_t *data, size_t len` (also `void *`) | one `List[int]` parameter |
| `struct T *` | a generated class `T` (null maps to `null`) |
| `#define` numbers and strings, enum values | static methods, e.g. `Vec.VEC_MAX()` |
| anything else | raw only (listed in the report with the reason) |

C++ headers are read too: classes with public constructors and methods, static
methods, namespaces, free functions, `std::string`, `std::string_view` and references
to wrapped classes. `quill wrap` writes `NAME_shim.cpp` next to the wrapper, an
`extern "C"` layer that catches C++ exceptions; the shim is compiled and linked
automatically. A C++ class becomes a Quill class: `Counter.create(...)` builds one
(the extra constructors are `create2`, `create3`, ...), methods are instance methods,
and the object is deleted when the last reference goes away or when you call `close()`.
Templates, `std::vector` and other standard containers, operators and callbacks are
reported as skipped.

### Options

```
quill wrap HEADER... [options]
  --name NAME          name of the wrapper class (default: from the header)
  --out FILE           output file (default: NAME.ql)
  --link LIB           link a library, like -l (repeatable)
  --libdir DIR         where libraries live, like -L
  --include DIR        include directory, like -I
  --source FILE        a .c/.cpp file to compile into the program (for a library
                       that ships as source)
  --flag FLAG          an extra compiler flag
  --prefix P           strip this prefix from function names (zlib_ -> crc32)
  --strip MACRO        export macro to ignore in prototypes (ZEXPORT, ...)
  --owns Struct=FN     free objects of this struct with FN when no longer used
  --free-strings FN    free returned char* with FN after copying it
  --only REGEX / --skip REGEX   choose which functions to wrap
  --lang c|c++  --std c++17     language, if the extension is not enough
  --yes                acknowledge the caveats
```

The report lists every function that was wrapped, left raw-only or skipped, and says
which handle classes are released automatically. If the library has a function that
frees an object (`foo_free`), pass `--owns foo=foo_free`; without it the wrapper cannot
know when it is safe to free, so the memory is never released.

A returned pointer is treated as owned when the function name looks like a constructor
(`new`, `create`, `open`, `alloc`, `init`, `make`, `load`, `parse`, `clone`, `copy`, ...)
and the class has a release function; any other returned pointer is borrowed and never
freed. Check the report; you can always call the raw function yourself.

### Output parameters and other leftovers: `Buffer`

For functions the friendly layer cannot express, use the raw class with `Buffer` from
`std.native`: native memory that frees itself.

```python
bring std.native

out = new Buffer(8)                                  # zero filled, freed automatically
VecRaw.vec_dims(v.handle, out.address(), out.address() + 4)
w = out.get(0)                                       # read the bytes back
```

`Buffer.of(list)` copies a `List[int]` in, `buf.toList()` and `buf.toText()` read it
back, and every access is bounds checked.

## Writing a binding by hand

`quill wrap` is optional. Any class can declare a native method:

```python
native link "m"                      # -lm; also: libdir, include, source, flag

class Fast:
    native static def hypot(a: float, b: float) -> float = "hypot(double, double) -> double"
```

The string is `symbol(ctype, ...) -> ctype`. The C types are `char schar uchar short ushort
int uint long ulong llong ullong size_t ssize_t i8 i16 i32 i64 u8 u16 u32 u64 float double
bool`, plus `cstr` (a `const char *`, `str` in Quill) and `ptr` (any other pointer, `int` in
Quill). Sizes follow the platform. The compiler checks that the Quill and C types agree,
converts arguments and results, and declares the C function. Directives go at the top of
a module and are resolved relative to it:

| Directive | Meaning |
|---|---|
| `native link "z"` | link `-lz` (or `"-framework Foo"` for raw arguments) |
| `native libdir "dir"` | add `-Ldir` |
| `native include "dir"` | add `-Idir` when compiling sources |
| `native source "file.c"` | compile and link this file with the program (`.cpp` selects the C++ driver) |
| `native flag "-DX=1"` | extra compiler flag |

## See what happens: Under the hood

```
quill hood program.ql --only native
```

prints, for each native method, the C signature, how each argument is converted, and how
the result comes back, together with the libraries linked and the exact commands that
built the executable. See [hood.md](hood.md).
