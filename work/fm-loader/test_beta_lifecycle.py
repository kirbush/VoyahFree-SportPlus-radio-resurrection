"""Execute the actual service/receiver on JVM with only Android I/O stubbed."""
import pathlib,subprocess,tempfile
P=pathlib.Path(__file__).resolve().parent;J=P.parent/'toolchains/jdk/jdk-17.0.21-lite/bin'
sources={
'android/content/Context.java':'''package android.content; public class Context {
 public static int starts;public SharedPreferences prefs=new SharedPreferences();
 public SharedPreferences getSharedPreferences(String n,int m){return prefs;}
 public <T>T getSystemService(Class<T> cls){try{return cls.newInstance();}catch(Exception e){return null;}}
 public ComponentName startForegroundService(Intent i){starts++;return null;}
}''',
'android/content/SharedPreferences.java':'''package android.content;public class SharedPreferences {
 java.util.Map<String,String> data=new java.util.HashMap<>();
 public String getString(String k,String d){return data.containsKey(k)?data.get(k):d;}
 public Editor edit(){return new Editor();}public class Editor{public Editor putString(String k,String v){data.put(k,v);return this;}public void apply(){}}
}''',
'android/content/Intent.java':'''package android.content;public class Intent {
 public static final String ACTION_BOOT_COMPLETED="boot",ACTION_MY_PACKAGE_REPLACED="replaced";String action;
 public Intent(Context c,Class<?> cls){}public Intent(String a){action=a;}public String getAction(){return action;}
}''',
'android/content/ComponentName.java':'package android.content;public class ComponentName{public ComponentName(String p,String c){}}',
'android/content/BroadcastReceiver.java':'package android.content;public abstract class BroadcastReceiver{public abstract void onReceive(Context c,Intent i);}',
'android/os/IBinder.java':'package android.os;public interface IBinder{}',
'android/os/SystemClock.java':'package android.os;public class SystemClock{public static long now;public static long elapsedRealtime(){return now;}}',
'android/os/Looper.java':'package android.os;public class Looper{}',
'android/os/Handler.java':'package android.os;public class Handler{public Handler(Looper l){}public void post(Runnable r){r.run();}}',
'android/app/Service.java':'''package android.app;import android.content.*;public class Service extends Context {
 public static final int START_STICKY=1;public void onCreate(){}public void onDestroy(){}
 public void startForeground(int id,Notification n){}public android.os.Looper getMainLooper(){return new android.os.Looper();}
}''',
'android/app/Notification.java':'''package android.app;public class Notification{public static class Builder {
 public Builder(android.content.Context c,String id){}public Builder setSmallIcon(int i){return this;}public Builder setContentTitle(String s){return this;}
 public Builder setContentText(String s){return this;}public Builder setContentIntent(PendingIntent p){return this;}public Notification build(){return new Notification();}
}}''',
'android/app/NotificationManager.java':'package android.app;public class NotificationManager{public static final int IMPORTANCE_LOW=2;public void createNotificationChannel(NotificationChannel c){}}',
'android/app/NotificationChannel.java':'package android.app;public class NotificationChannel{public NotificationChannel(String a,String b,int c){}}',
'android/app/PendingIntent.java':'package android.app;public class PendingIntent{public static final int FLAG_UPDATE_CURRENT=1,FLAG_IMMUTABLE=2;public static PendingIntent getActivity(android.content.Context c,int i,android.content.Intent n,int f){return null;}}',
'android/R.java':'package android;public class R{public static class drawable{public static final int ic_media_play=1;}}',
'android/media/browse/MediaBrowser.java':'''package android.media.browse;public class MediaBrowser {
 ConnectionCallback callback;public MediaBrowser(android.content.Context c,android.content.ComponentName n,ConnectionCallback cb,Object o){callback=cb;}
 public void disconnect(){}public Object getSessionToken(){return null;}public void connect(){callback.onConnected();}
 public static class ConnectionCallback{public void onConnected(){}public void onConnectionFailed(){}}
}''',
'android/media/session/MediaController.java':'''package android.media.session;public class MediaController {
 public static int plays;public MediaController(android.content.Context c,Object token){}public Controls getTransportControls(){return new Controls();}
 public static class Controls{public void play(){plays++;}}
}''',
'ru/local/voyah/fmloader/MainActivity.java':'package ru.local.voyah.fmloader;public class MainActivity{}',
'ru/local/voyah/fmloader/AppLog.java':'package ru.local.voyah.fmloader;public class AppLog{public static void add(android.content.Context c,String t,String m){}}',
'ru/local/voyah/fmloader/RuntimeFiles.java':'''package ru.local.voyah.fmloader;public class RuntimeFiles {
 static java.util.List<String> actions=new java.util.ArrayList<>();static boolean logFail,startFail;static int starts;
 static void prepare(android.content.Context c){actions.add("prepare");}
 static String run(String a)throws Exception{actions.add(a);if(a.equals("log-start")){if(logFail)throw new Exception("LOG_TEST_FAIL");return "LOG_ALREADY_RECORDING";}
 if(a.equals("start")){if(startFail)throw new Exception("USB_MISSING");return starts++==0?"READY serial=/dev/ttyACM0":"READY_ALREADY_ACTIVE";}throw new AssertionError(a);}
}''',
'ru/local/voyah/fmloader/TestLifecycle.java':'''package ru.local.voyah.fmloader;import android.media.session.MediaController;import android.content.*;
public class TestLifecycle {
 static void require(boolean b,String m){if(!b)throw new AssertionError(m);}
 public static void main(String[] args){
  LoaderService s=new LoaderService();s.tick();s.tick();
  require(LoaderService.ready,"radio ready");require(MediaController.plays==0,"background startup must not force FM playback over Tweaks preference");
  require(RuntimeFiles.actions.toString().equals("[prepare, log-start, start, prepare, log-start, start]"),"logging before radio on every health tick");
  RuntimeFiles.logFail=true;s.tick();require(LoaderService.ready,"log failure must not mute radio");
  require(s.prefs.getString("status","").contains("LOG_RECORDING_ERROR"),"recording error visible");
  RuntimeFiles.logFail=false;RuntimeFiles.startFail=true;s.tick();require(!LoaderService.ready,"missing USB clears readiness");
  int count=RuntimeFiles.actions.size();s.tick();require(RuntimeFiles.actions.size()==count,"retry backoff");
  android.os.SystemClock.now=30001;RuntimeFiles.startFail=false;s.tick();require(LoaderService.ready,"USB recovery");
  require(MediaController.plays==0,"background recovery must not force playback");
  s.onDestroy();require(!RuntimeFiles.actions.contains("log-stop")&&!RuntimeFiles.actions.contains("stop"),"closing UI/service must not stop recorder or native FM");
  BootReceiver boot=new BootReceiver();Context c=new Context();boot.onReceive(c,new Intent(Intent.ACTION_BOOT_COMPLETED));boot.onReceive(c,new Intent(Intent.ACTION_MY_PACKAGE_REPLACED));boot.onReceive(c,new Intent("other"));
  require(Context.starts==2,"boot and update enable core by default without prior checkbox");
  System.out.println("PASS actual service: autolog, no repeated play/focus, log failure, USB backoff/recovery, non-destructive close, boot/update defaults");
 }
}'''
}
with tempfile.TemporaryDirectory(prefix='fm-beta-lifecycle-') as temp:
 t=pathlib.Path(temp)
 for name,source in sources.items():f=t/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(source,encoding='utf8')
 originals=[P/'src/ru/local/voyah/fmloader'/n for n in ['LoaderService.java','BootReceiver.java','RetrySchedule.java']]
 subprocess.run([str(J/'javac.exe'),'--release','8','-encoding','UTF-8','-d',str(t/'classes'),*map(str,t.rglob('*.java')),*map(str,originals)],check=True)
 subprocess.run([str(J/'java.exe'),'-cp',str(t/'classes'),'ru.local.voyah.fmloader.TestLifecycle'],check=True,timeout=20)
