import pathlib,subprocess,tempfile,json
P=pathlib.Path(__file__).resolve().parent;J=P.parent/'toolchains/jdk/jdk-17.0.21-lite/bin'
with tempfile.TemporaryDirectory(prefix='fm-mailbox-') as td:
 t=pathlib.Path(td); package=t/'ru/local/voyah/fmloader';package.mkdir(parents=True)
 source=(P/'src/ru/local/voyah/fmloader/RuntimeFiles.java').read_text()
 source=source.replace('"/data/local/tmp/voyah-fm-loader-v1"',json.dumps(str(t/'runtime').replace('\\','/')))
 source=source.replace('90000:45000','1500:1500')
 source=source.replace('"/proc/sys/kernel/random/boot_id"','DIR+"/test-boot-id"')
 (package/'RuntimeFiles.java').write_text(source,encoding='utf-8')
 (package/'LocalBootstrap.java').write_text('package ru.local.voyah.fmloader; final class LocalBootstrap {static int activations;static final String VERSION="test";static void activate(android.content.Context c){activations++;}}')
 context=t/'android/content';context.mkdir(parents=True);(context/'Context.java').write_text('package android.content; public class Context {}')
 clock=t/'android/os';clock.mkdir(parents=True);(clock/'SystemClock.java').write_text('package android.os; public class SystemClock {public static long elapsedRealtime(){return System.nanoTime()/1000000;}}')
 subprocess.run([str(J/'javac.exe'),'--release','8','-encoding','UTF-8','-d',str(t/'classes'),*map(str,t.rglob('*.java')),str(P/'tests/TestMailbox.java')],check=True)
 subprocess.run([str(J/'java.exe'),'-cp',str(t/'classes'),'ru.local.voyah.fmloader.TestMailbox'],check=True,timeout=15)
