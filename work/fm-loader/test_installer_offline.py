"""Execute the real Windows installer with fake ADB; never access a device."""
import json, pathlib, subprocess, os, tempfile, zipfile, shutil
P=pathlib.Path(__file__).resolve().parent
ASSETS=['helper.sh','broker.sh','adapter.js','ui.js','radio-ui.dex','template.xml','frida-inject','AdayoDAB.apk','RdsApp.apk']
TOKEN='offline_private_token_'+('x'*32)
CONFIG={'endpoint':'https://reports.example/voyah-fm/v1','client':'owner-01','token':TOKEN}
compiler=pathlib.Path(os.environ['WINDIR'])/'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
with tempfile.TemporaryDirectory(prefix='fm-install-review-') as td:
 t=pathlib.Path(td);fake=t/'fake adb.exe'
 subprocess.run([str(compiler),'/nologo','/out:'+str(fake),str(P/'tests/FakeAdbInstall.cs')],check=True)
 package=t/'кириллица папка';package.mkdir();script=package/'Install-FM.ps1';shutil.copyfile(P/'Install-FM.ps1',script)
 apk=package/'tester space.apk';configuration=package/'upload.json'
 modes=['root','su','fresh','diag-query-fail','diag-remove-fail','diag-remove-still-present','noroot','sdk','enforcing','main-install-fail','install-fail','hardware-fail','none','multiple','unauthorized','bad-crlf','bad-bom','config-default','config-explicit','config-http','config-userinfo','config-query','config-fragment','config-path','config-client','config-token','config-json','config-large','config-missing']
 if os.environ.get('FM_INSTALL_TEST_MODES'):modes=os.environ['FM_INSTALL_TEST_MODES'].split(',')
 for mode in modes:
  with zipfile.ZipFile(apk,'w') as z:
   for name in ASSETS:
    raw=b'#!/system/bin/sh\n: fixture\n' if name.endswith('.sh') else b'offline fixture'
    if name=='helper.sh' and mode=='bad-crlf':raw=b'#!/system/bin/sh\r\numask 077\r\n'
    if name=='helper.sh' and mode=='bad-bom':raw=b'\xef\xbb\xbf#!/system/bin/sh\n'
    z.writestr('assets/'+name,raw)
  configuration.unlink(missing_ok=True);explicit=t/'private config.json';explicit.unlink(missing_ok=True)
  arguments=[]
  if mode.startswith('config-'):
   config=dict(CONFIG)
   modifications={'http':('endpoint','http://reports.example/voyah-fm/v1'),'userinfo':('endpoint','https://user@reports.example/voyah-fm/v1'),'query':('endpoint','https://reports.example/voyah-fm/v1?x=1'),'fragment':('endpoint','https://reports.example/voyah-fm/v1#x'),'path':('endpoint','https://reports.example/other'),'client':('client','bad/client'),'token':('token','short')}
   kind=mode.removeprefix('config-')
   if kind in modifications:key,value=modifications[kind];config[key]=value
   target=explicit if kind in ['explicit','missing'] else configuration
   if kind!='missing':target.write_text('{"token":"'+TOKEN+'",' if kind=='json' else (' '*17000 if kind=='large' else json.dumps(config)),encoding='utf8')
   if kind in ['explicit','missing']:arguments=['-UploadConfig',str(target)]
  calls=t/'calls.txt';boot=t/'bootstrap.sh'
  for f in [calls,boot,pathlib.Path(str(boot)+'.rootstage'),pathlib.Path(str(boot)+'.upload'),pathlib.Path(str(boot)+'.diagremoved')]:f.unlink(missing_ok=True)
  for f in package.glob('Install-FM-*.log'):f.unlink()
  env=os.environ.copy();env.update(FM_INSTALL_MODE=mode,FM_INSTALL_CALLS=str(calls),FM_INSTALL_BOOTSTRAP=str(boot))
  r=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(script),'-Adb',str(fake),'-Apk',str(apk),*arguments],env=env,capture_output=True,timeout=45)
  success=mode in ['root','su','fresh','config-default','config-explicit']
  assert (r.returncode==0)==success,(mode,r.stdout,r.stderr)
  log=calls.read_text(encoding='utf8') if calls.exists() else ''
  console=r.stdout+r.stderr+b''.join(f.read_bytes() for f in package.glob('Install-FM-*.log'))
  assert TOKEN.encode() not in console,(mode,'private token leaked',console.replace(TOKEN.encode(),b'<TOKEN>'))
  assert 'remount' not in log and '/system/etc/init.logcat.sh' not in log
  assert '|am|force-stop|--user|0|com.adayo' not in log and '|am|force-stop|--user|0|com.pateo' not in log
  assert 'REPORT_MENU' not in log and '|send|' not in log and 'fmdiagnostics/.MainActivity' not in log
  if success:
   assert log.count('|install|-r|')==1,(mode,log)
   assert 'helper.sh|log-start' in log and 'helper.sh|install-components' in log and 'helper.sh|check' in log
   assert log.index('helper.sh|log-start')<log.index('helper.sh|install-components')
   body=boot.read_text();assert '0.5.0-beta-v1' in body
   assert 'ui.js' in body and 'radio-ui.dex' in body
   assert '|am|start|--user|0|-n|ru.local.voyah.fmloader/.MainActivity' in log
   if mode=='fresh':assert '|pm|uninstall|' not in log
   else:assert log.index('|install|-r|')<log.index('|pm|uninstall|ru.local.voyah.fmdiagnostics')
   if mode.startswith('config-'):
    assert json.loads(pathlib.Path(str(boot)+'.upload').read_text())==CONFIG
    assert 'chmod 600 "$F/.upload.json.install"' in body
    assert 'chown "$uid:$uid" "$F/.upload.json.install"' in body
   else:
    assert not pathlib.Path(str(boot)+'.upload').exists()
    assert 'F=/data/user/0/ru.local.voyah.fmloader/files' not in body
   subprocess.run(['C:/Program Files/Git/bin/bash.exe','-n',str(boot)],check=True)
  if mode in ['diag-remove-fail','diag-remove-still-present']:assert b'LEGACY_DIAGNOSTICS_REMOVE_FAILED' in console
  if mode=='diag-query-fail':assert b'LEGACY_DIAGNOSTICS_QUERY_FAILED' in console
  if mode=='main-install-fail':assert '|pm|uninstall|' not in log
  if mode in ['noroot','sdk','enforcing','none','multiple','unauthorized','bad-crlf','bad-bom'] or (mode.startswith('config-') and not success):assert '|install|' not in log,(mode,log)
  print('PASS actual Windows installer',mode)
