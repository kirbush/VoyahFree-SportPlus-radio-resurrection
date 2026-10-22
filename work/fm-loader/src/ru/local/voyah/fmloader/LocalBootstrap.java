package ru.local.voyah.fmloader;
import android.content.Context;
import android.os.Process;
import java.io.*;
import java.net.*;
public final class LocalBootstrap {
 public static final String VERSION="0.5.0-beta-v1";
 static String quote(String s){return "'"+s.replace("'","'\\''")+"'";}
 public static void activate(Context c)throws Exception {
  AppLog.add(c,"BOOTSTRAP","Trying existing loopback maintenance service");
  File stage=new File(c.getFilesDir(),"payload-v05");stage.mkdirs();
  String[] names={"helper.sh","broker.sh","adapter.js","ui.js","radio-ui.dex","template.xml","frida-inject","AdayoDAB.apk","RdsApp.apk"};
  for(String name:names)try(InputStream in=c.getAssets().open(name);OutputStream out=new FileOutputStream(new File(stage,name))){byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1)out.write(b,0,n);}
  String d=RuntimeFiles.DIR;
  StringBuilder script=new StringBuilder("#!/system/bin/sh\nset -e\n[ \"$(id -u)\" = 0 ] || exit 81\nD="+d+"\nmkdir -p \"$D/mailbox\"\nchmod 755 \"$D\"\nchown "+Process.myUid()+":"+Process.myUid()+" \"$D/mailbox\"\nchmod 700 \"$D/mailbox\"\n");
  script.append("if [ -f \"$D/broker.pid\" ]; then\np=$(cat \"$D/broker.pid\")\ncase \"$p\" in ''|*[!0-9]*) ;; *)\nif [ -f /proc/$p/cmdline ]; then\ncmd=$(tr '\\000' ' ' < /proc/$p/cmdline)\ncase \"$cmd\" in *\"sh $D/broker.sh \"*) kill \"$p\"; sleep 1;; esac\nfi;; esac\nfi\n");
  for(String name:names){String f=quote(new File(stage,name).getAbsolutePath());script.append("if ! cmp -s ").append(f).append(" \"$D/").append(name).append("\"; then cp ").append(f).append(" \"$D/").append(name).append("\"; fi\nchown 0:0 \"$D/").append(name).append("\"\nchmod 644 \"$D/").append(name).append("\"\n");}
  script.append("chmod 755 \"$D/frida-inject\"\necho "+VERSION+" > \"$D/payload-version\"\nchmod 644 \"$D/payload-version\"\nnohup setsid sh \"$D/broker.sh\" > \"$D/broker.log\" 2>&1 < /dev/null &\nsleep 1\n");
  File activate=new File(stage,"activate.sh");try(FileOutputStream out=new FileOutputStream(activate)){out.write(script.toString().getBytes("UTF-8"));}
  try(Socket socket=new Socket()){
   socket.connect(new InetSocketAddress("127.0.0.1",23),2500);
   String result=TelnetSession.execute(socket,"sh "+quote(activate.getAbsolutePath()));AppLog.add(c,"BOOTSTRAP_OK",result);
  }catch(Exception e){AppLog.add(c,"BOOTSTRAP_FAILED",e.toString());throw new IOException("Локальный root-доступ недоступен. Сохраните отчёт; для запуска потребуется активация через ADB. "+e.getMessage(),e);}
 }
}
