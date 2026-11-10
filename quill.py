#!/usr/bin/env python3
"""Quill: a small statically-typed, class-only language with Python-style
syntax that compiles to LLVM IR (and then to a native binary via clang).

    quill.py run   file.ql          compile + run
    quill.py build file.ql -o out   compile to a native executable
    quill.py emit  file.ql          print LLVM IR
"""
import argparse
import copy
import dataclasses
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile

import quillpkg
from dataclasses import dataclass, field


class CompileError(Exception):
    def __init__(self, msg, line=0, file=None):
        super().__init__(msg)
        self.msg, self.line, self.file = msg, line, file


# ───────────────────────────── Lexer ─────────────────────────────

KEYWORDS = {
    "class", "def", "static", "return", "if", "elif", "else",
    "while", "for", "in", "new", "self", "true", "false", "null", "and",
    "or", "not", "break", "continue", "pass", "weak",
    "public", "private", "abstract", "interface", "super", "instanceof", "as",
    "try", "catch", "finally", "throw", "bring",
}

TOKEN_RE = re.compile(r'''
    (?P<WS>[ \t]+) |
    (?P<COMMENT>\#[^\n]*) |
    (?P<FLOAT>\d+\.\d+) |
    (?P<INT>\d+) |
    (?P<STR>"(?:[^"\\\n]|\\.)*") |
    (?P<NAME>[A-Za-z_]\w*) |
    (?P<OP>->|==|!=|<=|>=|\+=|-=|\*=|/=|%=|[-+*/%<>=(),.:{}\[\]])
''', re.X)

ESCAPES = {"n": "\n", "t": "\t", "\\": "\\", '"': '"', "0": "\0", "r": "\r"}


@dataclass
class Tok:
    kind: str
    val: object
    line: int

    def __repr__(self):
        return f"{self.kind}({self.val!r})"


def unescape(s, line):
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if c == "\\":
            i += 1
            if s[i] not in ESCAPES:
                raise CompileError(f"unknown escape \\{s[i]}", line)
            out.append(ESCAPES[s[i]])
        else:
            out.append(c)
        i += 1
    return "".join(out)


def lex(src):
    toks, stack, depth = [], [0], 0
    for lineno, raw in enumerate(src.split("\n"), 1):
        pos = 0
        if depth == 0:
            if not raw.strip() or raw.lstrip().startswith("#"):
                continue
            indent = len(raw) - len(raw.lstrip(" "))
            if raw[indent:indent + 1] == "\t":
                raise CompileError("tabs are not allowed; indent with spaces", lineno)
            if indent > stack[-1]:
                stack.append(indent)
                toks.append(Tok("INDENT", None, lineno))
            else:
                while indent < stack[-1]:
                    stack.pop()
                    toks.append(Tok("DEDENT", None, lineno))
                if indent != stack[-1]:
                    raise CompileError("inconsistent indentation", lineno)
            pos = indent
        while pos < len(raw):
            m = TOKEN_RE.match(raw, pos)
            if not m:
                raise CompileError(f"unexpected character {raw[pos]!r}", lineno)
            pos = m.end()
            kind, text = m.lastgroup, m.group()
            if kind in ("WS", "COMMENT"):
                continue
            if kind == "INT":
                toks.append(Tok("INT", int(text), lineno))
            elif kind == "FLOAT":
                toks.append(Tok("FLOAT", float(text), lineno))
            elif kind == "STR":
                toks.append(Tok("STR", unescape(text[1:-1], lineno), lineno))
            elif kind == "NAME":
                toks.append(Tok("KW" if text in KEYWORDS else "NAME", text, lineno))
            else:
                if text in "([{":
                    depth += 1
                elif text in ")]}":
                    depth -= 1
                toks.append(Tok("OP", text, lineno))
        if depth == 0:
            toks.append(Tok("NEWLINE", None, lineno))
    if depth != 0:
        raise CompileError("unbalanced brackets", len(src.split("\n")))
    last = toks[-1].line if toks else 1
    while len(stack) > 1:
        stack.pop()
        toks.append(Tok("DEDENT", None, last))
    toks.append(Tok("EOF", None, last))
    return toks


# ───────────────────────────── AST ─────────────────────────────

@dataclass
class N:
    line: int = field(default=0, kw_only=True)


@dataclass
class IntLit(N): v: int
@dataclass
class FloatLit(N): v: float
@dataclass
class StrLit(N): v: str
@dataclass
class BoolLit(N): v: bool
@dataclass
class NullLit(N): pass
@dataclass
class SelfExpr(N): pass
@dataclass
class Name(N): id: str
@dataclass
class Unary(N): op: str; e: N
@dataclass
class Binary(N): op: str; l: N; r: N
@dataclass
class FieldAccess(N): obj: N; name: str
@dataclass
class Call(N): callee: N; args: list
@dataclass
class New(N): cls: str; args: list
@dataclass
class Index(N): obj: N; index: N
@dataclass
class InstanceOf(N): e: N; cls: str
@dataclass
class Cast(N): e: N; cls: str
@dataclass
class Block(N): body: list   # internal: a statement list with its own scope
@dataclass
class LenOf(N): e: N          # internal: length of a for-each iterable

@dataclass
class VarDecl(N): name: str; type: str; init: N
@dataclass
class Assign(N): target: N; value: N
@dataclass
class If(N): cond: N; then: list; orelse: list
@dataclass
class While(N): cond: N; body: list
@dataclass
class ForRange(N): var: str; start: N; end: N; body: list
@dataclass
class Return(N): value: N
@dataclass
class ExprStmt(N): e: N
@dataclass
class ListLit(N): items: list
@dataclass
class MapLit(N): keys: list; vals: list
@dataclass
class Catch(N): cls: str; var: str; body: list
@dataclass
class Throw(N): value: N
@dataclass
class Try(N): body: list; catches: list; final: list = None   # catches: [Catch]
@dataclass
class Break(N): pass
@dataclass
class Continue(N): pass

@dataclass
class FieldDecl(N): name: str; type: str; access: str
@dataclass
class MethodDecl(N):
    name: str; params: list; ret: str; static: bool; body: list; access: str; abstract: bool
@dataclass
class ClassDecl(N):
    name: str; supers: list; fields: list; methods: list; abstract: bool; interface: bool
    tparams: list = field(default_factory=list)
@dataclass
class SuperCall(N): name: str; args: list


# ───────────────────────────── Parser ─────────────────────────────

class Parser:
    def __init__(self, toks):
        self.toks, self.i = toks, 0
        self.fe = 0          # counter for hidden for-each variables

    @property
    def tok(self):
        return self.toks[self.i]

    def peek(self, n=1):
        return self.toks[min(self.i + n, len(self.toks) - 1)]

    def next(self):
        t = self.tok
        self.i += 1
        return t

    def is_(self, kind, val=None):
        t = self.tok
        return t.kind == kind and (val is None or t.val == val)

    def accept(self, kind, val=None):
        if self.is_(kind, val):
            return self.next()

    def expect(self, kind, val=None):
        if not self.is_(kind, val):
            want = val if val is not None else kind
            got = self.tok.val if self.tok.val is not None else self.tok.kind
            raise CompileError(f"expected {want!r}, found {got!r}", self.tok.line)
        return self.next()

    # program / classes
    def program(self):
        classes, self.imports = [], []         # imports: [(dotted module path, line)]
        while not self.is_("EOF"):
            if self.is_("KW", "bring"):
                t = self.next()
                path = [self.expect("NAME").val]
                while self.accept("OP", "."):
                    path.append(self.expect("NAME").val)
                self.expect("NEWLINE")
                self.imports.append((".".join(path), t.line))
            else:
                classes.append(self.class_decl())
        return classes

    def class_decl(self):
        abstract = bool(self.accept("KW", "abstract"))
        iface = self.is_("KW", "interface")
        t = self.next() if iface else self.expect("KW", "class")
        if abstract and iface:
            raise CompileError("an interface is already abstract", t.line)
        name = self.expect("NAME").val
        tparams = []
        if self.accept("OP", "["):
            tparams.append(self.expect("NAME").val)
            while self.accept("OP", ","):
                tparams.append(self.expect("NAME").val)
            self.expect("OP", "]")
        supers = []
        if self.accept("OP", "<"):
            supers.append(self.expect("NAME").val)
            while self.accept("OP", ","):
                supers.append(self.expect("NAME").val)
        self.expect("OP", ":")
        self.expect("NEWLINE")
        self.expect("INDENT")
        fields, methods = [], []
        while not self.is_("DEDENT"):
            if self.accept("KW", "pass"):
                self.expect("NEWLINE")
                continue
            line, mods = self.tok.line, {}
            while self.is_("KW") and self.tok.val in ("public", "private", "static", "abstract"):
                m = self.next().val
                key = "access" if m in ("public", "private") else m
                if key in mods:
                    raise CompileError(f"duplicate modifier {m}", line)
                mods[key] = m if key == "access" else True
            if self.is_("KW", "def"):
                methods.append(self.method(mods, iface))
            elif self.is_("NAME") and self.peek().val == ":":
                if "static" in mods or "abstract" in mods:
                    raise CompileError("fields cannot be static or abstract", line)
                ft = self.next()
                self.expect("OP", ":")
                fields.append(FieldDecl(ft.val, self.type_name(), mods.get("access", "public"), line=ft.line))
                self.expect("NEWLINE")
            else:
                raise CompileError(f"unexpected {self.tok.val if self.tok.val is not None else self.tok.kind!r} in class body", line)
        self.expect("DEDENT")
        return ClassDecl(name, supers, fields, methods, abstract, iface, tparams, line=t.line)

    def type_name(self):
        """A type, written canonically: weak X, List[int], Map[str,List[int]]."""
        weak = "weak " if self.accept("KW", "weak") else ""
        name = self.expect("NAME").val
        if self.accept("OP", "["):
            args = [self.type_name()]
            while self.accept("OP", ","):
                args.append(self.type_name())
            self.expect("OP", "]")
            name = f"{name}[{','.join(args)}]"
        return weak + name

    def method(self, mods, in_interface):
        static = bool(mods.get("static"))
        abstract = bool(mods.get("abstract")) or in_interface
        t = self.expect("KW", "def")
        name = self.expect("NAME").val
        self.expect("OP", "(")
        params = []
        if not static:
            self.expect("KW", "self")
            if not self.is_("OP", ")"):
                self.expect("OP", ",")
        while not self.is_("OP", ")"):
            pn = self.expect("NAME").val
            self.expect("OP", ":")
            params.append((pn, self.type_name()))
            if not self.accept("OP", ","):
                break
        self.expect("OP", ")")
        ret = self.type_name() if self.accept("OP", "->") else "void"
        if abstract:
            if self.is_("OP", ":"):
                raise CompileError("abstract and interface methods have no body", self.tok.line)
            self.expect("NEWLINE")
            body = None
        else:
            body = self.block()
        return MethodDecl(name, params, ret, static, body, mods.get("access", "public"), abstract, line=t.line)

    # statements
    def block(self):
        self.expect("OP", ":")
        if self.accept("NEWLINE"):
            self.expect("INDENT")
            stmts = []
            while not self.is_("DEDENT"):
                stmts.extend(self.stmt())
            self.expect("DEDENT")
            return stmts
        return self.stmt()

    def stmt(self):
        t = self.tok
        if t.kind == "KW":
            kw = t.val
            if kw == "pass":
                self.next(); self.expect("NEWLINE"); return []
            if kw == "return":
                self.next()
                v = None if self.is_("NEWLINE") else self.expr()
                self.expect("NEWLINE")
                return [Return(v, line=t.line)]
            if kw == "throw":
                self.next()
                v = self.expr()
                self.expect("NEWLINE")
                return [Throw(v, line=t.line)]
            if kw == "try":
                self.next()
                body = self.block()
                catches = []
                while self.is_("KW", "catch"):
                    c = self.next()
                    cls = var = None
                    if self.is_("NAME"):
                        cls = self.next().val
                        if self.accept("KW", "as"):
                            var = self.expect("NAME").val
                    catches.append(Catch(cls, var, self.block(), line=c.line))
                final = None
                if self.accept("KW", "finally"):
                    final = self.block()
                if not catches and final is None:
                    raise CompileError("try needs at least one catch or a finally", t.line)
                return [Try(body, catches, final, line=t.line)]
            if kw in ("break", "continue"):
                self.next(); self.expect("NEWLINE")
                return [(Break if kw == "break" else Continue)(line=t.line)]
            if kw == "if":
                return [self.if_stmt()]
            if kw == "while":
                self.next()
                c = self.expr()
                return [While(c, self.block(), line=t.line)]
            if kw == "for":
                self.next()
                var = self.expect("NAME").val
                self.expect("KW", "in")
                if not (self.is_("NAME", "range") and self.peek().val == "("):
                    # for x in xs:  ->  $it = xs; for $i in range(len): x = $it[$i]; ...
                    it = self.expr()
                    body = self.block()
                    self.fe += 1
                    itn, idx = f"$it{self.fe}", f"$i{self.fe}"
                    nm = lambda n: Name(n, line=t.line)
                    # own scope, so the hidden iterable reference is released when the loop ends
                    return [Block([Assign(nm(itn), it, line=t.line),
                                   ForRange(idx, IntLit(0, line=t.line), LenOf(nm(itn), line=t.line),
                                            [Assign(nm(var), Index(nm(itn), nm(idx), line=t.line), line=t.line)] + body,
                                            line=t.line)], line=t.line)]
                self.next()
                self.expect("OP", "(")
                a = self.expr()
                if self.accept("OP", ","):
                    start, end = a, self.expr()
                else:
                    start, end = IntLit(0, line=t.line), a
                self.expect("OP", ")")
                return [ForRange(var, start, end, self.block(), line=t.line)]
        if t.kind == "NAME" and self.peek().val == ":" and self.peek().kind == "OP":
            self.next(); self.next()
            ty = self.type_name()
            init = None
            if self.accept("OP", "="):
                init = self.expr()
            self.expect("NEWLINE")
            return [VarDecl(t.val, ty, init, line=t.line)]
        e = self.expr()
        if self.is_("OP") and self.tok.val in ("=", "+=", "-=", "*=", "/=", "%="):
            op = self.next().val
            if not isinstance(e, (Name, FieldAccess, Index)):
                raise CompileError("invalid assignment target", t.line)
            v = self.expr()
            if op != "=":
                v = Binary(op[0], e, v, line=t.line)
            self.expect("NEWLINE")
            return [Assign(e, v, line=t.line)]
        self.expect("NEWLINE")
        return [ExprStmt(e, line=t.line)]

    def if_stmt(self):
        t = self.next()  # if / elif
        cond = self.expr()
        then = self.block()
        orelse = []
        if self.is_("KW", "elif"):
            orelse = [self.if_stmt()]
        elif self.accept("KW", "else"):
            orelse = self.block()
        return If(cond, then, orelse, line=t.line)

    # expressions
    def expr(self):
        return self.or_()

    def or_(self):
        l = self.and_()
        while self.is_("KW", "or"):
            t = self.next()
            l = Binary("or", l, self.and_(), line=t.line)
        return l

    def and_(self):
        l = self.not_()
        while self.is_("KW", "and"):
            t = self.next()
            l = Binary("and", l, self.not_(), line=t.line)
        return l

    def not_(self):
        if self.is_("KW", "not"):
            t = self.next()
            return Unary("not", self.not_(), line=t.line)
        return self.cmp()

    def cmp(self):
        l = self.add()
        while True:
            if self.is_("OP") and self.tok.val in ("==", "!=", "<", "<=", ">", ">="):
                t = self.next()
                l = Binary(t.val, l, self.add(), line=t.line)
            elif self.is_("KW", "instanceof"):
                t = self.next()
                l = InstanceOf(l, self.expect("NAME").val, line=t.line)
            else:
                return l

    def add(self):
        l = self.mul()
        while self.is_("OP") and self.tok.val in ("+", "-"):
            t = self.next()
            l = Binary(t.val, l, self.mul(), line=t.line)
        return l

    def mul(self):
        l = self.unary()
        while self.is_("OP") and self.tok.val in ("*", "/", "%"):
            t = self.next()
            l = Binary(t.val, l, self.unary(), line=t.line)
        return l

    def unary(self):
        if self.is_("OP", "-"):
            t = self.next()
            return Unary("-", self.unary(), line=t.line)
        e = self.postfix()
        while self.is_("KW", "as"):
            t = self.next()
            e = Cast(e, self.expect("NAME").val, line=t.line)
        return e

    def postfix(self):
        e = self.primary()
        while True:
            if self.is_("OP", "."):
                t = self.next()
                e = FieldAccess(e, self.expect("NAME").val, line=t.line)
            elif self.is_("OP", "("):
                t = self.next()
                e = Call(e, self.args(), line=t.line)
            elif self.is_("OP", "["):
                t = self.next()
                idx = self.expr()
                self.expect("OP", "]")
                e = Index(e, idx, line=t.line)
            else:
                return e

    def args(self):
        args = []
        while not self.is_("OP", ")"):
            args.append(self.expr())
            if not self.accept("OP", ","):
                break
        self.expect("OP", ")")
        return args

    def primary(self):
        t = self.next()
        if t.kind == "INT": return IntLit(t.val, line=t.line)
        if t.kind == "FLOAT": return FloatLit(t.val, line=t.line)
        if t.kind == "STR": return StrLit(t.val, line=t.line)
        if t.kind == "NAME": return Name(t.val, line=t.line)
        if t.kind == "KW":
            if t.val in ("true", "false"): return BoolLit(t.val == "true", line=t.line)
            if t.val == "null": return NullLit(line=t.line)
            if t.val == "self": return SelfExpr(line=t.line)
            if t.val == "super":
                self.expect("OP", ".")
                name = self.expect("NAME").val
                self.expect("OP", "(")
                return SuperCall(name, self.args(), line=t.line)
            if t.val == "new":
                cls = self.expect("NAME").val
                if self.accept("OP", "["):
                    targs = [self.type_name()]
                    while self.accept("OP", ","):
                        targs.append(self.type_name())
                    self.expect("OP", "]")
                    cls = f"{cls}[{','.join(targs)}]"
                self.expect("OP", "(")
                return New(cls, self.args(), line=t.line)
        if t.kind == "OP" and t.val == "(":
            e = self.expr()
            self.expect("OP", ")")
            return e
        if t.kind == "OP" and t.val == "[":
            items = []
            while not self.is_("OP", "]"):
                items.append(self.expr())
                if not self.accept("OP", ","):
                    break
            self.expect("OP", "]")
            return ListLit(items, line=t.line)
        if t.kind == "OP" and t.val == "{":
            keys, vals = [], []
            while not self.is_("OP", "}"):
                keys.append(self.expr())
                self.expect("OP", "->")
                vals.append(self.expr())
                if not self.accept("OP", ","):
                    break
            self.expect("OP", "}")
            return MapLit(keys, vals, line=t.line)
        raise CompileError(f"unexpected {t.val if t.val is not None else t.kind!r}", t.line)


