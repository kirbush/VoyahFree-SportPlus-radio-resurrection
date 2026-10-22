"""A standalone, UI-independent Windows collector; no APKs or install actions."""
import hashlib,json,pathlib,zipfile
from payload_format import validate_shell
P=pathlib.Path(__file__).resolve().parent;W=P.parent;O=W.parent/'outputs'
checks=json.loads((W/'fm-loader-validation/pc-collect-tests.json').read_text('utf8'))
assert len(checks)==11 and all(x['passed'] for x in checks)
validate_shell((P/'Collect-FM-state.sh').read_bytes(),'Collect-FM-state.sh')
assert (P/'Collect-FM-now.ps1').read_bytes().startswith(b'\xef\xbb\xbf')
files={n:P/n for n in ['Collect-FM-now.cmd','Collect-FM-now.ps1','Collect-FM-state.sh','Upload-FM-report.ps1','upload.example.json']}
files['ИНСТРУКЦИЯ.txt']=P/'COLLECT-START-HERE.txt'
for name in ['adb.exe','AdbWinApi.dll','AdbWinUsbApi.dll','NOTICE.txt']:files['adb/'+name]=W/'installer/package/adb'/name
hashes={n:hashlib.sha256(f.read_bytes()).hexdigest() for n,f in files.items()}
target=O/'Voyah-FM-PC-Collect-2.zip'
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
 for name,f in files.items():z.write(f,name)
 z.writestr('SHA256.json',json.dumps(hashes,indent=2))
with zipfile.ZipFile(target) as z:
 assert z.testzip() is None
 for name,h in hashes.items():assert hashlib.sha256(z.read(name)).hexdigest()==h,name
 assert not any(n.endswith(('.apk','.p12','.password')) for n in z.namelist())
result={'archive':str(target),'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'memberHashes':hashes}
(W/'fm-loader-validation/pc-collect-package.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in result.items() if k!='memberHashes'}))
