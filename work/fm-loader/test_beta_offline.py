"""Two-app release boundaries and executable report path traversal regression."""
import pathlib, subprocess, tempfile, unittest, xml.etree.ElementTree as ET
P=pathlib.Path(__file__).resolve().parent
D=P.parent/'fm-diagnostics'
N='{http://schemas.android.com/apk/res/android}'
class Beta(unittest.TestCase):
 def test_two_apps_one_backend(self):
  core=ET.parse(P/'AndroidManifest.xml').getroot()
  diag=ET.parse(D/'AndroidManifest.xml').getroot()
  self.assertEqual(core.get('package'),'ru.local.voyah.fmloader')
  self.assertEqual(diag.get('package'),'ru.local.voyah.fmdiagnostics')
  permission=core.find('permission')
  self.assertEqual(permission.get(N+'protectionLevel'),'signature')
  name=permission.get(N+'name'); app=core.find('application')
  self.assertEqual(app.find("service[@"+N+"name='.DiagnosticApiService']").get(N+'permission'),name)
  provider=app.find('provider'); self.assertEqual(provider.get(N+'readPermission'),name)
  self.assertEqual(app.get(N+'icon'),'@drawable/radio')
  self.assertIsNone(diag.find('instrumentation'))
  self.assertEqual(len(diag.find('application').findall('service')),0)
  self.assertFalse((D/'assets/frida-inject').exists())
  source='\n'.join(f.read_text(encoding='utf8') for f in (D/'src').rglob('*.java'))
  self.assertNotIn('RuntimeFiles',source)
  self.assertNotIn('127.0.0.1',source)
  self.assertNotIn('log-stop',source)
 def test_radio_entry_and_automatic_recording(self):
  s=(P/'src/ru/local/voyah/fmloader/MainActivity.java').read_text(encoding='utf8')
  self.assertIn('com.pateo.rdsapp.main.activity.MainActivity',s)
  self.assertNotIn('Сохранить отчёт',s)
  boot=(P/'src/ru/local/voyah/fmloader/BootReceiver.java').read_text(encoding='utf8')
  self.assertIn('MY_PACKAGE_REPLACED',boot)
  self.assertNotIn('getBoolean("boot",false)',boot)
  service=(P/'src/ru/local/voyah/fmloader/LoaderService.java').read_text(encoding='utf8')
  self.assertLess(service.index('RuntimeFiles.run("log-start")'),service.index('RuntimeFiles.run("start")'))
  self.assertNotIn('log-stop',service)
 def test_report_paths(self):
  j=P.parent/'toolchains/jdk/jdk-17.0.21-lite/bin'
  with tempfile.TemporaryDirectory(prefix='fm-report-paths-') as temp:
   t=pathlib.Path(temp); test=t/'TestReportFiles.java'
   test.write_text('''package ru.local.voyah.fmloader;
import java.io.*;
public class TestReportFiles {
 public static void main(String[] args)throws Exception {
  File dir=new File(args[0]);dir.mkdirs();
  String good="Voyah-FM-report-20261022-170000.zip";
  new File(dir,good).createNewFile();
  if(!ReportFiles.resolve(dir,good).isFile())throw new AssertionError("valid report");
  for(String bad:new String[]{"../events.log","/etc/passwd","events.log","Voyah-FM-report-20261022-170000.zip/../events.log",null}) {
   try{ReportFiles.resolve(dir,bad);throw new AssertionError("accepted "+bad);}catch(FileNotFoundException expected){}
  }
  try{ReportFiles.resolve(dir,"Voyah-FM-report-20261022-170001.zip");throw new AssertionError("missing accepted");}catch(FileNotFoundException expected){}
  System.out.println("PASS report whitelist and traversal");
 }
}''',encoding='utf8')
   subprocess.run([str(j/'javac.exe'),'--release','8','-d',temp,str(P/'src/ru/local/voyah/fmloader/ReportFiles.java'),str(test)],check=True,capture_output=True)
   subprocess.run([str(j/'java.exe'),'-cp',temp,'ru.local.voyah.fmloader.TestReportFiles',str(t/'files')],check=True)
if __name__=='__main__':unittest.main()