# ───────────────────────────── Code generation ─────────────────────────────

PRIMS = {"int": "i64", "float": "double", "bool": "i1", "str": "ptr", "void": "void"}
NUM = ("int", "float")


def cstr(name, text):
    data = text.encode() + b"\0"
    enc = "".join(chr(b) if 32 <= b < 127 and b not in (34, 92) else f"\\{b:02X}" for b in data)
    return f'{name} = private unnamed_addr constant [{len(data)} x i8] c"{enc}"'



# name -> (argument kinds, return kind, runtime function). "obj" = any class instance.
INTRINSICS = {
    "__thread_start": (["obj"], "int", "quill_thread_start"),
    "__thread_join": (["int"], "void", "quill_thread_join"),
    "__mutex_new": ([], "int", "quill_mutex_new"),
    "__mutex_lock": (["int"], "void", "quill_mutex_lock"),
    "__mutex_unlock": (["int"], "void", "quill_mutex_unlock"),
    "__mutex_free": (["int"], "void", "quill_mutex_free"),
    "__sleep_ms": (["int"], "void", "quill_sleep_ms"),
    "__panic": (["str"], "void", "quill_panic"),
    "__exc_msg": ([], "str", "quill_exc_msg"),
}

# Built-in classes, written in Quill and compiled with every program.
PRELUDE = """
class Thread:
    handle: int

    def run(self):
        pass

    def start(self):
        self.handle = __thread_start(self)

    def join(self):
        __thread_join(self.handle)

    static def sleep(ms: int):
        __sleep_ms(ms)

class Mutex:
    handle: int

    def init(self):
        self.handle = __mutex_new()

    def lock(self):
        __mutex_lock(self.handle)

    def unlock(self):
        __mutex_unlock(self.handle)

    def deinit(self):
        __mutex_free(self.handle)

# Base class for exceptions. Runtime errors (bad index, null dereference, ...)
# are thrown as plain Errors carrying the panic message.
class Error:
    message: str

    def init(self, message: str):
        self.message = message

    def toString(self) -> str:
        return "Error: " + self.message

    static def fromPanic() -> Error:
        return new Error(__exc_msg())

# A growable array. Written as a template: List[int], List[str], List[Node]...
class List[T]:
    private items: Array[T]
    private blank: Array[T]       # one zeroed slot, used to clear vacated positions
    private count: int

    def init(self):
        self.items = new Array[T](8)
        self.blank = new Array[T](1)
        self.count = 0

    def size(self) -> int:
        return self.count

    def isEmpty(self) -> bool:
        return self.count == 0

    def add(self, x: T):
        if self.count == self.items.length:
            self.grow()
        self.items[self.count] = x
        self.count += 1

    private def grow(self):
        bigger = new Array[T](self.items.length * 2)
        for i in range(self.count):
            bigger[i] = self.items[i]
        self.items = bigger

    private def check(self, i: int):
        if i < 0 or i >= self.count:
            __panic("list index out of range")

    def get(self, i: int) -> T:
        self.check(i)
        return self.items[i]

    def set(self, i: int, x: T):
        self.check(i)
        self.items[i] = x

    def insert(self, i: int, x: T):
        if i < 0 or i > self.count:
            __panic("list index out of range")
        self.add(x)
        j = self.count - 1
        while j > i:
            self.items[j] = self.items[j - 1]
            j -= 1
        self.items[i] = x

    def removeAt(self, i: int) -> T:
        self.check(i)
        x = self.items[i]
        j = i
        while j < self.count - 1:
            self.items[j] = self.items[j + 1]
            j += 1
        self.items[self.count - 1] = self.blank[0]
        self.count -= 1
        return x

    def pop(self) -> T:
        return self.removeAt(self.count - 1)

    def clear(self):
        self.items = new Array[T](8)
        self.count = 0

    def indexOf(self, x: T) -> int:
        for i in range(self.count):
            if self.items[i] == x:
                return i
        return -1

    def contains(self, x: T) -> bool:
        return self.indexOf(x) >= 0

class MapEntry[K, V]:
    key: K
    value: V
    hash: int
    next: MapEntry[K, V]

    def init(self, key: K, value: V, h: int):
        self.key = key
        self.value = value
        self.hash = h

# A hash map (separate chaining). Iteration order is unspecified.
class Map[K, V]:
    private buckets: Array[MapEntry[K, V]]
    private count: int

    def init(self):
        self.buckets = new Array[MapEntry[K, V]](16)
        self.count = 0

    def size(self) -> int:
        return self.count

    def isEmpty(self) -> bool:
        return self.count == 0

    private def slot(self, h: int, n: int) -> int:
        return ((h % n) + n) % n

    private def find(self, k: K) -> MapEntry[K, V]:
        h = hash(k)
        e = self.buckets[self.slot(h, self.buckets.length)]
        while e != null:
            if e.hash == h and e.key == k:
                return e
            e = e.next
        return null

    def has(self, k: K) -> bool:
        return self.find(k) != null

    def get(self, k: K) -> V:
        e = self.find(k)
        if e == null:
            __panic("key not found in map")
        return e.value

    def getOr(self, k: K, fallback: V) -> V:
        e = self.find(k)
        if e == null:
            return fallback
        return e.value

    def put(self, k: K, v: V):
        e = self.find(k)
        if e != null:
            e.value = v
            return
        if self.count >= self.buckets.length * 3 / 4:
            self.resize()
        h = hash(k)
        i = self.slot(h, self.buckets.length)
        n = new MapEntry[K, V](k, v, h)
        n.next = self.buckets[i]
        self.buckets[i] = n
        self.count += 1

    def set(self, k: K, v: V):
        self.put(k, v)

    private def resize(self):
        old = self.buckets
        nb = new Array[MapEntry[K, V]](old.length * 2)
        for b in range(old.length):
            e = old[b]
            while e != null:
                nxt = e.next
                i = self.slot(e.hash, nb.length)
                e.next = nb[i]
                nb[i] = e
                e = nxt
        self.buckets = nb

    def remove(self, k: K) -> bool:
        h = hash(k)
        i = self.slot(h, self.buckets.length)
        prev: MapEntry[K, V] = null
        e = self.buckets[i]
        while e != null:
            if e.hash == h and e.key == k:
                if prev == null:
                    self.buckets[i] = e.next
                else:
                    prev.next = e.next
                self.count -= 1
                return true
            prev = e
            e = e.next
        return false

    def keys(self) -> List[K]:
        out = new List[K]()
        for b in range(self.buckets.length):
            e = self.buckets[b]
            while e != null:
                out.add(e.key)
                e = e.next
        return out

    def values(self) -> List[V]:
        out = new List[V]()
        for b in range(self.buckets.length):
            e = self.buckets[b]
            while e != null:
                out.add(e.value)
                e = e.next
        return out

    def clear(self):
        self.buckets = new Array[MapEntry[K, V]](16)
        self.count = 0
"""

