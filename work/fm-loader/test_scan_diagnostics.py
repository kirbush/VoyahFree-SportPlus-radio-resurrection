"""Coverage contract for scanner diagnostics and read-only Binder snapshot."""
import pathlib, tempfile, subprocess, os, re
P=pathlib.Path(__file__).resolve().parent
s=(P/'assets/helper.sh').read_text(encoding='utf8')
for tag in ['RdsDataModel:V','PlayView:V','RadioListView:V','DABManagerImpl:V']:
 assert tag in s,'Scanner/UI tag missing: '+tag
assert 'LOG_PROFILE_UPGRADE' in s,'Updating the APK must also replace an old recorder profile'
assert 'scan_snapshot()' in s,'No scanner snapshot'
body=s.split('scan_snapshot() {',1)[1].split('\n}',1)[0]
assert 'dfafe5455ca9040306d012e3650df6181ab6e24d26f8bcaa9766a0cdc6d45905' in body
for forbidden in ['fullScan','quickScan','audioPlay','requestAudioFocus','setRadio',' 27',' 28']:
 assert forbidden not in body,forbidden
assert 'for code in 5 7 8;' in body
with tempfile.TemporaryDirectory(prefix='fm-scan-snapshot-') as temp:
 t=pathlib.Path(temp);calls=t/'calls.txt'
 prefix='''AD=com.adayo.service.dab
D="$TEST_D"
verify() { [ "$TEST_KNOWN_APK" = yes ]; }
timeout() { shift; [ "$TEST_TIMEOUT" != yes ] || return 124; "$@"; }
service() { echo "$*" >> "$TEST_CALLS"; echo "Result: Parcel(00000000 00000002)"; }
'''
 for known in ['yes','no','timeout']:
  calls.unlink(missing_ok=True)
  env=os.environ.copy();env.update(TEST_KNOWN_APK='no' if known=='no' else 'yes',TEST_TIMEOUT='yes' if known=='timeout' else 'no',TEST_D=str(t).replace('\\','/'),TEST_CALLS=str(calls).replace('\\','/'))
  r=subprocess.run(['C:/Program Files/Git/bin/bash.exe'],input=(prefix+body+'\n').encode(),env=env,capture_output=True)
  assert r.returncode==0,(r.stdout,r.stderr)
  if known=='yes':assert calls.read_text().splitlines()==['call adayo.dab 5','call adayo.dab 7','call adayo.dab 8']
  elif known=='no':assert not calls.exists(),'Unknown APK must not receive raw Binder transactions'
  else:assert not calls.exists() and b'SCAN_GETTER_STATUS transaction=5 exit=124' in r.stdout
  assert not (t/'scan-getter.tmp').exists()
 print('PASS scan snapshot: only three verified read-only getters, unknown APK skipped')
 # Execute the real recorder branch, with /proc and logcat launch replaced by fixtures.
 stop=s.split('stop_log() {',1)[1].split('\n}',1)[0]
 record=s.split('\nlog-start)\n',1)[1].split('\n    ;;',1)[0]
 script='''D="$TEST_D"
pidof() { for f in "$TEST_PROC"/*/cmdline; do [ ! -f "$f" ] || basename "$(dirname "$f")"; done; }
kill() { echo "$1" >> "$TEST_D/killed"; rm -f "$TEST_PROC/$1/cmdline"; }
sleep() { command sleep 0.1; }
nohup() { mkdir -p "$TEST_PROC/42"; printf '%s ' "$@" > "$TEST_PROC/42/cmdline"; }
stop_log() {
'''+stop+'\n}\n'+record
 script=script.replace('/proc/$p/cmdline','$TEST_PROC/$p/cmdline').replace('/proc/sys/kernel/random/boot_id','"$TEST_BOOT"')
 for mode in ['legacy','current','missing']:
  d=t/mode;d.mkdir();proc=d/'proc';proc.mkdir()
  (d/'session-boot-id').write_text('BOOT');(d/'boot').write_text('BOOT');(d/'capture.log').write_text('KEEP_PRIOR_HISTORY')
  def process(pid,cmd):
   f=proc/str(pid)/'cmdline';f.parent.mkdir();f.write_text(cmd)
  process(202,'logcat -f /unrelated/log.txt ')
  if mode!='missing':
   cmd='logcat -f '+str(d).replace('\\','/')+'/capture.log '
   if mode=='current':cmd+='RdsDataModel:V PlayView:V '
   process(201,cmd)
  env=os.environ.copy();env.update(TEST_D=str(d).replace('\\','/'),TEST_PROC=str(proc).replace('\\','/'),TEST_BOOT=str(d/'boot').replace('\\','/'))
  r=subprocess.run(['C:/Program Files/Git/bin/bash.exe'],input=script.encode(),env=env,capture_output=True,timeout=10)
  assert r.returncode==0,(mode,r.stdout,r.stderr)
  assert (proc/'202/cmdline').exists(),'Unrelated recorder killed'
  assert (d/'capture.log').read_text()=='KEEP_PRIOR_HISTORY'
  if mode=='current':
   assert b'LOG_ALREADY_RECORDING' in r.stdout and not (proc/'42').exists()
  else:
   assert 'RdsDataModel:V' in (proc/'42/cmdline').read_text()
   assert b'LOG_RECORDING_STARTED' in r.stdout
  if mode=='legacy':assert (d/'killed').read_text().strip()=='201'
  else:assert not (d/'killed').exists()
 print('PASS actual recorder: upgrade old profile, reuse current, start missing, preserve history/unrelated logger')
