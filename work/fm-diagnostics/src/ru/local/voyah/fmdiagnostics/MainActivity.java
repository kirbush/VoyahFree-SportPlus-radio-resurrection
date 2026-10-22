package ru.local.voyah.fmdiagnostics;
import android.app.*;
import android.content.*;
import android.os.*;
import android.net.Uri;
import android.graphics.Color;
import android.widget.*;
import java.io.*;
import java.util.zip.ZipFile;
public class MainActivity extends Activity {
 static final String CORE="ru.local.voyah.fmloader";
 TextView status; EditText notes; Button saveButton;
 Messenger api; boolean bound; volatile boolean busy,destroyed; int sequence,pending;
 volatile File report;
 final Handler handler=new Handler(Looper.getMainLooper());
 final Messenger replies=new Messenger(new Handler(Looper.getMainLooper()){
  public void handleMessage(Message reply){
   if(destroyed||reply.arg1!=pending)return;
   handler.removeCallbacks(timeout);Bundle data=reply.getData();
   if(data.containsKey("error")){busy=false;show("Не удалось собрать отчёт: "+data.getString("error"));return;}
   if(reply.what==1){show(data.getString("status",""));return;}
   String name=data.getString("report");
   if(name==null||!name.matches("Voyah-FM-report-[0-9]{8}-[0-9]{6}\\.zip")){busy=false;show("Получено неверное имя отчёта.");return;}
   copyReport(name);
  }
 });
 final Runnable timeout=()->{busy=false;pending=++sequence;show("Нет ответа от FM Радио. Повторите сохранение отчёта. Радио продолжает работать независимо от диагностики.");};
 final ServiceConnection connection=new ServiceConnection(){
  public void onServiceConnected(ComponentName n,IBinder binder){api=new Messenger(binder);request(1);}
  public void onServiceDisconnected(ComponentName n){api=null;busy=false;handler.removeCallbacks(timeout);pending=++sequence;show("Связь с FM Радио прервалась. Закройте и снова откройте диагностику.");}
 };
 protected void onCreate(Bundle state){super.onCreate(state);
  LinearLayout layout=new LinearLayout(this);layout.setOrientation(1);layout.setPadding(36,24,36,24);layout.setBackgroundColor(Color.rgb(18,23,30));
  ScrollView scroll=new ScrollView(this);scroll.addView(layout);setContentView(scroll);
  TextView title=new TextView(this);title.setText("FM Диагностика · 0.4.3 beta");title.setTextSize(26);title.setTextColor(Color.WHITE);layout.addView(title);
  TextView help=new TextView(this);help.setText("Журнал записывается автоматически, пока работает FM Радио, и после перезагрузки. При проблеме нажмите «Сохранить отчёт». Запись продолжится.\nСтарые записи заменяются по кругу, чтобы не занимать память.");help.setTextSize(18);help.setTextColor(Color.LTGRAY);layout.addView(help);
  notes=new EditText(this);notes.setTextColor(Color.WHITE);notes.setHintTextColor(Color.LTGRAY);notes.setHint("Что случилось? Частота, время сбоя (необязательно)");notes.setSingleLine(false);layout.addView(notes);
  if(state!=null)notes.setText(state.getString("notes",""));
  saveButton=new Button(this);saveButton.setText("Сохранить отчёт ZIP");saveButton.setOnClickListener(v->{if(busy){Toast.makeText(this,"Отчёт ещё готовится…",Toast.LENGTH_SHORT).show();return;}request(2);});layout.addView(saveButton);
  Button last=new Button(this);last.setText("Повторно сохранить готовый ZIP");last.setOnClickListener(v->{if(!busy)request(3);});layout.addView(last);
  Button refresh=new Button(this);refresh.setText("Обновить состояние");refresh.setOnClickListener(v->{if(!busy)request(1);});layout.addView(refresh);
  Button radio=new Button(this);radio.setText("Открыть FM Радио");radio.setOnClickListener(v->{try{startActivity(new Intent().setClassName(CORE,CORE+".MainActivity"));}catch(Exception e){show("FM Радио не установлено. Запустите общий установщик на ПК.");}});layout.addView(radio);
  status=new TextView(this);status.setTextSize(17);status.setTextColor(Color.LTGRAY);status.setTextIsSelectable(true);layout.addView(status);show("Подключение к FM Радио…");
  String name=getPreferences(0).getString("report",null);
  if(name!=null&&name.matches("Voyah-FM-report-[0-9]{8}-[0-9]{6}\\.zip")){File f=new File(getFilesDir(),name);if(f.isFile())report=f;}
  try{bound=bindService(new Intent().setClassName(CORE,CORE+".DiagnosticApiService"),connection,BIND_AUTO_CREATE);if(!bound)show("FM Радио недоступно. Запустите общий установщик на ПК.");}
  catch(Exception e){show("Не удалось подключиться: "+e);}
 }
 void show(String text){if(destroyed)return;runOnUiThread(()->{if(!destroyed)status.setText(text);});}
 void request(int action){
  if(api==null){show("Нет связи с FM Радио. Откройте его, затем снова диагностику.");return;}
  pending=++sequence;Message request=Message.obtain(null,action);request.arg1=pending;request.replyTo=replies;
  Bundle data=new Bundle();data.putString("notes",notes.getText().toString());request.setData(data);
  try{api.send(request);handler.removeCallbacks(timeout);handler.postDelayed(timeout,180000);if(action!=1){busy=true;show(action==2?"Собираю отчёт… Это может занять до двух минут.":"Открываю последний готовый ZIP…");}}
  catch(Exception e){busy=false;show("Связь с FM Радио недоступна: "+e);}
 }
 void copyReport(String name){new Thread(()->{
  File temp=new File(getFilesDir(),name+".partial");
  try{
   Uri source=Uri.parse("content://ru.local.voyah.fmloader.reports/"+name);
   try(InputStream in=getContentResolver().openInputStream(source);OutputStream out=new FileOutputStream(temp)){
    if(in==null)throw new IOException("Отчёт недоступен");copy(in,out);
   }
   try(ZipFile zip=new ZipFile(temp)){if(zip.getEntry("diagnostics.txt")==null)throw new IOException("Неполный отчёт");}
   File target=new File(getFilesDir(),name);if(!temp.renameTo(target))throw new IOException("Не удалось сохранить копию отчёта");
   report=target;getPreferences(0).edit().putString("report",name).apply();
   runOnUiThread(()->{if(destroyed)return;try{
    Intent intent=new Intent(Intent.ACTION_CREATE_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE).setType("application/zip").putExtra(Intent.EXTRA_TITLE,name);
    startActivityForResult(intent,42);busy=false;show("ZIP готов. Выберите папку. Запись логов продолжается.");
   }catch(ActivityNotFoundException e){saveDownloads();}catch(Exception e){busy=false;show("ZIP готов. Можно забрать его утилитой PC-Export на ПК. "+e);}});
  }catch(Exception e){temp.delete();busy=false;show("Не удалось получить ZIP: "+e+"\nКопия в FM Радио доступна утилите PC-Export на ПК.");}
 }).start();}
 static void copy(InputStream in,OutputStream out)throws IOException{byte[] buffer=new byte[32768];int n;while((n=in.read(buffer))!=-1)out.write(buffer,0,n);}
 void saveDownloads(){if(report==null)return;File source=report;busy=true;new Thread(()->{Uri uri=null;try{
  if(Build.VERSION.SDK_INT<29)throw new IOException("Нет системного выбора папки. Заберите ZIP утилитой PC-Export на ПК.");
  ContentValues values=new ContentValues();values.put(android.provider.MediaStore.MediaColumns.DISPLAY_NAME,source.getName());values.put(android.provider.MediaStore.MediaColumns.MIME_TYPE,"application/zip");values.put(android.provider.MediaStore.MediaColumns.RELATIVE_PATH,"Download/");values.put(android.provider.MediaStore.MediaColumns.IS_PENDING,1);
  uri=getContentResolver().insert(android.provider.MediaStore.Downloads.EXTERNAL_CONTENT_URI,values);if(uri==null)throw new IOException("Downloads недоступна");
  try(InputStream in=new FileInputStream(source);OutputStream out=getContentResolver().openOutputStream(uri)){if(out==null)throw new IOException("Нет доступа для записи");copy(in,out);}
  values.clear();values.put(android.provider.MediaStore.MediaColumns.IS_PENDING,0);getContentResolver().update(uri,values,null,null);show("Отчёт сохранён в Downloads: "+source.getName()+"\nЗапись логов продолжается.");
 }catch(Exception e){if(uri!=null)try{getContentResolver().delete(uri,null,null);}catch(Exception ignored){}show("Внутренний ZIP готов. Заберите его утилитой PC-Export на ПК. "+e);}finally{busy=false;}}).start();}
 protected void onActivityResult(int request,int result,Intent data){super.onActivityResult(request,result,data);if(request!=42)return;
  if(result!=RESULT_OK||data==null||data.getData()==null){show("ZIP готов. Можно сохранить его повторно или забрать через PC-Export на ПК.");return;}
  if(report==null){show("Соберите отчёт ещё раз.");return;}File source=report;Uri uri=data.getData();busy=true;
  new Thread(()->{try(InputStream in=new FileInputStream(source);OutputStream out=getContentResolver().openOutputStream(uri)){if(out==null)throw new IOException("Нет доступа для записи");copy(in,out);show("Отчёт сохранён: "+source.getName()+"\nОтправьте ZIP для разбора. Запись логов продолжается.");}catch(Exception e){show("Не удалось записать ZIP: "+e+"\nВнутренняя копия доступна через PC-Export на ПК.");}finally{busy=false;}}).start();
 }
 protected void onSaveInstanceState(Bundle state){state.putString("notes",notes.getText().toString());super.onSaveInstanceState(state);}
 protected void onDestroy(){destroyed=true;handler.removeCallbacksAndMessages(null);if(bound)unbindService(connection);super.onDestroy();}
}
