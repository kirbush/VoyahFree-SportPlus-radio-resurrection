package ru.local.voyah.fmloader;
import android.content.Context;
import android.os.Build;
import java.io.*;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.zip.*;
public final class DiagnosticReport {
 static final String AUTOMATIC_SOURCE="automatic-report-source";
 public static synchronized File create(Context c,String notes)throws Exception {
  return create(c,notes,false);
 }
 static synchronized File createAutomatic(Context c,String notes)throws Exception {
  return create(c,notes,true);
 }
 private static File create(Context c,String notes,boolean automatic)throws Exception {
  File marker=new File(c.getFilesDir(),AUTOMATIC_SOURCE);if(automatic&&marker.exists())throw new IOException("Automatic source is still pending");
  String diagnostic;
  try{RuntimeFiles.prepare(c);diagnostic=RuntimeFiles.run("diagnostic");AppLog.add(c,"REPORT","Root diagnostic bytes="+diagnostic.length());}
  catch(Exception e){diagnostic="ROOT DIAGNOSTIC UNAVAILABLE\n"+e.toString();AppLog.add(c,"REPORT_LIMITED",diagnostic);}
  SimpleDateFormat format=new SimpleDateFormat("yyyyMMdd-HHmmss",Locale.US);long stamp=System.currentTimeMillis();File file;
  String reserved=reservedAutomatic(marker);
  do{file=new File(c.getFilesDir(),"Voyah-FM-report-"+format.format(new Date(stamp))+".zip");stamp+=1000;}while(file.exists()||new File(c.getFilesDir(),file.getName()+".partial").exists()||file.getName().equals(reserved));
  // Persist ownership before writing ZIP bytes; a process death cannot orphan an auto source.
  if(automatic){File record=new File(c.getFilesDir(),AUTOMATIC_SOURCE+".partial");try{try(FileOutputStream out=new FileOutputStream(record)){out.write(file.getName().getBytes("UTF-8"));out.getFD().sync();}if(!record.renameTo(marker))throw new IOException("Automatic source tracking unavailable");}finally{record.delete();}}
  File temporary=new File(c.getFilesDir(),file.getName()+".partial");
  try{try(FileOutputStream raw=new FileOutputStream(temporary);ZipOutputStream z=new ZipOutputStream(automatic?new AutomaticLimit(raw):raw)){
   text(z,"environment.txt","Voyah FM 0.5.0-beta / integrated report menu\nReportFormat=2\nAutomaticLogging=enabled\nCrashEvidence=targeted crash buffer and FM DropBox in diagnostics.txt when root is available\nTime="+new Date()+"\nModel="+Build.MODEL+"\nFingerprint="+Build.FINGERPRINT+"\nSDK="+Build.VERSION.SDK_INT+"\nAppUID="+android.os.Process.myUid()+"\nNotes="+notes+"\n");
   text(z,"diagnostics.txt",diagnostic);
   for(String name:new String[]{"events.previous.log","events.log"}){File log=new File(c.getFilesDir(),name);if(log.exists()){z.putNextEntry(new ZipEntry(name));try(InputStream in=new FileInputStream(log)){byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1)z.write(b,0,n);}z.closeEntry();}}
  }
  if(!temporary.renameTo(file))throw new IOException("Не удалось завершить ZIP");
  }finally{temporary.delete();}
  return file;
 }
 private static String reservedAutomatic(File marker){try{if(marker.length()>256)return "";byte[] b=new byte[(int)marker.length()];try(DataInputStream in=new DataInputStream(new FileInputStream(marker))){in.readFully(b);}return new String(b,"UTF-8");}catch(IOException ignored){return "";}}
 private static final class AutomaticLimit extends FilterOutputStream {
  long bytes;AutomaticLimit(OutputStream out){super(out);}
  public void write(int value)throws IOException{if(bytes>=16L*1024*1024)throw new IOException("Automatic report size limit");out.write(value);bytes++;}
  public void write(byte[] data,int offset,int length)throws IOException{if(bytes+length>16L*1024*1024)throw new IOException("Automatic report size limit");out.write(data,offset,length);bytes+=length;}
 }
 static void text(ZipOutputStream z,String name,String s)throws Exception {z.putNextEntry(new ZipEntry(name));z.write(s.getBytes("UTF-8"));z.closeEntry();}
}
