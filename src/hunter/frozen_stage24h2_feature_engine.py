#!/usr/bin/env python3
"""
STAGE24H2 — Interpretable sequence feature-matrix freeze
HUNTER — Human mitochondrial targeting and N-terminome evidence resource

Primary purpose
---------------
Construct a frozen, biologically interpretable feature matrix for:
  (A) Core244: 31 ncMTS Gold positives vs 213 classical-presequence references
  (B) Challenge14: external non-mitochondrial specificity set

This stage performs NO model fitting, NO feature selection, NO threshold
optimization, and NO biological relabeling.

Input directories under ~/mitochondrial_targeting/HUNTER_2026
---------------------------------------------------------------
HUNTER_Stage24H1B_SequenceLeakageFreeze_v0_1_results/
  Stage24H1B_uniprot_canonical_sequence_cache.csv
  Stage24H1B_final_leakage_groups.csv

HUNTER_Stage24H1C_SequenceQC_v0_1_results/
  Stage24H1C_challenge14_sequence_cache.csv

Output
------
HUNTER_Stage24H2_FeatureMatrix_v0_1_results/
"""

from __future__ import annotations
import argparse, csv, hashlib, json, math, re
from collections import Counter
from pathlib import Path

KD = {
    "I":4.5,"V":4.2,"L":3.8,"F":2.8,"C":2.5,"M":1.9,"A":1.8,"G":-0.4,
    "T":-0.7,"S":-0.8,"W":-0.9,"Y":-1.3,"P":-1.6,"H":-3.2,"E":-3.5,
    "Q":-3.5,"D":-3.5,"N":-3.5,"K":-3.9,"R":-4.5,
}
HYDRO = set("AILMFWVYC")
AROM = set("FWY")
SMALL = set("AGST")
POLAR_UNCHARGED = set("NQST")
HELIX_BREAK = set("PG")
AA20 = "ACDEFGHIKLMNPQRSTVWY"

# Predeclared windows. These are fixed before model fitting.
N_WINDOWS = (30,60,100)
C_WINDOWS = (30,60)
HYDRO_WINDOW = 19
HM_ANGLE = 100.0
HYDRO_THRESHOLDS = (1.2,1.6)

def clean(x):
    return "" if x is None else str(x).strip()

def sha256_file(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""):
            h.update(c)
    return h.hexdigest()

def read_csv(p):
    with p.open(newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write_csv(p,rows,fields=None,delimiter=","):
    rows=list(rows)
    if fields is None:
        fields=list(rows[0].keys()) if rows else []
    with p.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,delimiter=delimiter,extrasaction="ignore")
        w.writeheader(); w.writerows(rows)

def frac(seq, chars):
    if not seq: return 0.0
    return sum(a in chars for a in seq)/len(seq)

def mean_kd(seq):
    if not seq: return 0.0
    return sum(KD[a] for a in seq)/len(seq)

def hm(seq, angle_deg=100.0):
    """Hydrophobic moment using KD scale and fixed alpha-helical angle."""
    if not seq: return 0.0
    ang=math.radians(angle_deg)
    x=sum(KD[a]*math.cos(i*ang) for i,a in enumerate(seq))
    y=sum(KD[a]*math.sin(i*ang) for i,a in enumerate(seq))
    return math.sqrt(x*x+y*y)/len(seq)

def entropy(seq):
    if not seq: return 0.0
    n=len(seq)
    c=Counter(seq)
    return -sum((v/n)*math.log2(v/n) for v in c.values())

def terminal_window(seq, n, side):
    if side=="N": return seq[:min(n,len(seq))]
    return seq[max(0,len(seq)-n):]

