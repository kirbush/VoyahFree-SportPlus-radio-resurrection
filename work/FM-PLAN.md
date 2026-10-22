## Latest: 0.4.3 raw Android shell format fix, 2026-10-22

Confirmed current tester error is shipped helper CRLF (270 lines), introduced by
Windows write_text. Deliver outputs/Voyah-FM-0.4.3-beta-Windows.zip, 43,461,694 bytes,
SHA256 dde55f80b74a7ca3115e636b1a8d7239905511882a0a78332534ae5c6d636def.
All 18 offline groups, signed APK raw-byte guards, final archive Windows root/su
fake-ADB installation/labels/export PASS. VersionCode7 and bootstrap cache version
replace broken cached helper. Keep FD0 installer fix. All 0.4.2 packages obsolete.
No car connected; next action tester installs fresh-folder full 0.4.3 and checks FM.
Details: work/FM-BETA-STATE.md latest.

## Historical full-package delivery,2026-10-22

User requested complete fixed0.4.2. Repackaged and verified archive/default Windows installer root+su/export/compiled manifests and FD compatibility. Deliver outputs/Voyah-FM-0.4.2-beta-Windows-fixed.zip (43461354bytes SHA2561987e36819b89537674996fdd7845cda76a4d8fdb8df8ef2044ecd9206b44e86), distinct filename avoids confusion with earlier broken package. APKs unchanged/version6; extract fresh folder and run Install-FM.cmd. Alias outputs/Voyah-FM-0.4.2-beta-Windows.zip byte-identical latest. No car connection, live retry still needed.

## Latest:0.4.2 installer repaired after live BadFD failure

Tester screenshot: bootstrap migration FD9 flock fails. Replaced with standard FD0 acquire/release pattern matching working helper/broker. Small outputs/Voyah-FM-0.4.2-install-repair.zip4940bytes SHA2566b4909e71cf7e641ea3e9e96dd6e57d190fef04c7baf908ecc510516d5a15cea; replace Install-FM.cmd/.ps1 in old beta folder and rerun, no commands/APK changes. Full outputs/Voyah-FM-0.4.2-beta-Windows.zip also updated SHA256b240a52eefc72bf430f93b0b33da4f6b7711b5a6ebf7f0ba5efe4a593f824406.17offlinegroups passed, real Windows fakeADB root/su patch-over-archive and full-archive paths pass, independent FD regression passes. New live retry awaited; no device connected here. See work/FM-BETA-STATE.md latest.

## Latest: FM beta0.4.2 scan diagnostic coverage expanded

Current archive outputs/Voyah-FM-0.4.2-beta-Windows.zip; SHA256 b3cf64fca195e50dc8f8e7907a4cd74b0d82377f5f62755c6e6e43b22dabf070. See work/FM-BETA-STATE.md latest. Expanded scanner/UI/controller logs with auto profile migration;3MB ring. Report adds exact-original-APK-gated read-only Binder getters5/7/8, filter prefs, timeout markers.16 offline groups/signatures/shipped installer checks pass; independent review. No car connection or scan/spinner fix claim. Snapshot plus logged events, not guarantee every action/cause captured.

## Latest: FM beta0.4.1, optional Tweaks autoplay clarified

See work/FM-BETA-STATE.md latest section for hashes/tests/current archive. Removed own explicit background MediaController.play; adapter/logs still start. Manual radio opening after wake is normal. Fresh install and update supported. Clean step plan and Export-All-FM-logs.cmd included. Stock UI right spinner identified as FINISH+empty playlist; unchanged in0.4.1, may recur. No car access or UI-spinner/frequency/sleep fix claim.

## Latest: FM beta 0.4 two-app installer completed offline

