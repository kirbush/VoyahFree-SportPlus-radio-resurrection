"""Build both APKs offline with the existing update signing key and official SDK."""
import pathlib, subprocess, zipfile, os, tempfile, json, hashlib
from payload_format import validate_source_assets,validate_apk_shells
P=pathlib.Path(__file__).resolve().parent; W=P.parent; O=W.parent/'outputs'
validate_source_assets(P/'assets')
J=W/'toolchains/jdk/jdk-17.0.21-lite/bin'; B=W/'toolchains/build-tools/android-14'; A=W/'toolchains/platform/android-11/android.jar'
os.environ['FM_BUILD_KEY_PASS']=(W/'fm-loader-signing.password').read_text(encoding='ascii')
def run(*args,cwd):subprocess.run([str(x) for x in args],check=True,cwd=cwd)
results=[]
for project,name in [(P,'Radio'),(W/'fm-diagnostics','Diagnostics')]:
 with tempfile.TemporaryDirectory(prefix='fm-beta-build-') as temp:
  t=pathlib.Path(temp);(t/'classes').mkdir();(t/'dex').mkdir()
  sources=[x for x in sorted((project/'src').rglob('*.java')) if x.name!='ProbeInstrumentation.java']
  run(J/'javac.exe','-encoding','UTF-8','--release','8','-classpath',A,'-d',t/'classes',*sources,cwd=project)
  with zipfile.ZipFile(t/'classes.jar','w') as z:
   for f in (t/'classes').rglob('*.class'):z.write(f,f.relative_to(t/'classes').as_posix())
  run(J/'java.exe','-cp',B/'lib/d8.jar','com.android.tools.r8.D8','--lib',A,'--min-api','26','--output',t/'dex',t/'classes.jar',cwd=project)
  # aapt's Windows archive reader requires ASCII relative paths in this workspace.
  args=[B/'aapt.exe','package','-f','-M','AndroidManifest.xml','-I',os.path.relpath(A,project),'-S','res','-F',t/'unsigned.apk']
  if (project/'assets').exists():args.extend(['-A','assets'])
  run(*args,cwd=project)
  with zipfile.ZipFile(t/'unsigned.apk','a',zipfile.ZIP_DEFLATED) as z:z.write(t/'dex/classes.dex','classes.dex')
  run(B/'zipalign.exe','-f','4',t/'unsigned.apk',t/'aligned.apk',cwd=project)
  apk=O/('Voyah-FM-'+name+'-0.4.3-beta.apk')
  run(J/'java.exe','-jar',B/'lib/apksigner.jar','sign','--ks',W/'fm-loader-signing.p12','--ks-key-alias','fmloader','--ks-pass','env:FM_BUILD_KEY_PASS','--out',apk,t/'aligned.apk',cwd=project)
  run(J/'java.exe','-jar',B/'lib/apksigner.jar','verify','--verbose','--print-certs',apk,cwd=project)
  if name=='Radio':validate_apk_shells(apk)
  results.append(dict(apk=str(apk),bytes=apk.stat().st_size,sha256=hashlib.sha256(apk.read_bytes()).hexdigest()))
(W/'fm-loader-validation/beta-build.json').write_text(json.dumps(results,indent=2),encoding='utf8')
print(json.dumps(results,indent=2))
