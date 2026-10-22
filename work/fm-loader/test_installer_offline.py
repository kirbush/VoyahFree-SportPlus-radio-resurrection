import pathlib,subprocess,os,tempfile,zipfile,shutil
p=pathlib.Path(__file__).resolve().parent
compiler=pathlib.Path(os.environ['WINDIR'])/'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
with tempfile.TemporaryDirectory(prefix='fm-install-review-') as td:
 t=pathlib.Path(td);fake=t/'fake adb.exe'
 subprocess.run([str(compiler),'/nologo','/out:'+str(fake),str(p/'tests/FakeAdbInstall.cs')],check=True)
 package=t/'кириллица папка';package.mkdir();script=package/'Install-FM.ps1';shutil.copyfile(p/'Install-FM.ps1',script)
 apk=package/'tester space.apk'
 diag=package/'diagnostics space.apk';diag.write_bytes(b'diagnostic fixture')
 with zipfile.ZipFile(apk,'w') as z:
  for n in ['helper.sh','broker.sh','adapter.js','template.xml','frida-inject','AdayoDAB.apk','RdsApp.apk']:z.writestr('assets/'+n,b'offline fixture')
 for mode in ['root','su','noroot','sdk','enforcing','install-fail','diag-install-fail','hardware-fail','none','multiple','unauthorized','bad-crlf','bad-bom']:
  with zipfile.ZipFile(apk,'w') as z:
   for name in ['helper.sh','broker.sh','adapter.js','template.xml','frida-inject','AdayoDAB.apk','RdsApp.apk']:
    raw=b'offline fixture'
    if name=='helper.sh' and mode=='bad-crlf':raw=b'#!/system/bin/sh\r\numask 077\r\n'
    if name=='helper.sh' and mode=='bad-bom':raw=b'\xef\xbb\xbf#!/system/bin/sh\n'
    z.writestr('assets/'+name,raw)
  calls=t/'calls.txt';boot=t/'bootstrap.sh';calls.unlink(missing_ok=True);boot.unlink(missing_ok=True);pathlib.Path(str(boot)+'.rootstage').unlink(missing_ok=True)
  env=os.environ.copy();env.update(FM_INSTALL_MODE=mode,FM_INSTALL_CALLS=str(calls),FM_INSTALL_BOOTSTRAP=str(boot))
  r=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(script),'-Adb',str(fake),'-Apk',str(apk),'-DiagnosticsApk',str(diag)],env=env,capture_output=True,timeout=45)
  success=mode in ['root','su'];assert (r.returncode==0)==success,(mode,r.stdout,r.stderr)
  log=calls.read_text(encoding='utf8');assert '/system/etc/init.logcat.sh' not in log and 'remount' not in log
  if success:
   assert 'helper.sh|log-start' in log and 'helper.sh|install-components' in log and 'helper.sh|check' in log
   assert log.index('helper.sh|log-start')<log.index('helper.sh|install-components')
   assert '|am|start|' in log and '0.4.3-beta-v1' in boot.read_text()
   assert log.count('|install|-r|')==2,log
   assert str(diag) in log
   subprocess.run(['C:/Program Files/Git/bin/bash.exe','-n',str(boot)],check=True)
  if mode in ['noroot','sdk','enforcing','none','multiple','unauthorized','bad-crlf','bad-bom']:assert '|install|' not in log,(mode,log)
  print('PASS actual Windows installer',mode)
