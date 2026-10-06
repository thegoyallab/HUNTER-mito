# HUNTER-v1.0 scientific freeze dossier for v0.7.23 NAR-readiness work

Date: 2026-10-06

## Certification result

**PASS â€” 38/38 fail-closed checks passed on Kairav.**

The verifier checked byte identity of the frozen model, ordered feature list, feature engine, scoring core, Core244 registry, H5 sequence freeze, H5/HPS golden vectors, locked validation result, and bundled production CLI. It also checked the 42-feature contract, Core244 31/213 class counts, H5 size and zero exact-sequence overlap with Core244, the exact threshold semantics, the no-retraining/no-recalibration validation locks, dynamic CLI integrity, package golden-vector parity, and a deliberate temporary corruption negative test.

Run:

```bash
cd <HUNTER_PROJECT_ROOT>/HUNTER_v1_FREEZE_DOSSIER_v0_7_23
python3 verify_hunter_v1_freeze.py
```

Latest result: `verification_report.json`.

## Frozen scientific identity

- Scientific model: **HUNTER-v1.0**
- Model SHA-256: `d916f1ad19aa830323373f4134ed3780dda2a065292f6c592cf764f4242c63d1`
- Ordered 42-feature list SHA-256: `49de523407d456ff1a4ca50d94f9221665decfb204bf99821fa3995d3b32eccb`
- Frozen feature-engine SHA-256: `4dffc54ce2317305139580859dc0b48e57bfedd70f5e723a84a4076ce19c2502`
- Public scoring core SHA-256: `2e35433b3c3dd7478c3fe645d119956834a285fa2cfb8991890f10db5f6af21d`
- Threshold: **0.5428662440774465**
- Call rule: **score >= threshold**
- Score semantics: class-1 probability from `predict_proba`
- Model: VarianceThreshold â†’ StandardScaler â†’ Elastic-Net LogisticRegression
- Logistic regression: C=0.01, l1_ratio=0.5, solver=saga
- Features: 42 generic N-terminal descriptors over N30, N60 and N100 windows

The task is sequence-architecture discrimination among proteins already established as mitochondrial; HUNTER-v1 is not a general mitochondrial-localization probability.

## Training and validation provenance

Core244 is frozen at 244 proteins: 31 ncMTS/non-classical positives and 213 classical cleavable-presequence references. The authoritative Core244 registry SHA-256 is `9a29cee323e0b881fb7920a2574427cae5329805d153800e864b2b29e963c94b`.

The Stage24H3C threshold was derived as the median of five outer-fold thresholds, with each threshold selected only within its corresponding outer-training partition. Challenge14 was not used for candidate selection.

H5 is frozen at 26 proteins: H5-I primary N=20 and H5-II secondary N=6. The H5 sequence-cache SHA-256 is `5339820e613e065bc23f3c68503781ca88a8829b09865469356e0d69364faef9`. Exact sequence duplicates between H5 and Core244: **0**.

Locked H5-I metrics are AP 0.9375, AUROC 0.91, MCC 0.57735, balanced accuracy 0.75, sensitivity 0.50, specificity 1.00, precision 1.00 and F1 0.6667. No retraining, recalibration, feature selection, threshold change or post-scoring label change occurred during locked external validation.

## Direct parity evidence

On 2026-10-06 the public scoring package reproduced:
- H5: 26/26, maximum absolute score delta `1.1102230246251565e-16`
- HPS golden sample: 21/21, maximum absolute score delta `2.220446049250313e-16`
- all frozen threshold calls exactly

The authoritative parity tolerance in `tests/test_parity.py` is absolute tolerance **1e-10**; threshold calls must match exactly.

The bundled Linux executable in v0.7.22 and the local v0.7.23 package is byte-identical:
`9f99ba5ab6d8fdc4d35695e8a676c8ede586a9929da07aa533a0a0321f0fd555`.

Its `validate-installation` command independently reported PASS and the same model, feature-list, feature-engine, feature-count and threshold values.

## Resolution of the Deep Research lineage conflict

The canonical lineage is the **d916â€¦ model / 49deâ€¦ feature-list** lineage.

It is present with identical hashes in Stage24H3C, the Master Freeze, the manuscript reproducibility package, the HPS11 public repository assembly, the final software release candidate and the Windows submission deposit.

The actual `prepare_HUNTER_repo_deposit.py` copies the HPS11A4 final software release candidate directly into the Windows submission-deposit folder.

No `HUNTER_FINAL_MODEL.joblib`, `HUNTER_FLOAT64_RETRAIN_FINAL`, or matching `4a296â€¦ / 670eâ€¦` artifact was found in the canonical Kairav HUNTER project tree. That competing Deep Research lineage is therefore rejected as non-authoritative.

## Release-layer issues still to remediate before v0.7.23 is tagged/deployed

1. Restore/preserve the original 10-sequence deterministic regression fixture. The local v0.7.23 package currently overwrote it with a biological example set.
2. Create a separate public 5+5 example from frozen validation/reference material.
3. Benchmark synchronous web performance before deciding whether persistent `/results/<id>` storage is needed.
4. Regenerate repository/package manifests for the actual v1.0.1 wheel. The inherited `PACKAGE_MANIFEST.json` still describes v1.0.0 and its older wheel.
5. Create a dedicated v0.7.23 web manifest; the inherited generic `WEB_INTERFACE_MANIFEST.json` is stale.
6. Complete clean-profile Chrome and Firefox cookie/storage/network QA after deployment.
7. Complete public repository URL, archival DOI and final software-contributor metadata before final release tagging.

No scientific-model development is required or permitted as part of these release-layer remediations.
