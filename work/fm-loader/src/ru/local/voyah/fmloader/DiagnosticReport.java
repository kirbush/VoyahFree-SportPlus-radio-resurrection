package ru.local.voyah.fmloader;
import android.content.Context;
import android.os.Build;
import java.io.*;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.zip.*;
public final class DiagnosticReport {
 public static synchronized File create(Context c,String notes)throws Exception {
  String diagnostic;
  try{RuntimeFiles.prepare(c);diagnostic=RuntimeFiles.run("diagnostic");AppLog.add(c,"REPORT","Root diagnostic bytes="+diagnostic.length());}
  catch(Exception e){diagnostic="ROOT DIAGNOSTIC UNAVAILABLE\n"+e.toString();AppLog.add(c,"REPORT_LIMITED",diagnostic);}
  SimpleDateFormat format=new SimpleDateFormat("yyyyMMdd-HHmmss",Locale.US);long stamp=System.currentTimeMillis();File file;
  do{file=new File(c.getFilesDir(),"Voyah-FM-report-"+format.format(new Date(stamp))+".zip");stamp+=1000;}while(file.exists());
  File temporary=new File(c.getFilesDir(),file.getName()+".partial");
  try{try(ZipOutputStream z=new ZipOutputStream(new FileOutputStream(temporary))){
   text(z,"environment.txt","Voyah FM 0.4.3 beta / separate diagnostics\nTime="+new Date()+"\nModel="+Build.MODEL+"\nFingerprint="+Build.FINGERPRINT+"\nSDK="+Build.VERSION.SDK_INT+"\nAppUID="+android.os.Process.myUid()+"\nNotes="+notes+"\n");
   text(z,"diagnostics.txt",diagnostic);
   for(String name:new String[]{"events.previous.log","events.log"}){File log=new File(c.getFilesDir(),name);if(log.exists()){z.putNextEntry(new ZipEntry(name));try(InputStream in=new FileInputStream(log)){byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1)z.write(b,0,n);}z.closeEntry();}}
  }
  if(!temporary.renameTo(file))throw new IOException("Не удалось завершить ZIP");
  }finally{temporary.delete();}
  return file;
 }
 static void text(ZipOutputStream z,String name,String s)throws Exception {z.putNextEntry(new ZipEntry(name));z.write(s.getBytes("UTF-8"));z.closeEntry();}
}
