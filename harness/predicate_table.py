"""Parse the spec-predicates block: what each rule-column value means.

The grammar is deliberately closed. A condition is a boolean expression over a
fixed vocabulary of normalized-input paths and derived observations, named sets
declared in spec-settings, and earlier column values. The compiler emits a JSON
tree; the runtime component and the harness oracle each evaluate that tree with
their own code.

    cond   := conj ('or' conj)*
    conj   := unary ('and' unary)*
    unary  := 'not' unary | '(' cond ')' | atom
    atom   := '[' Column ']' '=' VALUE
            | 'any' LIST 'has' '(' cond ')'
            | PATH ('in' | 'overlaps' | 'within') SET
            | PATH '=' LITERAL
            | PATH
    'otherwise' is a whole condition and must be the last row of its column.
"""

from __future__ import annotations

import re

# Paths the conditions may read, and their types. Derived observations are
# defined in spec.md "Derived observations"; both implementations compute them.
PATHS = {
    "source.media_type": "text",
    "evidence.extraction_usable": "flag",
    "evidence.helpers_usable": "flag",
    "evidence.contradictory": "flag",
    "facts.content_kind": "text",
    "facts.availability": "text",
    "facts.time_basis": "text",
    "facts.services": "list",
    "facts.restrictions": "rows",
    "notice.status": "text",
    "history.complete": "flag",
    "history.root_status": "text",
    "history.statuses": "list",
    "predecessor.present": "flag",
    "predecessor.status": "text",
    "predecessor.facts_equal": "flag",
    "time.ended": "flag",
    "time.current": "flag",
    "time.ended_in_any_timezone": "flag",
}
ROW_PATHS = {"facts.restrictions": {"service": "text", "availability": "text"}}

# Sets taken from existing settings rather than repeated in spec-settings.sets.
ALIASES = {
    "SUPPORTED_FORMATS": ("formats", "supported"),
    "ROOT_STATUSES": ("history_statuses", "root"),
    "LINKED_STATUSES": ("history_statuses", "linked"),
}

# Specs written before spec-predicates existed keep the meaning they were
# compiled with. Used only to compile historical specs for comparison.
LEGACY_SETS = {
    "FIRM_SERVICES": ["PRIMARY_FIRM", "SECONDARY_FIRM"],
    "RESTRICTED_AVAILABILITY": ["UNAVAILABLE", "PRIMARY_ONLY", "PARTIAL"],
    "INFORMATION_KINDS": ["ADMINISTRATIVE", "INFORMATIONAL"],
    "UNCHANGED_PREDECESSOR_STATUSES": ["INITIATE", "SUPERSEDE"],
}
LEGACY_PREDICATES = """Column | Value | Condition
Format | SUPPORTED | source.media_type in SUPPORTED_FORMATS
Format | UNSUPPORTED | otherwise
Oracle answer | USABLE | evidence.extraction_usable and evidence.helpers_usable
Oracle answer | UNUSABLE | otherwise
Information-only | YES | facts.content_kind in INFORMATION_KINDS
Information-only | NO | otherwise
Restriction | KNOWN | facts.availability in RESTRICTED_AVAILABILITY or any facts.restrictions has (availability in RESTRICTED_AVAILABILITY)
Restriction | NONE | [Information-only] = YES
Restriction | UNKNOWN | otherwise
Conflict | YES | evidence.contradictory or ([Information-only] = YES and [Restriction] = KNOWN)
Conflict | NO | otherwise
History | COMPLETE | history.complete and history.root_status in ROOT_STATUSES and history.statuses within LINKED_STATUSES
History | GAP | otherwise
Operational change | UNCHANGED | notice.status = SUPERSEDE and predecessor.status in UNCHANGED_PREDECESSOR_STATUSES and predecessor.facts_equal
Operational change | CHANGED | predecessor.present
Operational change | UNKNOWN | otherwise
Service class | FIRM_DISRUPTION | facts.content_kind = RESTRICTION and (any facts.restrictions has (service in FIRM_SERVICES and availability = UNAVAILABLE) or facts.availability = PRIMARY_ONLY or (facts.services overlaps FIRM_SERVICES and facts.availability = UNAVAILABLE))
Service class | OTHER | otherwise
Restriction current | ENDED | time.ended
Restriction current | CURRENT | time.current
Restriction current | UNKNOWN | otherwise"""