def terminal_features(seq, prefix):
    L=len(seq)
    out={}
    out[f"{prefix}_Len"]=L
    out[f"{prefix}_BasicFrac"]=frac(seq,set("KR"))
    out[f"{prefix}_AcidicFrac"]=frac(seq,set("DE"))
    out[f"{prefix}_NetChargeProxyPerRes"]=(
        (sum(a in "KR" for a in seq)-sum(a in "DE" for a in seq))/L if L else 0.0
    )
    out[f"{prefix}_ArgFrac"]=frac(seq,{"R"})
    out[f"{prefix}_LysFrac"]=frac(seq,{"K"})
    out[f"{prefix}_ProFrac"]=frac(seq,{"P"})
    out[f"{prefix}_GlyFrac"]=frac(seq,{"G"})
    out[f"{prefix}_CysFrac"]=frac(seq,{"C"})
    out[f"{prefix}_HydrophobicFrac"]=frac(seq,HYDRO)
    out[f"{prefix}_AromaticFrac"]=frac(seq,AROM)
    out[f"{prefix}_MeanKD"]=mean_kd(seq)
    out[f"{prefix}_HM100"]=hm(seq,100.0)
    out[f"{prefix}_Entropy"]=entropy(seq)
    return out

def kd_windows(seq,w=19):
    if len(seq)<w:
        return [(1,len(seq),mean_kd(seq))] if seq else []
    return [(i+1,i+w,sum(KD[a] for a in seq[i:i+w])/w)
            for i in range(len(seq)-w+1)]

def hm_windows(seq,w=19):
    if len(seq)<w:
        return [(1,len(seq),hm(seq))] if seq else []
    return [(i+1,i+w,hm(seq[i:i+w])) for i in range(len(seq)-w+1)]

def best_in_region(windows,start=None,end=None):
    arr=[]
    for s,e,v in windows:
        if start is not None and s<start: continue
        if end is not None and e>end: continue
        arr.append((s,e,v))
    if not arr:
        return (0,0,0.0)
    return max(arr,key=lambda x:x[2])

def top_separated_peaks(windows,min_sep=19,k=3):
    selected=[]
    for item in sorted(windows,key=lambda x:x[2],reverse=True):
        s,e,v=item
        if all(abs(s-ss)>=min_sep for ss,ee,vv in selected):
            selected.append(item)
            if len(selected)>=k: break
    while len(selected)<k:
        selected.append((0,0,0.0))
    return selected

def threshold_runs(windows,thr):
    """Count contiguous runs of windows with KD mean >= fixed threshold."""
    n=0; inrun=False
    for s,e,v in windows:
        if v>=thr and not inrun:
            n+=1; inrun=True
        elif v<thr:
            inrun=False
    return n

def cys_features(seq):
    pos=[i+1 for i,a in enumerate(seq) if a=="C"]
    gaps=[b-a-1 for a,b in zip(pos,pos[1:])]
    out={
        "Cys_Count":len(pos),
        "Cys_Frac":len(pos)/len(seq) if seq else 0.0,
        "Cys_N100_Count":seq[:100].count("C"),
        "Cys_Post60_Count":seq[60:].count("C") if len(seq)>60 else 0,
        "Cys_MinGap":min(gaps) if gaps else -1,
        "Cys_MedianGap":0.0,
        "Cys_MaxGap":max(gaps) if gaps else -1,
        "CysPair_Gap3_Count":sum(g==3 for g in gaps),
        "CysPair_Gap9_Count":sum(g==9 for g in gaps),
        "Motif_CX3C_Count":len(re.findall(r"C...C",seq)),
        "Motif_CX9C_Count":len(re.findall(r"C.........C",seq)),
    }
    if gaps:
        sg=sorted(gaps); m=len(sg)//2
        out["Cys_MedianGap"]=(sg[m] if len(sg)%2 else (sg[m-1]+sg[m])/2)
    # Maximum cysteine count in any 50-aa window.
    if len(seq)<=50:
        out["Cys_MaxCount50"]=seq.count("C")
    else:
        out["Cys_MaxCount50"]=max(seq[i:i+50].count("C") for i in range(len(seq)-49))
    return out

def carrier_diagnostic(seq):
    # Diagnostic only: classic mitochondrial-carrier signature motif family.
    # Kept OUT of primary generic feature list.
    patterns=[
        re.compile(r"P.[DE]..[KR]"),
        re.compile(r"[DE]G....[WYF][KR]G"),
    ]
    return {
        "Diag_CarrierMotif_PxDExxKR_like":sum(len(p.findall(seq)) for p in patterns[:1]),
        "Diag_CarrierMotif_secondary_like":sum(len(p.findall(seq)) for p in patterns[1:]),
    }

