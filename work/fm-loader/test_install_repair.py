"""Apply the small repair to the existing archive and run the patched installer."""
import pathlib,zipfile,tempfile,subprocess,os,hashlib,json
P=pathlib.Path(__file__).resolve().parent;O=P.parent.parent/'outputs'
compiler=pathlib.Path(os.environ['WINDIR'])/'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
with tempfile.TemporaryDirectory(prefix='fm-install-repair-') as temp:
 t=pathlib.Path(temp);package=t/'Бета радио';fake=t/'fake adb.exe'
 subprocess.run([str(compiler),'/nologo','/out:'+str(fake),str(P/'tests/FakeAdbInstall.cs')],check=True)
 with zipfile.ZipFile(O/'Voyah-FM-0.4.2-beta-Windows.zip') as z:
  z.extractall(package);apkhash={n:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if n.endswith('.apk')}
 with zipfile.ZipFile(O/'Voyah-FM-0.4.2-install-repair.zip') as z:z.extractall(package)
 for n,h in apkhash.items():assert hashlib.sha256((package/n).read_bytes()).hexdigest()==h
 for mode in ['root','su']:
  calls=t/(mode+'-calls.txt');bootstrap=t/(mode+'-bootstrap.sh');env=os.environ.copy()
  env.update(FM_INSTALL_MODE=mode,FM_INSTALL_CALLS=str(calls),FM_INSTALL_BOOTSTRAP=str(bootstrap))
  r=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(package/'Install-FM.ps1'),'-Adb',str(fake)],capture_output=True,env=env,timeout=45)
  assert r.returncode==0,(mode,r.stdout,r.stderr)
  body=bootstrap.read_text();assert 'exec 0>"$D/operation.lock"' in body and 'flock -n 0' in body and 'flock -n 9' not in body
  assert body.index('exec 0</dev/null')<body.index('nohup setsid sh "$D/broker.sh"')
  subprocess.run(['C:/Program Files/Git/bin/bash.exe','-n',str(bootstrap)],check=True)
  print('PASS repair applied over existing beta/default installer',mode,'APKs unchanged, FD0 released before broker')
