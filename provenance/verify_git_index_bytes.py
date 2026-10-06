#!/usr/bin/env python3
from pathlib import Path
import hashlib
import subprocess
import sys

root=Path(__file__).resolve().parents[1]
out=subprocess.check_output(["git","-C",str(root),"diff","--cached","--name-only","--diff-filter=ACMR"], text=True)
paths=[x for x in out.splitlines() if x]
mismatches=[]
for rel in paths:
    p=root/rel
    if not p.is_file():
        continue
    work=p.read_bytes()
    idx=subprocess.check_output(["git","-C",str(root),"show",f":{rel}"])
    if work != idx:
        mismatches.append({
            "path": rel,
            "working_sha256": hashlib.sha256(work).hexdigest(),
            "index_sha256": hashlib.sha256(idx).hexdigest(),
            "working_bytes": len(work),
            "index_bytes": len(idx),
        })
print(f"STAGED_FILES_CHECKED={len(paths)}")
print(f"BYTE_MISMATCHES={len(mismatches)}")
for m in mismatches:
    print(m)
sys.exit(1 if mismatches else 0)
