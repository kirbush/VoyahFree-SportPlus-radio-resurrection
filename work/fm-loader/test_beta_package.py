"""Run the shipped installer with its default filenames after Unicode extraction.
ADB is a compiled fake; this test never accesses a device.
"""
import pathlib,subprocess,os,tempfile,zipfile,json,hashlib
from payload_format import validate_apk_shells
P=pathlib.Path(__file__).resolve().parent;W=P.parent;O=W.parent/'outputs'
compiler=pathlib.Path(os.environ['WINDIR'])/'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
results=[]
with tempfile.TemporaryDirectory(prefix='fm-beta-shipped-') as temp:
 t=pathlib.Path(temp);fake=t/'fake adb.exe'
 subprocess.run([str(compiler),'/nologo','/out:'+str(fake),str(P/'tests/FakeAdbInstall.cs')],check=True)
 package=t/'Бета радио с пробелами'
 with zipfile.ZipFile(O/'Voyah-FM-0.4.3-beta-Windows.zip') as z:
  assert z.testzip() is None;z.extractall(package)
  hashes=json.loads(z.read('SHA256.json'))
  for name,h in hashes.items():assert hashlib.sha256((package/name).read_bytes()).hexdigest()==h
 validate_apk_shells(package/'Voyah-FM-Radio-0.4.3-beta.apk')
 for mode in ['root','su']:
  calls=t/(mode+'-calls.txt');boot=t/(mode+'-bootstrap.sh')
  env=os.environ.copy();env.update(FM_INSTALL_MODE=mode,FM_INSTALL_CALLS=str(calls),FM_INSTALL_BOOTSTRAP=str(boot))
  r=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(package/'Install-FM.ps1'),'-Adb',str(fake)],env=env,capture_output=True,timeout=90)
  assert r.returncode==0,(mode,r.stdout,r.stderr)
  log=calls.read_text(encoding='utf8')
  assert log.count('|install|-r|')==2
  installed={pathlib.Path(line.split('|')[-1]).resolve() for line in log.splitlines() if '|install|-r|' in line}
  for name in ['Voyah-FM-Radio-0.4.3-beta.apk','Voyah-FM-Diagnostics-0.4.3-beta.apk']:assert (package/name).resolve() in installed
  assert log.index('helper.sh|log-start')<log.index('helper.sh|install-components')<log.index('helper.sh|check')
  assert '|am|force-stop|--user|0|ru.local.voyah.fmloader' in log
  assert '|am|force-stop|--user|0|com.adayo' not in log
  assert '|am|start|--user|0|-n|ru.local.voyah.fmloader/.MainActivity' in log
  results.append({'mode':mode,'passed':True,'realArchiveDefaultPaths':True,'unicodeExtraction':True})
  print('PASS shipped beta archive/default APK names/actual Windows installer:',mode)
 # Exercise the one-click launcher without invoking any real exporter/device.
 stub=t/'wrapper check';(stub/'PC-Export').mkdir(parents=True)
 (stub/'Export-All-FM-logs.cmd').write_bytes((package/'Export-All-FM-logs.cmd').read_bytes())
 (stub/'PC-Export/Export-FM-logs.cmd').write_text('@echo off\n> "%FM_TEST_ARGS%" echo %*\n',encoding='ascii')
 env=os.environ.copy();env['FM_TEST_ARGS']=str(t/'wrapper-args.txt')
 r=subprocess.run([os.environ['COMSPEC'],'/d','/c','call',str(stub/'Export-All-FM-logs.cmd')],env=env,capture_output=True,timeout=10)
 assert r.returncode==0,(r.stdout,r.stderr)
 assert (t/'wrapper-args.txt').read_text().strip()=='-AllReports'
 results.append({'oneClickExportAllReports':True})
 print('PASS one-click export launcher forwards -AllReports')
b=W/'toolchains/build-tools/android-14/aapt.exe'
for name,label,package in [('Radio','FM Радио','ru.local.voyah.fmloader'),('Diagnostics','FM Диагностика','ru.local.voyah.fmdiagnostics')]:
 path='../../outputs/Voyah-FM-'+name+'-0.4.3-beta.apk'
 r=subprocess.run([str(b),'dump','badging',path],cwd=P,capture_output=True,check=True)
 data=r.stdout.decode('utf8')
 assert "name='"+package+"'" in data and "versionCode='7'" in data
 assert "application-label:'"+label+"'" in data
 if name=='Diagnostics':assert 'android.permission.INTERNET' not in data
 results.append({'apk':name,'compiledManifest':True,'label':label,'versionCode':7})
 print('PASS compiled APK label/package/version:',name)
(W/'fm-loader-validation/beta-shipped-package-tests.json').write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding='utf8')