RUNTIME = r'''
declare i32 @printf(ptr, ...)
declare i64 @strlen(ptr)
declare i32 @strcmp(ptr, ptr)
declare i32 @snprintf(ptr, i64, ptr, ...)
declare ptr @calloc(i64, i64)
declare void @free(ptr)
declare void @llvm.memcpy.p0.p0.i64(ptr, ptr, i64, i1)
declare i32 @pthread_create(ptr, ptr, ptr, ptr)
declare i32 @pthread_join(ptr, ptr)
declare i32 @pthread_mutex_init(ptr, ptr)
declare i32 @pthread_mutex_lock(ptr)
declare i32 @pthread_mutex_unlock(ptr)
declare i32 @pthread_mutex_destroy(ptr)
declare i32 @usleep(i32)
declare i32 @dprintf(i32, ptr, ...)
declare void @exit(i32)

; Every heap value (object or string) has a 16-byte header before the pointer
; we hand out: [strong count i64][weak count i64]. All count updates are
; atomic. A negative strong count marks an immortal value (string literals).
; The strong refs collectively hold one implicit weak ref, so the memory is
; freed only when both counts are gone. While an object's drop runs, the
; strong count holds a large sentinel so retain/release inside deinit cannot
; re-trigger the drop; weak upgrade treats it as dead.
@quill_live = global i64 0

define ptr @quill_alloc(i64 %size) {
  %t = add i64 %size, 16
  %m = call ptr @calloc(i64 1, i64 %t)
  store i64 1, ptr %m
  %w = getelementptr i8, ptr %m, i64 8
  store i64 1, ptr %w
  %o = atomicrmw add ptr @quill_live, i64 1 monotonic, align 8
  %p = getelementptr i8, ptr %m, i64 16
  ret ptr %p
}

define void @quill_free(ptr %hdr) {
  %o = atomicrmw sub ptr @quill_live, i64 1 monotonic, align 8
  call void @free(ptr %hdr)
  ret void
}

define void @quill_retain(ptr %p) {
  %isnull = icmp eq ptr %p, null
  br i1 %isnull, label %done, label %chk
chk:
  %h = getelementptr i8, ptr %p, i64 -16
  %rc = load atomic i64, ptr %h monotonic, align 8
  %imm = icmp slt i64 %rc, 0
  br i1 %imm, label %done, label %inc
inc:
  %o = atomicrmw add ptr %h, i64 1 monotonic, align 8
  br label %done
done:
  ret void
}

define void @quill_release_str(ptr %p) {
  %isnull = icmp eq ptr %p, null
  br i1 %isnull, label %done, label %chk
chk:
  %h = getelementptr i8, ptr %p, i64 -16
  %rc = load atomic i64, ptr %h monotonic, align 8
  %imm = icmp slt i64 %rc, 0
  br i1 %imm, label %done, label %dec
dec:
  %o = atomicrmw sub ptr %h, i64 1 acq_rel, align 8
  %z = icmp eq i64 %o, 1
  br i1 %z, label %kill, label %done
kill:
  call void @quill_free(ptr %h)
  br label %done
done:
  ret void
}

define void @quill_release_obj(ptr %p) {
  %isnull = icmp eq ptr %p, null
  br i1 %isnull, label %done, label %dec
dec:
  %h = getelementptr i8, ptr %p, i64 -16
  %o = atomicrmw sub ptr %h, i64 1 acq_rel, align 8
  %z = icmp eq i64 %o, 1
  br i1 %z, label %kill, label %done
kill:
  store atomic i64 1099511627776, ptr %h seq_cst, align 8
  %vt = load ptr, ptr %p
  %drop = load ptr, ptr %vt
  call void %drop(ptr %p)
  store atomic i64 0, ptr %h seq_cst, align 8
  %wp = getelementptr i8, ptr %p, i64 -8
  %ow = atomicrmw sub ptr %wp, i64 1 acq_rel, align 8
  %wz = icmp eq i64 %ow, 1
  br i1 %wz, label %free, label %done
free:
  call void @quill_free(ptr %h)
  br label %done
done:
  ret void
}

define void @quill_weak_retain(ptr %p) {
  %isnull = icmp eq ptr %p, null
  br i1 %isnull, label %done, label %inc
inc:
  %wp = getelementptr i8, ptr %p, i64 -8
  %o = atomicrmw add ptr %wp, i64 1 monotonic, align 8
  br label %done
done:
  ret void
}

define void @quill_weak_release(ptr %p) {
  %isnull = icmp eq ptr %p, null
  br i1 %isnull, label %done, label %dec
dec:
  %wp = getelementptr i8, ptr %p, i64 -8
  %o = atomicrmw sub ptr %wp, i64 1 acq_rel, align 8
  %z = icmp eq i64 %o, 1
  br i1 %z, label %kill, label %done
kill:
  %h = getelementptr i8, ptr %p, i64 -16
  call void @quill_free(ptr %h)
  br label %done
done:
  ret void
}

; Weak -> strong: succeeds only if the strong count is positive (and not the
; drop sentinel). Compare-and-swap loop so it cannot race with the last release.
define ptr @quill_weak_upgrade(ptr %p) {
  %isnull = icmp eq ptr %p, null
  br i1 %isnull, label %nil, label %loop
loop:
  %h = getelementptr i8, ptr %p, i64 -16
  %old = load atomic i64, ptr %h monotonic, align 8
  %dead = icmp sle i64 %old, 0
  %big = icmp sge i64 %old, 1099511627776
  %bad = or i1 %dead, %big
  br i1 %bad, label %nil, label %try
try:
  %new = add i64 %old, 1
  %r = cmpxchg ptr %h, i64 %old, i64 %new acq_rel monotonic, align 8
  %ok = extractvalue { i64, i1 } %r, 1
  br i1 %ok, label %good, label %loop
good:
  ret ptr %p
nil:
  ret ptr null
}

; Interface dispatch: vtable slot 1 points to a per-class table of
; { method id, function } entries ending with id -1.
define ptr @quill_find_method(ptr %obj, i64 %id) {
entry:
  %vt = load ptr, ptr %obj
  %itp = getelementptr ptr, ptr %vt, i64 1
  %it = load ptr, ptr %itp
  br label %loop
loop:
  %i = phi i64 [ 0, %entry ], [ %next, %chk ]
  %ep = getelementptr { i64, ptr }, ptr %it, i64 %i
  %eid = load i64, ptr %ep
  %hit = icmp eq i64 %eid, %id
  %end = icmp eq i64 %eid, -1
  %next = add i64 %i, 1
  br i1 %hit, label %found, label %chk
chk:
  br i1 %end, label %missing, label %loop
found:
  %fp = getelementptr { i64, ptr }, ptr %ep, i32 0, i32 1
  %f = load ptr, ptr %fp
  ret ptr %f
missing:
  ret ptr null
}

; ---- exceptions: a per-thread stack of setjmp frames ----
; frame = { prev frame, (padding), jmp_buf at +16 }; @quill_exc holds the thrown
; object (null for a runtime panic, whose message is in @quill_exc_text)
@quill_top = thread_local global ptr null
@quill_exc = thread_local global ptr null
@quill_exc_text = thread_local global ptr null

define void @quill_throw() {
  %f = load ptr, ptr @quill_top
  %none = icmp eq ptr %f, null
  br i1 %none, label %fatal, label %jump
fatal:
  call void @quill_uncaught()
  call void @exit(i32 1)
  unreachable
jump:
  %prev = load ptr, ptr %f
  store ptr %prev, ptr @quill_top
  %jb = getelementptr i8, ptr %f, i64 16
  call void @longjmp(ptr %jb, i32 1)
  unreachable
}

define ptr @quill_exc_msg() {
  %m = load ptr, ptr @quill_exc_text
  store ptr null, ptr @quill_exc_text
  ret ptr %m
}

define void @quill_panic(ptr %msg) {
  store ptr null, ptr @quill_exc
  store ptr %msg, ptr @quill_exc_text
  call void @quill_throw()
  unreachable
}

define void @quill_panic_index(i64 %i, i64 %n) {
  %buf = call ptr @quill_alloc(i64 96)
  %r = call i32 (ptr, i64, ptr, ...) @snprintf(ptr %buf, i64 96, ptr @.fmt.index, i64 %i, i64 %n)
  call void @quill_panic(ptr %buf)
  unreachable
}

; FNV-1a hash of a C string
define i64 @quill_hash_str(ptr %s) {
entry:
  br label %loop
loop:
  %i = phi i64 [ 0, %entry ], [ %i1, %body ]
  %h = phi i64 [ -3750763034362895579, %entry ], [ %h2, %body ]
  %cp = getelementptr i8, ptr %s, i64 %i
  %c = load i8, ptr %cp
  %z = icmp eq i8 %c, 0
  br i1 %z, label %done, label %body
body:
  %cz = zext i8 %c to i64
  %x = xor i64 %h, %cz
  %h2 = mul i64 %x, 1099511628211
  %i1 = add i64 %i, 1
  br label %loop
done:
  ret i64 %h
}

define ptr @quill_concat(ptr %a, ptr %b) {
  %la = call i64 @strlen(ptr %a)
  %lb = call i64 @strlen(ptr %b)
  %s = add i64 %la, %lb
  %t = add i64 %s, 1
  %m = call ptr @quill_alloc(i64 %t)
  call void @llvm.memcpy.p0.p0.i64(ptr %m, ptr %a, i64 %la, i1 false)
  %d = getelementptr i8, ptr %m, i64 %la
  %lb1 = add i64 %lb, 1
  call void @llvm.memcpy.p0.p0.i64(ptr %d, ptr %b, i64 %lb1, i1 false)
  ret ptr %m
}

; ---- threads and mutexes (handles are pthread values stored as int) ----
define i64 @quill_thread_start(ptr %obj) {
  %tid = alloca ptr
  %r = call i32 @pthread_create(ptr %tid, ptr null, ptr @quill_thread_entry, ptr %obj)
  %t = load ptr, ptr %tid
  %i = ptrtoint ptr %t to i64
  ret i64 %i
}

define void @quill_thread_join(i64 %h) {
  %p = inttoptr i64 %h to ptr
  %r = call i32 @pthread_join(ptr %p, ptr null)
  ret void
}

define i64 @quill_mutex_new() {
  %m = call ptr @calloc(i64 1, i64 128)
  %r = call i32 @pthread_mutex_init(ptr %m, ptr null)
  %i = ptrtoint ptr %m to i64
  ret i64 %i
}

define void @quill_mutex_lock(i64 %h) {
  %p = inttoptr i64 %h to ptr
  %r = call i32 @pthread_mutex_lock(ptr %p)
  ret void
}

define void @quill_mutex_unlock(i64 %h) {
  %p = inttoptr i64 %h to ptr
  %r = call i32 @pthread_mutex_unlock(ptr %p)
  ret void
}

define void @quill_mutex_free(i64 %h) {
  %p = inttoptr i64 %h to ptr
  %r = call i32 @pthread_mutex_destroy(ptr %p)
  call void @free(ptr %p)
  ret void
}

define void @quill_sleep_ms(i64 %ms) {
  %us = mul i64 %ms, 1000
  %t = trunc i64 %us to i32
  %r = call i32 @usleep(i32 %t)
  ret void
}
'''

RUNTIME += "\n" + cstr("@.fmt.panic", "error: %s\n") + "\n" + \
    cstr("@.fmt.index", "index %ld out of range (length %ld)") + "\n" + \
    cstr("@.fmt.uncaught", "error: uncaught exception: %s\n") + "\n" + \
    cstr("@.fmt.uncaught0", "error: uncaught exception\n") + "\n"

# setjmp/longjmp: the mingw runtime wants the frame address as a second argument
# of _setjmp, and passing null skips its SEH unwinding, which generated code lacks
RUNTIME += ("declare i32 @_setjmp(ptr, ptr) returns_twice\n" if sys.platform == "win32"
            else "declare i32 @_setjmp(ptr) returns_twice\n") + "declare void @longjmp(ptr, i32) noreturn\n"


def split_top(s):
    out, depth, cur = [], 0, ""
    for ch in s:
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur); cur = ""
        else:
            cur += ch
    return out + [cur]


def parse_type(t):
    """'Map[str,List[int]]' -> ('Map', ['str', 'List[int]'])"""
    i = t.find("[")
    if i < 0:
        return t, []
    return t[:i], split_top(t[i + 1:-1])


def subst_type(t, mp):
    weak = "weak " if t.startswith("weak ") else ""
    base, args = parse_type(t[len(weak):])
    if base in mp and not args:
        return weak + mp[base]
    if not args:
        return t
    return f"{weak}{base}[{','.join(subst_type(a, mp) for a in args)}]"


def subst_node(node, mp):
    """Rewrite every type mention in an AST (in place) using the type-parameter map."""
    if isinstance(node, list):
        return [subst_node(x, mp) for x in node]
    if not isinstance(node, N):
        return node
    if isinstance(node, (VarDecl, FieldDecl)):
        node.type = subst_type(node.type, mp)
    elif isinstance(node, New):
        node.cls = subst_type(node.cls, mp)
    elif isinstance(node, MethodDecl):
        node.params = [(n, subst_type(t, mp)) for n, t in node.params]
        node.ret = subst_type(node.ret, mp)
    elif isinstance(node, ClassDecl):
        node.supers = [subst_type(t, mp) for t in node.supers]
    for f in dataclasses.fields(node):
        setattr(node, f.name, subst_node(getattr(node, f.name), mp))
    return node


def iter_types(node):
    """Yield (type string, line) for every type mentioned in an AST."""
    if isinstance(node, list):
        for x in node:
            yield from iter_types(x)
        return
    if not isinstance(node, N):
        return
    if isinstance(node, (VarDecl, FieldDecl)):
        yield node.type, node.line
    elif isinstance(node, New):
        yield node.cls, node.line
    elif isinstance(node, MethodDecl):
        for _, t in node.params:
            yield t, node.line
        yield node.ret, node.line
    elif isinstance(node, ClassDecl):
        for t in node.supers:
            yield t, node.line
    for f in dataclasses.fields(node):
        yield from iter_types(getattr(node, f.name))


@dataclass
class MethodInfo:
    name: str
    owner: str
    params: list
    ret: str
    static: bool
    decl: MethodDecl
    access: str = "public"
    abstract: bool = False
    is_iface: bool = False      # declared in an interface

    @property
    def symbol(self):
        return f'@"{self.owner}.{self.name}"'


@dataclass
class ClassInfo:
    name: str
    parent: "ClassInfo"
    decl: ClassDecl
    fields: list = field(default_factory=list)    # [(name, type)] incl. inherited
    methods: dict = field(default_factory=dict)   # own methods
    vtable: list = field(default_factory=list)    # [method name] by slot
    interfaces: list = field(default_factory=list)
    supers: set = field(default_factory=set)      # own name + all ancestors
    field_info: dict = field(default_factory=dict)  # field -> (owner, access)
    required: dict = field(default_factory=dict)  # interface method name -> MethodInfo
    elem: str = None                              # element type, for built-in Array[T]

    @property
    def is_interface(self):
        return self.decl.interface

    @property
    def is_abstract(self):
        return self.decl.abstract or self.decl.interface


def hexdouble(x):
    return "0x%016X" % struct.unpack("<Q", struct.pack("<d", x))[0]


