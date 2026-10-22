"""Activate the data-only FM broker using the existing ADB root access."""
import argparse,pathlib,subprocess,zipfile,tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--adb',default='adb');p.add_argument('--serial',default='35be55ef');p.add_argument('--apk',default=str(pathlib.Path(__file__).resolve().parents[2]/'outputs/Voyah-FM-Tester-0.2.apk'));a=p.parse_args()
def adb(*args,**kw):return subprocess.run([a.adb,'-s',a.serial,*args],check=True,**kw)
D='/data/local/tmp/voyah-fm-loader-v1';S='/data/local/tmp/fm-loader-upload'
adb('install','-r',a.apk)
adb('shell','mkdir','-p',S)
with tempfile.TemporaryDirectory(prefix='fm-loader-') as td:
 with zipfile.ZipFile(a.apk) as z:
  for name in ['helper.sh','broker.sh','adapter.js','template.xml','frida-inject','AdayoDAB.apk','RdsApp.apk']:
   f=pathlib.Path(td)/name;f.write_bytes(z.read('assets/'+name));adb('push',str(f),S+'/'+name)
script=f'''set -e
D={D}
S={S}
uid=$(cmd package list packages -U ru.local.voyah.fmloader | sed -n 's/.*uid://p' | head -1)
case "$uid" in ''|*[!0-9]*) exit 1;; esac
mkdir -p "$D/mailbox"
chmod 755 "$D"
chown "$uid:$uid" "$D/mailbox"
chmod 700 "$D/mailbox"
for name in helper.sh broker.sh adapter.js template.xml frida-inject AdayoDAB.apk RdsApp.apk; do
    if ! cmp -s "$S/$name" "$D/$name"; then cp "$S/$name" "$D/$name"; fi
    chown 0:0 "$D/$name"
    chmod 644 "$D/$name"
done
chmod 755 "$D/frida-inject"
nohup setsid sh "$D/broker.sh" > "$D/broker.log" 2>&1 < /dev/null &
sleep 1
sh "$D/helper.sh" check
'''
adb('shell','su','0','sh',input=script.encode())
print('FM broker activated for the current boot. Firmware untouched; reboot needs activation again.')
