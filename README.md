# HUNTER v1

**HUNTER — Human mitochondrial targeting and N-terminome evidence resource**

HUNTER is a computational resource for prioritizing proteins with sequence features associated with non-classical mitochondrial targeting (ncMTS/ncMLS), supported by independent targeting and localization evidence.

## What HUNTER evaluates

HUNTER v1 evaluates aggregate N-terminal sequence descriptors and produces a model score relative to the validated decision threshold.

- model: elastic-net logistic regression
- sequence representation: 42 N-terminal descriptors
- windows: N30, N60 and N100
- decision threshold: 0.5428662440774465

An above-threshold result prioritizes a protein for further investigation. It does not by itself establish mitochondrial localization, mitochondrial import, or a functional targeting sequence. A below-threshold result does not exclude mitochondrial localization or an alternative targeting mechanism.

HUNTER v1 does not infer a residue-level targeting sequence.

## Commands

Run hunter validate-installation before use. The CLI supports score, describe, manifest and validate-installation commands for single sequences and FASTA input.

The describe command reports the HUNTER score together with four prespecified stable descriptors:

- N30_NetChargeProxyPerRes
- N30_AcidicFrac
- N60_NetChargeProxyPerRes
- N30_ArgFrac

These descriptors help explain the sequence-level basis of the model output; they are not independent localization tests.

## Complementary interpretation framework

HUNTER results may be interpreted alongside TargetP, MitoFates, TPpred3, DeepLoc, iMLP and PUPS. These methods provide complementary information on classical targeting, subcellular localization, internal targeting propensity and spatial/localization context. Their outputs remain independent and are not mathematically combined with the HUNTER v1 score.

Experimental evidence is required to establish mitochondrial localization, import or targeting mechanism.



## Web resource and reviewer test files

The public HUNTER v1 web resource is available at:

- https://hunter.goyal-lab.org/
- downloads and reviewer resources: https://hunter.goyal-lab.org/about#downloads

The live v0.7.23 web release uses a separate frozen H5-I 5+5 example panel for the one-click **Load example** workflow. It contains five non-classical H5-I references that score above the frozen threshold and five classical-presequence H5-I references that score below it. This set is illustrative and is not an additional validation cohort. Production scientific parity, synchronous performance, and fresh normal-browser Chrome/Edge workflow checks have passed; the only observed HUNTER-domain cookie is Hostinger's first-party `hcdn` session/security cookie.

The corresponding repository files are `examples/HUNTER_v1_public_example_5plus5.fasta` and `examples/HUNTER_v1_public_example_5plus5_expected.tsv`.

The original ten-sequence set is preserved separately as a deterministic software regression fixture in `examples/HUNTER_v1_regression_10.fasta` and `examples/HUNTER_v1_regression_10_expected.tsv`. It is retained for end-to-end parity testing and should not be described as the biological public example. The older `HUNTER_v1_example_10.*` filenames are retained only as compatibility copies of the same deterministic fixture.

A standalone Linux x86-64 CLI, quick-start instructions and SHA-256 checksum
are provided from the live Downloads page. The downloadable CLI is the same
frozen executable used by the web server.

## Reproducibility

Run hunter validate-installation before publication-scale analysis. The repository candidate includes golden-vector parity tests, frozen provenance files and SHA-256 records.

## Release status

This directory is the HUNTER v1.0.1 submission/deposition release candidate. The scientific HUNTER-v1.0 model is unchanged.

Software creator metadata:
- **Pankaj Goyal** is the confirmed primary software creator in `CITATION.cff`;
- additional software creators/contributors may be added later only by explicit PI decision;
- manuscript authorship remains independent of software authorship.

Canonical public repository:
- https://github.com/thegoyallab/HUNTER-mito

Open release metadata items:
- immutable `v1.0.1` release/tag URL;
- archival DOI.

The live web deployment, software-creator checkpoint, and public-repository publication are complete. Release-tested software package version: **1.0.1**. Live v0.7.23 production certification is complete. The next administrative action is creation and verification of the immutable `v1.0.1` tag, followed by archival DOI assignment.

The scientific HUNTER v1 model, feature engine and decision threshold are locked and must not be changed during these release steps.

## License

HUNTER v1 software is released under the BSD 3-Clause License. Copyright (c) 2026, Pankaj Goyal. See LICENSE and LICENSE_SCOPE.md.
