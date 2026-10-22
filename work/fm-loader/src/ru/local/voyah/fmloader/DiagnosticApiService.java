package ru.local.voyah.fmloader;
import android.app.Service;
import android.content.*;
import android.os.*;
import java.io.File;
import java.util.concurrent.*;
/** Signature protected, fixed read-only API; no radio lifecycle commands. */
public class DiagnosticApiService extends Service {
 final ExecutorService worker=Executors.newSingleThreadExecutor();
 final Messenger api=new Messenger(new Handler(Looper.getMainLooper()){
  public void handleMessage(Message request){
   if(request.replyTo==null)return;
   final int action=request.what,id=request.arg1;final Messenger reply=request.replyTo;
   final String notes=request.getData().getString("notes","");
   if(worker.isShutdown())return;
   worker.execute(()->{Bundle data=new Bundle();
    try{
     if(action==1){data.putString("status",getSharedPreferences("fm",0).getString("status","Радио ещё не подключалось.")+"\nАвтоматический журнал проверяется каждые 30 сек.");}
     else if(action==2){File report=DiagnosticReport.create(DiagnosticApiService.this,notes.length()>4000?notes.substring(0,4000):notes);
      getSharedPreferences("fm",0).edit().putString("pending_report",report.getName()).apply();
      data.putString("report",report.getName());data.putString("status","Отчёт готов. Запись логов продолжается.");}
     else if(action==3){String last=getSharedPreferences("fm",0).getString("pending_report",null);File report=ReportFiles.resolve(getFilesDir(),last);data.putString("report",report.getName());}
     else throw new IllegalArgumentException("Unsupported diagnostic operation");
    }catch(Exception e){AppLog.add(DiagnosticApiService.this,"DIAGNOSTICS_ERROR",e.toString());data.putString("error",e.toString());}
    Message result=Message.obtain(null,action);result.arg1=id;result.setData(data);try{reply.send(result);}catch(RemoteException ignored){}
   });
  }
 });
 public IBinder onBind(Intent i){return api.getBinder();}
 public void onDestroy(){worker.shutdown();super.onDestroy();}
}
