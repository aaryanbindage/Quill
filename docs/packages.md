# Modules and packages

A Quill program can be split over several files with `bring`, and a *package* is
a folder with a `quill.pkg` manifest that other programs can depend on.

## `bring`: using other files

```python
bring util.text          # src/util/text.ql
bring shapes             # the package "shapes" (its main module)
bring shapes.circle      # src/circle.ql inside the package "shapes"
```

`bring` lines go at the top of a file, before the classes. A dotted path names a
file below the package's source folder (`source` in the manifest, `src` by
default; for a loose file with no manifest, the folder of the entry file). If the
first word is a package listed in `needs`, the path is looked up inside that
package instead, and `bring shapes` alone loads `shapes.ql` from its source folder.

- Without `as`, every class goes into one shared namespace, and two modules
  defining the same class is a compile error naming both files.
- A module is loaded once, however many files bring it. Cycles are allowed.
- A package can only reach the packages it lists in its own `needs`.
- A name that is both a local module and a dependency is an error, not a guess.

### Giving a module its own name: `bring ... as`

```python
bring geo2d as flat
bring geo3d as solid

class Main:
    static def main():
        a = new flat.Point(1, 2)           # geo2d's Point
        b = new solid.Point(3, 4, 5)       # geo3d's Point, no clash
        pts: List[flat.Point] = [a]
        if a instanceof flat.Point:
            print(flat.Point.origin().describe())
```

With `as NAME`, every class the module declares is called `NAME.Class` outside
it (types, `new`, static calls, `instanceof`, casts, `catch`, `class X < NAME.Y`,
generic arguments). Inside the module nothing changes, and the program's own
classes keep their plain names. For a package, the alias covers all of the modules
of that package that the first one brings; the packages *it* depends on stay
unprefixed unless they are brought `as` something too.

- Aliases are program-wide names, not per-file. Two different modules brought as
  the same alias share one namespace (and clash if they define the same class).
- A variable with the alias's name wins over the alias inside expressions.
- A module cannot be brought both with and without an alias in one program.

## The manifest: `quill.pkg`

One statement per line; `#` starts a comment; `"double quotes"` keep spaces.

```
package shapes
version 1.0.3
about Circles, squares and friends
source src
start main

needs mathx 1.0 at git https://example.com/mathx.git
needs textkit 0.4 at path ../textkit
needs fastmap =2.1.0 at git https://example.com/fastmap.git branch stable
```

| line | meaning |
|---|---|
| `package NAME` | letters, digits and `_` (it is used in `bring`). Required. |
| `version X.Y.Z` | Required. |
| `about TEXT` | One line of description. |
| `source DIR` | Where the `.ql` files are (default `src`). |
| `start MODULE` | The module with `Main`, for `quill run` with no file. Leave it out for a library. |
| `needs NAME [CONSTRAINT] at SOURCE` | A dependency. |

### Version constraints

| write | accepts |
|---|---|
| `1.4` | 1.4.0 or newer, but still 1.x |
| `0.4` | 0.4.x only (below 1.0 the minor version is the compatibility line) |
| `=1.4.2` | exactly 1.4.2 |
| `1.2..2.0` | from 1.2.0 up to, not including, 2.0.0 |
| `any` (or nothing) | every version |

### Sources

| write | meaning |
|---|---|
| `at path DIR` | A folder, relative to the manifest. Used live, never copied. |
| `at git URL` | A git repository. Its versions are its tags (`v1.2.3` or `1.2.3`); each tagged commit must contain a `quill.pkg` with the same version. |
| `at git URL branch NAME` | The head of a branch (the manifest's version applies). |
| `at git URL tag NAME` / `rev COMMIT` | One specific tag or commit. |

There is no central registry: a git repository is the package. `URL` can be
anything `git clone` accepts, including local paths.

## Commands

```
quill new NAME [--lib]     create a project (a library with --lib) in a new folder
quill init [--lib]         add a quill.pkg to the current folder
quill add NAME [CONSTRAINT] --git URL | --path DIR [--branch B | --tag T | --rev R]
quill drop NAME            remove a dependency
quill install [--locked] [--offline]
quill update [NAME ...]    move to newer versions (all packages, or just these)
quill tree                 show what the project depends on
quill run | build | emit [FILE]    with no FILE, the project's `start` module
```

`quill add` edits `quill.pkg`, installs, and when you gave no constraint writes the
compatible range of what it picked (`1.4` for 1.4.2). If installing fails the
manifest is left as it was.

## How resolution works

`quill install` finds, for every package in the whole tree, **one** version that
satisfies every `needs` line that mentions it (one version because all classes
share a namespace). It tries the newest version first and backtracks when a later
requirement rules a choice out. When it cannot succeed it says which constraints
clashed and who asked for them:

```
no version of mathx satisfies every requirement:
    1.0   (needed by shapes 1.0.3)
    2.0   (needed by app (this package))
  available versions: 2.0.0, 1.1.0, 1.0.0
```

Also rejected: the same package name from two different sources, dependency
cycles, a package that needs the project itself, and a tag whose manifest names
a different version.

## `quill.lock`

`install` writes `quill.lock`: each package's exact version, source, commit and a
sha256 of its files. **Commit it.** Later installs and builds use exactly those
versions even if newer tags appear; `quill update` is how you move on.

- `quill install --locked` fails instead of changing the lock (use it in CI).
- A tag that is moved or force-pushed does not change what you build: the
  lock pins the commit.
- Unpacked packages live in `.quill/deps/NAME-VERSION/` (ignore this folder in
  git). Building checks their hash first, and refuses to compile a package whose
  files were edited; `quill install` restores it. If the files from the pinned
  commit do not match the lock's hash, install stops with an integrity error.
- Downloads are cached once per machine in `~/.quill/git` (set `QUILL_HOME` to move
  it). `--offline`, or `QUILL_OFFLINE=1`, uses only the cache.

## Writing a package

```
quill new --lib greeter       # src/greeter.ql is what `bring greeter` loads
cd greeter
git init && git add -A && git commit -m "first release" && git tag v0.1.0
```

Anyone can now write `needs greeter 0.1 at git <where you pushed it>`. Bump
`version` in `quill.pkg`, commit, and tag `vX.Y.Z` to release a new version.
