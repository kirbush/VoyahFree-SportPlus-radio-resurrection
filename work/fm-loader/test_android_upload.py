"""Offline JVM tests for the Android uploader; HTTPS stays on loopback."""
import pathlib, subprocess, tempfile

P = pathlib.Path(__file__).resolve().parent
J = P.parent / 'toolchains/jdk/jdk-17.0.21-lite/bin'
with tempfile.TemporaryDirectory(prefix='fm-android-upload-') as td:
    t = pathlib.Path(td)
    key = t / 'localhost.p12'
    subprocess.run([str(J / 'keytool.exe'), '-genkeypair', '-alias', 'localhost',
                    '-keyalg', 'RSA', '-storetype', 'PKCS12', '-keystore', str(key),
                    '-storepass', 'test-only-password', '-keypass', 'test-only-password',
                    '-dname', 'CN=localhost', '-ext', 'SAN=dns:localhost', '-validity', '1'],
                   check=True, capture_output=True)
    untrusted = t / 'untrusted.p12'
    subprocess.run([str(J / 'keytool.exe'), '-genkeypair', '-alias', 'untrusted',
                    '-keyalg', 'RSA', '-storetype', 'PKCS12', '-keystore', str(untrusted),
                    '-storepass', 'test-only-password', '-keypass', 'test-only-password',
                    '-dname', 'CN=localhost', '-ext', 'SAN=dns:localhost', '-validity', '1'],
                   check=True, capture_output=True)
    src = P / 'src/ru/local/voyah/fmloader'
    production = [src / n for n in ['UploadQueue.java', 'ReportCoordinator.java',
                                    'MenuActionReceiver.java', 'DiagnosticReport.java', 'AppLog.java',
                                    'LoaderService.java', 'RetrySchedule.java']]
    subprocess.run([str(J / 'javac.exe'), '--release', '8', '-encoding', 'UTF-8',
                    '-d', str(t / 'classes'), *map(str, (P / 'tests/android_upload_stubs').rglob('*.java')),
                    *map(str, production), str(P / 'tests/TestAndroidUpload.java')], check=True)
    subprocess.run([str(J / 'java.exe'), '-cp', str(t / 'classes'),
                    '-Djavax.net.ssl.trustStore=' + str(key),
                    '-Djavax.net.ssl.trustStorePassword=test-only-password',
                    'ru.local.voyah.fmloader.TestAndroidUpload', str(t / 'data'), str(key), str(untrusted)],
                   check=True, timeout=90)
