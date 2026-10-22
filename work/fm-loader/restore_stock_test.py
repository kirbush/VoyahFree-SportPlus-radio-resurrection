import subprocess,pathlib,time
A='C:/Users/Кирилл/Downloads/ADB_AppControl/adb/adb.exe';O=pathlib.Path('work/fm-loader-validation')
def adb(c):return subprocess.run([A,'-s','35be55ef','shell',c],capture_output=True,timeout=35)
for n,c in {'glitch-audio':'dumpsys media.audio_flinger','glitch-threads':'''su 0 sh -c 'p=$(pidof com.adayo.service.dab); cat /proc/$p/status; for t in /proc/$p/task/*/comm; do cat $t; done' ''','glitch-logs':'logcat -d -t 1500'}.items():
 r=adb(c);(O/(n+'.txt')).write_bytes(r.stdout)
script='''am stopservice --user 0 -n ru.local.voyah.fmloader/.LoaderService
sh /data/local/tmp/voyah-fm-loader-v1/helper.sh stop
p=$(pidof com.adayo.service.dab)
case "$p" in ''|*[!0-9]*) exit 1;; esac
cmd=$(tr '\\000' ' ' < /proc/$p/cmdline)
case "$cmd" in 'com.adayo.service.dab '*) kill -TERM "$p";; *) exit 2;; esac
sleep 3
am startservice --user 0 -n com.adayo.service.dab/com.adayo.dab.DABService
am force-stop --user 0 com.pateo.rdsapp
am start --user 0 -n com.pateo.rdsapp/com.pateo.rdsapp.main.activity.MainActivity
pidof com.adayo.service.dab
'''
r=subprocess.run([A,'-s','35be55ef','shell','su','0','sh'],input=script.encode(),capture_output=True,timeout=35)
(O/'stock-restore.txt').write_bytes(r.stdout+r.stderr);print(r.stdout.decode(errors='replace'));print('exit',r.returncode)
