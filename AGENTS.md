# Project instructions

- Work in `work/fm-loader` and `work/fm-diagnostics`. This workspace also contains unrelated camera/DVR research; keep it outside this repository's changes.
- Read `PLAN.md`, `TODO.md`, `DECISIONS.md` and `EVIDENCE.md` before non-trivial work. Detailed history is in `work/FM-BETA-STATE.md`.
- Current beta is 0.5.1-beta, versionCode 9: one FM Radio APK with an in-place OEM-screen settings menu. Legacy diagnostics sources are retained, but its APK is not shipped. Build with `build_beta.py`, validate with `verify_offline.py`, package with `package_beta.py`, then check the actual archive with `test_beta_package.py`.
- Build prerequisites and local paths are documented in README.md. Toolchains and binary payloads are not included in a fresh clone.
- Preserve LF and no BOM in Android shell scripts. Validate raw source and signed APK bytes with `payload_format.py`; universal-newline text readers hide CRLF defects.
- Keep signing keys/passwords, firmware images, device captures and proprietary APK payloads out of Git. Keep the original signing key locally for installed beta updates.
- Keep original OEM APKs byte-identical. Never resign their shared-system-UID packages.
- The separate FM Radio launcher uses the existing OEM RDS process; its runtime gear menu can also appear when opening the original launcher icon. Do not claim full UI/process isolation.
- Adayo DABService.onDestroy leaves audio threads alive. Do not force-stop or stop/start its service as a recovery strategy. Preserve one hardware owner and one PCM reader.
- Use the existing Tweaks channel for root startup; do not edit Tweaks files or system/vendor/boot/MCU. Use selective process identity checks rather than global kills.
- Diagnostics must not restart FM, tune/scan stations or stop logging while exporting a report.
- Manual radio opening after wake is normal. Do not introduce explicit autoplay or assume it is an acceptance condition.
- Do not equate static 7.3.1 compatibility with a confirmed live test. Exact known tester build and unresolved issues are recorded in EVIDENCE.md.
- Do not run scripts ending in `_device.py` or other live-control scripts merely to validate a source change. Local release tests use fake ADB.

- OEM MediaProvider breaks the pending-to-published Downloads rename. Manual ZIP export writes the final name and verifies content-URI length/SHA256; do not reintroduce that rename without live evidence.
