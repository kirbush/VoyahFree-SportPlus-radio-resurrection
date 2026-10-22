import pathlib,re,unittest,xml.etree.ElementTree as ET
P=pathlib.Path(__file__).parent
class Contract(unittest.TestCase):
 def test_no_firmware_mutations(self):
  s=(P/'assets/helper.sh').read_text()
  for bad in ['setenforce','mount -o','remount','dd if=','/dev/block','chmod 777','pkill','killall']:
   self.assertNotIn(bad,s)
  self.assertNotIn('am stopservice',s,'Adayo onDestroy leaves old PCM readers alive')
  self.assertNotIn('am force-stop',s)
  self.assertIn('DIRTY_PROCESS_MULTIPLE_AUDIO_THREADS',s)
  self.assertIn('TEMPLATE_HASH_MISMATCH',s)
  self.assertIn('HARDWARE_NOT_OPEN_BY_FM_PROCESS',s)
 def test_guards(self):
  s=(P/'assets/helper.sh').read_text()
  for required in ['Permissive','ro.build.version.sdk','sha256sum','0483','5740','04fc:8005','AMBIGUOUS_USB','flock','/proc/$p/cmdline','CONFIG_NOT_USED']:
   self.assertIn(required,s)
 def test_manifest(self):
  r=ET.parse(P/'AndroidManifest.xml').getroot(); ns='{http://schemas.android.com/apk/res/android}'
  self.assertEqual(r.find('uses-sdk').get(ns+'targetSdkVersion'),'30')
  app=r.find('application')
  self.assertIsNone(r.get(ns+'sharedUserId'))
  self.assertTrue(any(x.get(ns+'name')=='.BootReceiver' for x in app.findall('receiver')))
if __name__=='__main__': unittest.main()
