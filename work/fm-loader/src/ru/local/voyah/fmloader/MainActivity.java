package ru.local.voyah.fmloader;
import android.app.*;
import android.content.*;
import android.os.*;
import android.graphics.Color;
import android.view.Gravity;
import android.widget.*;
/** Prepare the single backend, then show the untouched OEM UI. */
public class MainActivity extends Activity {
 final Handler handler=new Handler(Looper.getMainLooper());
 TextView status; boolean opened; long began;
 final Runnable refresh=new Runnable(){public void run(){
  if(isFinishing()||opened)return;
  if(LoaderService.ready){try{
   startActivity(new Intent().setClassName("com.pateo.rdsapp","com.pateo.rdsapp.main.activity.MainActivity"));
   opened=true;finish();return;
  }catch(Exception e){status.setText("Не удалось открыть радио. Откройте FM Диагностику.\n"+e.getMessage());}}
  if(SystemClock.elapsedRealtime()-began>15000)status.setText("Подключение радио…\n"+getSharedPreferences("fm",0).getString("status",""));
  handler.postDelayed(this,500);
 }};
 protected void onCreate(Bundle state){super.onCreate(state);
  LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setGravity(Gravity.CENTER);root.setPadding(48,24,48,24);root.setBackgroundColor(Color.rgb(18,23,30));
  ImageView icon=new ImageView(this);icon.setImageResource(getResources().getIdentifier("radio","drawable",getPackageName()));root.addView(icon,new LinearLayout.LayoutParams(150,150));
  status=new TextView(this);status.setText("FM Радио\nПодключение…");status.setTextColor(Color.WHITE);status.setTextSize(23);status.setGravity(Gravity.CENTER);root.addView(status);
  setContentView(root);getSharedPreferences("fm",0).edit().putBoolean("boot",true).apply();
  AppLog.add(this,"RADIO_OPEN","beta 0.4.3");began=SystemClock.elapsedRealtime();
  try{startForegroundService(new Intent(this,LoaderService.class));}catch(Exception e){status.setText("Не удалось подключить радио. Откройте FM Диагностику.");AppLog.add(this,"START_ERROR",e.toString());}
 }
 protected void onResume(){super.onResume();handler.post(refresh);}
 protected void onPause(){handler.removeCallbacks(refresh);super.onPause();}
}
