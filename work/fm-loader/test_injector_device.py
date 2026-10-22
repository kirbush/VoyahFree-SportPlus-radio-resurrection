"""Regression: Frida changes argv[0] and setsid may fork. Check executable identity."""
import pathlib,subprocess,sys
p=pathlib.Path(__file__).parent;adb,serial=sys.argv[1:3]
s=(p/'assets/helper.sh').read_text();f=s[s.index('stop_injector() {'):s.index('\naudio_threads() {')]
base='/data/local/tmp/fm-loader-identity-tests';f=f.replace('/proc/',base+'/proc/')
def run(s):return subprocess.run([adb,'-s',serial,'shell','sh'],input=s.encode(),capture_output=True)
prefix=f'''D={base}/own
mkdir -p "$D" {base}/proc/101 {base}/proc/102 {base}/other
ln -sf "$D/frida-inject" {base}/proc/101/exe
ln -sf {base}/other/frida-inject {base}/proc/102/exe
printf 'frida-inject -p 77 -s %s/adapter.js ' "$D" > {base}/proc/101/cmdline
printf 'frida-inject -p 77 -s %s/adapter.js ' "$D" > {base}/proc/102/cmdline
pidof() {{ echo 101 102; }}
kill() {{ echo "KILL:$1"; }}
pid=77
'''+f+'\n'
r=run(prefix+'hook_alive || exit 11\ncat "$D/injector.pid"\nstop_injector\n')
assert r.returncode==0,(r.stdout,r.stderr)
assert b'KILL:101' in r.stdout and b'KILL:102' not in r.stdout,r.stdout
print('PASS renamed argv0, forked PID discovery, foreign injector untouched')
r=run(prefix+f'printf "%s/frida-inject -p 77 -s %s/adapter.js " "$D" "$D" > {base}/proc/101/cmdline\nhook_alive || exit 11\nstop_injector\n')
assert r.returncode==0 and b'KILL:101' in r.stdout and b'KILL:102' not in r.stdout,(r.stdout,r.stderr)
print('PASS absolute argv0 recognized')
r=run(prefix+f'ln -sf "$D/frida-inject" {base}/proc/102/exe\nhook_alive && exit 11\nexit 0\n')
assert r.returncode==0,(r.stdout,r.stderr)
print('PASS duplicate injector rejected')
r=run(prefix+'pid=88\nhook_alive && exit 11\nexit 0\n')
assert r.returncode==0,(r.stdout,r.stderr)
print('PASS stale target PID rejected')
run('rm -rf '+base+'\n')