TOKEN = re.compile(r"\s*(\(|\)|\[[^\]]+\]|=|[A-Za-z_][A-Za-z_0-9.\-]*)")
KEYWORDS = {"and", "or", "not", "any", "has", "in", "overlaps", "within", "otherwise"}


def tokenize(text: str) -> list[str]:
    tokens, position = [], 0
    while position < len(text):
        match = TOKEN.match(text, position)
        if not match:
            if text[position:].strip():
                raise ValueError("unexpected text: " + text[position:].strip())
            break
        tokens.append(match[1])
        position = match.end()
    return tokens


class Parser:
    def __init__(self, text: str, sets: dict, columns: dict, earlier: set[str]):
        self.tokens = tokenize(text)
        self.index = 0
        self.sets, self.columns, self.earlier = sets, columns, earlier

    def peek(self) -> str | None:
        return self.tokens[self.index] if self.index < len(self.tokens) else None

    def take(self, expected: str | None = None) -> str:
        token = self.peek()
        if token is None or (expected is not None and token != expected):
            raise ValueError(f"expected {expected or 'a term'}, found {token or 'end'}")
        self.index += 1
        return token

    def parse(self) -> dict:
        if self.tokens == ["otherwise"]:
            return {"op": "otherwise"}
        tree = self.disjunction({}, top=True)
        if self.peek() is not None:
            raise ValueError("unexpected " + str(self.peek()))
        return tree

    def disjunction(self, scope: dict, top: bool = False) -> dict:
        args = [self.conjunction(scope, top)]
        while self.peek() == "or":
            self.take()
            args.append(self.conjunction(scope, top))
        return args[0] if len(args) == 1 else {"op": "or", "args": args}

    def conjunction(self, scope: dict, top: bool) -> dict:
        args = [self.unary(scope, top)]
        while self.peek() == "and":
            self.take()
            args.append(self.unary(scope, top))
        return args[0] if len(args) == 1 else {"op": "and", "args": args}

    def unary(self, scope: dict, top: bool) -> dict:
        token = self.peek()
        if token == "not":
            self.take()
            return {"op": "not", "arg": self.unary(scope, top)}
        if token == "(":
            self.take()
            tree = self.disjunction(scope, top)
            self.take(")")
            return tree
        return self.atom(scope, top)

    def literal(self) -> str:
        token = self.take()
        if not re.fullmatch(r"[A-Z][A-Z_0-9]*", token):
            raise ValueError("literal values are upper-case identifiers: " + token)
        return token

    def set_name(self) -> str:
        name = self.take()
        if name not in self.sets:
            raise ValueError("unknown set " + name)
        return name

    def atom(self, scope: dict, top: bool) -> dict:
        token = self.take()
        if token.startswith("["):
            column = token[1:-1]
            if column not in self.columns or column not in self.earlier:
                raise ValueError(f"[{column}] must name a column defined earlier in the table")
            self.take("=")
            value = self.literal()
            if value not in self.columns[column] or value == "ANY":
                raise ValueError(f"{value} is not a value of [{column}]")
            return {"op": "column", "column": column, "value": value}
        if token == "any":
            path = self.take()
            if not top or PATHS.get(path) != "rows":
                raise ValueError("any ... has requires a row list: " + path)
            self.take("has")
            self.take("(")
            tree = self.disjunction(ROW_PATHS[path], top=False)
            self.take(")")
            return {"op": "any", "path": path, "cond": tree}
        if token in KEYWORDS:
            raise ValueError("unexpected keyword " + token)
        kinds = PATHS if top else scope
        if token not in kinds:
            raise ValueError("unknown path " + token)
        kind = kinds[token]
        following = self.peek()
        if following in {"in", "overlaps", "within"}:
            operator = self.take()
            wanted = "text" if operator == "in" else "list"
            if kind != wanted:
                raise ValueError(f"{operator} requires a {wanted} path: {token}")
            return {"op": operator, "path": token, "set": self.set_name()}
        if following == "=":
            self.take()
            if kind != "text":
                raise ValueError("= requires a text path: " + token)
            return {"op": "eq", "path": token, "value": self.literal()}
        if kind != "flag":
            raise ValueError("a bare path must be a flag: " + token)
        return {"op": "flag", "path": token}


