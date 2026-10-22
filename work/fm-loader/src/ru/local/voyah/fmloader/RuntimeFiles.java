package ru.local.voyah.fmloader;
import android.content.Context;
import java.io.*;
import java.util.UUID;
public final class RuntimeFiles {
 public static final String DIR="/data/local/tmp/voyah-fm-loader-v1";
 static final File BOX=new File(DIR,"mailbox");
 static boolean needsActivation;
 static String read(File f)throws Exception {try(FileInputStream in=new FileInputStream(f)){ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1)out.write(b,0,n);return out.toString("UTF-8");}}
 static synchronized void prepare(Context c)throws Exception {
  boolean active=false;
  try{active=BOX.isDirectory()&&new File(BOX,"online").exists()&&read(new File(BOX,"online")).trim().equals(read(new File("/proc/sys/kernel/random/boot_id")).trim())&&read(new File(DIR,"payload-version")).trim().equals(LocalBootstrap.VERSION);}catch(Exception ignored){}
  if(!active||needsActivation){LocalBootstrap.activate(c);needsActivation=false;}
  if(!new File(BOX,"online").exists())throw new IOException("FM-посредник не запустился. Сохраните отчёт.");
 }
 static synchronized String run(String action) throws Exception {
  if(!action.matches("check|status|start|stop|install-components|diagnostic|log-start|log-stop|ui-start"))throw new IllegalArgumentException();
  String id=UUID.randomUUID().toString();File temp=new File(BOX,"request.tmp"), request=new File(BOX,"request"), response=new File(BOX,id+".reply");
  try(FileOutputStream out=new FileOutputStream(temp)){out.write((id+" "+action+"\n").getBytes("UTF-8"));}
  if(!temp.renameTo(request))throw new IOException("Не удалось отправить запрос FM.");
  long deadline=android.os.SystemClock.elapsedRealtime()+(action.equals("install-components")?180000:action.equals("diagnostic")?90000:45000);
  while(android.os.SystemClock.elapsedRealtime()<deadline){if(response.exists()){String result=read(response);response.delete();if(!result.startsWith("OK\n"))throw new IOException(result);return result.substring(3);}Thread.sleep(200);}
  needsActivation=true;
  throw new IOException("FM-посредник не ответил. При следующей проверке он будет запущен повторно.");
 }
}