def sequence_features(seq):
    L=len(seq)
    out={
        "SeqLength":L,
        "Global_BasicFrac":frac(seq,set("KR")),
        "Global_AcidicFrac":frac(seq,set("DE")),
        "Global_NetChargeProxyPerRes":(
            (sum(a in "KR" for a in seq)-sum(a in "DE" for a in seq))/L if L else 0.0
        ),
        "Global_HydrophobicFrac":frac(seq,HYDRO),
        "Global_AromaticFrac":frac(seq,AROM),
        "Global_SmallFrac":frac(seq,SMALL),
        "Global_PolarUnchargedFrac":frac(seq,POLAR_UNCHARGED),
        "Global_HelixBreakFrac":frac(seq,HELIX_BREAK),
        "Global_MeanKD":mean_kd(seq),
        "Global_Entropy":entropy(seq),
    }
    for aa in AA20:
        out[f"AAfrac_{aa}"]=seq.count(aa)/L if L else 0.0

    for n in N_WINDOWS:
        out.update(terminal_features(terminal_window(seq,n,"N"),f"N{n}"))
    for n in C_WINDOWS:
        out.update(terminal_features(terminal_window(seq,n,"C"),f"C{n}"))

    kd=kd_windows(seq,HYDRO_WINDOW)
    hmw=hm_windows(seq,HYDRO_WINDOW)
    g=best_in_region(kd)
    n60=best_in_region(kd,end=min(60,L))
    post60=best_in_region(kd,start=61) if L>=HYDRO_WINDOW+60 else (0,0,0.0)
    c60=best_in_region(kd,start=max(1,L-60+1))
    hmmax=best_in_region(hmw)

    out.update({
        "KD19_GlobalMax":g[2],
        "KD19_GlobalMaxStart":g[0],
        "KD19_GlobalMaxRelStart":g[0]/L if L else 0.0,
        "KD19_GlobalMaxDistanceToC":max(0,L-g[1]) if g[1] else 0,
        "KD19_N60Max":n60[2],
        "KD19_Post60Max":post60[2],
        "KD19_C60Max":c60[2],
        "HM19_GlobalMax":hmmax[2],
        "HM19_GlobalMaxRelStart":hmmax[0]/L if L else 0.0,
    })

    peaks=top_separated_peaks(kd,19,3)
    for i,(s,e,v) in enumerate(peaks,1):
        out[f"KD19_Peak{i}"]=v
        out[f"KD19_Peak{i}_RelStart"]=s/L if (L and s) else 0.0

    for thr in HYDRO_THRESHOLDS:
        tag=str(thr).replace(".","p")
        out[f"KD19_RunCount_ge_{tag}"]=threshold_runs(kd,thr)

    # Charge/hydropathy contrasts are generic positional descriptors.
    out["Contrast_N30_minus_C30_MeanKD"]=out["N30_MeanKD"]-out["C30_MeanKD"]
    out["Contrast_N30_minus_Post60_KD"]=out["N30_MeanKD"]-out["KD19_Post60Max"]
    out["Contrast_C30_minus_N30_BasicFrac"]=out["C30_BasicFrac"]-out["N30_BasicFrac"]
    out["Contrast_N30_minus_C30_AcidicFrac"]=out["N30_AcidicFrac"]-out["C30_AcidicFrac"]

    out.update(cys_features(seq))
    out.update(carrier_diagnostic(seq))
    return out

