#!/bin/sh
# Discover an installed Python only. Dependency installation remains explicit.
set -eu

bootstrap_python=
supported() {
    "$1" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 14) else 1)' >/dev/null 2>&1
}

if [ -n "${HARNESS_BOOTSTRAP_PYTHON:-}" ]; then
    bootstrap_python=$(command -v "$HARNESS_BOOTSTRAP_PYTHON" 2>/dev/null || true)
    if [ -z "$bootstrap_python" ] || ! supported "$bootstrap_python"; then
        echo 'Requested Python is unavailable or older than 3.14.' >&2
        echo 'Install with the declared uv tooling, then run: uv python install 3.14 && make setup' >&2
        exit 1
    fi
else
    for candidate in python3.14 python3 "${HOME}/.local/bin/python3.14"; do
        resolved=$(command -v "$candidate" 2>/dev/null || true)
        if [ -n "$resolved" ] && supported "$resolved"; then
            bootstrap_python=$resolved
            break
        fi
    done
    if [ -z "$bootstrap_python" ]; then
        for candidate in uv "${HOME}/.local/bin/uv"; do
            resolved=$(command -v "$candidate" 2>/dev/null || true)
            if [ -n "$resolved" ]; then
                interpreter=$("$resolved" python find 3.14 --no-project --offline --no-python-downloads 2>/dev/null || true)
                if [ -n "$interpreter" ] && supported "$interpreter"; then
                    bootstrap_python=$interpreter
                    break
                fi
            fi
        done
    fi
fi

if [ -z "$bootstrap_python" ]; then
    echo 'No installed Python 3.14+ was found on PATH or through local uv.' >&2
    echo 'Install with the declared uv tooling, then run: uv python install 3.14 && make setup' >&2
    exit 1
fi
command -v git >/dev/null || { echo 'Git is required for source provenance.' >&2; exit 1; }
echo "Using Python: $bootstrap_python"
"$bootstrap_python" -m venv .venv
.venv/bin/python -m pip install -r artifacts/dependencies.lock.txt -r artifacts/dependencies-dev.lock.txt
.venv/bin/python -m pip check
