"""Offline APK build with previously verified official SDK/JDK archives."""
import pathlib,subprocess,zipfile,os,secrets,json,hashlib
P=pathlib.Path(__file__).resolve().parent; W=P.parent
J=W/'toolchains/jdk/jdk-17.0.21-lite/bin'; B=W/'toolchains/build-tools/android-14'; A=W/'toolchains/platform/android-11/android.jar'
out=P/'build';out.mkdir(exist_ok=True); (out/'classes').mkdir(exist_ok=True);(out/'dex').mkdir(exist_ok=True)
def run(*args):subprocess.run([str(a) for a in args],check=True,cwd=P)
run(J/'javac.exe','-encoding','UTF-8','--release','8','-classpath',A,'-d',out/'classes',*sorted((P/'src').rglob('*.java')))
jar=out/'classes.jar'
with zipfile.ZipFile(jar,'w') as z:
 for f in (out/'classes').rglob('*.class'):z.write(f,f.relative_to(out/'classes').as_posix())
run(J/'java.exe','-cp',B/'lib/d8.jar','com.android.tools.r8.D8','--lib',A,'--min-api','26','--output',out/'dex',jar)
apk=out/'unsigned.apk'
run(B/'aapt.exe','package','-f','-M','AndroidManifest.xml','-I','../toolchains/platform/android-11/android.jar','-A','assets','-F','build/unsigned.apk')
with zipfile.ZipFile(apk,'a',zipfile.ZIP_DEFLATED) as z:z.write(out/'dex/classes.dex','classes.dex')
run(B/'zipalign.exe','-f','4','build/unsigned.apk','build/aligned.apk')
key=W/'fm-loader-signing.p12'; password=W/'fm-loader-signing.password'
if not password.exists():password.write_text(secrets.token_urlsafe(32),encoding='ascii')
envpass=password.read_text(encoding='ascii');os.environ['FM_BUILD_KEY_PASS']=envpass
if not key.exists():run(J/'keytool.exe','-genkeypair','-keystore',key,'-storetype','PKCS12','-storepass:env','FM_BUILD_KEY_PASS','-alias','fmloader','-keyalg','RSA','-keysize','3072','-validity','3650','-dname','CN=Local Voyah FM Loader Prototype')
target=W.parent/'outputs/Voyah-FM-Tester-0.3.apk'
run(J/'java.exe','-jar',B/'lib/apksigner.jar','sign','--ks',key,'--ks-key-alias','fmloader','--ks-pass','env:FM_BUILD_KEY_PASS','--out',target,out/'aligned.apk')
run(J/'java.exe','-jar',B/'lib/apksigner.jar','verify','--verbose','--print-certs',target)
print(json.dumps({'apk':str(target),'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()},indent=2))
