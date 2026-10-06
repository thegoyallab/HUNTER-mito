#!/usr/bin/env python3
from pathlib import Path
import sys

p=Path(__file__).resolve().parents[1] / "CITATION.cff"
try:
    import yaml
except Exception as e:
    print("PYAML_IMPORT_FAIL", repr(e))
    sys.exit(2)

d=yaml.safe_load(p.read_text(encoding="utf-8"))
required=["cff-version","message","title","type","version","authors","license"]
missing=[k for k in required if k not in d]
assert not missing, f"Missing CFF keys: {missing}"
assert d["cff-version"] == "1.2.0"
assert d["type"] == "software"
assert d["version"] == "1.0.1"
assert d["license"] == "BSD-3-Clause"
assert isinstance(d["authors"], list) and len(d["authors"]) == 1
a=d["authors"][0]
assert a["given-names"] == "Pankaj"
assert a["family-names"] == "Goyal"
assert a["affiliation"] == "Department of Biotechnology, Central University of Rajasthan, India"
print("CITATION_CFF_YAML_AND_REQUIRED_FIELDS_PASS")
print("SOFTWARE_CREATORS=1")
print("PRIMARY_SOFTWARE_CREATOR=Pankaj Goyal")
