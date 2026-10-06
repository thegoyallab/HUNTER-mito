#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve().parent
DEFAULT_ROOT = HERE.parent
MANIFEST_PATH = HERE / "FREEZE_MANIFEST.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def add(checks, name, passed, detail):
    checks.append({"check": name, "pass": bool(passed), "detail": detail})


def read_csv_rows(path: Path, delimiter=","):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter=delimiter))


def run(cmd, *, cwd=None, env=None, timeout=180):
    p = subprocess.run(
        [str(x) for x in cmd],
        cwd=str(cwd) if cwd else None,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    return p.returncode, p.stdout


def main():
    ap = argparse.ArgumentParser(description="Fail-closed verifier for the frozen HUNTER-v1.0 scientific core.")
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="HUNTER_2026 project root")
    ap.add_argument("--static-only", action="store_true", help="Skip executable/package parity checks")
    ap.add_argument("--report", type=Path, default=HERE / "verification_report.json")
    args = ap.parse_args()

    root = args.root.resolve()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    checks = []

    # 1. Byte identity of every authoritative file.
    for item in manifest["authoritative_files"]:
        p = root / item["path"]
        if not p.is_file():
            add(checks, f"sha256:{item['role']}", False, f"MISSING {p}")
            continue
        observed = sha256(p)
        add(
            checks,
            f"sha256:{item['role']}",
            observed == item["sha256"],
            {"expected": item["sha256"], "observed": observed, "path": str(p)},
        )

    # 2. Core244 identity and class counts.
    core = root / "HUNTER_Stage24H1A_CoreTrainingUniverse_v0_1/Stage24H1A_core244_label_registry.csv"
    rows = read_csv_rows(core)
    labels = Counter(r["Core_Label"] for r in rows)
    targets = Counter(r["Binary_Target"] for r in rows)
    add(checks, "Core244:n", len(rows) == 244, {"observed": len(rows)})
    add(
        checks,
        "Core244:labels",
        labels == Counter({"CLASSICAL_MTS_REF_NEG": 213, "NCMTS_GOLD_POS": 31}),
        dict(labels),
    )
    add(checks, "Core244:binary_targets", targets == Counter({"0": 213, "1": 31}), dict(targets))

    # 3. Frozen ordered feature contract.
    feat = root / "HUNTER_Stage24H3C_CompactCandidate_v0_1_results/Stage24H3C_selected_features.txt"
    features = [x.strip() for x in feat.read_text(encoding="utf-8").splitlines() if x.strip()]
    add(checks, "feature_count", len(features) == 42, {"observed": len(features)})
    add(
        checks,
        "feature_windows",
        all(x.startswith(("N30_", "N60_", "N100_")) for x in features),
        {"first": features[:3], "last": features[-3:]},
    )

    # 4. H5 sequence freeze and leakage boundary.
    seqcache = root / "HUNTER_Stage24H5A_SequenceFreeze_v0_1_results/Stage24H5A_sequence_cache.csv"
    h5rows = read_csv_rows(seqcache)
    add(checks, "H5:sequence_cache_n", len(h5rows) == 26, {"observed": len(h5rows)})

    dup = root / "HUNTER_Stage24H5A_SequenceFreeze_v0_1_results/Stage24H5A_exact_sequence_duplicates_vs_Core244.csv"
    duprows = read_csv_rows(dup)
    add(checks, "H5:exact_sequence_duplicates_vs_Core244", len(duprows) == 0, {"observed": len(duprows)})

    # 5. Locked external-validation policy.
    h5b = root / "HUNTER_Stage24H5B_LockedExternalValidation_v0_1_results/Stage24H5B_locked_validation_result.json"
    vr = json.loads(h5b.read_text(encoding="utf-8"))
    add(checks, "H5B:status", vr.get("status") == "LOCKED_EXTERNAL_VALIDATION_COMPLETE", vr.get("status"))
    add(checks, "H5B:feature_count", vr.get("feature_count") == 42, vr.get("feature_count"))
    add(
        checks,
        "H5B:threshold",
        str(vr.get("frozen_threshold")) == "0.5428662440774465",
        vr.get("frozen_threshold"),
    )
    locks = {
        "retraining_performed": False,
        "recalibration_performed": False,
        "feature_selection_performed": False,
        "threshold_changed": False,
        "labels_changed_after_scoring": False,
    }
    add(checks, "H5B:no_postfreeze_science_changes", all(vr.get(k) == v for k, v in locks.items()), {k: vr.get(k) for k in locks})

    # 6. Golden-vector row counts.
    pkg = root / "HUNTER_HPS_v1/HPS11A4_Final_Software_Release_Candidate/HUNTER_v1_public_repo_v1.0.1"
    g_h5 = read_csv_rows(pkg / "tests/golden_vectors_h5.tsv", delimiter="\t")
    g_hps = read_csv_rows(pkg / "tests/golden_vectors_hps_sample.tsv", delimiter="\t")
    add(checks, "golden:H5_n", len(g_h5) == 26, {"observed": len(g_h5)})
    add(checks, "golden:HPS_n", len(g_hps) == 21, {"observed": len(g_hps)})

    # 7. Exact scoring semantics in the public core.
    core_py = (pkg / "src/hunter/core.py").read_text(encoding="utf-8")
    add(checks, "core:threshold_literal", "THRESHOLD = 0.5428662440774465" in core_py, "exact literal required")
    add(checks, "core:threshold_operator", 'score >= THRESHOLD' in core_py, ">= required")
    add(checks, "core:probability_class1", "model.predict_proba(arr)[0, 1]" in core_py, "class-1 probability required")

    # 8. Public model manifest contract.
    mm = json.loads((pkg / "src/hunter/data/model_manifest.json").read_text(encoding="utf-8"))
    contract = manifest["scientific_contract"]
    add(checks, "model_manifest:model_hash", mm.get("model_sha256") == contract["model_sha256"], mm.get("model_sha256"))
    add(checks, "model_manifest:feature_hash", mm.get("feature_list_sha256") == contract["feature_list_sha256"], mm.get("feature_list_sha256"))
    add(checks, "model_manifest:engine_hash", mm.get("feature_engine_sha256") == contract["feature_engine_sha256"], mm.get("feature_engine_sha256"))
    add(checks, "model_manifest:threshold", str(mm.get("threshold")) == contract["threshold_exact"], mm.get("threshold"))
    add(checks, "model_manifest:feature_count", mm.get("feature_count") == 42, mm.get("feature_count"))

    # 9. Negative corruption self-test without touching project assets.
    with tempfile.TemporaryDirectory(prefix="hunter-freeze-negative-") as td:
        src = feat
        tmp = Path(td) / "selected_features.txt"
        shutil.copy2(src, tmp)
        with tmp.open("ab") as f:
            f.write(b"\nCORRUPTION_TEST")
        negative_pass = sha256(tmp) != contract["feature_list_sha256"]
    add(checks, "negative_test:corruption_detected", negative_pass, "temporary copy deliberately altered")

    # 10. Dynamic executable/package parity.
    if not args.static_only:
        binary = root / manifest["production_binary"]["path"]
        rc, out = run([binary, "validate-installation"], cwd=binary.parent.parent)
        dyn_ok = False
        parsed = None
        if rc == 0:
            try:
                parsed = json.loads(out)
                dyn_ok = bool(parsed.get("pass"))
                dyn_ok = dyn_ok and parsed.get("model_sha256_observed") == contract["model_sha256"]
                dyn_ok = dyn_ok and parsed.get("feature_list_sha256_observed") == contract["feature_list_sha256"]
                dyn_ok = dyn_ok and parsed.get("feature_engine_sha256_observed") == contract["feature_engine_sha256"]
                dyn_ok = dyn_ok and parsed.get("feature_count") == 42
                dyn_ok = dyn_ok and str(parsed.get("threshold")) == contract["threshold_exact"]
            except Exception:
                dyn_ok = False
        add(checks, "dynamic:bundled_cli_validate_installation", dyn_ok, parsed if parsed is not None else out[-2000:])

        py = root / "hunter_env/bin/python"
        env = os.environ.copy()
        env["PYTHONPATH"] = str(pkg / "src")
        if py.is_file():
            rc, out = run([py, pkg / "tests/test_parity.py"], cwd=pkg, env=env)
            parity_ok = rc == 0 and "PARITY PASS" in out
            add(checks, "dynamic:package_golden_parity", parity_ok, out.strip())
        else:
            add(checks, "dynamic:package_golden_parity", False, f"missing validation interpreter {py}")

    passed = all(c["pass"] for c in checks)
    report = {
        "status": "PASS" if passed else "FAIL",
        "scientific_model": manifest["scientific_model"],
        "root": str(root),
        "static_only": args.static_only,
        "checks_total": len(checks),
        "checks_passed": sum(1 for c in checks if c["pass"]),
        "checks_failed": sum(1 for c in checks if not c["pass"]),
        "checks": checks,
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ["status", "checks_total", "checks_passed", "checks_failed"]}, indent=2))
    if not passed:
        for c in checks:
            if not c["pass"]:
                print("FAIL:", c["check"], c["detail"], file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
