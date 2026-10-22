package ru.local.voyah.fmloader;
import android.content.Context;
import java.io.*;
import java.text.SimpleDateFormat;
import java.util.*;
public final class AppLog {
 public static synchronized void add(Context c,String tag,String message){try{
  File f=new File(c.getFilesDir(),"events.log");if(f.length()>1048576){File old=new File(c.getFilesDir(),"events.previous.log");old.delete();f.renameTo(old);}
  try(FileOutputStream out=new FileOutputStream(f,true)){String line=new SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS",Locale.US).format(new Date())+" "+tag+" "+message+"\n";out.write(line.getBytes("UTF-8"));}
 }catch(Exception ignored){}}
}
