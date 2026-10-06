from __future__ import annotations
import argparse
import csv
import json
import sys

from .core import (
    score_sequence, parse_fasta, result_to_row, load_model, load_features,
    installation_integrity, VERSION
)

def write_rows(rows, outpath, delimiter="\t"):
    rows = list(rows)
    fields = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)
    if str(outpath) == "-":
        fh = sys.stdout
        close = False
    else:
        fh = open(outpath, "w", newline="", encoding="utf-8")
        close = True
    try:
        w = csv.DictWriter(fh, fieldnames=fields, delimiter=delimiter, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    finally:
        if close:
            fh.close()

def command_score(args):
    model = load_model()
    features = load_features()
    include = args.features == "all"
    rows = []
    if args.sequence is not None:
        r = score_sequence(args.sequence, args.id or "query", include, model, features)
        rows.append(result_to_row(r, include))
    else:
        for uid, seq in parse_fasta(args.fasta):
            r = score_sequence(seq, uid, include, model, features)
            rows.append(result_to_row(r, include))
    write_rows(rows, args.output, "\t")
    return 0 if all(r["Technical_Status"] == "SCORED" for r in rows) else 2


STABLE_FEATURES = [
    "N30_NetChargeProxyPerRes",
    "N30_AcidicFrac",
    "N60_NetChargeProxyPerRes",
    "N30_ArgFrac",
]

def _describe_record(sequence, identifier, model, features):
    r = score_sequence(sequence, identifier, True, model, features)
    row = result_to_row(r, False)
    row["Model_Task"] = "ncMTS/ncMLS-like versus classical cleavable-presequence sequence architecture"
    row["Model_Sequence_Representation"] = "N30|N60|N100 aggregate descriptors"
    row["Architecture_Region_Claim"] = "No residue-level HUNTER signal is inferred; v1 uses aggregate N30/N60/N100 features."
    if r.features:
        for f in STABLE_FEATURES:
            row[f] = r.features.get(f)
    row["Interpretation_Boundary"] = (
        "Sequence-level architecture evidence only; not proof of mitochondrial localization, "
        "mitochondrial import, or a functional targeting sequence."
    )
    return row

def command_describe(args):
    model = load_model()
    features = load_features()
    rows = []
    if args.sequence is not None:
        rows.append(_describe_record(args.sequence, args.id or "query", model, features))
    else:
        for uid, seq in parse_fasta(args.fasta):
            rows.append(_describe_record(seq, uid, model, features))
    write_rows(rows, args.output, "\t")
    return 0 if all(r["Technical_Status"] == "SCORED" for r in rows) else 2


def command_validate(args):
    d = installation_integrity()
    print(json.dumps(d, indent=2))
    return 0 if d["pass"] else 2

def command_manifest(args):
    from .core import load_manifest
    print(json.dumps(load_manifest(), indent=2))
    return 0

def build_parser():
    p = argparse.ArgumentParser(
        prog="hunter",
        description="HUNTER v1 frozen sequence-architecture scoring. Not a mitochondrial-localization predictor."
    )
    p.add_argument("--version", action="version", version=f"HUNTER {VERSION}")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("score", help="Score one sequence or a FASTA file.")
    g = s.add_mutually_exclusive_group(required=True)
    g.add_argument("--sequence", help="Single amino-acid sequence.")
    g.add_argument("--fasta", help="Input FASTA file.")
    s.add_argument("--id", help="Identifier for --sequence input.")
    s.add_argument("--output", default="-", help="TSV output path, or - for stdout.")
    s.add_argument("--features", choices=["none", "all"], default="none",
                   help="Include all 42 frozen feature values.")
    s.set_defaults(func=command_score)

    d = sub.add_parser("describe", help="Score and report frozen v1 architecture descriptors.")
    gd = d.add_mutually_exclusive_group(required=True)
    gd.add_argument("--sequence", help="Single amino-acid sequence.")
    gd.add_argument("--fasta", help="Input FASTA file.")
    d.add_argument("--id", help="Identifier for --sequence input.")
    d.add_argument("--output", default="-", help="TSV output path, or - for stdout.")
    d.set_defaults(func=command_describe)

    v = sub.add_parser("validate-installation", help="Verify frozen resource hashes and model shape.")
    v.set_defaults(func=command_validate)

    m = sub.add_parser("manifest", help="Print the frozen model manifest.")
    m.set_defaults(func=command_manifest)
    return p

def main():
    p = build_parser()
    args = p.parse_args()
    raise SystemExit(args.func(args))

if __name__ == "__main__":
    main()