2026-10-22. See work/FM-BETA-STATE.md for current requirements, final hashes, migration, validation and known limits. Deliver outputs/Voyah-FM-0.4-beta-Windows.zip (43458731 bytes; SHA256 5ad254bdcce0684b2a206e88fc62acfb7309133313573a0de911c4cbdaaf7b3b). 15 offline groups and shipped archive/default installer root+su checks passed. Same-key update replaces old tester; bounded selective cleanup preserves audio/stations/logs/reports. No car connection. New two-app beta not yet live-tested; frequency/standby unresolved. Earlier release gates/plans superseded by user explicit instruction to build this beta.

## Latest: EB/build18 live FM works; lost frequency and standby startup under investigation

2026-10-22 steering/correction: UserconfirmedFMworksafterfullrebootwithoutPC; laterstandbyreturnneededmanualradioopen+retune(noautomaticplayconfirmed). MMshowedlogoafterfewminuteslocked; preinstallbaselineunknown. DoNOTclaimstandby/autoplaystableorassumefixcausedreboot. ExacttesterphotoEB.01.20260530180528.rc1.1.user.f6802h;IgorKachalinquotedbyusercallsitprobably7.2.0. Supplied731imageEC.01.20260731171601.rc1.user.f6802h/build35remainsstatic-only. MarklivetestedEB/build18,not7.3.1. AdayopersistencefoundLb/a/a/f/h/a.P writesradio_fm_frq_id into appprivate shared_prefs/save_db.xml usingcommit;rootcauseofloststationnotyetproven. Read-onlyPCcollector outputs/Voyah-FM-sleep-diagnostics.zip capturesbefore/afterbootid,uptime,reasons,power,exit/dropbox/pstore,exactFMsaveprefs+ownbootprefs. FivefakeADBcases+shellsyntaxpass,nosystemchanges/installs/tuning/PowerShellpolicychanges. NativeFMiconrequested: APKic_launcherisgenericAndroidplaceholder;actualfactoryradioreceivericonextractedfrom731Launcherresources, work/fm-beta-assets/stock-radio-icon/all_app_radio.png150x150plusvariantsandSHAinventory. DoNOTuseAndroidplaceholder. BetaUIcleanupauthorizedinprinciplebutfrequency/standbydiagnosisgatesrelease.

## Latest: first external FM test successful; firmware/reboot confirmation pending

2026-10-22 external tester SUCCESS firstreport: Downloads/Voyah-FM-report-20261022-154848.zip17537bytes SHA25649cde46c5c877b8178afab221dd1218f10e4281cc1a755410fde7700e3111791. TesterNotes«все отлично». ActualAPI30Chinese build18 (supplied731imagebuild35, exactmarketingversionasked). OriginalAPKhashesinstalled/data UID1000, tty+USBPCMopen, captureRunning48000stereo,PID3680/onePCMthread, configcard2->1applied, activeAudioTrack4586240frames(~95.5s), RDSplayingFM101.2/errornull. OrdinaryappUID10064loopbackbootstrapOK15:46:48 confirmsTweaksrootchannelonrecipient. EarlyPID16640has4underrunrestartwarnings,currentunderrun640singlepoint—notprovablyzero/progressing. NoFMfatalmarkersinprovidedfragment. Processepochchangeconsistentwithrebootbutbootid/uptime/noPCnotrecorded; useraskedconfirmfullrebootwithoutPCandexactfirmware. Nohardwareconnectionorchangesperformed. Analysis work/fm-tester-report-20261022-154848, report outputs/Voyah-FM-test-result-20261022-154848.txt.

## Latest deliverable update: simplified instructions

2026-10-22 instruction simplification and repeat verification: latest tester archive outputs/Voyah-FM-Tester-0.3-simple.zip,43445763bytes,SHA2567a3fcc6da1f8ba65cd0ad43bfa7a80d04385be64c16a3e68a20f91481da8857c. Onlyrootinstruction ИНСТРУКЦИЯ.txt has3shortsteps; technicalnotes underDetails/. APK,installer,exporterandADBbyte-identicaltopreviouslyreviewed0.3. Re-ranall12offlinegroupssuccessfully, APKv2/v3signaturevalid, archiveCRC/memberhashes/unicodeextraction/launcherpathsverified. Hardware/reboot731stillrequiresrealtester.