class Module:
    def __init__(self, decls):
        self.classes = {}
        self.strings = {}
        self.out = []
        self.templates = {}    # generic class name -> ClassDecl
        self.iface_ids = {}    # interface method name -> dispatch id
        self.iface_sigs = {}
        self.collect(decls)

    # ---- class table ----
    def collect(self, decls):
        for d in decls:
            if d.name in self.classes or d.name in self.templates or d.name in PRIMS or d.name == "Array":
                raise CompileError(f"duplicate or reserved class name {d.name}", d.line)
            if d.tparams:
                self.templates[d.name] = d
            else:
                self.classes[d.name] = ClassInfo(d.name, None, d)
        # instantiate every generic type mentioned anywhere (instances are scanned too)
        work = [ci.decl for ci in self.classes.values()]
        while work:
            d = work.pop()
            for t, line in iter_types(d):
                self.ensure(t, line, work)
        self.built = set()
        for ci in self.classes.values():
            self.build_class(ci)

        # every concrete class must implement all abstract and interface methods
        for ci in self.classes.values():
            try:
                self.check_complete(ci)
            except CompileError as e:
                if e.file is None:
                    e.file = getattr(ci.decl, "file", None)
                raise

    def check_complete(self, ci):
        if ci.is_interface:
            return
        line = ci.decl.line
        if not ci.is_abstract:
            for name in ci.vtable:
                impl = self.find_class_method(ci, name)
                if impl.abstract:
                    raise CompileError(f"class {ci.name} must implement abstract method {impl.owner}.{name}", line)
        for name, im in ci.required.items():
            impl = self.find_class_method(ci, name)
            if impl is None or impl.abstract or impl.static:
                if ci.is_abstract:
                    continue
                raise CompileError(f"class {ci.name} does not implement {im.owner}.{name}", line)
            if impl.access == "private":
                raise CompileError(f"{impl.owner}.{name} implements an interface method, so it cannot be private", impl.decl.line)
            if impl.params != im.params or impl.ret != im.ret:
                raise CompileError(f"{impl.owner}.{name} has a different signature than interface method {im.owner}.{name}", impl.decl.line)

    def build_class(self, ci, stack=()):
        try:
            self.build_class_body(ci, stack)
        except CompileError as e:
            if e.file is None:
                e.file = getattr(ci.decl, "file", None)
            raise

    def build_class_body(self, ci, stack=()):
        if ci.name in self.built:
            return
        if ci.name in stack:
            raise CompileError(f"cyclic inheritance involving {ci.name}", ci.decl.line)
        d = ci.decl
        sup = []
        for n in d.supers:
            if n not in self.classes:
                raise CompileError(f"unknown class or interface {n}", d.line)
            sup.append(self.classes[n])
            self.build_class(sup[-1], stack + (ci.name,))
        parents = [c for c in sup if not c.is_interface]
        ifaces = [c for c in sup if c.is_interface]
        if d.interface and parents:
            raise CompileError("an interface can only extend interfaces", d.line)
        if len(parents) > 1:
            raise CompileError(f"{ci.name} can extend only one class (the rest must be interfaces)", d.line)
        ci.parent = parents[0] if parents else None
        ci.interfaces = ifaces
        ci.supers = {ci.name}.union(*[c.supers for c in sup]) if sup else {ci.name}
        if ci.parent:
            ci.fields = list(ci.parent.fields)
            ci.field_info = dict(ci.parent.field_info)
            ci.vtable = list(ci.parent.vtable)
            ci.required = dict(ci.parent.required)
        for i in ifaces:
            for n, im in i.required.items():
                old = ci.required.get(n)
                if old and (old.params != im.params or old.ret != im.ret):
                    raise CompileError(f"conflicting signatures for interface method {n}", d.line)
                ci.required[n] = im
        if d.interface and d.fields:
            raise CompileError("interfaces cannot have fields", d.line)
        for f in d.fields:
            self.check_type(f.type, f.line)
            if any(f.name == n for n, _ in ci.fields):
                raise CompileError(f"duplicate field {f.name}", f.line)
            ci.fields.append((f.name, f.type))
            ci.field_info[f.name] = (ci.name, f.access)
        for m in d.methods:
            if m.name in ci.methods:
                raise CompileError(f"duplicate method {m.name}", m.line)
            for _, t in m.params:
                self.check_type(t, m.line)
                if self.is_weak(t):
                    raise CompileError("parameters cannot be weak", m.line)
            self.check_type(m.ret, m.line)
            if self.is_weak(m.ret):
                raise CompileError("return types cannot be weak", m.line)
            if m.name == "deinit" and (m.static or m.params or m.ret != "void"):
                raise CompileError("deinit must be an instance method with no parameters and no result", m.line)
            if m.abstract and not d.abstract and not d.interface:
                raise CompileError(f"abstract method {m.name} in non-abstract class {ci.name}", m.line)
            if m.abstract and (m.static or m.access == "private"):
                raise CompileError("abstract methods cannot be static or private", m.line)
            if d.interface and (m.name in ("init", "deinit") or m.access == "private"):
                raise CompileError("interfaces can only declare public instance methods", m.line)
            mi = MethodInfo(m.name, ci.name, m.params, m.ret, m.static, m,
                            m.access, m.abstract, d.interface)
            ci.methods[m.name] = mi
            if d.interface:
                old = self.iface_sigs.setdefault(m.name, (m.params, m.ret))
                if old != (m.params, m.ret):
                    raise CompileError(f"interface method name {m.name} is declared with different signatures", m.line)
                self.iface_ids.setdefault(m.name, len(self.iface_ids))
                ci.required[m.name] = mi
                continue
            if m.static or m.name in ("init", "deinit"):
                continue
            prev = self.find_class_method(ci.parent, m.name) if ci.parent else None
            if prev and prev.access == "private":
                prev = None            # private methods are not inherited or overridden
            if m.access == "private":
                if prev:
                    raise CompileError(f"{ci.name}.{m.name} cannot reduce the visibility of the method it overrides", m.line)
                continue               # private methods are non-virtual
            if prev:
                if prev.static or prev.params != m.params or prev.ret != m.ret:
                    raise CompileError(f"{ci.name}.{m.name} has a different signature than the method it overrides", m.line)
            elif m.name not in ci.vtable:
                ci.vtable.append(m.name)
        self.built.add(ci.name)

    def instantiate(self, t, line):
        """Create a generic instance such as List[int] while code is being generated
        (literals only learn their element types then)."""
        if t in self.classes:
            return
        before = set(self.classes)
        work = []
        self.ensure(t, line, work)
        while work:
            d = work.pop()
            for tt, ln in iter_types(d):
                self.ensure(tt, ln, work)
        for name in [n for n in self.classes if n not in before]:
            self.build_class(self.classes[name])

    def ensure(self, t, line, work):
        """Instantiate a generic type like List[int] (and its arguments) if needed."""
        t = t[5:] if t.startswith("weak ") else t
        if "[" not in t:
            return
        base, args = parse_type(t)
        for a in args:
            if a.startswith("weak "):
                raise CompileError("type arguments cannot be weak", line)
            self.ensure(a, line, work)
        if t in self.classes:
            return
        if base == "Array":
            if len(args) != 1 or args[0] == "void" or not (args[0] in PRIMS or args[0] in self.classes):
                raise CompileError(f"invalid element type in {t}", line)
            ci = ClassInfo(t, None, ClassDecl(t, [], [], [], False, False, line=line))
            ci.elem = args[0]
            self.classes[t] = ci
            return
        tpl = self.templates.get(base)
        if not tpl:
            raise CompileError(f"unknown generic class {base}", line)
        if len(args) != len(tpl.tparams):
            raise CompileError(f"{base} takes {len(tpl.tparams)} type argument(s), got {len(args)}", line)
        decl = subst_node(copy.deepcopy(tpl), dict(zip(tpl.tparams, args)))
        decl.name, decl.tparams = t, []
        self.classes[t] = ClassInfo(t, None, decl)
        work.append(decl)

    def array_elem(self, t):
        ci = self.classes.get(t)
        return ci.elem if ci else None

    def is_weak(self, t):
        return t.startswith("weak ")

    def check_type(self, t, line):
        if self.is_weak(t):
            if t[5:] not in self.classes:
                raise CompileError("'weak' applies only to class types", line)
            return
        if t not in PRIMS and t not in self.classes:
            raise CompileError(f"unknown type {t}", line)

    def find_class_method(self, ci, name):
        """Nearest definition along the superclass chain (never an interface)."""
        while ci:
            if name in ci.methods:
                return ci.methods[name]
            ci = ci.parent
        return None

    def find_method(self, ci, name):
        """Class chain first, then the interfaces the class promises."""
        return self.find_class_method(ci, name) or ci.required.get(name)

    def is_subclass(self, a, b):
        """True if a is b, extends b, or implements b."""
        return a in self.classes and b in self.classes[a].supers

    def concrete(self, ci):
        return not ci.is_abstract

    def is_class(self, t):
        return t in self.classes

    def is_ref(self, t):
        return t == "str" or t in self.classes

    def uncaught_fn(self, concrete):
        """Reports an exception nobody caught: a panic message, an Error's message,
        or just the fact that something was thrown."""
        errs = [ci for ci in concrete if ci.elem is None and self.is_subclass(ci.name, "Error")]
        L = ["define void @quill_uncaught() {",
             "  %e = load ptr, ptr @quill_exc",
             "  %isn = icmp eq ptr %e, null",
             "  br i1 %isn, label %panic, label %obj",
             "panic:",
             "  %pm = load ptr, ptr @quill_exc_text",
             "  %r0 = call i32 (i32, ptr, ...) @dprintf(i32 2, ptr @.fmt.panic, ptr %pm)",
             "  ret void",
             "obj:",
             "  %vt = load ptr, ptr %e"]
        acc = "false"
        for i, ci in enumerate(errs):
            L.append(f'  %h{i} = icmp eq ptr %vt, @"vtable.{ci.name}"')
            L.append(f"  %a{i} = or i1 {acc}, %h{i}")
            acc = f"%a{i}"
        L += [f"  br i1 {acc}, label %err, label %other",
              "err:",
              '  %mp = getelementptr %"Error", ptr %e, i32 0, i32 1',
              "  %m = load ptr, ptr %mp",
              "  %mn = icmp eq ptr %m, null",
              f"  %ms = select i1 %mn, ptr {self.string('(no message)')}, ptr %m",
              "  %r1 = call i32 (i32, ptr, ...) @dprintf(i32 2, ptr @.fmt.uncaught, ptr %ms)",
              "  ret void",
              "other:",
              "  %r2 = call i32 (i32, ptr, ...) @dprintf(i32 2, ptr @.fmt.uncaught0)",
              "  ret void",
              "}"]
        return "\n".join(L)

    def drop_fn(self, ci):
        if ci.elem is not None:
            return self.array_drop_fn(ci)
        L = [f'define void @"drop.{ci.name}"(ptr %o) {{']
        d = self.find_class_method(ci, "deinit")
        if d:
            L.append(f"  call void {d.symbol}(ptr %o)")
        for i, (_, t) in enumerate(ci.fields):
            if self.is_ref(t) or self.is_weak(t):
                fn = ("quill_weak_release" if self.is_weak(t)
                      else "quill_release_str" if t == "str" else "quill_release_obj")
                L.append(f'  %p{i} = getelementptr %"{ci.name}", ptr %o, i32 0, i32 {i + 1}')
                L.append(f"  %v{i} = load ptr, ptr %p{i}")
                L.append(f"  call void @{fn}(ptr %v{i})")
        L.append("  ret void\n}")
        return "\n".join(L)

    def array_drop_fn(self, ci):
        name, et = ci.name, ci.elem
        if not self.is_ref(et):
            return f'define void @"drop.{name}"(ptr %o) {{\n  ret void\n}}'
        fn = "quill_release_str" if et == "str" else "quill_release_obj"
        return f"""define void @"drop.{name}"(ptr %o) {{
entry:
  %lp = getelementptr i8, ptr %o, i64 8
  %n = load i64, ptr %lp
  %base = getelementptr i8, ptr %o, i64 16
  br label %loop
loop:
  %i = phi i64 [ 0, %entry ], [ %i1, %body ]
  %c = icmp slt i64 %i, %n
  br i1 %c, label %body, label %done
body:
  %ep = getelementptr ptr, ptr %base, i64 %i
  %v = load ptr, ptr %ep
  call void @{fn}(ptr %v)
  %i1 = add i64 %i, 1
  br label %loop
done:
  ret void
}}"""

    def llty(self, t):
        return PRIMS[t] if t in PRIMS else "ptr"

    def string(self, s):
        if s not in self.strings:
            self.strings[s] = f"@.str.{len(self.strings)}"
        return f"getelementptr inbounds (i8, ptr {self.strings[s]}, i64 16)"

    # ---- emission ----
    def generate(self):
        main_ci = self.classes.get("Main")
        mm = main_ci.methods.get("main") if main_ci else None
        if not mm or not mm.static or mm.params:
            raise CompileError("program needs: class Main with 'static def main()'", 1)
        if mm.ret not in ("void", "int"):
            raise CompileError("Main.main must return void or int", mm.decl.line)

        funcs = []
        seen = set()
        while True:
            todo = [ci for ci in list(self.classes.values()) if ci.name not in seen]
            if not todo:
                break
            for ci in todo:
                seen.add(ci.name)
                for mi in ci.methods.values():
                    if not mi.abstract:
                        funcs.append(FuncGen(self, ci, mi).generate())

        out = [RUNTIME]
        objects = [ci for ci in self.classes.values() if not ci.is_interface]
        concrete = [ci for ci in objects if self.concrete(ci)]
        for ci in objects:
            body = "ptr, i64" if ci.elem is not None else ", ".join(["ptr"] + [self.llty(t) for _, t in ci.fields])
            out.append(f'%"{ci.name}" = type {{ {body} }}')
        for ci in concrete:
            # vtable: [drop, itable, methods...]; itable: [{method id, fn}..., {-1, null}]
            entries = [f'{{ i64, ptr }} {{ i64 {self.iface_ids[n]}, ptr {self.find_class_method(ci, n).symbol} }}'
                       for n in ci.required]
            entries.append("{ i64, ptr } { i64 -1, ptr null }")
            out.append(f'@"itable.{ci.name}" = constant [{len(entries)} x {{ i64, ptr }}] [{", ".join(entries)}]')
            slots = [f'ptr @"drop.{ci.name}"', f'ptr @"itable.{ci.name}"']
            for name in ci.vtable:
                slots.append(f"ptr {self.find_class_method(ci, name).symbol}")
            out.append(f'@"vtable.{ci.name}" = constant [{len(slots)} x ptr] [{", ".join(slots)}]')
        out.extend(funcs)
        out.append(self.uncaught_fn(concrete))
        for ci in concrete:
            out.append(self.drop_fn(ci))
        slot = self.classes["Thread"].vtable.index("run") + 2   # slots 0, 1 = drop, itable
        out.append(f"""define ptr @quill_thread_entry(ptr %obj) {{
  %vt = load ptr, ptr %obj
  %sp = getelementptr ptr, ptr %vt, i64 {slot}
  %fn = load ptr, ptr %sp
  call void %fn(ptr %obj)
  call void @quill_release_obj(ptr %obj)
  ret ptr null
}}""")
        ret = "i32"
        call = f'  %r = call i64 {mm.symbol}()\n  %c = trunc i64 %r to i32\n  ret i32 %c' if mm.ret == "int" \
            else f'  call void {mm.symbol}()\n  ret i32 0'
        out.append(f"define i32 @main() {{\n{call}\n}}")
        # string constants last (names are assigned while generating)
        consts = []
        for s, name in self.strings.items():
            data = s.encode("utf-8") + b"\0"
            enc = "".join(chr(b) if 32 <= b < 127 and b not in (34, 92) else f"\\{b:02X}" for b in data)
            consts.append(f'{name} = private unnamed_addr constant {{ i64, i64, [{len(data)} x i8] }} {{ i64 -1, i64 1, [{len(data)} x i8] c"{enc}" }}')
        return "\n".join(consts + out) + "\n"


