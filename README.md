# Quill

A small statically-typed, class-only language with Python-style syntax that
compiles to LLVM IR and then to a native binary.

```python
class Animal:
    name: str
    def init(self, name: str):
        self.name = name
    def speak(self) -> str:
        return "..."

class Dog < Animal:
    def speak(self) -> str:
        return "Woof"

class Main:
    static def main():
        a: Animal = new Dog("Rex")
        print(a.name, "says", a.speak())
```

## Usage

Requires Python 3 and `clang` (no other dependencies). On Windows it also needs
`gcc` from a MinGW-w64 toolchain (such as w64devkit or winlibs) on `PATH`, which
links the program. The real sanitizers need Linux or macOS; on Windows `--sanitize address` runs Quill's built-in memory checker instead (`--check`, see docs/check.md).

```
python3 quill.py run   file.ql            # compile and run
python3 quill.py build file.ql -o out     # native executable (-O0..-O3)
python3 quill.py emit  file.ql            # print LLVM IR
```

With no file name, `run`, `build` and `emit` use the current project's `start`
module (see below).

Add `--keep-ll` to `build` to keep the generated `.ll` file next to the output,
or `--sanitize address|thread` to build with a sanitizer, or `--check` for Quill's built-in memory checker (any platform, including Windows).

## Projects and packages

```
quill new hello          # a project: quill.pkg + src/main.ql
cd hello
quill add textkit --git https://example.com/textkit.git
quill run                # runs the start module; `bring textkit` works in the code
```

Programs can be split over files with `bring`, and projects depend on other
projects through a `quill.pkg` manifest and a `quill.lock` file. Dependencies are
git repositories (versions are tags) or local folders.

## Docs

- [Learn Quill](docs/course/README.md): a ten-lesson course for beginners, every program checked by the test suite
- [Language guide](docs/language-guide.md): syntax, types, classes, weak
  references, threads, generics, `List` and `Map`, built-ins
- [Compiler internals](docs/internals.md): pipeline, object layout, vtables,
  reference counting, threads
- [Modules and packages](docs/packages.md): `bring`, `quill.pkg`, version
  constraints, the lock file and every package command
- [Standard library](docs/stdlib.md): `std.math`, `std.random`, `std.stats`,
  hashing and encryption (`std.hash`, `std.cipher`, `std.crypto`)
- [Console and text art](docs/console-art.md): `std.console` (colours, cursor, input) and `std.art` (canvas, banners)
- [C and C++ libraries](docs/native.md): `quill wrap`, `native` methods, `Buffer`, and the caveats
- [Under the hood](docs/hood.md): `quill hood` shows layouts, reference counting, native calls and build commands
- [Memory checker](docs/check.md): `--check`, leak, double-free and overflow detection on every platform
- [Roadmap and limitations](docs/roadmap.md)

Examples live in `examples/`. Run the whole test suite, plain and under both
sanitizers, with `tests/run_all.sh` (it also runs the package manager's tests, which need `git`).
