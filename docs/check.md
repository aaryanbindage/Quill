# The built-in memory checker

```
quill run program.ql --check
quill build program.ql --check
```

`--check` builds the program with a checking allocator in place of the normal one. It works
on every platform. On Windows, where AddressSanitizer needs the MSVC toolchain, `--sanitize
address` means the same thing.

What it reports (to stderr, then the program exits with status 70, except for leaks):

| Message | Meaning |
|---|---|
| `heap object(s) still alive at exit` | a leak: usually a reference cycle (use `weak`) |
| `double free` | a block was freed twice |
| `use of freed memory` | a value was retained or released after it was freed |
| `heap buffer overflow` | something wrote past the end of an object or string |
| `invalid free` | the block header was overwritten |

How it works: every block gets a canary after it. On free the canary is checked, the block
is filled with `0xDD` and kept (never reused), so a later retain or release sees the poison.
Leaks are counted with the same counter as `heap_live()`.

## Limits

- It only sees Quill's own heap. Memory allocated by C or C++ code is not checked.
- An overflow is found when the block is freed, not at the moment of the write, and a stray
  read of a freed block is only caught when it goes through a retain or release.
- Freed blocks are never reused, so memory use grows for long-running programs; this is
  a debugging mode, not a release build.
- Nothing like ThreadSanitizer exists for the MinGW toolchain, so `--sanitize thread` is
  still unavailable on Windows. Guard shared state with a `Mutex`, and run the test suite
  on Linux or macOS if you need data-race checking.
