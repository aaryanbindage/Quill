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

Requires Python 3 and `clang` (no other dependencies).

```
python3 quill.py run   file.ql            # compile and run
python3 quill.py build file.ql -o out     # native executable (-O0..-O3)
python3 quill.py emit  file.ql            # print LLVM IR
```

Add `--keep-ll` to `build` to keep the generated `.ll` file next to the output,
or `--sanitize address|thread` to build with a sanitizer.

## Docs

- [Language guide](docs/language-guide.md): syntax, types, classes, weak
  references, threads, generics, `List` and `Map`, built-ins
- [Compiler internals](docs/internals.md): pipeline, object layout, vtables,
  reference counting, threads
- [Roadmap and limitations](docs/roadmap.md)

Examples live in `examples/`. Run the whole test suite, plain and under both
sanitizers, with `tests/run_all.sh`.
