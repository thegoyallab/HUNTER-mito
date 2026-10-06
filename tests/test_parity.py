from pathlib import Path
import pandas as pd
from hunter.core import score_sequence, load_model, load_features, installation_integrity

ATOL = 1e-10
ROOT = Path(__file__).resolve().parent
model = load_model()
features = load_features()
assert installation_integrity()["pass"]

def check(path, score_col):
    g = pd.read_csv(path, sep="\t", dtype={"Sequence": str})
    deltas = []
    for _, r in g.iterrows():
        x = score_sequence(r.Sequence, r.UniProt_ID, False, model, features)
        delta = abs(float(r[score_col]) - float(x.hunter_score))
        assert delta <= ATOL, (r.UniProt_ID, delta, r[score_col], x.hunter_score)
        assert x.threshold_call == r.Frozen_Call, (r.UniProt_ID, x.threshold_call, r.Frozen_Call)
        deltas.append(delta)
    return len(g), max(deltas)

n1, d1 = check(ROOT / "golden_vectors_h5.tsv", "Frozen_Score")
n2, d2 = check(ROOT / "golden_vectors_hps_sample.tsv", "HUNTER_v1_Score")

for seq, err in [
    ("", "EMPTY_SEQUENCE"),
    ("MABCZ", "UNSUPPORTED_RESIDUES:B,Z"),
    ("MA*AA", "UNSUPPORTED_RESIDUES:*"),
]:
    x = score_sequence(seq)
    assert x.technical_status == "ERROR_INVALID_SEQUENCE"
    assert x.error == err, (x.error, err)

print("PARITY PASS", {
    "H5_n": n1,
    "H5_max_abs_delta": d1,
    "HPS_n": n2,
    "HPS_max_abs_delta": d2,
})