class FuncGen:
    def __init__(self, mod, ci, mi):
        self.mod, self.ci, self.mi = mod, ci, mi
        self.lines, self.allocas = [], []
        self.n = 0
        self.scopes = [{}]
        self.terminated = False
        self.loops = []
        self.tries = []          # frames of the try blocks being compiled, innermost last
        self.uses_try = False
        self.fresh = set()   # temps that hold an owned (+1) reference

    # ---- low-level helpers ----
    def tmp(self):
        self.n += 1
        return f"%t{self.n}"

    def label(self, base):
        self.n += 1
        return f"{base}.{self.n}"

    def emit(self, s):
        if self.terminated:
            self.place(self.label("dead"))
        self.lines.append("  " + s)

    def place(self, lbl):
        self.lines.append(f"{lbl}:")
        self.terminated = False

    def br(self, lbl):
        if not self.terminated:
            self.lines.append(f"  br label %{lbl}")
            self.terminated = True

    def condbr(self, c, a, b):
        self.emit(f"br i1 {c}, label %{a}, label %{b}")
        self.terminated = True

    def alloca(self, ty, hint):
        self.n += 1
        name = f"%{hint}.{self.n}"
        self.allocas.append(f"  {name} = alloca {ty}")
        return name

    def op(self, text):
        t = self.tmp()
        self.emit(f"{t} = {text}")
        return t

    def err(self, msg, node):
        raise CompileError(msg, node.line, getattr(self.ci.decl, "file", None))

    # ---- reference counting ----
    # Ownership model: locals/params own one reference. Expression results are
    # either "borrowed" (loaded from a variable/field) or "fresh" (an owned +1
    # temp: new, concat, call results). Fresh temps must be consumed or released.
    def is_ref(self, t):
        return self.mod.is_ref(t)

    def retain(self, v):
        self.emit(f"call void @quill_retain(ptr {v})")

    def release(self, v, t):
        fn = "quill_release_str" if t == "str" else "quill_release_obj"
        self.emit(f"call void @{fn}(ptr {v})")

    def consume(self, v, t):
        """Take ownership of an expression result (retain if it was borrowed)."""
        if self.is_ref(t) and v in self.fresh:
            self.fresh.discard(v)
        elif self.is_ref(t) and v != "null" and not v.startswith("getelementptr"):
            self.retain(v)
        return v

    def release_fresh(self, v, t):
        if v in self.fresh and self.is_ref(t):
            self.fresh.discard(v)
            self.release(v, t)

    def upgrade(self, v, ty):
        """Read a weak slot: yields a fresh strong reference, or null if dead."""
        r = self.op(f"call ptr @quill_weak_upgrade(ptr {v})")
        self.fresh.add(r)
        return r, ty[5:]

    def release_scope(self, sc):
        for ptr, ty in reversed(list(sc.values())):
            if self.mod.is_weak(ty):
                self.emit(f"call void @quill_weak_release(ptr {self.op(f'load ptr, ptr {ptr}')})")
            elif self.is_ref(ty):
                self.release(self.op(f"load ptr, ptr {ptr}"), ty)

    def release_from(self, depth):
        if not self.terminated:
            for sc in reversed(self.scopes[depth:]):
                self.release_scope(sc)

    # ---- scopes ----
    def lookup(self, name):
        for sc in reversed(self.scopes):
            if name in sc:
                return sc[name]

    def declare(self, name, ty, node):
        if self.lookup(name):
            self.err(f"variable {name} is already defined", node)
        ptr = self.alloca(self.mod.llty(ty), name)
        self.scopes[-1][name] = (ptr, ty)
        return ptr

    # ---- types ----
    def assignable(self, frm, to):
        if frm == to or (frm == "int" and to == "float"):
            return True
        if frm == "null":
            return to == "str" or self.mod.is_class(to)
        return self.mod.is_class(frm) and self.mod.is_class(to) and self.mod.is_subclass(frm, to)

    def coerce(self, val, frm, to, node, what="value"):
        if not self.assignable(frm, to):
            self.err(f"cannot use {frm} as {to} ({what})", node)
        if frm == "int" and to == "float":
            return self.op(f"sitofp i64 {val} to double")
        return "null" if frm == "null" else val

    # ---- function ----
    def generate(self):
        mi, ci = self.mi, self.ci
        params = [] if mi.static else [("self", ci.name)]
        params += mi.params
        sig = ", ".join(f"{self.mod.llty(t)} %p.{n}" for n, t in params)
        ret = self.mod.llty(mi.ret)
        for n, t in params:
            ptr = self.declare(n, t, mi.decl)
            self.lines.append(f"  store {self.mod.llty(t)} %p.{n}, ptr {ptr}")
            if self.is_ref(t):
                self.retain(f"%p.{n}")      # callee owns its params (and self)
        self.block(mi.decl.body)
        self.release_from(0)
        if not self.terminated:
            zero = {"void": None, "i64": "0", "double": "0.0", "i1": "false", "ptr": "null"}[ret]
            self.emit("ret void" if ret == "void" else f"ret {ret} {zero}")
        attrs = " optnone noinline" if self.uses_try else ""    # keep locals in memory across longjmp
        return (f'define {ret} {mi.symbol}({sig}){attrs} {{\nentry:\n'
                + "\n".join(self.allocas + self.lines) + "\n}")

    # ---- statements ----
    def block(self, stmts):
        self.scopes.append({})
        for s in stmts:
            getattr(self, "s_" + type(s).__name__)(s)
        self.release_from(len(self.scopes) - 1)
        self.scopes.pop()

    def s_VarDecl(self, s):
        self.mod.check_type(s.type, s.line)
        if s.type == "void":
            self.err("variable cannot be void", s)
        if self.mod.is_weak(s.type):
            val = "null"
            if s.init is not None:
                v, t = self.expr(s.init)
                val = self.coerce(v, t, s.type[5:], s, "initializer")
                if val != "null":
                    self.emit(f"call void @quill_weak_retain(ptr {val})")
                self.release_fresh(v, t)
            ptr = self.declare(s.name, s.type, s)
            self.emit(f"store ptr {val}, ptr {ptr}")
            return
        val = None
        if s.init is not None:
            v, t = self.expr_want(s.init, s.type)
            val = self.coerce(self.consume(v, t), t, s.type, s, "initializer")
        ptr = self.declare(s.name, s.type, s)
        lt = self.mod.llty(s.type)
        zero = {"i64": "0", "double": "0.0", "i1": "false", "ptr": "null"}[lt]
        self.emit(f"store {lt} {val if val is not None else zero}, ptr {ptr}")

    def s_Assign(self, s):
        if isinstance(s.target, Index):
            return self.assign_index(s)
        if isinstance(s.target, Name) and not self.lookup(s.target.id):
            v, t = self.expr(s.value)           # first assignment declares + infers type
            if t in ("null", "void"):
                self.err(f"cannot infer type of {s.target.id}", s)
            self.consume(v, t)
            ptr = self.declare(s.target.id, t, s)
            self.emit(f"store {self.mod.llty(t)} {v}, ptr {ptr}")
            return
        v, t = self.expr_want(s.value, self.peek_type(s.target))   # value first, then the target
        self.consume(v, t)
        ptr, ty, ov, ot = self.lvalue(s.target)
        if self.mod.is_weak(ty):
            # weak slot: take a weak ref on the value, then drop the strong +1 we hold
            v = self.coerce(v, t, ty[5:], s, "assignment")
            old = self.op(f"load ptr, ptr {ptr}")
            if v != "null":
                self.emit(f"call void @quill_weak_retain(ptr {v})")
            self.emit(f"store ptr {v}, ptr {ptr}")
            self.emit(f"call void @quill_weak_release(ptr {old})")
            if v != "null":
                self.release(v, t)
            if ov:
                self.release_fresh(ov, ot)
            return
        v = self.coerce(v, t, ty, s, "assignment")
        lt = self.mod.llty(ty)
        old = self.op(f"load ptr, ptr {ptr}") if self.is_ref(ty) else None
        self.emit(f"store {lt} {v}, ptr {ptr}")
        if old:
            self.release(old, ty)
        if ov:
            self.release_fresh(ov, ot)

    def s_ExprStmt(self, s):
        v, t = self.expr(s.e)
        self.release_fresh(v, t)

    def s_Block(self, s):
        self.block(s.body)

    def s_Pass(self, s):
        pass

    def s_Return(self, s):
        want = self.mi.ret
        if s.value is None:
            if want != "void":
                self.err(f"must return a {want}", s)
            self.leave(0, 0)
            if not self.terminated:
                self.emit("ret void")
        else:
            if want == "void":
                self.err("void method cannot return a value", s)
            v, t = self.expr_want(s.value, want)
            v = self.coerce(self.consume(v, t), t, want, s, "return value")
            self.leave(0, 0)
            if not self.terminated:
                self.emit(f"ret {self.mod.llty(want)} {v}")
        self.terminated = True

    def s_If(self, s):
        c = self.cond(s.cond)
        then, end = self.label("if.then"), self.label("if.end")
        els = self.label("if.else") if s.orelse else end
        self.condbr(c, then, els)
        self.place(then); self.block(s.then); self.br(end)
        if s.orelse:
            self.place(els); self.block(s.orelse); self.br(end)
        self.place(end)

    def s_While(self, s):
        c_l, b_l, e_l = self.label("while.cond"), self.label("while.body"), self.label("while.end")
        self.br(c_l); self.place(c_l)
        self.condbr(self.cond(s.cond), b_l, e_l)
        self.place(b_l)
        self.loops.append((c_l, e_l, len(self.scopes), len(self.tries))); self.block(s.body); self.loops.pop()
        self.br(c_l); self.place(e_l)

    def s_ForRange(self, s):
        sv, st = self.expr(s.start)
        ev, et = self.expr(s.end)
        if st != "int" or et != "int":
            self.err("range bounds must be int", s)
        self.scopes.append({})
        ptr = self.declare(s.var, "int", s)
        self.emit(f"store i64 {sv}, ptr {ptr}")
        c_l, b_l, i_l, e_l = (self.label(x) for x in ("for.cond", "for.body", "for.inc", "for.end"))
        self.br(c_l); self.place(c_l)
        cur = self.op(f"load i64, ptr {ptr}")
        self.condbr(self.op(f"icmp slt i64 {cur}, {ev}"), b_l, e_l)
        self.place(b_l)
        self.loops.append((i_l, e_l, len(self.scopes), len(self.tries))); self.block(s.body); self.loops.pop()
        self.br(i_l); self.place(i_l)
        cur = self.op(f"load i64, ptr {ptr}")
        nxt = self.op(f"add i64 {cur}, 1")
        self.emit(f"store i64 {nxt}, ptr {ptr}")
        self.br(c_l); self.place(e_l)
        self.scopes.pop()

    def release_range(self, lo, hi, scopes):
        for sc in reversed(scopes[lo:hi]):
            self.release_scope(sc)

    def leave(self, try_depth, scope_depth):
        """Control leaves early (return, break, continue): release the scopes it
        skips, unlink the try frames above `try_depth` and run their finally blocks,
        innermost first. A finally block may itself end the flow (return, throw)."""
        if self.terminated:
            return
        scopes, tries = self.scopes, self.tries
        hi = len(scopes)
        for k in range(len(tries) - 1, try_depth - 1, -1):
            frame, final, sd = tries[k]
            self.release_range(sd, hi, scopes)
            hi = sd
            prev = self.op(f"load ptr, ptr {frame}")
            self.emit(f"store ptr {prev}, ptr @quill_top")
            if final is not None:
                self.scopes, self.tries = scopes[:sd], tries[:k]
                self.block(final)
                self.scopes, self.tries = scopes, tries
                if self.terminated:
                    return
        self.release_range(scope_depth, hi, scopes)

    def s_Throw(self, s):
        v, t = self.expr(s.value)
        if not self.mod.is_class(t):
            self.err(f"can only throw objects, got {t}", s)
        self.null_check(v, "cannot throw null")
        self.consume(v, t)                       # the exception slot owns the reference
        self.emit(f"store ptr {v}, ptr @quill_exc")
        self.emit("call void @quill_throw()")
        self.emit("unreachable")
        self.terminated = True

    def push_frame(self):
        """Link a new exception frame and run setjmp; returns (frame, i1 'first time')."""
        self.uses_try = True
        frame = self.alloca("[66 x i64], align 16", "exc.frame")
        prev = self.op("load ptr, ptr @quill_top")
        self.emit(f"store ptr {prev}, ptr {frame}")
        self.emit(f"store ptr {frame}, ptr @quill_top")
        jb = self.op(f"getelementptr i8, ptr {frame}, i64 16")
        call = f"call i32 @_setjmp(ptr {jb}, ptr null)" if sys.platform == "win32" else f"call i32 @_setjmp(ptr {jb})"
        r = self.op(call + " returns_twice")
        return frame, self.op(f"icmp eq i32 {r}, 0")

    def s_Try(self, s):
        if s.final is None:
            return self.try_catch(s.body, s.catches, s)
        # try/finally: an outer frame catches whatever escapes, runs the finally
        # block, then throws it again; normal exits and return/break/continue run
        # the same block inline (see leave)
        frame, first = self.push_frame()
        body, handler, end = self.label("fin.body"), self.label("fin.catch"), self.label("fin.end")
        self.condbr(first, body, handler)
        self.place(body)
        self.tries.append((frame, s.final, len(self.scopes)))
        if s.catches:
            self.try_catch(s.body, s.catches, s)
        else:
            self.block(s.body)
        self.tries.pop()
        if not self.terminated:
            back = self.op(f"load ptr, ptr {frame}")
            self.emit(f"store ptr {back}, ptr @quill_top")
            self.block(s.final)
        self.br(end)
        self.place(handler)
        # keep the in-flight exception (object or panic text) safe across the finally block
        exc, txt = self.alloca("ptr", "fin.exc"), self.alloca("ptr", "fin.txt")
        self.emit(f"store ptr {self.op('load ptr, ptr @quill_exc')}, ptr {exc}")
        self.emit(f"store ptr {self.op('load ptr, ptr @quill_exc_text')}, ptr {txt}")
        self.block(s.final)
        if not self.terminated:
            self.emit(f"store ptr {self.op(f'load ptr, ptr {exc}')}, ptr @quill_exc")
            self.emit(f"store ptr {self.op(f'load ptr, ptr {txt}')}, ptr @quill_exc_text")
            self.emit("call void @quill_throw()")
            self.emit("unreachable")
            self.terminated = True
        self.place(end)

    def try_catch(self, body_stmts, catches, s):
        frame, first = self.push_frame()
        body, handler, end = self.label("try.body"), self.label("try.catch"), self.label("try.end")
        self.condbr(first, body, handler)

        self.place(body)
        self.tries.append((frame, None, len(self.scopes)))
        self.block(body_stmts)
        self.tries.pop()
        if not self.terminated:
            back = self.op(f"load ptr, ptr {frame}")
            self.emit(f"store ptr {back}, ptr @quill_top")      # leaving normally: unlink
        self.br(end)

        # a throw already unlinked the frame; pick up the exception
        self.place(handler)
        slot = self.alloca("ptr", "exc")
        self.emit(f"store ptr {self.op('load ptr, ptr @quill_exc')}, ptr {slot}")
        self.emit("store ptr null, ptr @quill_exc")
        panic, have = self.label("exc.panic"), self.label("exc.have")
        self.condbr(self.op(f"icmp eq ptr {self.op(f'load ptr, ptr {slot}')}, null"), panic, have)
        self.place(panic)                        # a runtime panic: wrap its message in an Error
        pv, pt = self.expr(Call(FieldAccess(Name("Error", line=s.line), "fromPanic", line=s.line), [], line=s.line))
        self.consume(pv, pt)
        self.emit(f"store ptr {pv}, ptr {slot}")
        self.br(have)
        self.place(have)
        for cat in catches:
            cls, var, cbody, cline = cat.cls, cat.var, cat.body, cat.line
            nxt, hit = self.label("catch.next"), self.label("catch.hit")
            exc = self.op(f"load ptr, ptr {slot}")
            if cls is not None:
                self.condbr(self.type_test(exc, cls, Name(cls, line=cline)), hit, nxt)
            else:
                self.br(hit)
            self.place(hit)
            self.scopes.append({})
            if var is not None:
                ptr = self.declare(var, cls, Name(var, line=cline))
                self.emit(f"store ptr {exc}, ptr {ptr}")        # the variable now owns it
            else:
                self.release(exc, "obj")
            self.block(cbody)
            self.release_from(len(self.scopes) - 1)
            self.scopes.pop()
            self.br(end)
            self.place(nxt)
        # nothing matched: throw it again to the enclosing handler
        self.emit(f"store ptr {self.op(f'load ptr, ptr {slot}')}, ptr @quill_exc")
        self.emit("call void @quill_throw()")
        self.emit("unreachable")
        self.terminated = True
        self.place(end)

    def s_Break(self, s):
        if not self.loops: self.err("break outside loop", s)
        self.leave(self.loops[-1][3], self.loops[-1][2])
        self.br(self.loops[-1][1])

    def s_Continue(self, s):
        if not self.loops: self.err("continue outside loop", s)
        self.leave(self.loops[-1][3], self.loops[-1][2])
        self.br(self.loops[-1][0])

    # ---- expressions: each returns (llvm operand, quill type) ----
    def expr(self, e):
        return getattr(self, "e_" + type(e).__name__)(e)

    def expr_want(self, e, want):
        """Evaluate e; a list or map literal takes its element types from `want`."""
        if want is not None and isinstance(e, (ListLit, MapLit)):
            return getattr(self, "e_" + type(e).__name__)(e, want)
        return self.expr(e)

    def peek_type(self, target):
        """The declared type of an assignment target, when it is cheap to know."""
        if isinstance(target, Name):
            var = self.lookup(target.id)
            return var[1] if var else None
        if isinstance(target, FieldAccess) and isinstance(target.obj, SelfExpr):
            return dict(self.ci.fields).get(target.name)
        return None

    def common_type(self, types, node, what):
        ts = [t for t in types if t != "null"]
        if not ts:
            return None
        if any(t == "void" for t in ts):
            self.err(f"a {what} cannot hold a void value", node)
        if all(t == ts[0] for t in ts):
            return ts[0]
        if all(t in NUM for t in ts):
            return "float"
        for cand in ts:
            if all(self.assignable(t, cand) for t in ts):
                return cand
        self.err(f"the {what}'s elements have no common type; declare the type you want", node)

    def e_ListLit(self, e, want=None):
        et = None
        if want and parse_type(want)[0] == "List":
            et = parse_type(want)[1][0]
        vals = [self.expr_want(x, et) for x in e.items]
        if et is None:
            et = self.common_type([t for _, t in vals], e, "list")
            if et is None:
                self.err("cannot tell what this list holds; declare the variable's type", e)
        name = f"List[{et}]"
        self.mod.instantiate(name, e.line)
        lst, _ = self.e_New(New(name, [], line=e.line))
        add = self.mod.find_method(self.mod.classes[name], "add")
        for (v, t), x in zip(vals, e.items):
            cv = self.coerce(v, t, et, x, "list element")
            self.emit(f"call void {add.symbol}(ptr {lst}, {self.mod.llty(et)} {cv})")
            self.release_fresh(v, t)
        return lst, name

    def e_MapLit(self, e, want=None):
        kt = vt = None
        if want and parse_type(want)[0] == "Map":
            kt, vt = parse_type(want)[1]
        ks = [self.expr_want(x, kt) for x in e.keys]
        vs = [self.expr_want(x, vt) for x in e.vals]
        if kt is None:
            kt = self.common_type([t for _, t in ks], e, "map")
            vt = self.common_type([t for _, t in vs], e, "map")
            if kt is None or vt is None:
                self.err("cannot tell what this map holds; declare the variable's type", e)
        name = f"Map[{kt},{vt}]"
        self.mod.instantiate(name, e.line)
        mp, _ = self.e_New(New(name, [], line=e.line))
        put = self.mod.find_method(self.mod.classes[name], "put")
        for (k, ktype), (v, vtype), kx, vx in zip(ks, vs, e.keys, e.vals):
            ck = self.coerce(k, ktype, kt, kx, "map key")
            cv = self.coerce(v, vtype, vt, vx, "map value")
            self.emit(f"call void {put.symbol}(ptr {mp}, {self.mod.llty(kt)} {ck}, {self.mod.llty(vt)} {cv})")
            self.release_fresh(k, ktype)
            self.release_fresh(v, vtype)
        return mp, name

    def cond(self, e):
        v, t = self.expr(e)
        if t != "bool":
            self.err(f"condition must be bool, got {t}", e)
        return v

    def e_IntLit(self, e): return str(e.v), "int"
    def e_FloatLit(self, e): return hexdouble(e.v), "float"
    def e_BoolLit(self, e): return ("true" if e.v else "false"), "bool"
    def e_NullLit(self, e): return "null", "null"
    def e_StrLit(self, e): return self.mod.string(e.v), "str"

    def e_SelfExpr(self, e):
        if self.mi.static:
            self.err("'self' used in a static method", e)
        return self.e_Name(Name("self", line=e.line))

    def e_Name(self, e):
        var = self.lookup(e.id)
        if not var:
            self.err(f"undefined variable {e.id}", e)
        ptr, ty = var
        val = self.op(f"load {self.mod.llty(ty)}, ptr {ptr}")
        if self.mod.is_weak(ty):
            return self.upgrade(val, ty)
        return val, ty

    def e_Unary(self, e):
        v, t = self.expr(e.e)
        if e.op == "not":
            if t != "bool": self.err("'not' needs a bool", e)
            return self.op(f"xor i1 {v}, true"), "bool"
        if t == "int": return self.op(f"sub i64 0, {v}"), "int"
        if t == "float": return self.op(f"fneg double {v}"), "float"
        self.err(f"cannot negate {t}", e)

    def e_Binary(self, e):
        if e.op in ("and", "or"):
            return self.short_circuit(e)
        l, r = self.expr(e.l), self.expr(e.r)
        (lv, lt), (rv, rt) = l, r
        if e.op in ("==", "!=", "<", "<=", ">", ">="):
            return self.compare(e, lv, lt, rv, rt)
        if e.op == "+" and lt == "str" and rt == "str":
            self.null_check(lv, "null string (concatenation)")
            self.null_check(rv, "null string (concatenation)")
            r = self.op(f"call ptr @quill_concat(ptr {lv}, ptr {rv})")
            self.release_fresh(lv, lt); self.release_fresh(rv, rt)
            self.fresh.add(r)
            return r, "str"
        if lt not in NUM or rt not in NUM:
            self.err(f"operator {e.op} not supported for {lt} and {rt}", e)
        if "float" in (lt, rt):
            lv, rv = self.coerce(lv, lt, "float", e), self.coerce(rv, rt, "float", e)
            ins = {"+": "fadd", "-": "fsub", "*": "fmul", "/": "fdiv", "%": "frem"}[e.op]
            return self.op(f"{ins} double {lv}, {rv}"), "float"
        ins = {"+": "add", "-": "sub", "*": "mul", "/": "sdiv", "%": "srem"}[e.op]
        return self.op(f"{ins} i64 {lv}, {rv}"), "int"

    def compare(self, e, lv, lt, rv, rt):
        op = e.op
        if lt in NUM and rt in NUM:
            if "float" in (lt, rt):
                lv, rv = self.coerce(lv, lt, "float", e), self.coerce(rv, rt, "float", e)
                p = {"<": "olt", "<=": "ole", ">": "ogt", ">=": "oge", "==": "oeq", "!=": "une"}[op]
                return self.op(f"fcmp {p} double {lv}, {rv}"), "bool"
            p = {"<": "slt", "<=": "sle", ">": "sgt", ">=": "sge", "==": "eq", "!=": "ne"}[op]
            return self.op(f"icmp {p} i64 {lv}, {rv}"), "bool"
        if op not in ("==", "!="):
            self.err(f"cannot order {lt} and {rt}", e)
        p = "eq" if op == "==" else "ne"
        if lt == rt == "bool":
            return self.op(f"icmp {p} i1 {lv}, {rv}"), "bool"
        if lt == rt == "str":
            c = self.op(f"call i32 @strcmp(ptr {lv}, ptr {rv})")
            r = self.op(f"icmp {p} i32 {c}, 0")
            self.release_fresh(lv, lt); self.release_fresh(rv, rt)
            return r, "bool"
        if self.assignable(lt, rt) or self.assignable(rt, lt):
            r = self.op(f"icmp {p} ptr {lv}, {rv}")
            self.release_fresh(lv, lt); self.release_fresh(rv, rt)
            return r, "bool"
        self.err(f"cannot compare {lt} and {rt}", e)

    def type_test(self, v, cls, node):
        """i1: v is non-null and its dynamic class is cls or a subclass/implementer."""
        if cls not in self.mod.classes or self.mod.classes[cls].elem is not None:
            self.err(f"unknown class {cls}", node)
        impls = [ci for ci in self.mod.classes.values()
                 if not ci.is_interface and self.mod.concrete(ci) and ci.elem is None
                 and self.mod.is_subclass(ci.name, cls)]
        res = self.alloca("i1", "io")
        self.emit(f"store i1 false, ptr {res}")
        nn, chk, end = self.label("io.nn"), self.label("io.chk"), self.label("io.end")
        self.condbr(self.op(f"icmp ne ptr {v}, null"), nn, end)
        self.place(nn)
        vt = self.op(f"load ptr, ptr {v}")
        acc = "false"
        for ci in impls:
            hit = self.op(f'icmp eq ptr {vt}, @"vtable.{ci.name}"')
            acc = self.op(f"or i1 {acc}, {hit}")
        self.emit(f"store i1 {acc}, ptr {res}")
        self.br(end)
        self.place(end)
        return self.op(f"load i1, ptr {res}")

    def e_InstanceOf(self, e):
        v, t = self.expr(e.e)
        if not self.mod.is_class(t):
            self.err(f"instanceof needs an object, got {t}", e)
        r = self.type_test(v, e.cls, e)
        self.release_fresh(v, t)
        return r, "bool"

    def e_Cast(self, e):
        v, t = self.expr(e.e)
        if not self.mod.is_class(t):
            self.err(f"cannot cast {t} to {e.cls}", e)
        if e.cls not in self.mod.classes:
            self.err(f"unknown class {e.cls}", e)
        either_iface = self.mod.classes[t].is_interface or self.mod.classes[e.cls].is_interface
        if not (either_iface or self.mod.is_subclass(t, e.cls) or self.mod.is_subclass(e.cls, t)):
            self.err(f"cannot cast {t} to {e.cls}: the types are unrelated", e)
        isnull = self.op(f"icmp eq ptr {v}, null")
        ok = self.op(f"or i1 {isnull}, {self.type_test(v, e.cls, e)}")   # null casts to null
        self.panic_unless(ok, f"invalid cast to {e.cls}")
        return v, e.cls          # same reference, same ownership, narrower static type

    def short_circuit(self, e):
        slot = self.alloca("i1", "sc")
        lv = self.cond(e.l)
        self.emit(f"store i1 {lv}, ptr {slot}")
        rhs, end = self.label("sc.rhs"), self.label("sc.end")
        if e.op == "and": self.condbr(lv, rhs, end)
        else: self.condbr(lv, end, rhs)
        self.place(rhs)
        self.emit(f"store i1 {self.cond(e.r)}, ptr {slot}")
        self.br(end); self.place(end)
        return self.op(f"load i1, ptr {slot}"), "bool"

    # fields
    def field_ptr(self, e, write=False):
        ov, ot = self.expr(e.obj)
        if not self.mod.is_class(ot):
            self.err(f"{ot} has no fields", e)
        self.null_check(ov, "null pointer dereference")
        ci = self.mod.classes[ot]
        if ci.elem is not None:
            if e.name != "length":
                self.err(f"{ot} has no field {e.name} (arrays have only 'length')", e)
            if write:
                self.err("array length is read-only", e)
            return self.op(f'getelementptr %"{ot}", ptr {ov}, i32 0, i32 1'), "int", ov, ot
        for i, (n, t) in enumerate(ci.fields):
            if n == e.name:
                owner, access = ci.field_info[n]
                if access == "private" and self.ci.name != owner:
                    self.err(f"field {n} is private to {owner}", e)
                return self.op(f'getelementptr %"{ot}", ptr {ov}, i32 0, i32 {i + 1}'), t, ov, ot
        self.err(f"class {ot} has no field {e.name}", e)

    def lvalue(self, t):
        if isinstance(t, Name):
            var = self.lookup(t.id)
            if not var: self.err(f"undefined variable {t.id}", t)
            return var[0], var[1], None, None
        return self.field_ptr(t, write=True)

    def e_FieldAccess(self, e):
        ptr, ty, ov, ot = self.field_ptr(e)
        val = self.op(f"load {self.mod.llty(ty)}, ptr {ptr}")
        if self.mod.is_weak(ty):
            val, ty = self.upgrade(val, ty)
        elif ov in self.fresh and self.is_ref(ty):   # field of a temporary object:
            self.retain(val)                         # keep it alive past the temp
            self.fresh.add(val)
        self.release_fresh(ov, ot)
        return val, ty

    # calls
    def e_New(self, e):
        if e.cls not in self.mod.classes:
            self.err(f"unknown class {e.cls}", e)
        ci = self.mod.classes[e.cls]
        if ci.elem is not None:
            return self.new_array(ci, e)
        if ci.is_abstract:
            self.err(f"cannot instantiate {'interface' if ci.is_interface else 'abstract class'} {ci.name}", e)
        size_p = self.op(f'getelementptr %"{ci.name}", ptr null, i32 1')
        size = self.op(f"ptrtoint ptr {size_p} to i64")
        obj = self.op(f"call ptr @quill_alloc(i64 {size})")
        self.fresh.add(obj)
        self.emit(f'store ptr @"vtable.{ci.name}", ptr {obj}')
        init = self.mod.find_class_method(ci, "init")
        if init:
            if init.access == "private" and self.ci.name != init.owner:
                self.err(f"constructor of {ci.name} is private", e)
            self.call_args(init, obj, e.args, e)
        elif e.args:
            self.err(f"class {ci.name} has no init, but arguments were given", e)
        return obj, ci.name

    def call_args(self, mi, self_val, args, node, virtual=False, recv_ci=None, iface=False):
        if len(args) != len(mi.params):
            self.err(f"{mi.owner}.{mi.name} takes {len(mi.params)} argument(s), got {len(args)}", node)
        vals = [] if self_val is None else [f"ptr {self_val}"]
        temps = []
        for a, (pn, pt) in zip(args, mi.params):
            v, t = self.expr_want(a, pt)
            vals.append(f"{self.mod.llty(pt)} {self.coerce(v, t, pt, a, 'argument ' + pn)}")
            temps.append((v, pt))
        rt = self.mod.llty(mi.ret)
        if virtual:
            vt = self.op(f"load ptr, ptr {self_val}")
            slot = recv_ci.vtable.index(mi.name) + 2   # slots 0, 1 = drop, itable
            sp = self.op(f"getelementptr ptr, ptr {vt}, i64 {slot}")
            target = self.op(f"load ptr, ptr {sp}")
        elif iface:
            target = self.op(f"call ptr @quill_find_method(ptr {self_val}, i64 {self.mod.iface_ids[mi.name]})")
        else:
            target = mi.symbol
        call = f"call {rt} {target}({', '.join(vals)})"
        if rt == "void":
            self.emit(call)
            res = (None, "void")
        else:
            r = self.op(call)
            if self.is_ref(mi.ret):
                self.fresh.add(r)             # callee returns an owned reference
            res = (r, mi.ret)
        for v, t in temps:
            self.release_fresh(v, t)
        return res

    def e_Call(self, e):
        c = e.callee
        if isinstance(c, Name):
            return self.builtin(e, c.id)
        if not isinstance(c, FieldAccess):
            self.err("only methods and builtins can be called", e)
        # static call: ClassName.method(...)
        if isinstance(c.obj, Name) and not self.lookup(c.obj.id) and c.obj.id in self.mod.classes:
            ci = self.mod.classes[c.obj.id]
            mi = self.mod.find_class_method(ci, c.name)
            if not mi or not mi.static:
                self.err(f"{ci.name} has no static method {c.name}", e)
            self.check_access(mi, e)
            return self.call_args(mi, None, e.args, e)
        ov, ot = self.expr(c.obj)
        return self.call_method(ov, ot, c.name, e.args, e)

    def call_method(self, ov, ot, name, args, node):
        """Call an instance method on an already-evaluated receiver."""
        if not self.mod.is_class(ot):
            self.err(f"cannot call a method on {ot}", node)
        ci = self.mod.classes[ot]
        mi = self.mod.find_method(ci, name)
        if not mi:
            self.err(f"class {ot} has no method {name}", node)
        if mi.static:
            self.err(f"{name} is static; call it as {mi.owner}.{name}(...)", node)
        self.check_access(mi, node)
        self.null_check(ov, f"null pointer dereference (calling {name})")
        res = self.call_args(mi, ov, args, node, recv_ci=ci,
                             virtual=(not mi.is_iface) and name in ci.vtable,
                             iface=mi.is_iface)
        self.release_fresh(ov, ot)
        return res

    # ---- arrays, indexing, for-each ----
    def panic_unless(self, cond, msg):
        good, bad = self.label("chk.ok"), self.label("chk.bad")
        self.condbr(cond, good, bad)
        self.place(bad)
        self.emit(f"call void @quill_panic(ptr {self.mod.string(msg)})")
        self.emit("unreachable")
        self.terminated = True
        self.place(good)

    def null_check(self, v, msg):
        if v == "null":
            self.emit(f"call void @quill_panic(ptr {self.mod.string(msg)})")
            self.emit("unreachable")
            self.terminated = True
            self.place(self.label("after.null"))
            return
        self.panic_unless(self.op(f"icmp ne ptr {v}, null"), msg)

    def bounds_check(self, idx, arr):
        n = self.op(f"load i64, ptr {self.op(f'getelementptr i8, ptr {arr}, i64 8')}")
        good, bad = self.label("idx.ok"), self.label("idx.bad")
        self.condbr(self.op(f"icmp ult i64 {idx}, {n}"), good, bad)   # unsigned: also rejects negatives
        self.place(bad)
        self.emit(f"call void @quill_panic_index(i64 {idx}, i64 {n})")
        self.emit("unreachable")
        self.terminated = True
        self.place(good)

    def elem_ptr(self, arr, idx, et):
        base = self.op(f"getelementptr i8, ptr {arr}, i64 16")
        return self.op(f"getelementptr {self.mod.llty(et)}, ptr {base}, i64 {idx}")

    def new_array(self, ci, e):
        if len(e.args) != 1:
            self.err(f"{ci.name} takes one argument: its length", e)
        nv, nt = self.expr(e.args[0])
        if nt != "int":
            self.err("array length must be int", e)
        self.panic_unless(self.op(f"icmp sge i64 {nv}, 0"), "negative array length")
        size = "1" if ci.elem == "bool" else "8"
        total = self.op(f"add i64 {self.op(f'mul i64 {nv}, {size}')}, 16")
        obj = self.op(f"call ptr @quill_alloc(i64 {total})")
        self.fresh.add(obj)
        self.emit(f'store ptr @"vtable.{ci.name}", ptr {obj}')
        self.emit(f"store i64 {nv}, ptr {self.op(f'getelementptr i8, ptr {obj}, i64 8')}")
        return obj, ci.name

    def e_Index(self, e):
        ov, ot = self.expr(e.obj)
        et = self.mod.array_elem(ot)
        if et is not None:
            iv, it = self.expr(e.index)
            if it != "int":
                self.err("index must be int", e)
            self.null_check(ov, "null pointer dereference (indexing)")
            self.bounds_check(iv, ov)
            val = self.op(f"load {self.mod.llty(et)}, ptr {self.elem_ptr(ov, iv, et)}")
            if ov in self.fresh and self.is_ref(et):      # element of a temporary array
                self.retain(val)
                self.fresh.add(val)
            self.release_fresh(ov, ot)
            return val, et
        if not (self.mod.is_class(ot) and self.mod.find_method(self.mod.classes[ot], "get")):
            self.err(f"{ot} cannot be indexed (it needs a get method)", e)
        return self.call_method(ov, ot, "get", [e.index], e)

    def assign_index(self, s):
        t = s.target
        ov, ot = self.expr(t.obj)
        et = self.mod.array_elem(ot)
        if et is None:
            if not (self.mod.is_class(ot) and self.mod.find_method(self.mod.classes[ot], "set")):
                self.err(f"{ot} does not support index assignment (it needs a set method)", s)
            self.call_method(ov, ot, "set", [t.index, s.value], s)
            return
        iv, it = self.expr(t.index)
        if it != "int":
            self.err("index must be int", s)
        v, vt = self.expr(s.value)
        self.consume(v, vt)
        v = self.coerce(v, vt, et, s, "array element")
        self.null_check(ov, "null pointer dereference (indexing)")
        self.bounds_check(iv, ov)
        p = self.elem_ptr(ov, iv, et)
        old = self.op(f"load ptr, ptr {p}") if self.is_ref(et) else None
        self.emit(f"store {self.mod.llty(et)} {v}, ptr {p}")
        if old:
            self.release(old, et)
        self.release_fresh(ov, ot)

    def e_LenOf(self, e):
        t = self.lookup(e.e.id)[1]
        ci = self.mod.classes.get(t)
        if ci is not None and ci.elem is not None:
            return self.expr(FieldAccess(e.e, "length", line=e.line))
        if ci is None or not (self.mod.find_method(ci, "size") and self.mod.find_method(ci, "get")):
            self.err(f"cannot iterate over {t} (it needs size() and get(i))", e)
        return self.expr(Call(FieldAccess(e.e, "size", line=e.line), [], line=e.line))

    def check_access(self, mi, node):
        if mi.access == "private" and self.ci.name != mi.owner:
            self.err(f"method {mi.name} is private to {mi.owner}", node)

    def e_SuperCall(self, e):
        if self.mi.static:
            self.err("'super' used in a static method", e)
        parent = self.ci.parent
        if not parent:
            self.err(f"{self.ci.name} has no parent class, so 'super' is not available", e)
        mi = self.mod.find_class_method(parent, e.name)
        if mi is None:
            if e.name == "init" and not e.args:
                return None, "void"            # parent has no constructor: nothing to run
            self.err(f"parent class {parent.name} has no method {e.name}", e)
        if mi.static:
            self.err(f"{e.name} is static", e)
        if mi.abstract:
            self.err(f"cannot call abstract method {mi.owner}.{e.name} through super", e)
        self.check_access(mi, e)
        sv, _ = self.e_Name(Name("self", line=e.line))
        return self.call_args(mi, sv, e.args, e)       # direct, non-virtual call

    def builtin(self, e, name):
        if name == "print":
            return self.print_(e)
        if name in INTRINSICS:
            kinds, ret, fn = INTRINSICS[name]
            if len(e.args) != len(kinds):
                self.err(f"{name} takes {len(kinds)} argument(s)", e)
            vals = []
            for a, k in zip(e.args, kinds):
                v, t = self.expr(a)
                if k == "int" and t == "int":
                    vals.append(f"i64 {v}")
                elif k == "str" and t == "str":
                    vals.append(f"ptr {v}")
                elif k == "obj" and self.mod.is_class(t):
                    vals.append(f"ptr {self.consume(v, t)}")   # ownership moves to the callee
                else:
                    self.err(f"bad argument to {name}: {t}", a)
            call = f"call {'i64' if ret == 'int' else 'ptr' if ret == 'str' else 'void'} @{fn}({', '.join(vals)})"
            if ret == "str":
                r = self.op(call)
                self.fresh.add(r)           # the runtime hands over an owned string
                return r, "str"
            if ret == "int":
                return self.op(call), "int"
            self.emit(call)
            return None, "void"
        if name == "hash" and len(e.args) == 1:
            v, t = self.expr(e.args[0])
            if t == "int": r = v
            elif t == "bool": r = self.op(f"zext i1 {v} to i64")
            elif t == "float": r = self.op(f"bitcast double {v} to i64")
            elif t == "str": r = self.op(f"call i64 @quill_hash_str(ptr {v})")
            elif self.mod.is_class(t): r = self.op(f"ptrtoint ptr {v} to i64")   # identity hash
            else: self.err(f"cannot hash {t}", e)
            self.release_fresh(v, t)
            return r, "int"
        if name == "heap_live" and not e.args:      # debugging aid: live heap objects
            return self.op("load i64, ptr @quill_live"), "int"
        if name == "str" and len(e.args) == 1:
            v, t = self.expr(e.args[0])
            if t == "str":
                return v, t
            if t in ("int", "float"):
                buf = self.op("call ptr @quill_alloc(i64 40)")
                fmt, arg = ("%ld", f"i64 {v}") if t == "int" else ("%g", f"double {v}")
                self.emit(f"call i32 (ptr, i64, ptr, ...) @snprintf(ptr {buf}, i64 40, ptr {self.mod.string(fmt)}, {arg})")
                self.fresh.add(buf)
                return buf, "str"
            if t == "bool":
                return self.op(f"select i1 {v}, ptr {self.mod.string('true')}, ptr {self.mod.string('false')}"), "str"
            if self.has_to_string(t):
                return self.to_str(v, t, e), "str"
            self.err(f"cannot convert {t} to str (give the class a toString method)", e)
        if name in ("int", "float", "len") and len(e.args) == 1:
            v, t = self.expr(e.args[0])
            if name == "len" and self.mod.is_class(t):
                if self.mod.array_elem(t) is not None:
                    self.null_check(v, "null pointer dereference (len)")
                    r = self.op(f"load i64, ptr {self.op(f'getelementptr i8, ptr {v}, i64 8')}")
                    self.release_fresh(v, t)
                    return r, "int"
                return self.call_method(v, t, "size", [], e)
            if name == "len" and t == "str":
                self.null_check(v, "null string (len)")
                r = self.op(f"call i64 @strlen(ptr {v})")
                self.release_fresh(v, t)
                return r, "int"
            if name == "int" and t == "float": return self.op(f"fptosi double {v} to i64"), "int"
            if name == "int" and t == "bool": return self.op(f"zext i1 {v} to i64"), "int"
            if name == "int" and t == "int": return v, "int"
            if name == "float" and t in NUM: return self.coerce(v, t, "float", e), "float"
            self.err(f"cannot apply {name}() to {t}", e)
        self.err(f"unknown function {name} (all code lives in classes)", e)

    def has_to_string(self, t):
        if not self.mod.is_class(t):
            return False
        mi = self.mod.find_method(self.mod.classes[t], "toString")
        return bool(mi and not mi.static and not mi.params and mi.ret == "str"
                    and (mi.access != "private" or self.ci.name == mi.owner))

    def print_to_string(self, v, t, pf, node):
        """Print an object through its toString(), or <null> when it is null."""
        s = self.to_str(v, t, node)
        pf("%s", ("ptr", s))
        self.release_fresh(s, "str")
        self.release_fresh(v, t)

    def to_str(self, v, t, node):
        """Convert a value to a fresh-or-borrowed str using toString for objects."""
        slot = self.alloca("ptr", "ts")
        isnull = self.op(f"icmp eq ptr {v}, null")
        yes, no, end = self.label("ts.null"), self.label("ts.obj"), self.label("ts.end")
        self.condbr(isnull, yes, no)
        self.place(yes)
        self.emit(f"store ptr {self.mod.string('null')}, ptr {slot}")
        self.br(end)
        self.place(no)
        r, _ = self.call_method(v, t, "toString", [], node)
        self.fresh.discard(r)
        self.emit(f"store ptr {r}, ptr {slot}")
        self.br(end)
        self.place(end)
        out = self.op(f"load ptr, ptr {slot}")
        # the object branch yields an owned string; the null branch an immortal literal
        # (immortal strings ignore release), so treat the result as fresh either way
        self.fresh.add(out)
        return out

    def print_(self, e):
        def pf(fmt, *args):
            a = "".join(f", {t} {v}" for t, v in args)
            self.emit(f"call i32 (ptr, ...) @printf(ptr {self.mod.string(fmt)}{a})")
        for i, a in enumerate(e.args):
            v, t = self.expr(a)
            if i: pf(" ")
            if t == "int": pf("%ld", ("i64", v))
            elif t == "float": pf("%g", ("double", v))
            elif t == "str":
                pf("%s", ("ptr", self.op(f"select i1 {self.op(f'icmp eq ptr {v}, null')}, ptr {self.mod.string('null')}, ptr {v}")))
            elif t == "bool":
                s = self.op(f"select i1 {v}, ptr {self.mod.string('true')}, ptr {self.mod.string('false')}")
                pf("%s", ("ptr", s))
            elif self.has_to_string(t):
                self.print_to_string(v, t, pf, a)
                continue
            else: pf(f"<{t} object at %p>", ("ptr", v))
            self.release_fresh(v, t)
        pf("\n")
        return None, "void"


