package ru.local.voyah.fmloader;
import java.io.*;
import java.util.zip.*;
public class TestReports {
 public static void main(String[] args)throws Exception {
  android.content.Context c=new android.content.Context(new File(args[0]));
  java.util.Set<String> names=new java.util.HashSet<>();
  for(boolean unavailable:new boolean[]{false,true}){
   System.setProperty("fm.root.fail",String.valueOf(unavailable));
   File report=DiagnosticReport.create(c,"Частота89.9, Unicode notes");
   if(!names.add(report.getName()))throw new AssertionError("Report overwritten within the same second");
   if(!report.getName().matches("Voyah-FM-report-[0-9]{8}-[0-9]{6}\\.zip"))throw new AssertionError("Exporter incompatible name");
   try(ZipFile zip=new ZipFile(report)){
    String diagnostic=read(zip,"diagnostics.txt"),env=read(zip,"environment.txt");
    if(!env.contains("Частота89.9")||!env.contains("AppUID=10057"))throw new AssertionError(env);
    if(unavailable?!diagnostic.contains("ROOT DIAGNOSTIC UNAVAILABLE"):!diagnostic.contains("ROOT_RESULT"))throw new AssertionError(diagnostic);
    if(zip.getEntry("events.log")==null)throw new AssertionError("Missing app log");
   }
  }
  for(File f:c.getFilesDir().listFiles())if(f.getName().endsWith(".partial"))throw new AssertionError("Incomplete report left behind");
  System.out.println("PASS ZIP report, Unicode notes, app log, root-failure fallback");
 }
 static String read(ZipFile z,String name)throws Exception{try(InputStream in=z.getInputStream(z.getEntry(name));ByteArrayOutputStream out=new ByteArrayOutputStream()){byte[] b=new byte[1024];int n;while((n=in.read(b))!=-1)out.write(b,0,n);return out.toString("UTF-8");}}
}
