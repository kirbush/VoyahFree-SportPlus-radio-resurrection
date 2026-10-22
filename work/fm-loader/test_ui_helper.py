"""Execute actual UI helper action with controlled process table; never real ADB."""
import os,pathlib,subprocess,tempfile
P=pathlib.Path(__file__).resolve().parent
source=(P/'assets/helper.sh').read_bytes();assert b'ensure_ui()' in source,'UI helper action is missing'
PREFIX=r'''
id(){ echo 0; }
chown(){ :; }
chmod(){ :; }
flock(){ :; }
pm(){ echo "package:$TEST_D/Rds.apk"; }
sha256sum(){ case "$1" in *frida-inject) echo '0d99be0e44d4ca3449056fa0a0b868fca1cf66c8ad704508949945afc07706aa file';; *) echo '36b4d73a889aa78325f6a6ff0c8113c6b13605620a5a4b045209fbff36449cca file';; esac; }
pidof(){ case "$1" in com.pateo.rdsapp) echo 777;; frida-inject) cat "$TEST_D/pids";; esac; }
readlink(){ case "$1" in */exe) echo "$TEST_D/frida-inject";; esac; }
kill(){ echo "$1" >> "$TEST_D/kills"; echo 999 > "$TEST_D/pids"; }
sleep(){ command sleep 0.02; }
nohup(){
 echo "$*" >> "$TEST_D/launches"
 [ "$1" != setsid ] || shift
 printf '%s\000' "$@" > "$TEST_PROC/889/cmdline"
 echo '0.5.0-beta-v1' > "$TEST_D/runtime/ui-ready-777"
 echo '889 999' > "$TEST_D/pids"
}
am(){ echo "$*" >> "$TEST_D/am-calls"; return 99; }
'''
for mode in ['active','stale']:
 with tempfile.TemporaryDirectory(prefix='fm-ui-helper-') as td:
  t=pathlib.Path(td);runtime=t/'runtime';runtime.mkdir();proc=t/'proc';proc.mkdir()
  for pid in [888,889,999]:(proc/str(pid)).mkdir()
  for name in ['Rds.apk','frida-inject','ui.js','radio-ui.dex']:(t/name).write_bytes(b'fixture')
  (t/'pids').write_text('888 999')
  active=(str(t/'frida-inject').replace('\\','/')+' -p 777 -s '+str(t/'ui.js').replace('\\','/'))
  stale=(str(t/'frida-inject').replace('\\','/')+' -p 555 -s '+str(t/'ui.js').replace('\\','/'))
  hardware=(str(t/'frida-inject').replace('\\','/')+' -p 1234 -s '+str(t/'adapter.js').replace('\\','/'))
  (proc/'888/cmdline').write_bytes((active if mode=='active' else stale).encode()+b'\0')
  (proc/'999/cmdline').write_bytes(hardware.encode()+b'\0')
  if mode=='active':(runtime/'ui-ready-777').write_text('0.5.0-beta-v1\n')
  env=os.environ.copy();env.update(TEST_D=str(t).replace('\\','/'),TEST_PROC=str(proc).replace('\\','/'))
  env['PATH']='C:/Program Files/Git/usr/bin;'+env['PATH']
  body=source.decode().replace('D=/data/local/tmp/voyah-fm-loader-v1','D="$TEST_D"').replace('/proc/','"$TEST_PROC"/')
  script=t/'fixture.sh';script.write_bytes((PREFIX+body).encode())
  r=subprocess.run(['C:/Program Files/Git/bin/bash.exe',str(script),'ui-start'],env=env,capture_output=True,timeout=10)
  assert r.returncode==0 and b'UI_READY' in r.stdout,(mode,r.stdout,r.stderr)
  if mode=='active':assert not (t/'kills').exists() and not (t/'launches').exists()
  else:
   assert (t/'kills').read_text().strip()=='888','Hardware injector or unrelated process was killed'
   assert (t/'launches').read_text().count('-s '+str(t/'ui.js').replace('\\','/'))==1
  assert not (t/'am-calls').exists(),'Existing RDS process should not be restarted'
  print('PASS UI helper',mode,'preserves hardware injector/process')