# ───────────────────────────── Driver ─────────────────────────────

def compile_source(src):
    decls = Parser(lex(PRELUDE)).program() + Parser(lex(src)).program()
    return Module(decls).generate()


def load_program(entry):
    """Parse `entry` and every module it brings in; returns all class declarations."""
    ctx = quillpkg.context_for(entry)
    decls, seen, origin = [], set(), {}

    def visit(path, pkg):
        real = os.path.realpath(path)
        if real in seen:
            return
        seen.add(real)
        with open(path, encoding="utf-8") as f:
            src = f.read()
        try:
            parser = Parser(lex(src))
            found = parser.program()
        except CompileError as e:
            e.file = e.file or path
            raise
        for d in found:
            d.file = path
            if d.name in origin:
                raise CompileError(f"class {d.name} is already defined in {origin[d.name]}", d.line, path)
            origin[d.name] = path
        decls.extend(found)
        for name, line in parser.imports:
            try:
                target, tpkg = ctx.resolve(pkg, name)
            except quillpkg.PackageError as e:
                raise CompileError(str(e), line, path)
            visit(target, tpkg)

    visit(entry, ctx.package_of(entry))
    return decls, origin


def compile_file(path):
    prelude = Parser(lex(PRELUDE)).program()
    for d in prelude:
        d.file = "<built-in>"
    decls, _ = load_program(path)
    seen = {d.name for d in prelude}
    for d in decls:
        if d.name in seen:
            raise CompileError(f"class {d.name} clashes with a built-in class", d.line, d.file)
    return Module(prelude + decls).generate()


