package ru.local.voyah.fmloader;
import android.app.*;
import android.content.*;
import android.os.*;
import java.util.concurrent.*;
public class LoaderService extends Service {
 public static volatile boolean ready;
 ScheduledExecutorService executor; volatile boolean stopped; final RetrySchedule retry=new RetrySchedule();
 public void onCreate(){super.onCreate();ready=false;AppLog.add(this,"CORE_CREATED","beta 0.4.3 auto recording enabled");
  NotificationManager nm=getSystemService(NotificationManager.class);
  nm.createNotificationChannel(new NotificationChannel("fm","FM Радио",NotificationManager.IMPORTANCE_LOW));
  PendingIntent pi=PendingIntent.getActivity(this,0,new Intent(this,MainActivity.class),PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);
  startForeground(1,new Notification.Builder(this,"fm").setSmallIcon(android.R.drawable.ic_media_play).setContentTitle("FM Радио").setContentText("Адаптер радио · автоматический журнал").setContentIntent(pi).build());
  executor=Executors.newSingleThreadScheduledExecutor();executor.scheduleWithFixedDelay(()->tick(),0,30,TimeUnit.SECONDS);
 }
 void save(String s){getSharedPreferences("fm",0).edit().putString("status",s).apply();}
 void tick(){if(stopped||!retry.shouldAttempt(SystemClock.elapsedRealtime()))return;try{
  RuntimeFiles.prepare(this);
  String recording;
  try{recording=RuntimeFiles.run("log-start");}catch(Exception e){recording="LOG_RECORDING_ERROR: "+e;AppLog.add(this,"LOG_START_FAILED",e.toString());}
  String result=RuntimeFiles.run("start");if(stopped)return;ready=true;save(result+"\n"+recording);retry.reset();
 }catch(Exception e){ready=false;if(stopped)return;long delay=retry.failed(SystemClock.elapsedRealtime());AppLog.add(this,"FM_START_FAILED",e.toString());save("Не удалось запустить FM. Повторная проверка через "+(delay/1000)+" сек.\n"+e.getMessage());}}
 public int onStartCommand(Intent i,int flags,int id){if(retry.failures()>0&&executor!=null&&!stopped)executor.execute(()->{retry.reset();tick();});return START_STICKY;}
 public void onDestroy(){stopped=true;ready=false;AppLog.add(this,"CORE_DESTROYED","System stopped core");if(executor!=null)executor.shutdownNow();super.onDestroy();}
 public IBinder onBind(Intent i){return null;}
}
