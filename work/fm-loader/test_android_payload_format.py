"""Raw-byte check: Windows text readers silently hide CRLF; Android shell does not."""
import pathlib,unittest,sys,zipfile
P=pathlib.Path(__file__).resolve().parent
class PayloadFormat(unittest.TestCase):
 def test_android_shell_source_bytes(self):
  for f in (P/'assets').glob('*.sh'):
   raw=f.read_bytes()
   self.assertTrue(b'\r' not in raw,str(f)+' contains Windows CR bytes')
   self.assertFalse(raw.startswith(b'\xef\xbb\xbf'),str(f)+' has BOM')
   self.assertTrue(raw.startswith(b'#!/system/bin/sh\n'))
 def test_validator_rejects_windows_and_bom(self):
  from payload_format import validate_shell
  validate_shell(b'#!/system/bin/sh\numask 077\nfor x in a; do\n:; done\n','valid')
  for raw in [b'#!/system/bin/sh\r\numask 077\r\n',b'\xef\xbb\xbf#!/system/bin/sh\n',b'echo no-shebang\n']:
   with self.assertRaises(ValueError):validate_shell(raw,'fixture')
if __name__=='__main__':
 if len(sys.argv)>1 and sys.argv[1]=='--apk':
  from payload_format import validate_apk_shells
  validate_apk_shells(pathlib.Path(sys.argv[2]));print('PASS raw shell bytes inside actual signed APK')
 else:unittest.main()
