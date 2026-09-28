"""Generate the code-read ledger from agent session transcripts.

    python3 evidence/code-read-ledger/generate.py ~/.claude/projects/<project> \
        > evidence/code-read-ledger/LEDGER.md

Every tool call in every session and subagent transcript that names a Python file
under harness/, rebuilt/, inherited/ or tests/ (in this checkout or any scratch copy
of it) is classified, and every file a human opened in the IDE is listed. The
classification is mechanical, not a judgement:

- read: the Read tool, or a shell command (cat, sed -n, head, tail, grep, rg, nl, git
  show/diff) that names the file;
- search: the Grep or Glob tool with a path or pattern that names the file or directory;
- edit: the Edit, Write or NotebookEdit tool, or a shell command that names the file and
  writes (sed -i, write_text, open(..., 'w'), apply, a redirect);
- ran: a shell command that names the file but neither reads nor edits it (it runs it);
- imported: a shell script that imports a module from those directories, i.e. executed it;
- a glob such as `harness/*.py` is recorded as written, since it reads or searches every
  file it matches;
- ide-open: the human opened the file in the IDE while the session ran.

A shell command that both reads and edits counts as edit, and every code file it names
counts as edited, so edit overcounts (a script that writes one file and names another
lists both). A scripted replacement that
asserts an exact old string counts as edit without a separate read, which understates
reads. Transcripts are not in the repository, so the ledger cannot be regenerated from a
clone; the script is kept so the method is inspectable. Only Claude Code transcripts are
covered: the Codex sessions of 09-26 to 09-28 are not, and their reads are the ones
reconstructed by hand in code_reads.md.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOTS = ("harness", "rebuilt", "inherited", "tests")
FILE = re.compile(
    r"(?<![\w.-])(?:[\w./-]*/)?((?:harness|rebuilt|inherited|tests)/(?:[\w/]*\w+|\*\*?(?:/\*)?)\.py)"
)
IMPORT = re.compile(r"(?:from|import)\s+((?:harness|rebuilt|inherited|tests)(?:\.\w+)+)")
DIRECTORY = re.compile(
    r"(?<![\w.-])(?:[\w./-]*/)?((?:harness|rebuilt|inherited|tests))/?(?:\*\*?/?\*?\.py)?(?=[\s'\"]|$)"
)
WRITES = re.compile(
    r"sed -i|write_text\(|open\([^)]*['\"]w['\"]|\.write\(|git apply|git checkout --|patch |>\s*[\w./-]+\.py"
)
READS = re.compile(r"\b(cat|sed -n|head|tail|grep|rg|nl|less|awk|git show|git diff|wc)\b")


def files_in(text: str) -> set[str]:
    return set(FILE.findall(text))


def classify(name: str, data: dict) -> list[tuple[str, str]]:
    if name == "Read":
        return [("read", f) for f in files_in(data.get("file_path", ""))]
    if name in {"Edit", "Write", "NotebookEdit", "MultiEdit"}:
        return [("edit", f) for f in files_in(data.get("file_path", ""))]
    if name in {"Grep", "Glob"}:
        text = " ".join(str(data.get(k, "")) for k in ("path", "pattern", "glob"))
        found = files_in(text) or {d + "/" for d in DIRECTORY.findall(text) if d in ROOTS}
        return [("search", f) for f in found]
    if name == "Bash":
        command = data.get("command", "")
        found = files_in(command)
        imported = [
            ("imported", module.replace(".", "/") + ".py") for module in IMPORT.findall(command)
        ]
        if not found:
            return imported
        if WRITES.search(command):
            kind = "edit"
        elif READS.search(command):
            kind = "read"
        else:
            kind = "ran"
        return [(kind, f) for f in found] + imported
    return []


def sessions(directory: Path):
    for path in sorted(directory.rglob("*.jsonl")):
        parts = path.relative_to(directory).parts
        session = parts[0].removesuffix(".jsonl")
        agent = path.stem if len(parts) > 1 else "main"
        workflow = next((p for p in parts if p.startswith("wf_")), "")
        yield session, agent, workflow, path


def scan(path: Path) -> tuple[str, dict[str, set[str]]]:
    seen: dict[str, set[str]] = defaultdict(set)
    first = ""
    for line in path.read_text(errors="replace").splitlines():
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        stamp = entry.get("timestamp") or ""
        if stamp and not first:
            first = stamp
        attachment = entry.get("attachment") or {}
        if attachment.get("type") == "opened_file_in_ide":
            for f in files_in(attachment.get("filename", "")):
                seen["ide-open"].add(f)
        content = (entry.get("message") or {}).get("content")
        if isinstance(content, str) and "opened the file" in content:
            for f in files_in(content):
                seen["ide-open"].add(f)
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text" and "opened the file" in block.get("text", ""):
                match = re.search(r"opened the file (\S+) in the IDE", block["text"])
                if match:
                    seen["ide-open"].update(files_in(match.group(1)))
            if block.get("type") == "tool_use":
                for kind, f in classify(block.get("name", ""), block.get("input") or {}):
                    seen[kind].add(f)
    return first, seen


def main() -> None:
    directory = Path(sys.argv[1])
    kinds = ("edit", "read", "search", "ran", "imported", "ide-open")
    rows = []
    for session, agent, workflow, path in sessions(directory):
        first, seen = scan(path)
        if any(seen.values()):
            rows.append((first, session, agent, workflow, seen))
    rows.sort()
    print("# Code-read ledger (generated)\n")
    print(
        "Generated by `evidence/code-read-ledger/generate.py` from the agent transcripts of "
        "this project; do not edit by hand. Classification rules are in the script's "
        "docstring. Session is the top-level transcript; agent is `main` or the subagent "
        "file; workflow subagents are marked. Paths are normalized to the repository "
        "layout, so scratch copies count as the same file.\n"
    )
    totals = {k: 0 for k in kinds}
    touched_rebuilt = sum(
        1 for *_, seen in rows if any(f.startswith("rebuilt/") for k in kinds for f in seen[k])
    )
    for *_, seen in rows:
        for k in kinds:
            totals[k] += bool(seen[k])
    print(
        f"{len(rows)} transcripts name a code file. Transcripts with at least one: "
        + ", ".join(f"{k} {v}" for k, v in totals.items())
        + f". Transcripts touching rebuilt/ in any way: {touched_rebuilt}.\n"
    )
    print("| Started (UTC) | Session | Agent | " + " | ".join(kinds) + " |")
    print("|---|---|---|" + "---|" * len(kinds))
    for first, session, agent, workflow, seen in rows:
        label = agent if not workflow else f"{agent} ({workflow[:11]})"
        cells = [", ".join(f"`{f}`" for f in sorted(seen[k])) or "" for k in kinds]
        print(f"| {first[:19]} | {session[:8]} | {label} | " + " | ".join(cells) + " |")


if __name__ == "__main__":
    main()
