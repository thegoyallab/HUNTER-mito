# HPS11A1 repository release checklist

## Included
- Python source package
- frozen model assets
- frozen 42-feature list
- feature engine
- CLI with score / describe / validate-installation / manifest
- parity tests and golden vectors
- interpretation documentation
- SERPINE1 examples
- scientific provenance and parity reports
- RC2 wheel candidate

## Remaining release metadata
- additional CITATION.cff authors, if applicable
- repository URL / DOI

## Version reconciliation note
The HPS10B package contains the parity-validated hunter_mito-1.0.0 wheel. The later RC2 source tree builds hunter_mito-1.0.1rc2 and adds a describe CLI command. The scientific model/core remain locked, but HPS11A3 must run a fresh reproducibility/parity gate on the RC2 repository candidate before final release.

## Final software tag
- Package version: 1.0.1
- Git/release tag: v1.0.1
- Scientific model identity remains HUNTER-v1.0.
