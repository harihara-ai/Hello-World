purpose: phase 6 package build and its verification (2026-11-07).

- Built: `bash forge/forge.sh package` -> dist/northstar-kit.zip, 149156 bytes, 162 entries, no bytecode.
- zip sha256: 74013e4b15558cf2753d5e8a52a9e73e9f569d4a7988fb6b8386be3a72ae13bb
- Unpacked to a fresh folder: 70 workspace files match kit.lock hashes, no files outside the lock.
- In the unpacked package: kit tests unit 169, contract 5, mutation 14 OK; forge tests OK; run_traps 22/22, false alarms 0.
- Label: Silver on the synthetic test bed, accepted with conditions (see EVIDENCE.md).
