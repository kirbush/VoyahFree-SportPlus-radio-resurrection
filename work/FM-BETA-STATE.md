## Repository transition, 2026-10-22

User selected https://github.com/kirbush/VoyahFree-SportPlus-radio-resurrection.
Existing workspace is now its local Git checkout, main tracking origin/main
(existing README history retained, latest pre-import commit 60a9c0f).
Source files stay in work/fm-loader and work/fm-diagnostics; paths/toolchains and
current release artifacts remain intact. Initial source import includes both apps,
installer, existing tests, historical scripts, current state and root project docs.
Root .gitignore allows only FM sources/state and excludes local keys, captures,
firmware images, build outputs/toolchains, OEM APK payloads and frida-inject.
.gitattributes enforces LF for Android shell scripts. core.autocrlf=false locally.
GitHub connector has repository write access; local gh has no login. Use connector
for remote API operations when needed. Build dependencies are documented in README;
fresh clones need local toolchains, proprietary payloads and signing key separately.
Fresh import validation: all 18 offline groups and existing shipped archive root/su,
compiled labels and export wrapper checks pass. No app behavior change or car call.
Next product task: collect tester result for 0.4.3, then frequency/scan/standby issues.

## Latest: 0.4.3 fixes confirmed CRLF corruption in shipped helper, 2026-10-22

Tester photo reported helper.sh[3] umask bad number and [27] unexpected do.
Confirmed by raw byte inspection: released signed 0.4.2 APK contains 270 CRLF
lines in assets/helper.sh. Windows Python write_text during version bump introduced
them; previous universal-newline text tests hid the defect. This is our packaging
error. All previous 0.4.2 packages, including installer-only repair, are obsolete.

Deliver outputs/Voyah-FM-0.4.3-beta-Windows.zip, 43,461,694 bytes,
SHA256 dde55f80b74a7ca3115e636b1a8d7239905511882a0a78332534ae5c6d636def.
Radio APK SHA256 07d819e896ca69c292c518b191e42535f0e699f9475bbe6e70033cc2eed5e306.
Diagnostics APK SHA256 7e1cae833753ef9279ac3da9905800362299035f504800b0e1ab5bb2378c2d8e.
Both versionCode 7 / 0.4.3-beta, same signer. LocalBootstrap.VERSION also bumped,
so cached broken helper is replaced. User extracts new archive into a fresh folder,
connects USB and runs Install-FM.cmd; no manual uninstall or terminal commands.

Normalized Android shell assets with write_bytes/LF. New payload_format.py rejects
CR bytes, UTF-8 BOM and invalid shebang in raw source and actual signed APK members.
Build/package/shipped-archive tests enforce it. Windows installer validates extracted
shell bytes before installing any APK. Added actual installer negative CRLF/BOM
cases (13 fake-ADB modes). Test rejected real old signed 0.4.2 APK before fix.
All 18 offline groups PASS; signed APK byte check PASS; final extracted archive
real Windows installer root/su fake-ADB, compiled manifests and export wrapper PASS.
Independent reviewer found no important issue and confirmed migration/guards.
Retained prior FD0 repair. No FM audio/scanner behavior changed; camera untouched.
No device connected: live installation and playback retry still required.
Evidence: work/fm-loader-validation/offline-0.4.3-tests.json,
beta-build.json and beta-shipped-package-tests.json.

## Historical full-package delivery,2026-10-22

User requested complete fixed0.4.2. Repackaged and verified archive/default Windows installer root+su/export/compiled manifests and FD compatibility. Deliver outputs/Voyah-FM-0.4.2-beta-Windows-fixed.zip (43461354bytes SHA2561987e36819b89537674996fdd7845cda76a4d8fdb8df8ef2044ecd9206b44e86), distinct filename avoids confusion with earlier broken package. APKs unchanged/version6; extract fresh folder and run Install-FM.cmd. Alias outputs/Voyah-FM-0.4.2-beta-Windows.zip byte-identical latest. No car connection, live retry still needed.

# Latest:0.4.2 installer FD fix after real tester failure,2026-10-22

Tester screenshot showed repeated flock Bad file descriptor then INSTALL_FAILED
inside uploaded bootstrap. Migration introduced FD9 (exec9>operation.lock/flock-n9),
unlike known-working helper/broker FD0. Fix installer to exec0>lock/flock-n0, then
exec0</dev/null before starting broker. Script is read from its file, not stdin.
Exact shell inheritance cause not yet confirmed by tester command output; compatible
pattern is grounded in previously working live FD0 helper/broker. Do not claim new
live INSTALL_OK until tester retries.