def resolve_sets(settings: dict, declared: dict | None) -> dict:
    sets = dict(declared if declared is not None else LEGACY_SETS)
    for name, (section, key) in ALIASES.items():
        if name in sets:
            raise ValueError(f"{name} is derived from spec-settings {section}.{key}")
        sets[name] = settings[section][key]
    for name, members in sets.items():
        if (
            not re.fullmatch(r"[A-Z][A-Z_0-9]*", name)
            or not isinstance(members, list)
            or not members
            or len(set(members)) != len(members)
            or any(not isinstance(m, str) for m in members)
        ):
            raise ValueError(f"set {name} must be a nonempty list of distinct strings")
    return sets


def parse_table(lines: list[str], start: int, columns: dict, sets: dict) -> list[dict]:
    """Return ordered predicate rows; errors carry a (line, row, message) tuple."""
    if not lines or [x.strip() for x in lines[0].split("|")] != ["Column", "Value", "Condition"]:
        raise ValueError((start, "header", "expected columns: Column, Value, Condition"))
    rows: list[dict] = []
    order: list[str] = []
    for number, line in enumerate(lines[1:], start + 1):
        parts = [x.strip() for x in line.split("|", 2)]
        if len(parts) != 3 or not all(parts):
            raise ValueError((number, "-", "one Column, Value and Condition per row"))
        column, value, text = parts
        label = f"{column}={value}"
        if column not in columns:
            raise ValueError((number, label, "unknown rule column"))
        if value == "ANY" or value not in columns[column]:
            raise ValueError((number, label, f"value must be one of {columns[column][1:]}"))
        if order and order[-1] != column and column in order:
            raise ValueError((number, label, "rows for one column must be contiguous"))
        if column not in order:
            if order and rows[-1]["ast"]["op"] != "otherwise":
                raise ValueError((number, label, f"[{order[-1]}] must end with otherwise"))
            order.append(column)
        if any(r["column"] == column and r["value"] == value for r in rows):
            raise ValueError((number, label, "duplicate column value"))
        if rows and rows[-1]["column"] == column and rows[-1]["ast"]["op"] == "otherwise":
            raise ValueError((number, label, "otherwise must be the last row of its column"))
        try:
            tree = Parser(text, sets, columns, set(order[:-1])).parse()
        except ValueError as exc:
            raise ValueError((number, label, str(exc.args[0]))) from exc
        rows.append(
            {"column": column, "value": value, "condition": text, "ast": tree, "spec_line": number}
        )
    if not rows or rows[-1]["ast"]["op"] != "otherwise":
        raise ValueError((start, "-", "every column must end with otherwise"))
    for column, allowed in columns.items():
        defined = {r["value"] for r in rows if r["column"] == column}
        if defined != set(allowed) - {"ANY"}:
            raise ValueError((start, column, "define every value of this column exactly once"))
    return rows


def compile_predicates(found: dict, settings: dict, columns: dict, fail) -> tuple[list, dict]:
    declared = settings.get("sets")
    try:
        sets = resolve_sets(settings, declared)
    except (ValueError, KeyError) as exc:
        raise fail("spec-settings", "sets", found["spec-settings"][0], str(exc)) from exc
    if "spec-predicates" in found:
        start, lines = found["spec-predicates"]
    else:
        start, lines = 1, LEGACY_PREDICATES.splitlines()
    try:
        return parse_table(lines, start, columns, sets), sets
    except ValueError as exc:
        line, row, message = exc.args[0]
        raise fail("spec-predicates", row, line, message) from exc
