"""Package the reviewed single-app beta and public PC tools, without private config."""
import pathlib,zipfile,hashlib,json,subprocess,tempfile
from payload_format import validate_apk_shells,validate_shell
P=pathlib.Path(__file__).resolve().parent;W=P.parent;O=W.parent/'outputs'
sha=lambda b:hashlib.sha256(b).hexdigest()
tests=json.loads((W/'fm-loader-validation/offline-0.5.1-tests.json').read_text(encoding='utf8'))
assert {'test_installer_offline.py','test_upload_config_install.py','test_android_payload_format.py'}.issubset(tests),'Required release checks are missing'
assert all(r['code']==0 for r in tests.values())
builds=json.loads((W/'fm-loader-validation/beta-build.json').read_text(encoding='utf8'))
assert len(builds)==1 and pathlib.Path(builds[0]['apk']).name=='Voyah-FM-Radio-0.5.1-beta.apk'
files={
 'Voyah-FM-Radio-0.5.1-beta.apk':O/'Voyah-FM-Radio-0.5.1-beta.apk',
 'Install-FM.cmd':P/'Install-FM.cmd','Install-FM.ps1':P/'Install-FM.ps1',
 'ИНСТРУКЦИЯ.txt':P/'BETA-START-HERE.txt',
 'Export-All-FM-logs.cmd':P/'Export-All-FM-logs.cmd',
 'Details/TECHNICAL-NOTES.txt':P/'BETA-TECHNICAL-NOTES.txt',
 'Details/OFFLINE-CHECKS.json':W/'fm-loader-validation/offline-0.5.1-tests.json',
 'PC-Export/Export-FM-logs.cmd':P/'Export-FM-logs.cmd',
 'PC-Export/Export-FM-logs.ps1':P/'Export-FM-logs.ps1',
}
for name in ['Collect-FM-now.cmd','Collect-FM-now.ps1','Collect-FM-state.sh','Upload-FM-report.ps1','upload.example.json']:files[name]=P/name
files['Details/PC-COLLECT.txt']=P/'COLLECT-START-HERE.txt'
validate_shell((P/'Collect-FM-state.sh').read_bytes(),'Collect-FM-state.sh')
for name in ['adb.exe','AdbWinApi.dll','AdbWinUsbApi.dll','NOTICE.txt']:files['adb/'+name]=W/'installer/package/adb'/name
for b in builds:
 apk=pathlib.Path(b['apk']);assert sha(apk.read_bytes())==b['sha256']
 with zipfile.ZipFile(apk) as z:
  assert z.testzip() is None
  validate_apk_shells(apk)
  assert z.read('assets/radio-ui.dex').startswith(b'dex\n')
  for f in (P/'assets').iterdir():
   if f.is_file():assert z.read('assets/'+f.name)==f.read_bytes(),f.name
  assert not any(pathlib.PurePosixPath(n).name.lower()=='upload.json' for n in z.namelist())
hashes={n:sha(f.read_bytes()) for n,f in files.items()}
target=O/'Voyah-FM-0.5.1-beta-Windows.zip'
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for name,f in files.items():z.write(f,name)
 z.writestr('SHA256.json',json.dumps(hashes,indent=2))
with zipfile.ZipFile(target) as z:
 assert z.testzip() is None
 assert set(z.namelist())==set(files)|{'SHA256.json'}
 for name,h in hashes.items():assert sha(z.read(name))==h
 for name in ['Install-FM.ps1','PC-Export/Export-FM-logs.ps1','Collect-FM-now.ps1']:assert z.read(name).startswith(b'\xef\xbb\xbf')
 with tempfile.TemporaryDirectory(prefix='fm-beta-extract-') as temp:
  dest=pathlib.Path(temp)/'Папка беты с пробелами';z.extractall(dest)
  for name,h in hashes.items():assert sha((dest/name).read_bytes())==h
 assert not any('.password' in n or '.p12' in n or pathlib.PurePosixPath(n).name.lower() in ['upload.json','upload-private.json'] for n in z.namelist())
 assert [n for n in z.namelist() if n.endswith('.apk')]==['Voyah-FM-Radio-0.5.1-beta.apk']
result=dict(archive=str(target),bytes=target.stat().st_size,sha256=sha(target.read_bytes()),offlineGroups=len(tests),apks=builds,memberHashes=hashes)
(O/'Voyah-FM-0.5.1-beta-release.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in result.items() if k!='memberHashes'},indent=2))
