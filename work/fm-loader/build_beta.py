"""Build the single FM Radio APK, including its separately loaded native UI DEX."""
import pathlib, subprocess, zipfile, os, tempfile, json, hashlib, shutil, xml.etree.ElementTree as ET
from payload_format import validate_source_assets,validate_apk_shells
P=pathlib.Path(__file__).resolve().parent; W=P.parent; O=W.parent/'outputs'
VERSION='0.5.0-beta'; VERSION_CODE='8'
J=W/'toolchains/jdk/jdk-17.0.21-lite/bin'; B=W/'toolchains/build-tools/android-14'; A=W/'toolchains/platform/android-11/android.jar'
def run(*args,cwd=P):subprocess.run([str(x) for x in args],check=True,cwd=cwd)
def dex_sources(sources,root):
 (root/'classes').mkdir();(root/'dex').mkdir()
 run(J/'javac.exe','-encoding','UTF-8','--release','8','-classpath',A,'-d',root/'classes',*sources)
 with zipfile.ZipFile(root/'classes.jar','w') as z:
  for f in sorted((root/'classes').rglob('*.class')):z.write(f,f.relative_to(root/'classes').as_posix())
 run(J/'java.exe','-cp',B/'lib/d8.jar','com.android.tools.r8.D8','--lib',A,'--min-api','26','--output',root/'dex',root/'classes.jar')
 dex=root/'dex/classes.dex'
 assert dex.read_bytes().startswith(b'dex\n'),'D8 did not produce a DEX'
 return dex
validate_source_assets(P/'assets')
assert not (P/'assets/upload.json').exists(),'Private upload configuration must not be bundled'
manifest=ET.parse(P/'AndroidManifest.xml').getroot(); ns='{http://schemas.android.com/apk/res/android}'
assert manifest.get(ns+'versionName')==VERSION and manifest.get(ns+'versionCode')==VERSION_CODE,'Release manifest/version mismatch'
for name,digest in {'AdayoDAB.apk':'dfafe5455ca9040306d012e3650df6181ab6e24d26f8bcaa9766a0cdc6d45905','RdsApp.apk':'36b4d73a889aa78325f6a6ff0c8113c6b13605620a5a4b045209fbff36449cca'}.items():
 assert hashlib.sha256((P/'assets'/name).read_bytes()).hexdigest()==digest,'Original OEM payload changed: '+name
ui=P/'src/ru/local/voyah/fmloader/ui';ui_sources=sorted(ui.rglob('*.java'))
assert ui_sources,'Native UI bridge sources are missing'
assert (P/'assets/ui.js').is_file(),'UI injector is missing'
O.mkdir(exist_ok=True);(W/'fm-loader-validation').mkdir(exist_ok=True)
old_password=os.environ.get('FM_BUILD_KEY_PASS');os.environ['FM_BUILD_KEY_PASS']=(W/'fm-loader-signing.password').read_text(encoding='ascii')
try:
 with tempfile.TemporaryDirectory(prefix='fm-beta-build-') as temp:
  t=pathlib.Path(temp);(t/'ui').mkdir();(t/'main').mkdir()
  print('Building native radio UI DEX...',flush=True)
  shutil.copyfile(dex_sources(ui_sources,t/'ui'),P/'assets/radio-ui.dex')
  # The loader also uses this UI for its startup/error fallback; RDS loads its own copy.
  sources=[x for x in sorted((P/'src').rglob('*.java')) if x.name!='ProbeInstrumentation.java']
  print('Building FM Radio application DEX...',flush=True)
  main_dex=dex_sources(sources,t/'main')
  # aapt's Windows archive reader requires ASCII relative paths in this workspace.
  print('Packaging and signing FM Radio...',flush=True)
  run(B/'aapt.exe','package','-f','-M','AndroidManifest.xml','-I',os.path.relpath(A,P),'-S','res','-A','assets','-F',t/'unsigned.apk')
  with zipfile.ZipFile(t/'unsigned.apk','a',zipfile.ZIP_DEFLATED) as z:z.write(main_dex,'classes.dex')
  run(B/'zipalign.exe','-f','4',t/'unsigned.apk',t/'aligned.apk')
  apk=O/('Voyah-FM-Radio-'+VERSION+'.apk')
  run(J/'java.exe','-jar',B/'lib/apksigner.jar','sign','--ks',W/'fm-loader-signing.p12','--ks-key-alias','fmloader','--ks-pass','env:FM_BUILD_KEY_PASS','--out',apk,t/'aligned.apk')
  run(J/'java.exe','-jar',B/'lib/apksigner.jar','verify','--verbose','--print-certs',apk)
  validate_apk_shells(apk)
  with zipfile.ZipFile(apk) as z:
   assert z.read('assets/radio-ui.dex')==(P/'assets/radio-ui.dex').read_bytes()
   assert z.read('assets/ui.js')==(P/'assets/ui.js').read_bytes()
  results=[dict(apk=str(apk),bytes=apk.stat().st_size,sha256=hashlib.sha256(apk.read_bytes()).hexdigest())]
  (W/'fm-loader-validation/beta-build.json').write_text(json.dumps(results,indent=2),encoding='utf8')
  print(json.dumps(results,indent=2))
finally:
 if old_password is None:os.environ.pop('FM_BUILD_KEY_PASS',None)
 else:os.environ['FM_BUILD_KEY_PASS']=old_password
