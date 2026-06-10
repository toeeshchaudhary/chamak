"""Tiny DSL parser for the rule language.

Grammar (case-insensitive keywords):

    expr     := or_expr
    or_expr  := and_expr ( "OR" and_expr )*
    and_expr := not_expr ( "AND" not_expr )*
    not_expr := "NOT" not_expr | primary
    primary  := "(" expr ")" | between | cmp
    between  := ref "BETWEEN" number "AND" number
    cmp      := ref OP number | number OP ref
    OP       := "<" | "<=" | ">" | ">=" | "=" | "=="| "!="
    ref      := IDENT
    number   := signed float
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from chamak.core.errors import RuleParseError
from chamak.rules import ast


_TOKEN = re.compile(
    r"""
    \s+                              |
    (?P<NUM>-?\d+(?:\.\d+)?)         |
    (?P<OP><=|>=|==|!=|<|>|=)        |
    (?P<LP>\()                       |
    (?P<RP>\))                       |
    (?P<IDENT>[A-Za-z_][A-Za-z0-9_]*)
    """,
    re.VERBOSE,
)


_KEYWORDS = {"AND", "OR", "NOT", "BETWEEN"}


@dataclass
class _Tok:
    kind: str
    value: str


def _tokenize(s: str) -> list[_Tok]:
    out: list[_Tok] = []
    i = 0
    while i < len(s):
        m = _TOKEN.match(s, i)
        if not m:
            raise RuleParseError(f"unexpected char {s[i]!r} at position {i}")
        i = m.end()
        if m.group("NUM"):
            out.append(_Tok("NUM", m.group("NUM")))
        elif m.group("OP"):
            out.append(_Tok("OP", m.group("OP")))
        elif m.group("LP"):
            out.append(_Tok("LP", "("))
        elif m.group("RP"):
            out.append(_Tok("RP", ")"))
        elif m.group("IDENT"):
            v = m.group("IDENT").upper()
            if v in _KEYWORDS:
                out.append(_Tok("KW", v))
            else:
                out.append(_Tok("IDENT", m.group("IDENT")))
    return out


_OP_MAP = {"<": "lt", "<=": "le", ">": "gt", ">=": "ge", "=": "eq", "==": "eq", "!=": "ne"}


class _Parser:
    def __init__(self, toks: list[_Tok]) -> None:
        self.toks = toks
        self.i = 0

    def peek(self) -> _Tok | None:
        return self.toks[self.i] if self.i < len(self.toks) else None

    def eat(self) -> _Tok:
        if self.i >= len(self.toks):
            raise RuleParseError("unexpected end of input")
        t = self.toks[self.i]
        self.i += 1
        return t

    def accept(self, kind: str, value: str | None = None) -> _Tok | None:
        t = self.peek()
        if t and t.kind == kind and (value is None or t.value == value):
            return self.eat()
        return None

    def expect(self, kind: str, value: str | None = None) -> _Tok:
        t = self.accept(kind, value)
        if t is None:
            got = self.peek()
            raise RuleParseError(
                f"expected {kind} {value or ''}, got {got.kind if got else 'EOF'} "
                f"{got.value if got else ''}"
            )
        return t

    # grammar

    def parse(self) -> dict:
        node = self.or_expr()
        if self.peek() is not None:
            raise RuleParseError(f"trailing tokens at position {self.i}")
        return node

    def or_expr(self) -> dict:
        left = self.and_expr()
        nodes = [left]
        while self.accept("KW", "OR"):
            nodes.append(self.and_expr())
        return nodes[0] if len(nodes) == 1 else ast.or_(*nodes)

    def and_expr(self) -> dict:
        left = self.not_expr()
        nodes = [left]
        while self.accept("KW", "AND"):
            nodes.append(self.not_expr())
        return nodes[0] if len(nodes) == 1 else ast.and_(*nodes)

    def not_expr(self) -> dict:
        if self.accept("KW", "NOT"):
            return ast.not_(self.not_expr())
        return self.primary()

    def primary(self) -> dict:
        if self.accept("LP"):
            inner = self.or_expr()
            self.expect("RP")
            return inner
        # Look ahead for IDENT BETWEEN
        t = self.peek()
        if t and t.kind == "IDENT":
            # IDENT BETWEEN num AND num   OR   IDENT OP num
            ident = self.eat().value
            if self.accept("KW", "BETWEEN"):
                lo = self._number()
                self.expect("KW", "AND")
                hi = self._number()
                return ast.between(ast.ref(ident), ast.lit(lo), ast.lit(hi))
            op = self.expect("OP").value
            num = self._number()
            return ast.cmp(_OP_MAP[op], ast.ref(ident), ast.lit(num))
        if t and t.kind == "NUM":
            num = self._number()
            op = self.expect("OP").value
            ident = self.expect("IDENT").value
            return ast.cmp(_OP_MAP[op], ast.lit(num), ast.ref(ident))
        raise RuleParseError(f"unexpected token: {t.kind if t else 'EOF'}")

    def _number(self) -> float:
        return float(self.expect("NUM").value)


def parse(s: str) -> dict:
    s = s.strip()
    if not s:
        raise RuleParseError("empty rule")
    return _Parser(_tokenize(s)).parse()


def to_text(node: dict) -> str:
    """Pretty-print an AST back to DSL form."""
    t = node["t"]
    if t == "lit":
        v = node["v"]
        if isinstance(v, float) and v.is_integer():
            return str(int(v))
        return str(v)
    if t == "ref":
        return node["k"]
    if t == "cmp":
        op = {"lt": "<", "le": "<=", "gt": ">", "ge": ">=", "eq": "=", "ne": "!="}[node["op"]]
        return f"{to_text(node['l'])} {op} {to_text(node['r'])}"
    if t == "btw":
        return f"{to_text(node['x'])} BETWEEN {to_text(node['lo'])} AND {to_text(node['hi'])}"
    if t == "and":
        return " AND ".join(_wrap(to_text(c), c) for c in node["xs"])
    if t == "or":
        return " OR ".join(_wrap(to_text(c), c) for c in node["xs"])
    if t == "not":
        inner = to_text(node["x"])
        if node["x"]["t"] in ("and", "or"):
            return f"NOT ({inner})"
        return f"NOT {inner}"
    raise RuleParseError(f"unknown node type {t}")


def _wrap(text: str, n: dict) -> str:
    if n["t"] in ("or", "and"):
        return f"({text})"
    return text
