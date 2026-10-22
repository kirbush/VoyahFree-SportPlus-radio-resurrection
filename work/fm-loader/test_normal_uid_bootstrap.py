import subprocess,pathlib,json
A='C:/Users/Кирилл/Downloads/ADB_AppControl/adb/adb.exe';O=pathlib.Path('work/fm-loader-validation')
subprocess.run([A,'-s','35be55ef','install','-r','outputs/Voyah-FM-Tester-0.2.apk'],check=True)
script='''D=/data/local/tmp/voyah-fm-loader-v1
if [ -f "$D/broker.pid" ]; then
p=$(cat "$D/broker.pid")
case "$p" in ''|*[!0-9]*) exit 1;; esac
cmd=$(tr '\\000' ' ' < /proc/$p/cmdline)
case "$cmd" in *"sh $D/broker.sh "*) kill "$p";; *) exit 2;; esac
fi
sleep 1
echo 'OLD_BROKER_STOPPED'
'''
r=subprocess.run([A,'-s','35be55ef','shell','su','0','sh'],input=script.encode(),capture_output=True,check=True)
print(r.stdout.decode(errors='replace'),flush=True)
r=subprocess.run([A,'-s','35be55ef','shell','am','instrument','-w','ru.local.voyah.fmloader/.ProbeInstrumentation'],capture_output=True,timeout=150)
data=r.stdout+r.stderr;(O/'normal-uid-selftest.txt').write_bytes(data);print(data.decode(errors='replace'))
assert b'INSTRUMENTATION_CODE: -1' in data and b'INSTRUMENTATION_RESULT: error=' not in data
