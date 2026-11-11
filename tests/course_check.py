"""Checks the programs in docs/course: every ```python block whose first line is
"# course: runs" is compiled and run, and if a ```text block follows it, the program's
output must equal that block. With --fill the text blocks are rewritten from the real
output instead (use it after editing a lesson).

    python tests/course_check.py [--fill] [lesson.md ...]
"""
import glob
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FENCE = re.compile(r"^```(\w*)\s*$")


def blocks(lines):
    """(language, first line index, last line index, [code lines]) for each fenced block."""
    out, i = [], 0
    while i < len(lines):
        m = FENCE.match(lines[i])
        if m and m.group(1):
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            out.append((m.group(1), i, j, lines[i + 1:j]))
            i = j
        i += 1
    return out


def run(code, stdin_text):
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "lesson.ql")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(code) + "\n")
        r = subprocess.run([sys.executable, os.path.join(ROOT, "quill.py"), "run", path],
                           input=stdin_text, capture_output=True, text=True, encoding="utf-8")
        return r.returncode, (r.stdout + r.stderr).replace("\r\n", "\n").rstrip()


def main():
    args = sys.argv[1:]
    fill = "--fill" in args
    files = [a for a in args if not a.startswith("--")] or sorted(glob.glob(os.path.join(ROOT, "docs", "course", "*.md")))
    bad = 0
    for path in files:
        with open(path, encoding="utf-8", newline="") as f:
            raw = f.read()
        eol = "\r\n" if "\r\n" in raw else "\n"
        lines = raw.replace("\r\n", "\n").split("\n")
        bl = blocks(lines)
        edits = []
        ran = 0
        for k, (lang, a, b, code) in enumerate(bl):
            if lang != "python" or not code or code[0].strip() != "# course: runs":
                continue
            stdin_text = ""
            code_to_run = code
            if len(code) > 1 and code[1].startswith("# input: "):
                stdin_text = code[1][len("# input: "):].replace("\\n", "\n") + "\n"
            status, text = run(code_to_run, stdin_text)
            ran += 1
            nxt = bl[k + 1] if k + 1 < len(bl) else None
            has_out = nxt is not None and nxt[0] == "text" and nxt[1] <= b + 3
            if status != 0 and "# course: fails" not in code[0]:
                print(f"FAIL {os.path.basename(path)}:{a + 1} exited {status}\n{text}")
                bad += 1
                continue
            if has_out:
                if fill:
                    edits.append((nxt[1], nxt[2], text.split("\n")))
                elif "\n".join(nxt[3]).rstrip() != text:
                    print(f"FAIL {os.path.basename(path)}:{nxt[1] + 1} output differs\n--- expected\n"
                          + "\n".join(nxt[3]) + "\n--- actual\n" + text)
                    bad += 1
        if fill:
            for a, b, new in sorted(edits, reverse=True):
                lines[a + 1:b] = new
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(eol.join(lines))
        if not bad:
            print(f"pass {os.path.relpath(path, ROOT)} ({ran} programs)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
