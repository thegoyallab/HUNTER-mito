# Public-repository path sanitization

Date: 2026-10-06

Before public Git publication, a privacy/hygiene scan found no credentials, access tokens, private keys, password strings, or files >=50 MB.

Two historical provenance files contained machine-specific absolute local paths from the Kairav analysis environment:
- `provenance/HUNTER_v1_FREEZE_DOSSIER_v0_7_23/FREEZE_DOSSIER.md`
- `provenance/HUNTER_v1_FREEZE_DOSSIER_v0_7_23/verification_report.json`

Only those local path strings were replaced with placeholders such as `<HUNTER_PROJECT_ROOT>` or `<LOCAL_USER_HOME>`.

This sanitation does **not** change:
- HUNTER-v1.0 model bytes;
- feature-list bytes;
- feature-engine bytes;
- scoring-core bytes;
- release wheel;
- threshold;
- golden vectors;
- example sequences;
- live web release;
- manuscript or figure files.

The repository checksum manifest was regenerated after sanitation and scientific parity was rerun.
