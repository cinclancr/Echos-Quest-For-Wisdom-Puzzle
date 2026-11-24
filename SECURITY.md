# Security policy

## Scope

This repository is a read-only analysis toolkit for a public puzzle. It
never holds secrets. The "sensitive" asset that can appear here is **a
recovered mnemonic for a possibly-funded wallet**.

## If you find a phrase that matches the puzzle address

1. **Do not publish the phrase** (issue, PR, README, anywhere public) while
   funds may be live. This is the project's standing policy.
2. Reproduce the match with BOTH implementations (the Python toolkit and the
   C scanner) and verify the target address decodes to the same hash160.
3. Contact the puzzle author via their public channels and this repository's
   maintainers, describing the extraction rule and offering the redacted
   proof (word-position hashes + derivation parameters). `scripts/verify_target.py --json`
   produces such a redacted artefact.
4. The maintainers will publish a SOLUTION.md update with the method, the
   redacted proof, and a note on responsible disclosure timing.

## Reporting a toolkit bug that produces wrong derivations

Open an issue with the failing vector; validation failures of the
differential selftests are treated as release blockers.

## Key hygiene

Never use personal seed phrases with these tools; the code is for the
public puzzle only.
