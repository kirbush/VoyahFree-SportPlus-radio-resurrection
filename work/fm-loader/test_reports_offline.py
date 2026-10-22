import pathlib,tempfile,subprocess
P=pathlib.Path(__file__).resolve().parent;J=P.parent/'toolchains/jdk/jdk-17.0.21-lite/bin'
with tempfile.TemporaryDirectory(prefix='fm-reports-') as td:
 t=pathlib.Path(td);context=t/'android/content';context.mkdir(parents=True)
 (context/'Context.java').write_text('package android.content; public class Context {private java.io.File dir; public Context(java.io.File d){dir=d;dir.mkdirs();} public java.io.File getFilesDir(){return dir;}}')
 system=t/'android/os';system.mkdir(parents=True)
 (system/'Build.java').write_text('package android.os; public class Build {public static final String MODEL="TEST",FINGERPRINT="TEST_FINGERPRINT";public static class VERSION {public static final int SDK_INT=30;}}')
 (system/'Process.java').write_text('package android.os; public class Process {public static int myUid(){return 10057;}}')
 package=t/'ru/local/voyah/fmloader';package.mkdir(parents=True)
 (package/'RuntimeFiles.java').write_text('package ru.local.voyah.fmloader; public class RuntimeFiles {public static void prepare(android.content.Context c)throws Exception {if(Boolean.getBoolean("fm.root.fail"))throw new java.io.IOException("NO_ROOT");}public static String run(String s){return "ROOT_RESULT";}}')
 originals=[P/'src/ru/local/voyah/fmloader'/n for n in ['AppLog.java','DiagnosticReport.java']]
 subprocess.run([str(J/'javac.exe'),'--release','8','-encoding','UTF-8','-d',str(t/'classes'),*map(str,t.rglob('*.java')),*map(str,originals),str(P/'tests/TestReports.java')],check=True)
 subprocess.run([str(J/'java.exe'),'-cp',str(t/'classes'),'ru.local.voyah.fmloader.TestReports',str(t/'output')],check=True,timeout=15)