def feature_dictionary(feature_names):
    rows=[]
    diagnostic={"Diag_CarrierMotif_PxDExxKR_like","Diag_CarrierMotif_secondary_like",
                "Motif_CX3C_Count","Motif_CX9C_Count","CysPair_Gap3_Count","CysPair_Gap9_Count"}
    for f in feature_names:
        if f in diagnostic:
            block="MECHANISM_DIAGNOSTIC"
            use="DIAGNOSTIC_OR_ABLATION_NOT_PRIMARY_BASELINE"
        elif f.startswith(("N30_","N60_","N100_")):
            block="N_TERMINAL"
            use="PRIMARY_GENERIC"
        elif f.startswith(("C30_","C60_")):
            block="C_TERMINAL"
            use="PRIMARY_GENERIC"
        elif f.startswith(("KD19_","HM19_")):
            block="POSITIONAL_HYDROPATHY"
            use="PRIMARY_GENERIC"
        elif f.startswith("Cys_") or f=="Cys_Count" or f=="Cys_Frac" or f=="Cys_MaxCount50":
            block="CYSTEINE_ARCHITECTURE"
            use="PRIMARY_GENERIC"
        elif f.startswith("AAfrac_") or f.startswith("Global_"):
            block="GLOBAL_COMPOSITION"
            use="PRIMARY_GENERIC"
        elif f.startswith("Contrast_"):
            block="POSITIONAL_CONTRAST"
            use="PRIMARY_GENERIC"
        elif f=="SeqLength":
            block="GLOBAL_COMPOSITION"; use="PRIMARY_GENERIC"
        else:
            block="OTHER"; use="PRIMARY_GENERIC"
        rows.append({"Feature":f,"Feature_Block":block,"Planned_Use":use})
    return rows

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",default=str(Path.home()/"mitochondrial_targeting"/"HUNTER_2026"))
    args=ap.parse_args()
    root=Path(args.root).expanduser().resolve()

    h1b=root/"HUNTER_Stage24H1B_SequenceLeakageFreeze_v0_1_results"
    h1c=root/"HUNTER_Stage24H1C_SequenceQC_v0_1_results"

    core_cache=h1b/"Stage24H1B_uniprot_canonical_sequence_cache.csv"
    leakage_file=h1b/"Stage24H1B_final_leakage_groups.csv"
    chal_cache=h1c/"Stage24H1C_challenge14_sequence_cache.csv"

    for p in (core_cache,leakage_file,chal_cache):
        if not p.exists(): raise FileNotFoundError(p)

    out=root/"HUNTER_Stage24H2_FeatureMatrix_v0_1_results"
    out.mkdir(parents=True,exist_ok=True)

    core=read_csv(core_cache)
    leakage=read_csv(leakage_file)
    chal=read_csv(chal_cache)

    if len(core)!=244: raise RuntimeError(f"Expected 244 core records, got {len(core)}")
    if len(chal)!=14: raise RuntimeError(f"Expected 14 challenge records, got {len(chal)}")
    if len(leakage)!=244: raise RuntimeError(f"Expected 244 leakage rows, got {len(leakage)}")

    lg={r["UniProt_ID"]:r["Leakage_Group"] for r in leakage}
    if len(lg)!=244: raise RuntimeError("Leakage-group mapping is not unique.")

    core_rows=[]
    feature_names=None
    for r in core:
        seq=r["Sequence"].strip().upper()
        if not seq or set(seq)-set(AA20):
            raise RuntimeError(f"Invalid sequence for {r['Gene']} {r['Requested_UniProt_ID']}")
        f=sequence_features(seq)
        if feature_names is None: feature_names=list(f.keys())
        core_rows.append({
            "Gene":r["Gene"],
            "UniProt_ID":r["Requested_UniProt_ID"],
            "Core_Label":r["Core_Label"],
            "Binary_Target":int(r["Binary_Target"]),
            "Mechanism_Code":r["Mechanism_Code"],
            "Leakage_Group":lg[r["Requested_UniProt_ID"]],
            **f
        })

    chal_rows=[]
    for r in chal:
        seq=r["Sequence"].strip().upper()
        if not seq or set(seq)-set(AA20):
            raise RuntimeError(f"Invalid challenge sequence for {r['Gene']} {r['UniProt_ID']}")
        f=sequence_features(seq)
        chal_rows.append({
            "Gene":r["Gene"],
            "UniProt_ID":r["UniProt_ID"],
            "Challenge_Lane":r["Challenge_Lane"],
            "Documented_Destination":r["Documented_Destination"],
            "Evaluation_Role":"EXTERNAL_SPECIFICITY_CHALLENGE",
            **f
        })

    core_path=out/"Stage24H2_Core244_feature_matrix.csv"
    chal_path=out/"Stage24H2_Challenge14_feature_matrix.csv"
    write_csv(core_path,core_rows)
    write_csv(chal_path,chal_rows)

    fd=feature_dictionary(feature_names)
    write_csv(out/"Stage24H2_feature_dictionary.csv",fd)

    primary=[r["Feature"] for r in fd if r["Planned_Use"]=="PRIMARY_GENERIC"]
    diagnostic=[r["Feature"] for r in fd if r["Planned_Use"]!="PRIMARY_GENERIC"]
    (out/"Stage24H2_primary_generic_features.txt").write_text("\n".join(primary)+"\n",encoding="utf-8")
    (out/"Stage24H2_diagnostic_features.txt").write_text("\n".join(diagnostic)+"\n",encoding="utf-8")

    # QC: finite numeric features and invariant labels/groups.
    problems=[]
    for dataset,rows in [("CORE244",core_rows),("CHALLENGE14",chal_rows)]:
        for r in rows:
            for f in feature_names:
                v=r[f]
                if not isinstance(v,(int,float)) or not math.isfinite(float(v)):
                    problems.append((dataset,r["Gene"],f,v))
    if problems:
        raise RuntimeError(f"Non-finite feature values detected: {problems[:10]}")

    labels=Counter(r["Core_Label"] for r in core_rows)
    binary=Counter(r["Binary_Target"] for r in core_rows)
    groups=set(r["Leakage_Group"] for r in core_rows)
    positive_groups=set(r["Leakage_Group"] for r in core_rows if r["Binary_Target"]==1)

    if labels!=Counter({"CLASSICAL_MTS_REF_NEG":213,"NCMTS_GOLD_POS":31}):
        raise RuntimeError(f"Unexpected labels: {labels}")
    if len(groups)!=222 or len(positive_groups)!=20:
        raise RuntimeError(f"Unexpected leakage groups: all={len(groups)} positive={len(positive_groups)}")

    # Descriptive feature-block inventory only; no class statistics and no selection.
    block_counts=Counter(r["Feature_Block"] for r in fd)
    write_csv(out/"Stage24H2_feature_block_counts.csv",
              [{"Feature_Block":k,"N":v} for k,v in sorted(block_counts.items())])

    summary={
        "stage":"STAGE24H2",
        "version":"v0.1",
        "status":"PASS_FEATURE_MATRIX_FREEZE",
        "core244":{"total":244,"positive":31,"classical_reference":213,
                   "leakage_groups":222,"positive_leakage_groups":20},
        "challenge14":{"total":14,"training_use":"NONE"},
        "n_total_features":len(feature_names),
        "n_primary_generic_features":len(primary),
        "n_mechanism_diagnostic_features":len(diagnostic),
        "feature_blocks":dict(sorted(block_counts.items())),
        "external_predictor_outputs_used_as_features":"NO",
        "model_fitting":"NONE",
        "feature_selection":"NONE",
        "threshold_tuning":"NONE",
        "source_hashes":{
            core_cache.name:sha256_file(core_cache),
            leakage_file.name:sha256_file(leakage_file),
            chal_cache.name:sha256_file(chal_cache)
        },
        "next_stage":"STAGE24H3 group-aware baseline modeling + nested CV design freeze"
    }
    (out/"Stage24H2_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")

    qc=[
        "STAGE24H2 — INTERPRETABLE FEATURE-MATRIX FREEZE",
        "="*62,
        "Core244 rows: 244",
        "Core positives/classical refs: 31/213",
        "Leakage groups: 222",
        "Positive leakage groups: 20",
        "Challenge14 rows: 14",
        f"Total numeric sequence features: {len(feature_names)}",
        f"Primary generic features: {len(primary)}",
        f"Mechanism-diagnostic/ablation features: {len(diagnostic)}",
        "Non-finite values: 0",
        "External predictor outputs used as model features: NO",
        "Model fitting: NONE",
        "Feature selection: NONE",
        "Threshold tuning: NONE",
        "",
        "STAGE24H2 FEATURE-MATRIX FREEZE: PASS"
    ]
    (out/"Stage24H2_QC.txt").write_text("\n".join(qc)+"\n",encoding="utf-8")

    targets=sorted(p for p in out.iterdir() if p.is_file())
    manifest=[{"File":p.name,"SHA256":sha256_file(p),"Bytes":p.stat().st_size} for p in targets]
    write_csv(out/"Stage24H2_manifest_sha256.tsv",manifest,delimiter="\t")

    print("\n".join(qc))
    print("\nFEATURE BLOCKS")
    for k,v in sorted(block_counts.items()):
        print(f"{k:<28} {v}")
    print("\nOUTPUT DIRECTORY")
    print(out)

if __name__=="__main__":
    main()
