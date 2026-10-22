"""Exercise the real shell discovery function on isolated fake sysfs/proc trees."""
import pathlib,subprocess,sys
adb=sys.argv[1];serial=sys.argv[2];p=pathlib.Path(__file__).parent
s=(p/'assets/helper.sh').read_text();function=s[s.index('discover() {'):s.index('\nchecks() {')]
base='/data/local/tmp/fm-loader-discovery-tests'
function=function.replace('/sys/',base+'/sys/').replace('/proc/',base+'/proc/').replace('/dev/',base+'/dev/')
def run(script):return subprocess.run([adb,'-s',serial,'shell','sh'],input=script.encode(),capture_output=True)
setup=f'''mkdir -p {base}/sys/class/tty/ttyACM3 {base}/usb/a/interface {base}/proc/asound/card3 {base}/dev/snd
echo 0483 > {base}/usb/a/idVendor
echo 5740 > {base}/usb/a/idProduct
ln -sf {base}/usb/a/interface {base}/sys/class/tty/ttyACM3/device
echo 04fc:8005 > {base}/proc/asound/card3/usbid
ln -sf /dev/null {base}/dev/ttyACM3
ln -sf /dev/null {base}/dev/snd/pcmC3D0c
'''
assert run(setup).returncode==0
prefix='fail() { echo "ERROR $*"; exit 1; }\n'+function+'\n'
def case(name,change,expected,ok):
 r=run(change+'\n'+prefix+'discover\necho "FOUND $PORT $CARD"\n')
 assert (r.returncode==0)==ok,(name,r.stdout,r.stderr)
 assert expected.encode() in r.stdout,(name,r.stdout,r.stderr)
 print('PASS',name)
case('dynamic card3 + ttyACM3','','FOUND '+base+'/dev/ttyACM3 3',True)
case('reject wrong serial vendor',f'echo 0000 > {base}/usb/a/idVendor','serial_count=0',False)
case('reject duplicate matching serial',f'echo 0483 > {base}/usb/a/idVendor\nmkdir -p {base}/sys/class/tty/ttyACM4\nln -sf {base}/usb/a/interface {base}/sys/class/tty/ttyACM4/device','serial_count=2',False)
case('reject missing audio',f'rm {base}/sys/class/tty/ttyACM4/device\necho 0000:0000 > {base}/proc/asound/card3/usbid','audio_count=0',False)
case('reject duplicate audio',f'echo 04fc:8005 > {base}/proc/asound/card3/usbid\nmkdir -p {base}/proc/asound/card4\necho 04fc:8005 > {base}/proc/asound/card4/usbid','audio_count=2',False)
# Exact, fixed temporary fixture path; never touches live device nodes.
run('rm -rf '+base+'\n')