## Latest state: FM tester0.3 ready, Chinese7.3.1, offline preflight complete
2026-10-22. Deliver outputs/Voyah-FM-Tester-0.3-for-tester.zip (43,444,067bytes), SHA2563184f4f87531e02f6edf4dbdb8a1a3026cb8f5690ddd993ff22d8cb847fc3ac7. APK45f01db1042154336cd83cc5c066c162dd031057b2f124f21ac8fe63324e82cb. USBInstall-FM.cmd bundles officialADB35.0.2, prefers confirmedadbroot, existing su0fallback; own/data broker only, missingoriginalFMcomponents only. Windowsfolder-pickerexport supports rootadbd/su/public.12offlinegroupspassed, archiveCRC/allmemberhashes/APKsignatureverified. Reviewerissuesfixed.
Userpriority: fullreboot/sleepwake stableautostart, Tweaks acceptableprerequisite. SavedTweaksbootchain confirmed: initlogcat_sdcard->modified/system/etc/init.logcat.sh->rootbusyboxtelnetd + /data/local/tmp/load.bin; load.binensureslistener every5sec. OwnappBOOT/FGS reuseslistener; noTweaksfileedits. Retry30s/120s has no permanent3failurelockout. ActualChineseTweaks/rebootmustbetested; donotclaimguarantee.
Actual731.zip analyzedboot/vendor/system;MD5matchfactory, platformcertmatches, missingAdayo/Rds/config, supportingAPI/drivers/audio/nativeimportsremain. OD13.1RARdonorreadvendorMD5verified; Adayoexactmatch; Rdsmanifest/resources/classes.dexidenticalto car-testedUI, classes2SDK/encodingdiff. Keepcar-testedRdsforfirsttest. NoADB/hardware/flashduringofflinepreflight. Userreceivespackageand performs liveFM+reboot/sleepwaketests withZIP. One-iconproductionwrapper remainsnextstep aftersuccessfulChinesehardwaretest.

## Latest state,2026-10-22
User requested a shareable tester for another Chinese-firmware Voyah Free with Tweaks. Completed outputs/Voyah-FM-Tester-0.2.apk (41198554bytes, SHA2563d69e0e2a970776b6635aa380b5814453857322d243c65d4d73134168ae53d34), README, validation, package/source archives and hashes. Ordinary UID10057 self-bootstrap through existing vendor loopback root channel, log recording with live marker, diagnostic ZIP/CRC, single PCM reader and in-place adapter were verified. User confirmed smooth audio. No firmware/Tweaks files changed. Full reboot and Chinese-firmware compatibility remain untested; recipient test/ZIP needed. Vehicle session ended from laptop battery; final packaging offline with exact DEX/manifest/executable-payload hashes matching tested build. Earlier plan-only/direct-su/constructor-hook/service-restart entries are historical and superseded.

# FM investigation
Goal: trace the currently working analog FM implementation and prepare an evidence-based restoration plan for the user's intended latest Chinese firmware for vehicles without FM hardware.
Scope: read-only snapshots while FM plays; pull original APKs/native libraries/configurations and preserve hashes. No retuning, audio route changes, service restarts, vehicle control or firmware installation.
User's final constraint: original radio services may be absent on7.3.0; restoration must run from /data without modifying firmware or depending on Tweaks startup. Planonly, not implementation of anewloader.
1. Identify foreground radio app, services, HAL/native processes and current audio path.
2. Trace app APIs to hardware/MCU/QNX boundary from local binaries and runtime evidence.
3. Preserve a focused restoration inventory including dependencies, version/build and permission/configuration requirements.
4. Compare exact intended Chinese firmware if supplied; otherwise label missing target-package evidence explicitly and give conditional restoration steps.
5. Save concise Russian report and actionable verification plan in outputs.

