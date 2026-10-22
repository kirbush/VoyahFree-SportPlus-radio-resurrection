package ru.local.voyah.fmloader;
import android.app.*;
import android.content.*;
import android.os.*;
import android.graphics.Color;
import android.view.Gravity;
import android.widget.*;
import java.util.concurrent.*;
import ru.local.voyah.fmloader.ui.MenuBridge;
/** One launcher; settings remain available when radio bootstrap is unavailable. */
public class MainActivity extends Activity {
 final Handler handler=new Handler(Looper.getMainLooper());
 final ExecutorService worker=Executors.newSingleThreadExecutor();
 TextView status; boolean opened,resumed,preparing; volatile boolean uiReady; long began,nextUiAttempt;
 final Runnable refresh=new Runnable(){public void run(){
  if(isFinishing()||opened||!resumed)return;
  if(MenuBridge.isShowing(MainActivity.this)){handler.postDelayed(this,500);return;}
  if(LoaderService.ready&&uiReady){try{
   Intent radio=new Intent().setClassName("com.pateo.rdsapp","com.pateo.rdsapp.main.activity.MainActivity");
   radio.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TOP|Intent.FLAG_ACTIVITY_SINGLE_TOP);
   startActivity(radio);opened=true;finish();return;
  }catch(Exception e){status.setText("Не удалось открыть радио. Настройки и логи доступны ниже.");AppLog.add(MainActivity.this,"RADIO_UI_OPEN_FAILED",e.getClass().getSimpleName());}}
  if(LoaderService.ready&&!uiReady&&!preparing&&SystemClock.elapsedRealtime()>=nextUiAttempt){
   preparing=true;worker.execute(()->{
    try{String result=RuntimeFiles.run("ui-start");uiReady=result.contains("UI_READY");}
    catch(Exception e){AppLog.add(MainActivity.this,"MENU_PREPARE_FAILED",e.getClass().getSimpleName());}
    finally{handler.post(()->{preparing=false;nextUiAttempt=SystemClock.elapsedRealtime()+10000;});}
   });
  }
  if(SystemClock.elapsedRealtime()-began>15000)status.setText("Подключение радио…\n"+getSharedPreferences("fm",0).getString("status","")+"\nНастройки и логи доступны ниже.");
  handler.postDelayed(this,500);
 }};
 protected void onCreate(Bundle state){super.onCreate(state);
  LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setGravity(Gravity.CENTER);root.setPadding(48,24,48,24);root.setBackgroundColor(Color.rgb(18,23,30));
  ImageView icon=new ImageView(this);icon.setImageResource(getResources().getIdentifier("radio","drawable",getPackageName()));root.addView(icon,new LinearLayout.LayoutParams(120,120));
  status=new TextView(this);status.setText("FM Радио\nПодключение…");status.setTextColor(Color.WHITE);status.setTextSize(23);status.setGravity(Gravity.CENTER);root.addView(status);
  Button settings=new Button(this);settings.setText("Настройки FM");settings.setOnClickListener(v->MenuBridge.showSettings(this));root.addView(settings);
  setContentView(root);getSharedPreferences("fm",0).edit().putBoolean("boot",true).apply();
  AppLog.add(this,"RADIO_OPEN","beta 0.5.0");began=SystemClock.elapsedRealtime();
  try{startForegroundService(new Intent(this,LoaderService.class));}catch(Exception e){status.setText("Не удалось подключить радио. Откройте настройки FM.");AppLog.add(this,"START_ERROR",e.getClass().getSimpleName());}
 }
 protected void onResume(){super.onResume();resumed=true;handler.post(refresh);}
 protected void onPause(){resumed=false;handler.removeCallbacks(refresh);MenuBridge.closeSettings(this);super.onPause();}
 protected void onDestroy(){MenuBridge.closeSettings(this);handler.removeCallbacksAndMessages(null);worker.shutdownNow();super.onDestroy();}
}
