#!/bin/sh
# Runs every test normally and under both sanitizers. Fails on any LEAK line,
# sanitizer report, or non-zero exit.
cd "$(dirname "$0")/.." || exit 1
fail=0
for san in "" address thread; do
  for t in tests/*.ql; do
    if [ -n "$san" ]; then flag="--sanitize $san"; else flag=""; fi
    out=$(ASAN_OPTIONS=detect_leaks=0 python3 quill.py run $flag "$t" 2>&1); code=$?
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
  out=$(python3 quill.py emit "$t" 2>&1 >/dev/null); code=$?
  if [ $code -eq 1 ] && echo "$out" | grep -qF "$want"; then
    echo "pass $t"
  else
    echo "FAIL $t (wanted: $want)"; echo "$out" | head -3; fail=1
  fi
done

# runtime-panic tests: must exit 1 and print the expected message on stderr
for t in tests/panics/*.ql; do
  want=$(head -1 "$t" | sed 's/^# expect: //')
  out=$(python3 quill.py run "$t" 2>&1 >/dev/null); code=$?
  if [ $code -eq 1 ] && echo "$out" | grep -qF "$want"; then
    echo "pass $t"
  else
    echo "FAIL $t (wanted exit 1 and: $want; got exit $code)"; echo "$out" | head -3; fail=1
  fi
done
exit $fail
