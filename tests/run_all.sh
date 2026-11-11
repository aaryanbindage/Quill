#!/bin/sh
# Runs every test normally and under both sanitizers. Fails on any LEAK line,
# sanitizer report, or non-zero exit.
cd "$(dirname "$0")/.." || exit 1
fail=0
# Windows (Git Bash) has `python`, not `python3`, and no sanitizers
if command -v python3 >/dev/null 2>&1 && python3 -c "" 2>/dev/null; then PY=python3; else PY=python; fi
case "$(uname -s)" in MINGW*|MSYS*|CYGWIN*) sans="" ;; *) sans=" address thread" ;; esac
for san in "" $sans; do
  for t in tests/*.ql; do
    if [ -n "$san" ]; then flag="--sanitize $san"; else flag=""; fi
    out=$(ASAN_OPTIONS=detect_leaks=0 $PY quill.py run $flag "$t" 2>&1 </dev/null); code=$?
    if [ $code -ne 0 ] || echo "$out" | grep -qE '^LEAK|ERROR: AddressSanitizer|WARNING: ThreadSanitizer'; then
      echo "FAIL $t [${san:-plain}]"; echo "$out" | head -20; fail=1
    else
      echo "pass $t [${san:-plain}]"
    fi
  done
done

# the built-in memory checker: runs everywhere, and is what Windows uses instead of AddressSanitizer
for t in tests/*.ql; do
  out=$($PY quill.py run --check "$t" 2>&1 </dev/null); code=$?
  if [ $code -ne 0 ] || echo "$out" | grep -qE '^LEAK|^quill check:'; then
    echo "FAIL $t [check]"; echo "$out" | head -20; fail=1
  else
    echo "pass $t [check]"
  fi
done
# the checker must catch a real leak, and `--sanitize address` must map to it on Windows
printf 'class Node:
    other: Node
class Main:
    static def main():
        a = new Node()
        a.other = a
' > "${TMPDIR:-/tmp}/quill_leak.ql"
if $PY quill.py run --check "${TMPDIR:-/tmp}/quill_leak.ql" 2>&1 | grep -q 'quill check: 1 heap object'; then
  echo "pass check detects a leak"
else
  echo "FAIL check detects a leak"; fail=1
fi
rm -f "${TMPDIR:-/tmp}/quill_leak.ql"

# console input: the program reads lines from standard input
out=$(printf 'hello world\r\nsecond\n' | $PY quill.py run tests/stdin/read.ql 2>&1)
if [ "$(echo "$out" | grep -c '^ok')" = 3 ] && ! echo "$out" | grep -q 'FAIL\|LEAK'; then
  echo "pass tests/stdin/read.ql"
else
  echo "FAIL tests/stdin/read.ql"; echo "$out"; fail=1
fi

# compile-error tests: each file's first line is "# expect: <message fragment>"
for t in tests/errors/*.ql; do
  want=$(head -1 "$t" | sed 's/^# expect: //')
  out=$($PY quill.py emit "$t" 2>&1 >/dev/null); code=$?
  if [ $code -eq 1 ] && echo "$out" | grep -qF "$want"; then
    echo "pass $t"
  else
    echo "FAIL $t (wanted: $want)"; echo "$out" | head -3; fail=1
  fi
done

# runtime-panic tests: must exit 1 and print the expected message on stderr
for t in tests/panics/*.ql; do
  want=$(head -1 "$t" | sed 's/^# expect: //')
  out=$($PY quill.py run "$t" 2>&1 >/dev/null); code=$?
  if [ $code -eq 1 ] && echo "$out" | grep -qF "$want"; then
    echo "pass $t"
  else
    echo "FAIL $t (wanted exit 1 and: $want; got exit $code)"; echo "$out" | head -3; fail=1
  fi
done
# a project made of three packages: the output must match expected.txt
out=$($PY quill.py run tests/modules/app/src/main.ql 2>&1 | tr -d '\r')
if [ "$out" = "$(tr -d '\r' < tests/modules/app/expected.txt)" ]; then
  echo "pass tests/modules/app"
else
  echo "FAIL tests/modules/app"; echo "$out" | head -5; fail=1
fi

# modules under different names: the output must match expected.txt
out=$($PY quill.py run tests/modules/ns/main.ql 2>&1 | tr -d '\r')
if [ "$out" = "$(tr -d '\r' < tests/modules/ns/expected.txt)" ]; then
  echo "pass tests/modules/ns"
else
  echo "FAIL tests/modules/ns"; echo "$out" | head -5; fail=1
fi

# native code: wrap a C library and a C++ library with `quill wrap`, then use them.
# The program prints "ok"/"FAIL"/"LEAK" lines like the other tests.
export QUILL_QUIET_NATIVE=1
nat=$(mktemp -d)
native_case() {   # name, library module, program, wrap arguments...
  name=$1; lib=$2; prog=$3; shift 3
  if $PY quill.py wrap "$@" --out "$nat/$lib.ql" --yes >"$nat/$name.log" 2>&1; then
    cp "$prog" "$nat/"
    for san in "" $sans; do
      if [ "$san" = thread ]; then continue; fi        # TSan cannot link the C++ runtime reliably
      if [ -n "$san" ]; then flag="--sanitize $san"; else flag=""; fi
      out=$(ASAN_OPTIONS=detect_leaks=0 $PY quill.py run $flag "$nat/$(basename "$prog")" 2>&1); code=$?
      if [ $code -ne 0 ] || echo "$out" | grep -qE '^FAIL|^LEAK|ERROR: AddressSanitizer' || ! echo "$out" | grep -q 'no leaks'; then
        echo "FAIL tests/native/$name [${san:-plain}]"; echo "$out" | head -12; fail=1
      else
        echo "pass tests/native/$name [${san:-plain}]"
      fi
    done
  else
    echo "FAIL tests/native/$name (quill wrap)"; head -20 "$nat/$name.log"; fail=1
  fi
}
native_case c vec tests/native/main.ql tests/native/vec.h --name Vec --source tests/native/vec.c \
  --prefix vec_ --owns vec=vec_free --free-strings vec_free_string
if command -v clang++ >/dev/null 2>&1 || command -v g++ >/dev/null 2>&1; then
  native_case cpp geo tests/native/main_cpp.ql tests/native/counter.hpp --name Geo --source tests/native/counter.cpp
fi
# a `needs` dependency that contains native code must be refused
out=$(cd tests/native/refused/app && $PY ../../../../quill.py run src/main.ql 2>&1); code=$?
if [ $code -eq 1 ] && echo "$out" | grep -qF 'contains native (C/C++) code'; then
  echo "pass tests/native/refused"
else
  echo "FAIL tests/native/refused (got exit $code)"; echo "$out" | head -3; fail=1
fi
# wrapping needs an explicit acknowledgement of the caveats
if $PY quill.py wrap tests/native/vec.h --out "$nat/x.ql" </dev/null >/dev/null 2>&1; then
  echo "FAIL tests/native/acknowledge (wrapped without --yes)"; fail=1
else
  echo "pass tests/native/acknowledge"
fi
# "Under the hood" runs and explains a native program
if $PY quill.py hood "$nat/main.ql" --only classes,native --no-build 2>&1 | grep -q 'VecRaw.vec_push'; then
  echo "pass tests/native/hood"
else
  echo "FAIL tests/native/hood"; fail=1
fi
rm -rf "$nat"

# package manager unit tests (they build real git repositories in a temp folder)
if command -v git >/dev/null 2>&1; then
  if $PY -m unittest discover -s tests/pkg >/tmp/quill_pkg_tests.txt 2>&1; then
    echo "pass tests/pkg"
  else
    echo "FAIL tests/pkg"; tail -20 /tmp/quill_pkg_tests.txt; fail=1
  fi
fi
exit $fail
