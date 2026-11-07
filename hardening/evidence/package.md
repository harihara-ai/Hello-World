purpose: phase 6 package build and its verification (2026-11-07).

- Built: `bash forge/forge.sh package` -> dist/northstar-kit.zip, 149156 bytes, 162 entries, no bytecode.
- zip sha256: 74013e4b15558cf2753d5e8a52a9e73e9f569d4a7988fb6b8386be3a72ae13bb
- Unpacked to a fresh folder: 70 workspace files match kit.lock hashes, no files outside the lock.
- In the unpacked package: kit tests unit 169, contract 5, mutation 14 OK; forge tests OK; run_traps 22/22, false alarms 0.
- Label: Silver on the synthetic test bed, accepted with conditions (see EVIDENCE.md).

## Rebuild 1.0.1 (2026-11-07, after fix plan items 1, 1b, 1c, 3, 4)
- Built: `bash forge/forge.sh package` -> dist/northstar-kit.zip, 156228 bytes, 164 entries, no bytecode.
- zip sha256: 1aaf49c54e5c05944eaf986d94cf078d7571a238a3dca508edb68a45fd2589e5 (this note is written after the build, so
  the zip holds this file without this section).
- Unpacked to a fresh folder: 70 workspace files match kit.lock, none outside the lock; INSTALL has the two CI jobs.
- In the unpacked package: kit tests unit 170, contract 5, mutation 14 OK; forge tests OK; run_traps (1 run) 22/22,
  false alarms 0. The 5-run repeat ran on the repo's pinned workspace, same files.

## Rebuild 1.0.2 (2026-11-07, after fix plan item 5)
- Built: `bash forge/forge.sh package` -> dist/northstar-kit.zip, 159698 bytes, 166 entries, no bytecode,
  sha256 b81942efbbcdd7a7c8667e43640637886b3c246833e8254dac35dfdfd69edb28; dist/northstar-kit-install.zip, 56822 bytes,
  58 entries (kit/, kit.manifest.yml, .claude/commands/), no root CLAUDE.md, no bytecode,
  sha256 82584df5d068630d8a3b980e4f15ea7342ea30d7b7bc3eafadd3fc64878b50a0 (written after the build, so the full zip holds
  this file without this section).
- The built install zip, unzipped into a fresh synthetic repo: root CLAUDE.md kept; plan PR ready pass, exit 0; clean
  code PR done pass, exit 0; out-of-scope control exit 1 (two-job recipe simulated, `install-zip.md`).

## Rebuild 1.0.3 (2026-11-07, after N01)
- Built: `bash forge/forge.sh package` -> dist/northstar-kit.zip, 164585 bytes, 167 entries, sha256 1dbf3bdd...;
  dist/northstar-kit-install.zip, 57055 bytes, 58 entries, sha256 2ff6b3e8... (INSTALL holds the N01 lines).
- Not run: unzip of 1.0.3 into trial-main (it runs 1.0.2; only INSTALL prose differs).

## Rebuild 1.0.4 (2026-11-07, N01 fix a dropped)
- Built: `bash forge/forge.sh package` -> dist/northstar-kit.zip, 166431 bytes, 167 entries, sha256 2871a975...;
  dist/northstar-kit-install.zip, 57109 bytes, 58 entries, sha256 d91404f4... (INSTALL holds "Only a human merges").
- Not run: unzip of 1.0.4 into trial-main (it runs 1.0.2; only INSTALL prose differs).

## Rebuild 1.0.5 (2026-11-07, pilot findings P01-P05)
- Built: `bash forge/forge.sh package` -> dist/northstar-kit.zip, 172102 bytes, 168 entries, sha256 aafe5c92...;
  dist/northstar-kit-install.zip, 57287 bytes, 58 entries, sha256 177b5281...; no bytecode in either.
- Not run: upgrade of the pilot repos from 1.0.4 to 1.0.5 (INSTALL Upgrade; P01 makes that PR pass the gate).