Small repair: outputs/Voyah-FM-0.4.2-install-repair.zip,4940bytes,
SHA2566b4909e71cf7e641ea3e9e96dd6e57d190fef04c7baf908ecc510516d5a15cea.
Contains replacement Install-FM.cmd/.ps1 plus simple Russian instructions. Extract
over existing0.4.2 folder, replace files, rerun Install-FM.cmd; no typed commands.
APKs/version6 unchanged. Keep USB attached, no manual uninstall/data deletion.
Full archive also replaced with fixed installer,43,461,354bytes,
SHA256b240a52eefc72bf430f93b0b33da4f6b7711b5a6ebf7f0ba5efe4a593f824406.
17offlinegroups passed; current complete archive root/su/default/label/export checks pass.

New test_installer_fd_compat.py executes real installer lock body against a real
child process that closesFD9 at exec boundary: old code reproduces same BadFD and
exit84/MIGRATION_HELPER_BUSY; fixedFD0 passes. Real Windows installer11fakeADBcases
passed again. test_install_repair.py applies patch over existing actual archive,
runs default installer root/su paths, verifies uploadedFD0 acquire/release order,
shell syntax and byte-identical APKs. Reviewer independently reran FD test, noissue;
acknowledged prior static review missed FD9 inheritance issue. No car/ADB calls.

## Previous0.4.2 scan diagnostics below

User asked whether logs cover scanning failures. 0.4.1 had partial coverage of UI;
implemented0.4.2/versionCode6, same signer. No playback/UI/scanner algorithm changes.
Deliver outputs/Voyah-FM-0.4.2-beta-Windows.zip,43,461,295bytes,
SHA256 b3cf64fca195e50dc8f8e7907a4cd74b0d82377f5f62755c6e6e43b22dabf070.
RadioAPK41,206,874bytes SHA256c1521e848f11a5d2545eeff0f8944ad7e7803062858bf7b089db28f75a0aba98.
DiagnosticsAPK20,957bytes SHA25651ac31483839de2d36b81db28c2cb945eb446adc5cc806da2393574f29d97066.

helper.sh log profile adds RdsDataModel/PlayView/RadioListView/PlayViewAdapter/FmView/
RdsPlayer/DABManagerImpl/AudioPolicyManager tags; recorder ring3x1MB and report tails
match1MB each. Idempotent log-start recognizes new profile, replaces only its own old
capture logger, preserves recorded history and unrelated loggers, never restarts FM.
New scan_snapshot reads three exact-AIDL getters via service call adayo.dab5/7/8:
FMstation list /favorite frequency array/current station. Invoked only if installed
Adayo APK SHA256 equals exact original. Timeout3s each, explicit exit/timeout markers,
output bounded64KB, temp file cleaned. No scan, tune, audiofocus or69DAB-state query.
Also captures only relevant RDS preference entries SP_PLAY_DATA/SP_PTY_STATE/playType/
ptyCode. Existing report gets these automatically; no extra user controls/actions.

Tests16groups passed, APKv2/v3 signatures valid. New test_scan_diagnostics.py executes
actual getter block known/unknown APK/timeouts and recorder branch legacy/current/
missing with fake/proc. Preserves prior logs/unrelated recorder. Regression caught
and fixed adjacent-tag space-pattern mismatch before release. Independent review
fm_beta_review independently reran tests: no important risk, suggested timeout marker
which was added. Shipped root/su installer/default filenames/compiled labels/export
wrapper validated by test_beta_package.py. No vehicle/ADB used.

Coverage wording: extra scan-related native/UI logs plus station/filter snapshot at
report time. Does not guarantee every OEM action is logged or that one ZIP resolves
every failure. Save report promptly after reproducing, before retune/restart. This
does not fix scanning or spinner itself. Prior frequency/sleep questions unchanged.

## Previous0.4.1 below (historical)

User correction: automatic playback after wake is OPTIONAL and has a Tweaks setting.
Manual opening is normal, not a defect. Removed LoaderService's entire explicit
MediaBrowser/MediaController.play path, including after recovery. Background adapter
and automatic logs remain. OEM/Tweaks behavior still needs live observation.
Actual JVM service regression fails on old code and passes with zero own play calls;
independent reviewer reran it and found no important regression. 15 offline groups
and shipped archive/default installer root+su/compiled manifest checks passed.

Current deliverable: outputs/Voyah-FM-0.4.1-beta-Windows.zip,43,460,306bytes,
SHA256 c7c11c5a440bea23cb3a24233a78d1547f3f76941cbd87a98a66f155f0ea7209.
Radio APK41,202,778bytes SHA2561418d2d9ec93b526eee11e9bf7ef6cbb58fd1f1d7bec68b4888ccb9b57891192.
Diagnostics APK20,957bytes SHA256294e5bde75b895c22bb4ba8c9ac82363300c10ad08d7d0e5b5322ff85ad62ccd.
Both versionCode5 /0.4.1-beta, same original our signer; update from0.3/0.4 or
fresh install with no prior tester is supported. Required hardware/API/root/Tweaks
still checked. First-install missing/partial component paths covered offline.
Archive includes clean ПЛАН ПРОВЕРКИ.txt, no typing on HU or extra meta instructions,
observations sent in chat, manual open after wake, and one-click Export-All-FM-logs.cmd.
Auto logging and migration are unchanged. Plan/README wording updated, no car access.