def mark_sanitize(ir, kind):
    """Sanitizers only instrument functions carrying this attribute (clang adds it
    for C source; raw .ll files need it added explicitly)."""
    attr = {"address": "sanitize_address", "thread": "sanitize_thread"}[kind]
    return re.sub(r"^(define [^\n]*) \{$", r"\1 " + attr + " {", ir, flags=re.M)


WIN_SHIM = """#include <stdarg.h>
#include <stdio.h>
#include <io.h>
int dprintf(int fd, const char *fmt, ...) {
    char buf[1024];
    va_list ap; va_start(ap, fmt);
    int n = vsnprintf(buf, sizeof buf, fmt, ap);
    va_end(ap);
    if (n > (int)sizeof buf - 1) n = sizeof buf - 1;
    return n < 0 ? n : _write(fd, buf, n);
}
"""


def find_tool(name):
    """Locate a tool on PATH, falling back to the default Windows LLVM install."""
    found = shutil.which(name)
    if found:
        return found
    fallback = os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "LLVM", "bin", name + ".exe")
    return fallback if os.path.exists(fallback) else name


def build_windows(ll, out, opt):
    """The runtime uses POSIX calls (pthreads, dprintf), so on Windows compile with
    clang for the mingw target and link with gcc plus a dprintf shim."""
    with tempfile.TemporaryDirectory() as d:
        shim = os.path.join(d, "shim.c")
        with open(shim, "w") as f:
            f.write(WIN_SHIM)
        obj = os.path.join(d, "prog.o")
        r = subprocess.run([find_tool("clang"), opt, "-c", "--target=x86_64-w64-mingw32",
                            "-Wno-override-module", ll, "-o", obj],
                           capture_output=True, text=True)
        if r.returncode:
            return r
        exe = out if out.endswith(".exe") else out + ".exe"
        r = subprocess.run(["gcc", obj, shim, "-o", exe, "-lpthread"],
                           capture_output=True, text=True)
        r.exe = exe
        return r


