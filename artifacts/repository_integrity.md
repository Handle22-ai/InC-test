# Repository integrity

Initial inspection found no Git metadata. User explicitly authorized initializing Git from the
current files, creating snapshot `765442763efef85b72b1c0abf25c853177684f3a`.
This is a clean local inherited baseline, not a claim of verified original upstream provenance.
The earlier preflight blocker is preserved in that root commit.

Inherited inventory: 97 project files; 119 regular files including virtual-environment and IDE
artifacts. Exclusions and SHA-256 hashes are explicit in inherited_manifest.json. Source, labeled
HTML, samples, docs and supplied old results are all covered. Supplied old outputs remain unchanged
and are not accepted as fresh evidence. No inherited files have been edited.

.env is ignored by the root .gitignore and absent from the Git index. Its values have not been
printed, copied, committed or written into artifacts. Credential presence was verified in memory.
Dependencies were installed in the root virtual environment; inherited/.venv is not used.

The physical workspace path is this repository. It has no enclosing Git workspace and no inherited
project symlinks/hardlinked regular files. User states only one coding agent operates here.
A local nonblocking file lock prevents overlapping harness evaluations; every run/scenario gets
its own state database. No external application state or another workspace database is used.
These checks do not establish OS-wide exclusive access; a separate process could still write files.
Before/after inherited content hashes detect changes in the retained input inventory.
