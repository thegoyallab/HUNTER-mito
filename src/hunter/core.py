from __future__ import annotations
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
import hashlib
import json
import re
import numpy as np
import joblib

from .frozen_stage24h2_feature_engine import sequence_features

VERSION = "1.0.0"
THRESHOLD = 0.5428662440774465
AA20 = set("ACDEFGHIKLMNPQRSTVWY")

@dataclass(frozen=True)
class HunterResult:
    identifier: str
    sequence_length: int
    hunter_score: float | None
    threshold: float
    threshold_call: str
    distance_from_threshold: float | None
    technical_status: str
    applicability_note: str
    interpretation: str
    features: dict[str, float] | None = None
    error: str = ""

def _resource(name: str) -> Path:
    return Path(str(files("hunter.data").joinpath(name)))

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()

def load_manifest() -> dict:
    return json.loads(_resource("model_manifest.json").read_text())

def load_features() -> list[str]:
    vals = [x.strip() for x in _resource("selected_features.txt").read_text().splitlines()
            if x.strip() and not x.startswith("#")]
    if len(vals) != 42 or len(set(vals)) != 42:
        raise RuntimeError(f"Frozen feature-list integrity failure: expected 42 unique features, found {len(vals)}")
    return vals

def load_model():
    model_path = _resource("HUNTER_v1.joblib")
    man = load_manifest()
    got = sha256_file(model_path)
    if got != man["model_sha256"]:
        raise RuntimeError(f"Frozen model SHA256 mismatch: {got}")
    model = joblib.load(model_path)
    if int(getattr(model, "n_features_in_", 42)) != 42:
        raise RuntimeError("Frozen model does not accept 42 features.")
    return model

def normalize_sequence(raw: str) -> str:
    return re.sub(r"\s+", "", str(raw)).upper()

def validate_sequence(seq: str) -> tuple[bool, str]:
    if not seq:
        return False, "EMPTY_SEQUENCE"
    invalid = sorted(set(seq) - AA20)
    if invalid:
        return False, "UNSUPPORTED_RESIDUES:" + ",".join(invalid)
    return True, ""

def score_sequence(sequence: str, identifier: str = "query", include_features: bool = False,
                   model=None, feature_order: list[str] | None = None) -> HunterResult:
    seq = normalize_sequence(sequence)
    ok, err = validate_sequence(seq)
    if not ok:
        return HunterResult(
            identifier=identifier, sequence_length=len(seq), hunter_score=None,
            threshold=THRESHOLD, threshold_call="NOT_SCORED", distance_from_threshold=None,
            technical_status="ERROR_INVALID_SEQUENCE",
            applicability_note="Sequence-only technical gate failed; no HUNTER score produced.",
            interpretation="No biological interpretation should be made.",
            features=None, error=err
        )
    if model is None:
        model = load_model()
    if feature_order is None:
        feature_order = load_features()
    fv = sequence_features(seq)
    missing = [f for f in feature_order if f not in fv]
    if missing:
        raise RuntimeError("Frozen feature engine missing feature(s): " + ",".join(missing))
    arr = np.asarray([[float(fv[f]) for f in feature_order]], dtype=float)
    if not np.isfinite(arr).all():
        raise RuntimeError("Non-finite frozen feature value(s).")
    score = float(model.predict_proba(arr)[0, 1])
    call = "ABOVE_THRESHOLD" if score >= THRESHOLD else "BELOW_THRESHOLD"
    interp = (
        "ncMTS-like sequence architecture priority; mitochondrial localization requires independent evidence."
        if call == "ABOVE_THRESHOLD"
        else "Below frozen HUNTER v1 threshold; this is non-exclusionary for non-classical targeting."
    )
    return HunterResult(
        identifier=identifier, sequence_length=len(seq), hunter_score=score,
        threshold=THRESHOLD, threshold_call=call, distance_from_threshold=score - THRESHOLD,
        technical_status="SCORED",
        applicability_note="Sequence-only scoring completed. Biological applicability/localization must be assessed independently.",
        interpretation=interp,
        features={f: float(fv[f]) for f in feature_order} if include_features else None,
        error=""
    )

def parse_fasta(path: str | Path):
    path = Path(path)
    cur = None
    buf = []
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            line = raw.strip()
            if not line:
                continue
            if line.startswith(">"):
                if cur is not None:
                    yield cur, "".join(buf)
                header = line[1:].strip()
                token = header.split()[0] if header else "unnamed"
                parts = token.split("|")
                cur = parts[1] if len(parts) >= 3 else token
                buf = []
            else:
                buf.append(line)
        if cur is not None:
            yield cur, "".join(buf)

def result_to_row(r: HunterResult, include_features: bool = False) -> dict:
    row = {
        "Identifier": r.identifier,
        "Sequence_Length": r.sequence_length,
        "HUNTER_Version": "HUNTER-v1.0",
        "HUNTER_Score": r.hunter_score,
        "Frozen_Threshold": r.threshold,
        "Threshold_Call": r.threshold_call,
        "Distance_From_Threshold": r.distance_from_threshold,
        "Technical_Status": r.technical_status,
        "Applicability_Note": r.applicability_note,
        "Interpretation": r.interpretation,
        "Error": r.error,
    }
    if include_features and r.features:
        row.update(r.features)
    return row

def installation_integrity() -> dict:
    man = load_manifest()
    modelp = _resource("HUNTER_v1.joblib")
    featp = _resource("selected_features.txt")
    enginep = Path(__file__).parent / "frozen_stage24h2_feature_engine.py"
    checks = {
        "model_sha256_expected": man["model_sha256"],
        "model_sha256_observed": sha256_file(modelp),
        "feature_list_sha256_expected": man["feature_list_sha256"],
        "feature_list_sha256_observed": sha256_file(featp),
        "feature_engine_sha256_expected": man["feature_engine_sha256"],
        "feature_engine_sha256_observed": sha256_file(enginep),
        "feature_count": len(load_features()),
        "threshold": THRESHOLD,
    }
    checks["pass"] = (
        checks["model_sha256_expected"] == checks["model_sha256_observed"]
        and checks["feature_list_sha256_expected"] == checks["feature_list_sha256_observed"]
        and checks["feature_engine_sha256_expected"] == checks["feature_engine_sha256_observed"]
        and checks["feature_count"] == 42
    )
    model = load_model()
    checks["model_n_features_in"] = int(getattr(model, "n_features_in_", 42))
    checks["pass"] = bool(checks["pass"] and checks["model_n_features_in"] == 42)
    return checks