Video investigation: work/fm-video-review/FINDINGS.md. Right spinner is stock empty
playlist indicator (FINISH + empty list -> VISIBLE), not audio buffering. This stock UI
is unchanged in0.4.1, so can repeat. Full reason for empty list and scan success not
proven from video. No spinner fix claimed. Frequency loss/MM logo still unresolved.
Old report contains7 scanStateFINISH lines15:43:37–15:44:56 and later nonempty station
updates; no captured fullScan/onScanStatusChange RUNNING->FINISH cycle. Thus do not
claim scanner acceptance based on list/audio alone. Added antenna scan/list selection
and list persistence checks to archive plan; no APK/code changes for spinner.

## Historical beta0.4 build below

User authorized two apps, one ADB installer, default automatic logs, button ZIP export,
and migration of old tester/cleanup of interfering remnants.

- Deliverable: outputs/Voyah-FM-0.4-beta-Windows.zip, 43,458,731 bytes.
- SHA256: 5ad254bdcce0684b2a206e88fc62acfb7309133313573a0de911c4cbdaaf7b3b.
- Radio: ru.local.voyah.fmloader versionCode4 / 0.4-beta, same signer as 0.3.
  APK 41,206,874 bytes, SHA256 f223f4058ee825ec2eed22e7cc59200830f3fa372689ce02f4ee287157120ae5.
- Diagnostics: ru.local.voyah.fmdiagnostics versionCode4 / 0.4-beta, separate UID,
  same signer. APK 20,957 bytes, SHA256 5f6dbb8aa82fa7a3742b72ce4a70613abf077deafcce9b855c6e5c07d14ccc7e.

Radio owns the existing single FGS/root broker/Frida adapter. MainActivity starts
the backend then opens untouched stock RDS UI. Icon is the actual receiver extracted
from 731 Launcher, not RdsApp's generic Android placeholder. Original Adayo/RDS APKs
remain byte-identical, signed by OEM. A standard launcher may also expose RdsApp.
Diagnostics is a separate normal UID app: fixed Messenger API and read-only report
provider, both signature protected. No own root client, injector or radio service.
ZIP export/repeat export and closing Diagnostics do not stop recorder or native FM.

BOOT_COMPLETED/MY_PACKAGE_REPLACED start core by default; no prior checkbox needed.
Every health tick prepares broker, requests idempotent log-start, then start. Recorder
is bounded to about 1.5 MB; app events rotate at ~2 MB. Native healthy repeats do not
send another play/focus request. Logging failure is visible and does not prevent audio.
Reports include boot ID, uptime/reasons, saved station prefs, prior/current session
snapshots, app exit history, existing logs. Atomic .partial -> ZIP with collision-free
second-format names. Completed ZIP persists in core and is recoverable via API action3.
Existing Windows PC folder-picker exporter still reads the same core report location.

Migration: install -r replaces old tester code/APK in place; no second old tester remains.
Only own core is force-stopped during deployment. Own broker cmdline is verified before
TERM/bounded KILL. Bootstrap waits <=95s for the existing helper lock (timeout120s),
never unlinks advisory locks. Removes stale mailbox files and runtime markers for other
PIDs, preserves active Adayo markers/config, station settings, logs, ZIP and boot evidence.
No Adayo lifecycle call/restart, firmware write, Tweaks loader change or global cleanup.

Validation: 15 offline groups passed in work/fm-loader-validation/offline-0.4-tests.json.
Includes actual JVM service/receiver behavior, mailbox concurrency/stale-broker recovery,
atomic report collisions/root failure, path traversal, migration fixture execution twice,
real Windows installer 11 fake-ADB modes, exporter, JS adapter and shell syntax.
Final archive CRC/member hashes/Unicode extraction checked. Shipped default installer
tested root/su with fake ADB after actual archive extraction; compiled APK manifest labels
checked. Evidence: work/fm-loader-validation/beta-shipped-package-tests.json.
Both APK signatures v2/v3 verified, same certificate 428d66013df53372bcc42f6eafb5e24ac6d89f522807a8d5a49b8605f621c98c.
Independent read-only reviewer fm_beta_review: both P2 findings fixed (stale broker marker,
report recovery); migration reviewed and test independently passed; no remaining important finding.

Build: work/fm-loader/build_beta.py. Tests: verify_offline.py. Package: package_beta.py.
Archive test: test_beta_package.py. Legacy build.py/package_final.py target OLD tester,
do not use them for beta. Sources: work/fm-loader and work/fm-diagnostics.

No car/ADB connection used this turn. New 0.4 requires live acceptance. Prior FM worked
on exact EB/build18 (likely7.2.0), including reboot without PC, but lost frequency and
manual launch after standby remain unresolved. MM logo cause unknown. 731 is static-only.
Do not claim frequency/sleep fixed or live 7.3.1 validation. Camera fix untouched.
