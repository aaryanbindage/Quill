"""Tests for the package manager. Git dependencies are exercised against real
repositories created in a temporary folder, so `git` must be installed."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import quillpkg as q  # noqa: E402
import quill  # noqa: E402

GIT = shutil.which("git")
ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t",
           GIT_COMMITTER_EMAIL="t@t", GIT_CONFIG_NOSYSTEM="1")


def git(cwd, *args):
    r = subprocess.run(["git", "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false", *args],
                       cwd=cwd, env=ENV, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="quilltest")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        os.environ["QUILL_HOME"] = os.path.join(self.tmp, "home")
        self.addCleanup(os.environ.pop, "QUILL_HOME", None)

    def path(self, *parts):
        return os.path.join(self.tmp, *parts)

    def lib(self, name, versions, needs=(), body=None):
        """A git repository `name` with one tagged commit per version."""
        d = self.path("repos", name)
        os.makedirs(d, exist_ok=True)
        git(d, "init", "-q")
        for v in versions:
            write(os.path.join(d, "quill.pkg"),
                  f"package {name}\nversion {v}\nsource src\n\n" + "".join(f"{n}\n" for n in needs))
            cls = name.capitalize()
            write(os.path.join(d, "src", f"{name}.ql"),
                  body or f'class {cls}:\n    static def version() -> str:\n        return "{v}"\n')
            git(d, "add", "-A")
            git(d, "commit", "-q", "-m", f"v{v}")
            git(d, "tag", f"v{v}")
        return d

    def app(self, needs, name="app"):
        d = self.path(name)
        write(os.path.join(d, "quill.pkg"),
              f"package {name}\nversion 0.1.0\nsource src\nstart main\n\n" + "\n".join(needs) + "\n")
        write(os.path.join(d, "src", "main.ql"), "class Main:\n    static def main():\n        print(1)\n")
        return d

    def installed(self, project):
        lock = q.read_lock(project)
        return {n: q.fmt_version(p.version) for n, p in lock.items()}


class VersionTests(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(q.parse_version("1.2.3"), (1, 2, 3))
        self.assertEqual(q.parse_version("v2.1"), (2, 1, 0))
        self.assertEqual(q.parse_version("3"), (3, 0, 0))
        for bad in ("", "x", "1.2.3.4", "1.a", "1.2-beta"):
            with self.assertRaises(q.PackageError):
                q.parse_version(bad)

    def test_constraints(self):
        c = q.Constraint.parse
        self.assertTrue(c("any").allows((9, 9, 9)))
        self.assertTrue(c("1.4").allows((1, 4, 0)) and c("1.4").allows((1, 9, 2)))
        self.assertFalse(c("1.4").allows((1, 3, 9)) or c("1.4").allows((2, 0, 0)))
        self.assertTrue(c("0.4").allows((0, 4, 7)))
        self.assertFalse(c("0.4").allows((0, 5, 0)))      # 0.x: the minor version is the compatibility line
        self.assertTrue(c("=1.4.2").allows((1, 4, 2)))
        self.assertFalse(c("=1.4.2").allows((1, 4, 3)))
        self.assertTrue(c("1.2..2.0").allows((1, 9, 9)))
        self.assertFalse(c("1.2..2.0").allows((2, 0, 0)))
        self.assertFalse(c("1.2..2.0").allows((1, 1, 9)))
        with self.assertRaises(q.PackageError):
            c("2.0..1.0")


class ManifestTests(unittest.TestCase):
    def parse(self, text):
        return q.parse_manifest(text, os.getcwd())

    def test_full(self):
        m = self.parse('# comment\npackage demo\nversion 1.0.0\nabout A demo # trailing\nsource src\nstart main\n'
                       'needs a 1.2 at path ../a\nneeds b at git https://x/y.git branch dev\n'
                       'needs c =2.0.1 at git "my repo" tag v1\n')
        self.assertEqual((m.name, m.version, m.about, m.start), ("demo", (1, 0, 0), "A demo", "main"))
        self.assertEqual([n.name for n in m.needs], ["a", "b", "c"])
        self.assertEqual(m.needs[1].source.ref_kind, "branch")
        self.assertEqual(m.needs[1].constraint.text, "any")
        self.assertTrue(m.needs[0].source.where.endswith("a"))
        self.assertEqual(m.needs[2].source.where.split(os.sep)[-1], "my repo")

    def test_errors(self):
        bad = {
            "package x\n": "missing `version`",
            "version 1.0.0\n": "missing `package",
            "package x\nversion 1.0.0\nwat 1\n": "unknown keyword",
            "package x\npackage y\nversion 1.0.0\n": "given twice",
            "package 9x\nversion 1.0.0\n": "package name",
            "package x\nversion nope\n": "bad version",
            "package x\nversion 1.0.0\nneeds x at path .\n": "cannot need itself",
            "package x\nversion 1.0.0\nneeds a at path .\nneeds a at path .\n": "needed twice",
            "package x\nversion 1.0.0\nneeds a\n": "where it comes from",
            "package x\nversion 1.0.0\nneeds a at ftp z\n": "expected `at path",
            "package x\nversion 1.0.0\nneeds a at path . extra\n": "unexpected words",
            "package x\nversion 1.0.0\nneeds a at git --upload-pack=x\n": "cannot start with '-'",
            'package x\nversion 1.0.0\nneeds a at path "oops\n': "unterminated quote",
        }
        for text, frag in bad.items():
            with self.assertRaises(q.PackageError, msg=text) as cm:
                self.parse(text)
            self.assertIn(frag, str(cm.exception), msg=text)

    def test_edit_keeps_layout(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        write(os.path.join(d, q.MANIFEST),
              "# header\npackage x\nversion 1.0.0\n\nneeds a 1.0 at path ../a  # keep\nneeds b at path ../b\n\n# tail\n")
        q.edit_manifest(d, add="needs c any at path ../c")
        q.edit_manifest(d, add="needs a 2.0 at path ../a2")
        q.edit_manifest(d, drop="b")
        text = read(os.path.join(d, q.MANIFEST))
        self.assertEqual(text, "# header\npackage x\nversion 1.0.0\n\nneeds a 2.0 at path ../a2\n"
                               "needs c any at path ../c\n\n# tail\n")
        m = q.load_manifest(d)
        self.assertEqual([n.name for n in m.needs], ["a", "c"])


class LockTests(Base):
    def test_round_trip(self):
        project = self.path("p")
        os.makedirs(project)
        locked = {
            "a": q.Locked("a", (1, 2, 0), q.Source("git", "https://h/a.git", "branch", "main"), "abc123", "sha256:ff", ["b"]),
            "b": q.Locked("b", (0, 3, 1), q.Source("path", self.path("b")), "", "", []),
        }
        q.write_lock(project, locked)
        again = q.read_lock(project)
        self.assertEqual(again, locked)

    def test_bad_lock(self):
        project = self.path("p")
        for text, frag in {"nonsense\n": "unexpected line", "lock 2\n": "unsupported",
                           "lock 1\n    from git x\n": "outside a `pinned`",
                           "pinned a 1.0.0\n": "missing `lock 1`",
                           "lock 1\npinned a 1.0.0\n": "no `from` line"}.items():
            write(os.path.join(project, q.LOCKFILE), text)
            with self.assertRaises(q.PackageError, msg=text) as cm:
                q.read_lock(project)
            self.assertIn(frag, str(cm.exception))


@unittest.skipUnless(GIT, "git is not installed")
class ResolveTests(Base):
    def need(self, name, cons, repo, extra=""):
        return f'needs {name} {cons} at git "{repo}"{extra}'

    def test_picks_newest_compatible(self):
        a = self.lib("alpha", ["1.0.0", "1.1.0", "1.2.0", "2.0.0"])
        for cons, want in [("1.0", "1.2.0"), ("=1.1.0", "1.1.0"), ("1.0..1.2", "1.1.0"), ("any", "2.0.0"), ("2.0", "2.0.0")]:
            p = self.app([self.need("alpha", cons, a)], name="app" + cons.replace(".", "").replace("=", "e").replace("any", "n"))
            q.install(p)
            self.assertEqual(self.installed(p), {"alpha": want}, cons)

    def test_unsatisfiable_lists_versions(self):
        a = self.lib("alpha", ["1.0.0", "1.1.0"])
        p = self.app([self.need("alpha", "3.0", a)])
        with self.assertRaises(q.PackageError) as cm:
            q.install(p)
        self.assertIn("no version of alpha", str(cm.exception))
        self.assertIn("1.1.0, 1.0.0", str(cm.exception))

    def test_transitive_and_backtracking(self):
        x = self.lib("xlib", ["1.0.0", "1.1.0", "1.2.0"])
        a = self.lib("alib", ["1.0.0"], needs=[self.need("xlib", "1.0", x)])
        b = self.lib("blib", ["1.0.0"], needs=[self.need("xlib", "=1.1.0", x)])
        p = self.app([self.need("alib", "1.0", a), self.need("blib", "1.0", b)])
        q.install(p)
        # alib alone would take xlib 1.2.0; blib forces the solver back to 1.1.0
        self.assertEqual(self.installed(p), {"alib": "1.0.0", "blib": "1.0.0", "xlib": "1.1.0"})
        self.assertTrue(os.path.isdir(os.path.join(p, ".quill", "deps", "xlib-1.1.0")))

    def test_conflict(self):
        x = self.lib("xlib", ["1.0.0", "2.0.0"])
        a = self.lib("alib", ["1.0.0"], needs=[self.need("xlib", "1.0", x)])
        b = self.lib("blib", ["1.0.0"], needs=[self.need("xlib", "2.0", x)])
        p = self.app([self.need("alib", "1.0", a), self.need("blib", "1.0", b)])
        with self.assertRaises(q.PackageError) as cm:
            q.install(p)
        msg = str(cm.exception)
        self.assertIn("no version of xlib satisfies every requirement", msg)
        self.assertIn("alib 1.0.0", msg)
        self.assertIn("blib 1.0.0", msg)

    def test_two_sources_for_one_name(self):
        x1 = self.lib("xlib", ["1.0.0"])
        os.rename(x1, self.path("repos", "xlib2"))
        x2 = self.path("repos", "xlib2")
        x1 = self.lib("xlib", ["1.0.0"])
        a = self.lib("alib", ["1.0.0"], needs=[self.need("xlib", "1.0", x2)])
        p = self.app([self.need("alib", "1.0", a), self.need("xlib", "1.0", x1)])
        with self.assertRaises(q.PackageError) as cm:
            q.install(p)
        self.assertIn("needed from two different places", str(cm.exception))

    def test_cycle(self):
        for n, other in (("one", "two"), ("two", "one")):
            write(os.path.join(self.path(n), "quill.pkg"),
                  f"package {n}\nversion 1.0.0\nneeds {other} at path ../{other}\n")
        p = self.app(["needs one at path ../one"])
        with self.assertRaises(q.PackageError) as cm:
            q.install(p)
        self.assertIn("dependency cycle", str(cm.exception))

    def test_needs_the_root(self):
        write(os.path.join(self.path("dep"), "quill.pkg"), "package dep\nversion 1.0.0\nneeds app at path ../app\n")
        p = self.app(["needs dep at path ../dep"])
        with self.assertRaises(q.PackageError) as cm:
            q.install(p)
        self.assertIn("package being built", str(cm.exception))

    def test_branch_rev_and_tag_sources(self):
        a = self.lib("alpha", ["1.0.0"])
        git(a, "checkout", "-q", "-b", "dev")
        write(os.path.join(a, "quill.pkg"), "package alpha\nversion 1.5.0\nsource src\n")
        git(a, "commit", "-q", "-am", "dev work")
        rev = git(a, "rev-parse", "HEAD")
        p = self.app([self.need("alpha", "any", a, " branch dev")])
        q.install(p)
        self.assertEqual(self.installed(p), {"alpha": "1.5.0"})
        self.assertEqual(q.read_lock(p)["alpha"].commit, rev)
        p2 = self.app([self.need("alpha", "any", a, " tag v1.0.0")], name="app2")
        q.install(p2)
        self.assertEqual(self.installed(p2), {"alpha": "1.0.0"})
        p3 = self.app([self.need("alpha", "any", a, f" rev {rev}")], name="app3")
        q.install(p3)
        self.assertEqual(self.installed(p3), {"alpha": "1.5.0"})
        p4 = self.app([self.need("alpha", "any", a, " branch nope")], name="app4")
        with self.assertRaises(q.PackageError) as cm:
            q.install(p4)
        self.assertIn("no branch nope", str(cm.exception))

    def test_tag_with_wrong_version(self):
        a = self.lib("alpha", ["1.0.0"])
        git(a, "tag", "v1.9.0")                      # tag says 1.9.0, manifest says 1.0.0
        p = self.app([self.need("alpha", "1.9", a)])
        with self.assertRaises(q.PackageError) as cm:
            q.install(p)
        self.assertIn("contains version 1.0.0", str(cm.exception))


@unittest.skipUnless(GIT, "git is not installed")
class InstallTests(Base):
    def setUp(self):
        super().setUp()
        self.a = self.lib("alpha", ["1.0.0", "1.1.0"])
        self.p = self.app([f'needs alpha 1.0 at git "{self.a}"'])

    def new_version(self, v):
        write(os.path.join(self.a, "quill.pkg"), f"package alpha\nversion {v}\nsource src\n")
        git(self.a, "commit", "-q", "-am", v)
        git(self.a, "tag", f"v{v}")

    def test_lock_keeps_versions_until_update(self):
        q.install(self.p)
        self.assertEqual(self.installed(self.p), {"alpha": "1.1.0"})
        self.new_version("1.2.0")
        q.install(self.p)
        self.assertEqual(self.installed(self.p), {"alpha": "1.1.0"})      # locked
        q.install(self.p, update=True)
        self.assertEqual(self.installed(self.p), {"alpha": "1.2.0"})
        self.assertFalse(os.path.exists(os.path.join(self.p, ".quill", "deps", "alpha-1.1.0")))
        self.assertTrue(os.path.exists(os.path.join(self.p, ".quill", "deps", "alpha-1.2.0")))

    def test_update_one_package_only(self):
        b = self.lib("beta", ["1.0.0"])
        write(os.path.join(self.p, "quill.pkg"),
              read(os.path.join(self.p, "quill.pkg")) + f'needs beta 1.0 at git "{b}"\n')
        q.install(self.p)
        self.new_version("1.2.0")
        write(os.path.join(b, "quill.pkg"), "package beta\nversion 1.0.1\nsource src\n")
        git(b, "commit", "-q", "-am", "b"); git(b, "tag", "v1.0.1")
        q.install(self.p, update={"beta"})
        self.assertEqual(self.installed(self.p), {"alpha": "1.1.0", "beta": "1.0.1"})

    def test_moved_tag_does_not_change_the_build(self):
        q.install(self.p)
        locked_commit = q.read_lock(self.p)["alpha"].commit
        write(os.path.join(self.a, "src", "alpha.ql"), "class Alpha:\n    static def evil() -> int:\n        return 666\n")
        git(self.a, "commit", "-q", "-am", "rewrite")
        git(self.a, "tag", "-f", "v1.1.0")
        q.install(self.p)
        self.assertEqual(q.read_lock(self.p)["alpha"].commit, locked_commit)
        text = read(os.path.join(self.p, ".quill", "deps", "alpha-1.1.0", "src", "alpha.ql"))
        self.assertNotIn("evil", text)

    def test_tampered_files_are_caught_and_repaired(self):
        q.install(self.p)
        f = os.path.join(self.p, ".quill", "deps", "alpha-1.1.0", "src", "alpha.ql")
        with open(f, "a") as fh:
            fh.write("\n# tampered\n")
        with self.assertRaises(q.PackageError) as cm:        # compiling refuses modified packages
            q.context_for(os.path.join(self.p, "src", "main.ql"))
        self.assertIn("was modified", str(cm.exception))
        q.install(self.p)                                    # install restores them
        q.context_for(os.path.join(self.p, "src", "main.ql"))
        self.assertNotIn("tampered", read(f))

    def test_lock_hash_mismatch_is_an_error(self):
        q.install(self.p)
        lock = os.path.join(self.p, q.LOCKFILE)
        text = read(lock)
        h = q.read_lock(self.p)["alpha"].hash
        write(lock, text.replace(h, "sha256:" + "0" * 64))
        shutil.rmtree(os.path.join(self.p, ".quill"))
        with self.assertRaises(q.IntegrityError):
            q.install(self.p)

    def test_frozen(self):
        with self.assertRaises(q.PackageError) as cm:
            q.install(self.p, frozen=True)
        self.assertIn("no quill.lock", str(cm.exception))
        q.install(self.p)
        q.install(self.p, frozen=True)                       # fine while the lock matches
        q.edit_manifest(self.p, add=q.format_need("alpha", q.Constraint.parse("=1.0.0"), q.Source("git", self.a), self.p))
        with self.assertRaises(q.PackageError):
            q.install(self.p, frozen=True)

    def test_changed_manifest_reresolves(self):
        q.install(self.p)
        q.edit_manifest(self.p, add=q.format_need("alpha", q.Constraint.parse("=1.0.0"), q.Source("git", self.a), self.p))
        q.install(self.p)
        self.assertEqual(self.installed(self.p), {"alpha": "1.0.0"})

    def test_offline(self):
        q.install(self.p)
        shutil.rmtree(os.path.join(self.p, ".quill"))
        q.install(self.p, offline=True)                      # the cache has everything
        self.assertTrue(os.path.isdir(os.path.join(self.p, ".quill", "deps", "alpha-1.1.0")))
        os.environ["QUILL_HOME"] = self.path("empty-home")
        shutil.rmtree(os.path.join(self.p, ".quill"))
        with self.assertRaises(q.PackageError) as cm:
            q.install(self.p, offline=True)
        self.assertIn("not in the cache", str(cm.exception))

    def test_removing_all_needs_cleans_up(self):
        q.install(self.p)
        q.edit_manifest(self.p, drop="alpha")
        q.install(self.p)
        self.assertFalse(os.path.exists(os.path.join(self.p, q.LOCKFILE)))
        self.assertFalse(os.path.exists(os.path.join(self.p, ".quill", "deps")))

    def test_add_and_drop(self):
        p = self.app([], name="fresh")
        q.cmd_add(p, "alpha", None, q.Source("git", self.a))
        m = q.load_manifest(p)
        self.assertEqual(str(m.needs[0].constraint), "1.1")            # pinned to the compatible range
        self.assertEqual(self.installed(p), {"alpha": "1.1.0"})
        with self.assertRaises(q.PackageError):
            q.cmd_add(p, "alpha", "9.0", q.Source("git", self.a))      # fails and leaves the manifest alone
        self.assertEqual(str(q.load_manifest(p).needs[0].constraint), "1.1")
        q.cmd_drop(p, "alpha")
        self.assertEqual(q.load_manifest(p).needs, [])
        with self.assertRaises(q.PackageError):
            q.cmd_drop(p, "alpha")

    def test_tree(self):
        x = self.lib("xlib", ["1.0.0"])
        b = self.lib("blib", ["1.0.0"], needs=[f'needs xlib 1.0 at git "{x}"'])
        write(os.path.join(self.p, "quill.pkg"),
              read(os.path.join(self.p, "quill.pkg")) + f'needs blib 1.0 at git "{b}"\n')
        q.install(self.p)
        self.assertEqual(q.tree_lines(self.p), ["app 0.1.0", "|-- alpha 1.1.0", "`-- blib 1.0.0", "    `-- xlib 1.0.0"])


@unittest.skipUnless(GIT, "git is not installed")
class CompileTests(Base):
    def test_bring_from_git_package(self):
        a = self.lib("alpha", ["1.0.0"], body="class Alpha:\n    static def hi() -> int:\n        return 7\n")
        p = self.app([f'needs alpha 1.0 at git "{a}"'])
        write(os.path.join(p, "src", "main.ql"),
              "bring alpha\nbring tools.more\n\nclass Main:\n    static def main():\n        print(Alpha.hi() + More.two())\n")
        write(os.path.join(p, "src", "tools", "more.ql"), "class More:\n    static def two() -> int:\n        return 2\n")
        with self.assertRaises(q.PackageError):                       # not installed yet
            quill.compile_file(os.path.join(p, "src", "main.ql"))
        q.install(p)
        ir = quill.compile_file(os.path.join(p, "src", "main.ql"))
        self.assertIn("Alpha.hi", ir)
        self.assertIn("More.two", ir)

    def test_module_errors(self):
        p = self.app([])
        main = os.path.join(p, "src", "main.ql")
        write(main, "bring nothing.here\nclass Main:\n    static def main():\n        pass\n")
        with self.assertRaises(quill.CompileError) as cm:
            quill.compile_file(main)
        self.assertIn("no module `nothing.here`", cm.exception.msg)
        self.assertEqual(cm.exception.line, 1)
        write(main, "bring other\nclass Main:\n    static def main():\n        pass\n")
        write(os.path.join(p, "src", "other.ql"), "class Main:\n    pass\n")
        with self.assertRaises(quill.CompileError) as cm:
            quill.compile_file(main)
        self.assertIn("already defined", cm.exception.msg)
        write(os.path.join(p, "src", "other.ql"), "class Oops:\n    def f(self) -> int:\n        return \"x\"\n")
        with self.assertRaises(quill.CompileError) as cm:                # error in a module names that file
            quill.compile_file(main)
        self.assertTrue(cm.exception.file.endswith("other.ql"))

    def test_modules_load_once_and_cycles_are_fine(self):
        p = self.app([])
        write(os.path.join(p, "src", "main.ql"), "bring a\nbring b\nclass Main:\n    static def main():\n        pass\n")
        write(os.path.join(p, "src", "a.ql"), "bring b\nclass A:\n    pass\n")
        write(os.path.join(p, "src", "b.ql"), "bring a\nclass B:\n    pass\n")
        quill.compile_file(os.path.join(p, "src", "main.ql"))

    def test_dependency_is_not_visible_to_unrelated_packages(self):
        x = self.lib("xlib", ["1.0.0"])
        a = self.lib("alib", ["1.0.0"], body="bring xlib\nclass Alib:\n    pass\n")      # alib forgot to need xlib
        p = self.app([f'needs alib 1.0 at git "{a}"', f'needs xlib 1.0 at git "{x}"'])
        write(os.path.join(p, "src", "main.ql"), "bring alib\nclass Main:\n    static def main():\n        pass\n")
        q.install(p)
        with self.assertRaises(quill.CompileError) as cm:
            quill.compile_file(os.path.join(p, "src", "main.ql"))
        self.assertIn("no module `xlib`", cm.exception.msg)

    def test_alias_names_a_whole_package(self):
        a = self.lib("alpha", ["1.0.0"],
                     body="bring alpha_util\nclass Alpha:\n    static def hi() -> int:\n        return Util.one()\n")
        write(os.path.join(a, "src", "alpha_util.ql"), "class Util:\n    static def one() -> int:\n        return 1\n")
        git(a, "add", "-A")
        git(a, "commit", "-q", "-m", "util")
        git(a, "tag", "-f", "v1.0.0")
        p = self.app([f'needs alpha 1.0 at git "{a}"'])
        write(os.path.join(p, "src", "main.ql"),
              "bring alpha as al\nclass Alpha:\n    pass\n\nclass Main:\n    static def main():\n"
              "        x = new Alpha()\n        print(al.Alpha.hi())\n")
        q.install(p)
        ir = quill.compile_file(os.path.join(p, "src", "main.ql"))
        # the package's classes, including those of its other module, live under the alias
        self.assertIn('"al.Alpha.hi"', ir)
        self.assertIn('"al.Util.one"', ir)
        self.assertIn('@"vtable.Alpha"', ir)        # the program's own Alpha is a different class
        self.assertIn('@"vtable.al.Alpha"', ir)

    def test_ambiguous_name(self):
        x = self.lib("xlib", ["1.0.0"])
        p = self.app([f'needs xlib 1.0 at git "{x}"'])
        write(os.path.join(p, "src", "xlib.ql"), "class Local:\n    pass\n")
        write(os.path.join(p, "src", "main.ql"), "bring xlib\nclass Main:\n    static def main():\n        pass\n")
        q.install(p)
        with self.assertRaises(quill.CompileError) as cm:
            quill.compile_file(os.path.join(p, "src", "main.ql"))
        self.assertIn("ambiguous", cm.exception.msg)

    def test_templates(self):
        self.addCleanup(os.chdir, os.getcwd())      # runs before the temp folder is deleted
        os.chdir(self.tmp)
        app = q.cmd_new("hello")
        lib = q.cmd_new("greeter", lib=True)
        self.assertTrue(quill.compile_file(os.path.join(app, "src", "main.ql")))
        quill.Parser(quill.lex(read(os.path.join(lib, "src", "greeter.ql")))).program()
        with self.assertRaises(q.PackageError):
            q.cmd_new("hello")                                       # already exists
        with self.assertRaises(q.PackageError):
            q.cmd_new("bad-name")
        entry, m = q.default_entry(app)
        self.assertTrue(entry.endswith("main.ql"))
        with self.assertRaises(q.PackageError):
            q.default_entry(lib)                                     # libraries have no start module


if __name__ == "__main__":
    unittest.main()
