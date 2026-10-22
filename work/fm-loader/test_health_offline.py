"""Regression: a live injector marker must not hide lost FM hardware."""
import os,pathlib,subprocess,tempfile,shutil
p=pathlib.Path(__file__).resolve().parent
body=(p/'assets/helper.sh').read_text().split('\nstart)\n',1)[1].split('\n    ;;',1)[0]
with tempfile.TemporaryDirectory(prefix='fm-health-') as td:
 d=pathlib.Path(td);(d/'runtime').mkdir();shutil.copyfile(p/'assets/template.xml',d/'template.xml')
 prefix='''D="$TEST_D"
AD=com.adayo.service.dab
checks() { PORT=/dev/ttyACM0; CARD=1; }
fail() { echo "ERROR $*"; exit 1; }
pidof() { echo 123; }
hook_alive() { return 0; }
hardware_ready() { [ "$TEST_HEALTHY" = yes ]; }
stop_injector() { echo REVALIDATION_REACHED; exit 23; }
'''
 for healthy,expected in [('yes',0),('no',23)]:
  (d/'config.xml').write_bytes((d/'template.xml').read_bytes());(d/'active').touch();(d/'runtime/used-123').touch()
  env=os.environ.copy();env.update(TEST_D=str(d).replace('\\','/'),TEST_HEALTHY=healthy)
  r=subprocess.run(['C:/Program Files/Git/bin/bash.exe'],input=(prefix+body).encode(),env=env,capture_output=True)
  assert r.returncode==expected,(healthy,r.returncode,r.stdout,r.stderr)
 print('PASS active fast path accepts healthy hardware; lost hardware reaches revalidation')
