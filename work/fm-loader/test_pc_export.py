"""Offline integration tests: the actual Windows exporter against a fake ADB executable."""
import pathlib,subprocess,os,tempfile,zipfile,hashlib
P=pathlib.Path(__file__).resolve().parent
compiler=pathlib.Path(os.environ['WINDIR'])/'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
with tempfile.TemporaryDirectory(prefix='fm-pc-export-') as td:
 t=pathlib.Path(td); fake=t/'fake adb.exe'
 subprocess.run([str(compiler),'/nologo','/out:'+str(fake),str(P/'tests/FakeAdbExport.cs')],check=True)
 fixture=t/'fixture.zip'
 with zipfile.ZipFile(fixture,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('environment.txt','test UID10057\n');z.writestr('diagnostics.txt','binary transfer test\n'+bytes(range(256)).decode('latin1'))
 env=os.environ.copy();env['FM_FAKE_ZIP']=str(fixture)
 script=P/'Export-FM-logs.ps1'
 def run(mode,dest,ok,extra=()):
  env['FM_FAKE_MODE']=mode
  r=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(script),'-Adb',str(fake),'-Destination',str(dest),*extra],env=env,capture_output=True)
  assert (r.returncode==0)==ok,(mode,r.stdout.decode(errors='replace'),r.stderr.decode(errors='replace'))
  return r
 for mode in ['root-no-su','private','public']:
  dest=t/('папка с пробелами '+mode);run(mode,dest,True);run(mode,dest,True)
  files=list(dest.glob('*.zip'));assert len(files)==2,'Repeated export must not overwrite an existing report'
  for f in files:
   assert f.read_bytes()==fixture.read_bytes(),'Binary ZIP changed during transfer'
   with zipfile.ZipFile(f) as z:assert z.testzip() is None
  print('PASS',mode,'binary copy, unicode folder, collision preservation')
 for mode in ['none','missing','bad-hash','transfer-error','multiple-devices']:
  dest=t/('fail-'+mode);run(mode,dest,False)
  assert not list(dest.glob('*.zip')) and not list(dest.glob('*.partial'))
  print('PASS',mode,'fails without leaving a report or partial transfer')
 dest=t/'latest';run('many',dest,True);assert [f.name for f in dest.glob('*.zip')]==['Voyah-FM-report-20261022-140001.zip']
 dest=t/'all';run('many',dest,True,('-AllReports',));assert len(list(dest.glob('*.zip')))==2
 dest=t/'selected-device';run('multiple-devices',dest,True,('-Serial','FAKE123'));assert len(list(dest.glob('*.zip')))==1
 dest=t/'no-sha';run('no-sha',dest,True);assert next(dest.glob('*.zip')).read_bytes()==fixture.read_bytes()
 print('PASS latest/all reports, explicit device selection, unavailable remote checksum')
 broken=t/'broken.zip';broken.write_bytes(b'NOT A ZIP FILE');env['FM_FAKE_ZIP']=str(broken)
 dest=t/'broken';run('private',dest,False);assert not list(dest.iterdir())
 with zipfile.ZipFile(broken,'w') as z:z.writestr('environment.txt','missing diagnostics')
 dest=t/'incomplete';run('private',dest,False);assert not list(dest.iterdir())
 print('PASS corrupt ZIP and incomplete report rejected without leftover files')
