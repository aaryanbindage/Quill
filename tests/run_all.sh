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
    out=$(ASAN_OPTIONS=detect_leaks=0 $PY quill.py run $flag "$t" 2>&1); code=$?
    if [ $code -ne 0 ] || echo "$out" | grep -qE '^LEAK|ERROR: AddressSanitizer|WARNING: ThreadSanitizer'; then
      echo "FAIL $t [${san:-plain}]"; echo "$out" | head -20; fail=1
    else
      echo "pass $t [${san:-plain}]"
    fi
  done
done

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
if [ "$out" = "$(cat tests/modules/app/expected.txt)" ]; then
  echo "pass tests/modules/app"
else
  echo "FAIL tests/modules/app"; echo "$out" | head -5; fail=1
fi

# modules under different names: the output must match expected.txt
out=$($PY quill.py run tests/modules/ns/main.ql 2>&1 | tr -d '\r')
if [ "$out" = "$(cat tests/modules/ns/expected.txt)" ]; then
  echo "pass tests/modules/ns"
else
  echo "FAIL tests/modules/ns"; echo "$out" | head -5; fail=1
fi

# package manager unit tests (they build real git repositories in a temp folder)
if command -v git >/dev/null 2>&1; then
  if $PY -m unittest discover -s tests/pkg >/tmp/quill_pkg_tests.txt 2>&1; then
    echo "pass tests/pkg"
  else
    echo "FAIL tests/pkg"; tail -20 /tmp/quill_pkg_tests.txt; fail=1
  fi
fi
exit $fail
