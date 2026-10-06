# HUNTER v1.0.1

HUNTER v1.0.1 is the public software release candidate for the frozen HUNTER-v1.0 scientific model.

## Scientific core

Unchanged from the frozen model:
- 42 N-terminal input descriptors
- frozen Stage24H2 feature engine
- elastic-net logistic-regression model
- decision threshold: 0.5428662440774465
- H5 and HPS scoring behavior

## Software/interface release

The v1.0.1 package provides:
- hunter score
- hunter describe
- hunter validate-installation
- hunter manifest
- single-sequence and FASTA input
- four stable explanatory descriptors in describe
- golden-vector parity tests
- frozen provenance and SHA-256 manifests
- 10-sequence reviewer example with expected scores/calls

## Web resource

Live HUNTER v1 server:
https://hunter.goyal-lab.org/

Reviewer downloads:
https://hunter.goyal-lab.org/about#downloads

## License

BSD 3-Clause License.
Copyright (c) 2026 Pankaj Goyal.

## Validation

Clean-install validation: PASS.
Frozen model/feature/engine integrity: PASS.
H5 golden-vector parity: 26 proteins; maximum absolute score difference 1.1102230246251565e-16.
HPS golden-vector parity: 21 proteins; maximum absolute score difference 2.220446049250313e-16.
10-sequence reviewer example: exact expected scores/calls reproduced.

## Interpretation boundary

The HUNTER score is a sequence-architecture prioritization measure for the development classification task. It is not a calibrated probability of mitochondrial localization, does not establish mitochondrial import, and does not identify a residue-level targeting sequence.

## Software creator

Primary software creator: **Pankaj Goyal**.

Additional software creators/contributors may be added later only by explicit PI decision. The manuscript author list is maintained independently.

## Administrative metadata still to finalize before public release

- canonical repository URL
- immutable `v1.0.1` release/tag URL
- archival DOI