Completed1/2/3/5. Task4 conditionalplancomplete; exact7.3.0packagecomparisonstillpendingbecausepackageunavailable. Findingsandportablebootstrapdesign in outputs/Voyah-FM-7.3.0-restoration-plan.txt; originals/reference/config/audit archive outputs/Voyah-FM-originals-and-plan-2026-10-22.zip (17629495bytes,22entries,CRCandallhashesverified). Finalread-onlycheck13:00:01 shows USBcaptureRunning48kHz2chS16_LE, originalAPKhashesunchanged. Audit script executedread-onlysuccessfully; noFMcontrolorpermission/ROMchanges. No claim of working7.3.0restoration or completedbootstrapimplementation.

Previous camera work: permanent native two-file fix confirmed installed by live hashes at12:43:33; /vendor ro, original init services running, no armed temporary camera watchdog. Reboot verification remains user's step. VoyahTweaks loader unchanged. Do not change camera files during FM research.

PC export added offline: outputs/Export-FM-logs.zip contains CMD launcher, UTF8-BOM Windows PowerShell5.1 script with FolderBrowserDialog, instructions and hashes. It copies latest/all pre-generated app ZIPs via ADB, prefers private report via root then shared Downloads/Documents, binary-safe .NET process streams, ZIP structure/remote SHA256 check, no overwriting, own partial cleanup only. Offline fake-ADB integration tests passed for private/public, Unicode paths/collisions and no-device/no-report/hash/transfer failures. New utility not yet tested against disconnected vehicle. APK unchanged SHA2563d69e0e2a970776b6635aa380b5814453857322d243c65d4d73134168ae53d34.


2026-10-22 final offline preflight: user supplied actual731.zip (SHA25615e753ceb31815274c99c94a05a708cbcd223abaa7e9931c31580d85d4f63690). Target now7.3.1, supersedes7.3.0. Restored boot/vendor/system locally, all factoryMD5 match. API30/Permissive/ACM+USBaudio+XHCI present;162APKmanifestscan proves Adayo/RDS absent, configabsent. Platformcert matches preservedoriginals;6AudioPolicyserviceclasses+72QGAPIpolicyclasses instructioncomparisonidentical. ARM64JNI strongimports allresolved. Busybox/telnetdscript present but bootinvocation unconfirmed; suroot:shell4750 allows optionalADBfallback. Details outputs/Voyah-FM-7.3.1-image-check.txt and work/firmware-731. Noimageflashed, noADB. APK0.3preflight fixes IPCserialization, SAFstate/Downloadfallback, coldstartretry, failedserviceexplicitretry and180sinstalltimeout. FreshChinese/reboot/audio stillrequiresrealtester. Final0.3packaging pendingindependentreview.

2026-10-22 usersteering: ADB-only installer acceptable/preferred; adbrootprimary, su0fallback. Autostartreliabilitycritical; actualTweaksbootchainnowconfirmedinsavedfiles: init service logcat_sdcard->modifiedinit.logcat.sh startsrootbusyboxtelnetd andload.bin;load.binensure_telnetdevery5s. ReuselistenerwithouteditingTweaks, ownBOOTreceiver/FGS/roothelper/dataonly. Fixedpermanent3failurelockout viaRetrySchedule30s/120sbackoff, testedlateboot/outages. Reviewhardware-readyfastpathfixedred/green; ADBsu-stagingownershipfixed; exporterrootadbdwithoutsubranchfixedred/green. UserOD13.1RARdonorinspectedvendorMD5matches;Adayoexactmatch,RdsUIresources+manifest+classes.dexidentical, classes2diff20methods mostlySDK/encoding. Keepcar-testedRdsforfirsttester; donorAPKsretainedwork/firmware-13.1/fm. NoADB/flash.
