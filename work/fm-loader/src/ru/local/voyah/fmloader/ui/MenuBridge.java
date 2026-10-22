package ru.local.voyah.fmloader.ui;

import android.app.*;
import android.content.*;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.os.*;
import android.util.Log;
import android.view.*;
import android.widget.*;
import org.json.JSONObject;
import java.lang.ref.WeakReference;
import java.util.WeakHashMap;

/** Native listeners remain valid even if the instrumentation session detaches. */
public final class MenuBridge implements Application.ActivityLifecycleCallbacks {
 private static final String CORE="ru.local.voyah.fmloader";
 private static final String ACTION=CORE+".REPORT_MENU";
 private static final int BUTTON_ID=0x5a0f0001;
 private static boolean installed;
 private static final WeakHashMap<Activity,WeakReference<AlertDialog>> dialogs=new WeakHashMap<>();
 public static boolean isShowing(Activity activity){WeakReference<AlertDialog> ref=dialogs.get(activity);AlertDialog dialog=ref==null?null:ref.get();return dialog!=null&&dialog.isShowing();}
 public static void closeSettings(Activity activity){WeakReference<AlertDialog> ref=dialogs.remove(activity);AlertDialog dialog=ref==null?null:ref.get();if(dialog!=null)try{dialog.dismiss();}catch(Exception ignored){}}
 public static synchronized void install(Application app){
  if(installed)return;
  app.registerActivityLifecycleCallbacks(new MenuBridge());installed=true;
  Log.i("VoyahFMUI","MENU_CALLBACKS_INSTALLED");
 }
 static int dp(Activity a,int value){return Math.round(value*a.getResources().getDisplayMetrics().density);}
 public static void attach(final Activity a){
  if(!a.getClass().getName().equals("com.pateo.rdsapp.main.activity.MainActivity")||a.isFinishing()||a.isDestroyed())return;
  final View root=a.getWindow().getDecorView();
  if(!(root instanceof ViewGroup)||root.findViewById(BUTTON_ID)!=null)return;
  Button button=new Button(a);button.setId(BUTTON_ID);button.setText("\u2699");
  button.setContentDescription("Настройки FM");button.setTextSize(28);button.setTextColor(Color.WHITE);
  button.setAllCaps(false);button.setPadding(0,0,0,0);button.setMinWidth(0);button.setMinimumWidth(0);
  GradientDrawable background=new GradientDrawable();background.setColor(0xDD202A35);background.setCornerRadius(dp(a,14));button.setBackground(background);
  button.setElevation(dp(a,12));button.setOnClickListener(v->showSettings(a));
  FrameLayout.LayoutParams p=new FrameLayout.LayoutParams(dp(a,54),dp(a,54),Gravity.TOP|Gravity.END);
  p.topMargin=dp(a,16);p.rightMargin=dp(a,20);
  ((ViewGroup)root).addView(button,p);button.bringToFront();
  Log.i("VoyahFMUI","MENU_BUTTON_ATTACHED");
 }
 public static void showSettings(final Activity a){
  if(a.isFinishing()||a.isDestroyed()||isShowing(a))return;
  new Settings(a).show();
 }
 private static final class Settings {
  final Activity activity;final Handler handler=new Handler(Looper.getMainLooper());
  final TextView status;final Button send,save;final CheckBox automatic;final AlertDialog dialog;
  boolean updating,closed;int sequence;
  Settings(Activity a){
   activity=a;
   LinearLayout content=new LinearLayout(a);content.setOrientation(LinearLayout.VERTICAL);content.setPadding(dp(a,24),dp(a,8),dp(a,24),dp(a,12));
   TextView description=new TextView(a);description.setText("FM Радио · 0.5.1 beta\nЖурнал записывается автоматически.");description.setTextSize(18);content.addView(description);
   status=new TextView(a);status.setTextSize(17);status.setPadding(0,dp(a,14),0,dp(a,14));status.setText("Проверяю состояние…");content.addView(status);
   send=new Button(a);send.setText("Отправить логи");send.setOnClickListener(v->command("send"));content.addView(send);
   save=new Button(a);save.setText("Сохранить ZIP");save.setOnClickListener(v->command("save"));content.addView(save);
   automatic=new CheckBox(a);automatic.setText("Автоотправка раз в 30 минут");automatic.setTextSize(17);
   automatic.setOnCheckedChangeListener((button,checked)->{if(!updating)command(checked?"auto_on":"auto_off");});content.addView(automatic);
   ScrollView scroll=new ScrollView(a);scroll.addView(content);
   dialog=new AlertDialog.Builder(a).setTitle("Настройки FM").setView(scroll).setNegativeButton("Закрыть",null).create();
   dialog.setOnDismissListener(d->{closed=true;handler.removeCallbacksAndMessages(null);WeakReference<AlertDialog> ref=dialogs.get(activity);if(ref!=null&&ref.get()==dialog)dialogs.remove(activity);});
  }
  void show(){dialog.show();dialogs.put(activity,new WeakReference<>(dialog));command("status");handler.postDelayed(poll,2000);}
  final Runnable poll=new Runnable(){public void run(){if(closed||!dialog.isShowing()||activity.isFinishing()||activity.isDestroyed()){closed=true;handler.removeCallbacksAndMessages(null);return;}command("status");handler.postDelayed(this,2000);}};
  void command(String operation){
   if(closed)return;
   if(!operation.equals("status")){send.setEnabled(false);save.setEnabled(false);status.setText(operation.equals("send")?"Собираю отчёт для отправки…":operation.equals("save")?"Сохраняю ZIP…":"Сохраняю настройку…");}
   final int request=++sequence;
   Intent intent=new Intent(ACTION).setComponent(new ComponentName(CORE,CORE+".MenuActionReceiver")).putExtra("operation",operation);
   try{
    activity.sendOrderedBroadcast(intent,null,new BroadcastReceiver(){public void onReceive(Context context,Intent reply){
     if(closed||activity.isFinishing()||activity.isDestroyed()||request<sequence-2)return;
     try{
      String text=getResultData();if(text==null||text.length()>8192)throw new IllegalStateException("Нет ответа от FM Радио");
      JSONObject data=new JSONObject(text);boolean busy=data.optBoolean("busy",false),configured=data.optBoolean("configured",false);
      status.setText(statusText(data.optString("status","IDLE"),busy)+(configured?"":"\nОбратитесь к разработчику для настройки отправки.")+(data.optInt("pending",0)>0?"\nВ очереди: "+data.optInt("pending",0):""));
      send.setEnabled(!busy&&configured);save.setEnabled(!busy);
      updating=true;automatic.setChecked(data.optBoolean("auto",true));updating=false;
     }catch(Exception e){status.setText("Нет связи с FM Радио. Откройте его через значок приложения.");send.setEnabled(false);save.setEnabled(false);}
    }},handler,Activity.RESULT_OK,null,null);
   }catch(Exception e){status.setText("Не удалось связаться с FM Радио.");Log.w("VoyahFMUI","MENU_IPC_FAILED "+e.getClass().getSimpleName());}
  }
  String statusText(String code,boolean busy){
   if(busy)return "Готовлю отчёт… Журнал продолжает записываться.";
   if("SENT".equals(code))return "Отчёт отправлен на сервер.";
   if("SAVED".equals(code))return "ZIP сохранён в папке Downloads.";
   if("QUEUED".equals(code))return "Отчёт сохранён и ждёт отправки. Проверьте подключение к интернету.";
   if("QUEUE_FULL".equals(code))return "Очередь отчётов заполнена. Сохраните ZIP и сообщите разработчику.";
   if("NOT_CONFIGURED".equals(code))return "Отправка ещё не настроена.";
   if("ERROR".equals(code))return "Не удалось завершить операцию. Повторите попытку.";
   if("BUSY".equals(code))return "Отчёт уже готовится…";
   return "Готово. Отчёт можно отправить по кнопке.";
  }
 }
 public void onActivityResumed(Activity a){attach(a);}
 public void onActivityCreated(Activity a,Bundle b){}
 public void onActivityStarted(Activity a){}
 public void onActivityPaused(Activity a){}
 public void onActivityStopped(Activity a){closeSettings(a);}
 public void onActivitySaveInstanceState(Activity a,Bundle b){}
 public void onActivityDestroyed(Activity a){closeSettings(a);}
}