def build(path, out, opt="-O1", keep_ll=False, sanitize=None):
    try:
        ir = compile_file(path)
    except CompileError as e:
        print(f"{e.file or path}:{e.line}: error: {e.msg}", file=sys.stderr)
        sys.exit(1)
    if sanitize:
        ir = mark_sanitize(ir, sanitize)
    ll = out + ".ll" if keep_ll else tempfile.mktemp(suffix=".ll")
    with open(ll, "w") as f:
        f.write(ir)
    flags = [f"-fsanitize={sanitize}", "-g"] if sanitize else []
    if sys.platform == "win32":
        if sanitize:
            print("error: --sanitize is not supported on Windows", file=sys.stderr)
            sys.exit(2)
        r = build_windows(ll, out, opt)
    else:
        r = subprocess.run(["clang", opt, *flags, "-Wno-override-module", ll, "-o", out],
                           capture_output=True, text=True)
    if not keep_ll:
        os.unlink(ll)
    if r.returncode:
        print("internal error: clang rejected generated IR\n" + r.stderr, file=sys.stderr)
        sys.exit(2)
    return r.exe if hasattr(r, "exe") else out


def main():
    ap = argparse.ArgumentParser(prog="quill", description="The Quill compiler and package manager")
    sub = ap.add_subparsers(dest="cmd", required=True, metavar="command")

    def compiler_cmd(name, help_text):
        sp = sub.add_parser(name, help=help_text)
        sp.add_argument("file", nargs="?", help="a .ql file (default: the project's start module)")
        sp.add_argument("-O", default="1", help="optimization level (0-3)")
        return sp

    san = dict(choices=["address", "thread"], help="build with AddressSanitizer or ThreadSanitizer")
    sp = compiler_cmd("run", "compile and run a program")
    sp.add_argument("--sanitize", **san)
    sp = compiler_cmd("build", "compile to a native executable")
    sp.add_argument("-o", "--out")
    sp.add_argument("--keep-ll", action="store_true")
    sp.add_argument("--sanitize", **san)
    compiler_cmd("emit", "print the LLVM IR")

    sp = sub.add_parser("new", help="create a project in a new folder")
    sp.add_argument("name")
    sp.add_argument("--lib", action="store_true", help="a library: no start module")
    sp = sub.add_parser("init", help="create quill.pkg in the current folder")
    sp.add_argument("--lib", action="store_true")
    sp = sub.add_parser("install", help="resolve and fetch dependencies, write quill.lock")
    sp.add_argument("--locked", action="store_true", help="fail instead of changing quill.lock")
    sp.add_argument("--offline", action="store_true", help="use only what is already downloaded")
    sp = sub.add_parser("update", help="re-resolve dependencies to newer versions")
    sp.add_argument("names", nargs="*", help="only these packages (default: all)")
    sp.add_argument("--offline", action="store_true")
    sp = sub.add_parser("add", help="add a dependency")
    sp.add_argument("name")
    sp.add_argument("version", nargs="?", help="constraint: 1.4, =1.4.2, 1.2..2.0 or any")
    sp.add_argument("--git", metavar="URL")
    sp.add_argument("--path", metavar="DIR")
    sp.add_argument("--branch")
    sp.add_argument("--rev")
    sp.add_argument("--tag")
    sp.add_argument("--offline", action="store_true")
    sp = sub.add_parser("drop", help="remove a dependency")
    sp.add_argument("name")
    sub.add_parser("tree", help="show the dependency tree")
    a = ap.parse_args()

    if a.cmd in ("new", "init", "install", "update", "add", "drop", "tree"):
        sys.exit(quillpkg.cli(a.cmd, a))

    try:
        out_default = None
        path = a.file
        if path is None:
            path, m = quillpkg.default_entry()
            out_default = os.path.join(m.dir, "build", m.name)
        if a.cmd == "emit":
            try:
                print(compile_file(path))
            except CompileError as e:
                print(f"{e.file or path}:{e.line}: error: {e.msg}", file=sys.stderr)
                sys.exit(1)
        elif a.cmd == "build":
            out = a.out or out_default or os.path.splitext(path)[0]
            os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
            exe = build(path, out, f"-O{a.O}", a.keep_ll, a.sanitize)
            print(f"built {os.path.relpath(exe)}")
        else:
            with tempfile.TemporaryDirectory() as d:
                exe = build(path, os.path.join(d, "prog"), f"-O{a.O}", sanitize=a.sanitize)
                sys.exit(subprocess.run([exe]).returncode)
    except quillpkg.PackageError as e:
        print(f"quill: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
