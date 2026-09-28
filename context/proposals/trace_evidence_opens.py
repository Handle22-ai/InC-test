import os, sys
_log = os.environ.get("EVIDENCE_OPEN_LOG")
if _log:
    def _hook(event, args):
        if event in ("open", "os.listdir", "os.scandir") and args and isinstance(args[0], (str, bytes, os.PathLike)):
            p = os.fsdecode(args[0])
            if "/evidence/" in p or p.startswith("evidence/"):
                with open(_log, "a") as f:
                    f.write(event + "\t" + os.path.abspath(p) + "\n")
    sys.addaudithook(_hook)
