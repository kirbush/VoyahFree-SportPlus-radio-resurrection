"""Validate Android scripts as raw bytes, never through universal-newline readers."""
import pathlib,zipfile
def validate_shell(raw:bytes,name:str):
 if b'\r' in raw:raise ValueError(name+': ANDROID_SCRIPT_CRLF_NOT_ALLOWED')
 if raw.startswith(b'\xef\xbb\xbf'):raise ValueError(name+': ANDROID_SCRIPT_BOM_NOT_ALLOWED')
 if not raw.startswith(b'#!/system/bin/sh\n'):raise ValueError(name+': ANDROID_SCRIPT_SHEBANG_INVALID')
def validate_source_assets(directory):
 files=list(pathlib.Path(directory).glob('*.sh'))
 if not files:raise ValueError('No Android shell assets')
 for f in files:validate_shell(f.read_bytes(),str(f))
def validate_apk_shells(apk):
 with zipfile.ZipFile(apk) as z:
  names=[n for n in z.namelist() if n.startswith('assets/') and n.endswith('.sh')]
  if not {'assets/helper.sh','assets/broker.sh'}.issubset(names):raise ValueError('Required Android scripts missing')
  for name in names:validate_shell(z.read(name),str(apk)+'!'+name)
