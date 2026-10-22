"""Real Windows collector: UI-independent reports, root modes and transport errors.

Missing root fallback, encoding loss, hidden partial transfers and no-clobber
regressions must fail this test. Only the external ADB endpoint is substituted.
"""
import argparse,json,os,pathlib,shlex,subprocess,tempfile,zipfile
P=pathlib.Path(__file__).resolve().parent
args=argparse.ArgumentParser();args.add_argument('--package',type=pathlib.Path);options=args.parse_args()
script=P/'Collect-FM-now.ps1'
assert script.is_file(),'UI-independent PC collector is missing'
compiler=pathlib.Path(os.environ['WINDIR'])/'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
with tempfile.TemporaryDirectory(prefix='fm-pc-collect-') as td:
 t=pathlib.Path(td);fake=t/'fake adb.exe'
 if options.package:
  extracted=t/'Распаковка архива с пробелами';extracted.mkdir()
  with zipfile.ZipFile(options.package) as z:
   assert z.testzip() is None
   z.extractall(extracted)
  script=extracted/'Collect-FM-now.ps1'
  assert (extracted/'Collect-FM-now.cmd').is_file() and (extracted/'adb/adb.exe').is_file()
  assert script.read_bytes().startswith(b'\xef\xbb\xbf'),'Windows PowerShell needs the UTF-8 BOM'
 subprocess.run([str(compiler),'/nologo','/out:'+str(fake),str(P/'tests/FakeAdbCollect.cs')],check=True)
 cases=[]
 for mode in ['root','su','adb-root','limited','none','unauthorized','multiple','transport-error','incomplete','su-hang','su-hang-adb-root']:
  dest=t/('Папка с пробелами '+mode);calls=t/(mode+'.calls');command=t/(mode+'.command')
  env=os.environ.copy();env.update(FM_COLLECT_MODE=mode,FM_COLLECT_CALLS=str(calls),FM_COLLECT_COMMAND=str(command))
  r=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(script),'-Adb',str(fake),'-Destination',str(dest)],env=env,capture_output=True,timeout=35)
  ok=mode in ['root','su','adb-root','limited','su-hang','su-hang-adb-root']
  assert (r.returncode==0)==ok,(mode,r.stdout.decode(errors='replace'),r.stderr.decode(errors='replace'))
  files=list(dest.glob('*.zip'))
  if ok:
   assert len(files)==1,(mode,files)
   with zipfile.ZipFile(files[0]) as z:
    assert z.testzip() is None
    assert {'environment.txt','diagnostics.txt','collection.txt'}.issubset(z.namelist())
    s=z.read('diagnostics.txt').decode('utf8');assert 'Проверка UTF-8 / 日本' in s and 'java.lang.IllegalStateException: fixture' in s
    e=z.read('environment.txt').decode('utf8');assert ('ROOT_MODE=limited' in e)==(mode in ['limited','su-hang'])
   keep=files[0].read_bytes()
   if mode=='root':
    r2=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(script),'-Adb',str(fake),'-Destination',str(dest)],env=env,capture_output=True,timeout=35)
    assert r2.returncode==0 and len(list(dest.glob('*.zip')))==2
    assert files[0].read_bytes()==keep,'An existing report was overwritten'
  else:assert not files and not list(dest.glob('*.partial'))
  trace=calls.read_text('utf8')
  for forbidden in ['|install|','|push|','|reboot','am force-stop','am startservice','am start ','pm clear','setenforce','remount']:
   assert forbidden not in trace,(mode,forbidden)
  if mode=='su':assert 'su 0 sh -c ' in command.read_text('utf8')
  if mode=='root':
   payload=script.with_name('Collect-FM-state.sh').read_bytes()
   actual=shlex.split(command.read_text('utf8'))
   assert actual[:2]==['sh','-c'] and actual[2].encode('utf8')==payload,'ADB shell quoting damaged the actual collector'
  cases.append({'mode':mode,'passed':True})
  print('PASS collector',mode,flush=True)
 # Exercise the shipped double-click entry point, including error propagation.
 for mode in ['root','none']:
  env=os.environ.copy();env.update(FM_COLLECT_MODE=mode,FM_COLLECT_CALLS=str(t/('cmd-'+mode+'.calls')),FM_COLLECT_COMMAND=str(t/('cmd-'+mode+'.command')))
  dest=t/('cmd output '+mode)
  command='"'+os.environ['COMSPEC']+'" /d /s /c ""'+str(script.with_suffix('.cmd'))+'" -Adb "'+str(fake)+'" -Destination "'+str(dest)+'""'
  r=subprocess.run(command,input=b'\r\n',env=env,capture_output=True,timeout=35)
  assert (r.returncode==0)==(mode=='root'),(mode,r.stdout,r.stderr)
  assert bool(list(dest.glob('*.zip')))==(mode=='root')
 print('PASS actual CMD launcher: successful report and failure exit status')
 out=P.parent/'fm-loader-validation';out.mkdir(exist_ok=True)
 (out/'pc-collect-tests.json').write_text(json.dumps(cases,indent=2),encoding='utf8')

 # Execute the real Android payload. Only Android-only commands are substituted.
 shell=script.with_name('Collect-FM-state.sh').read_bytes()
 assert b'\r' not in shell and shell.startswith(b'#!/system/bin/sh\n')
 subprocess.run(['C:/Program Files/Git/bin/bash.exe','-n',str(script.with_name('Collect-FM-state.sh'))],check=True)
 runtime=t/'runtime';runtime.mkdir();drop=t/'dropbox.txt';mutation=t/'mutation.txt'
 drop.write_text('''====================================
2026-10-22 21:00:00 data_app_crash
Process: com.unrelated.app
SECRET_UNRELATED
====================================
2026-10-22 21:01:00 data_app_crash
Process: ru.local.voyah.fmdiagnostics
java.lang.IllegalStateException: TARGET_EXCEPTION
====================================
2026-10-22 21:02:00 system_app_crash
Process: com.pateo.rdsapp
java.lang.NullPointerException: RADIO_EXCEPTION
====================================
2026-10-22 21:03:00 data_app_crash
Process: com.unrelated.other
SECRET_OTHER
''',encoding='utf8')
 prefix=r'''
id() { if [ "$1" = -u ]; then echo 0; else echo uid=0; fi; }
timeout() { shift; "$@"; }
dumpsys() {
 case "$1" in
  dropbox) command cat "$TEST_DROP";;
  activity) echo 'TOP_ACTIVITY ru.local.voyah.fmdiagnostics';;
  window) echo 'FOCUSED_WINDOW com.pateo.rdsapp';;
  package) echo 'versionName=0.4.3-beta';;
  *) return 91;;
 esac
}
getprop() { echo FAKE_PROPERTY; }
getenforce() { echo Permissive; }
logcat() { echo 'LOGCAT_CRASH_READ_ONLY'; }
ps() { echo 'ru.local.voyah.fmdiagnostics'; }
ls() { echo 'FAKE_CAPTURE_METADATA'; }
tail() {
 case "$*" in *'/data/user/'*) echo 'CORE_EVENT fixture';; *) command tail "$@";; esac
}
am() { echo am >> "$TEST_MUTATION"; return 99; }
pm() { echo pm >> "$TEST_MUTATION"; return 99; }
kill() { echo kill >> "$TEST_MUTATION"; return 99; }
mount() { echo mount >> "$TEST_MUTATION"; return 99; }
'''
 env=os.environ.copy();env.update(TEST_D=str(runtime).replace('\\','/'),TEST_DROP=str(drop).replace('\\','/'),TEST_MUTATION=str(mutation).replace('\\','/'))
 env['PATH']=r'C:/Program Files/Git/usr/bin;'+env['PATH']
 body=shell.decode('utf8').replace('D=/data/local/tmp/voyah-fm-loader-v1','D="$TEST_D"')
 for helper in [True,False]:
  f=runtime/'helper.sh'
  if helper:f.write_bytes(b'#!/bin/sh\necho REAL_HELPER_SNAPSHOT\n')
  else:f.unlink()
  r=subprocess.run(['C:/Program Files/Git/bin/bash.exe'],input=(prefix+body).encode(),env=env,capture_output=True,timeout=15)
  text=r.stdout.decode('utf8');assert r.returncode==0,(r.stdout,r.stderr)
  assert 'TARGET_EXCEPTION' in text and 'RADIO_EXCEPTION' in text
  assert 'SECRET_UNRELATED' not in text and 'SECRET_OTHER' not in text,'Unrelated DropBox crashes leaked into report'
  assert 'TOP_ACTIVITY' in text and 'FOCUSED_WINDOW' in text
  assert 'DROPBOX_COMMAND_EXIT=0' in text
  assert ('REAL_HELPER_SNAPSHOT' in text)==helper
  assert 'VOYAH_PC_DIAGNOSTIC_END' in text and not mutation.exists()
 drop.write_text('====================================\nProcess: com.unrelated.app\nSECRET_ONLY_OTHER\n',encoding='utf8')
 r=subprocess.run(['C:/Program Files/Git/bin/bash.exe'],input=(prefix+body).encode(),env=env,capture_output=True,timeout=15)
 text=r.stdout.decode('utf8');assert r.returncode==0 and 'NO_MATCHING_FM_CRASH_ENTRY' in text and 'SECRET_ONLY_OTHER' not in text
 print('PASS actual Android collector: helper present/missing, UI state, targeted/empty crash text, no control calls')
