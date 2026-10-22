"""Execute the real install branch with mocked Android commands, never a vehicle."""
import pathlib,tempfile,subprocess,os
P=pathlib.Path(__file__).resolve().parent
source=(P/'assets/helper.sh').read_text();body=source.split('\ninstall-components)\n',1)[1].split('\n    ;;',1)[0]
with tempfile.TemporaryDirectory(prefix='fm-install-') as td:
 logfile=pathlib.Path(td)/'calls.txt'
 prefix='''AD=com.adayo.service.dab
RD=com.pateo.rdsapp
D=/test-payload
fail() { echo "ERROR $*"; exit 1; }
getprop() { echo "$TEST_SDK"; }
getenforce() { echo "$TEST_SELINUX"; }
pm() {
 if [ "$1" = path ]; then
  if [ "$TEST_MODE" = present ] || { [ "$TEST_MODE" = partial ] && [ "$2" = "$AD" ]; }; then echo "package:/existing/$2.apk"; fi
 elif [ "$1" = install ]; then
  echo "$2" >> "$TEST_LOG"
  if [ "$TEST_MODE" = signature-fail ]; then echo 'Failure [INSTALL_FAILED_SHARED_USER_INCOMPATIBLE]'; return 1; fi
  echo Success
 else return 91; fi
}
'''
 def case(mode,sdk='30',selinux='Permissive',success=True,expected=0):
  if logfile.exists():logfile.unlink()
  env=os.environ.copy();env.update(TEST_MODE=mode,TEST_SDK=sdk,TEST_SELINUX=selinux,TEST_LOG=str(logfile).replace('\\','/'))
  r=subprocess.run(['C:/Program Files/Git/bin/bash.exe'],input=(prefix+body).encode(),env=env,capture_output=True)
  calls=logfile.read_text().splitlines() if logfile.exists() else []
  assert (r.returncode==0)==success,(mode,r.stdout,r.stderr)
  assert len(calls)==expected,(mode,calls)
  print('PASS install branch',mode,sdk,selinux,'PM installations=',len(calls))
 case('present',expected=0);case('missing',expected=2);case('partial',expected=1)
 case('signature-fail',success=False,expected=1)
 case('missing',sdk='31',success=False,expected=0);case('missing',selinux='Enforcing',success=False,expected=0)
