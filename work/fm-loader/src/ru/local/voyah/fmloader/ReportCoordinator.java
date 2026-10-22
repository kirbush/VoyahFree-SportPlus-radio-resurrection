package ru.local.voyah.fmloader;

import android.content.*;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.provider.MediaStore;
import java.io.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.locks.ReentrantLock;
import org.json.*;

/** Report work has its own executor and never occupies the FM health executor. */
public final class ReportCoordinator {
 private static volatile ReportCoordinator instance;
 private static final ReentrantLock captureHealthGate=new ReentrantLock();
 private final Context context;
 private final SharedPreferences preferences;
 private final ScheduledExecutorService worker=Executors.newSingleThreadScheduledExecutor(r->new Thread(r,"fm-reports"));
 private final AtomicBoolean busy=new AtomicBoolean();
 private volatile boolean capturing,stopped;
 private volatile int pending;
 private volatile String status,lastReport;
 private ScheduledFuture<?> retry;
 private ReportCoordinator(Context c){
  context=c.getApplicationContext();preferences=context.getSharedPreferences("fm-reports",0);
  status=preferences.getString("upload_status","IDLE");lastReport=preferences.getString("last_report","");
  UploadQueue queue=queue();if(queue!=null)pending=queue.pending();
  worker.scheduleWithFixedDelay(()->automatic(),30,30,TimeUnit.MINUTES);
 }
 public static synchronized void start(Context c){if(instance==null)instance=new ReportCoordinator(c);}
 public static JSONObject command(Context c,String action){
  start(c);ReportCoordinator current=instance;
  if(current==null)return new JSONObject();
  if("status".equals(action))return current.snapshot(null);
  if("auto_on".equals(action)||"auto_off".equals(action)){
   boolean enabled="auto_on".equals(action);current.preferences.edit().putBoolean("auto",enabled).apply();
   if(!enabled)current.cancelRetry();
   AppLog.add(current.context,"REPORT_AUTO",enabled?"enabled; next periodic report at scheduled interval":"disabled");
   return current.snapshot(null);
  }
  if(!"send".equals(action)&&!"save".equals(action))return current.snapshot("INVALID_OPERATION");
  if(current.busy.get())return current.snapshot("BUSY");
  if("send".equals(action)&&current.configuration()==null)return current.snapshot("NOT_CONFIGURED");
  if(!current.submit(action))return current.snapshot("BUSY");
  return current.snapshot(null);
 }
 public static boolean isCapturing(){ReportCoordinator current=instance;return current!=null&&current.capturing;}
 static boolean tryHealthCheck(){return captureHealthGate.tryLock();}
 static void endHealthCheck(){captureHealthGate.unlock();}
 public static synchronized void shutdown(){ReportCoordinator current=instance;instance=null;if(current!=null){current.stopped=true;current.cancelRetry();current.worker.shutdownNow();}}
 private JSONObject snapshot(String override){
  JSONObject out=new JSONObject();try{out.put("status",override==null?status:override);out.put("configured",configuration()!=null);out.put("auto",preferences.getBoolean("auto",true));out.put("busy",busy.get());out.put("version","0.5.0-beta");out.put("lastReport",lastReport);out.put("pending",pending);}catch(JSONException ignored){}return out;
 }
 private UploadQueue.Config configuration(){try{return UploadQueue.Config.read(new File(context.getFilesDir(),"upload.json"));}catch(IOException ignored){return null;}}
 private UploadQueue queue(){UploadQueue.Config config=configuration();if(config==null)return null;try{return new UploadQueue(new File(context.getFilesDir(),"upload-queue"),config);}catch(IOException ignored){return null;}}
 private boolean submit(String operation){
  if(stopped||!busy.compareAndSet(false,true))return false;
  status="QUEUED";
  try{worker.execute(()->perform(operation));return true;}catch(RejectedExecutionException ignored){busy.set(false);return false;}
 }
 private void perform(String operation){
  try{
   if(stopped)return;
   boolean automatic="auto".equals(operation),flushed=false;int sent=0;UploadQueue queue=null;
   if(automatic){
    if(!preferences.getBoolean("auto",true))return;
    queue=queue();if(queue==null){setStatus("NOT_CONFIGURED");return;}
    boolean recovered=recoverAutomatic(queue);
    if(!recovered||!queue.canCaptureAutomatic()){
     sent=queue.flush();flushed=true;recovered=recoverAutomatic(queue);
     if(!recovered||!queue.canCaptureAutomatic()){pending=queue.pending();setStatus("QUEUE_FULL");AppLog.add(context,"REPORT_AUTO_PAUSED","Queue or tracked automatic source requires recovery");if(pending>0)scheduleRetry();return;}
    }
    if(stopped||!preferences.getBoolean("auto",true))return;
   }
   capturing=true;File report;boolean locked=false;
   try{captureHealthGate.lockInterruptibly();locked=true;if(stopped)return;report=automatic?DiagnosticReport.createAutomatic(context,"Report operation="+operation):DiagnosticReport.create(context,"Report operation="+operation);}
   finally{if(locked)captureHealthGate.unlock();capturing=false;}
   lastReport=report.getName();preferences.edit().putString("last_report",lastReport).apply();
   if(!automatic)context.getSharedPreferences("fm",0).edit().putString("pending_report",lastReport).apply();
   if(stopped)return;
   if("save".equals(operation)){saveDownloads(report);setStatus("SAVED");AppLog.add(context,"REPORT_SAVED",lastReport+" copied to Downloads; logging continues");return;}
   if(queue==null)queue=queue();if(queue==null){setStatus("NOT_CONFIGURED");return;}
   boolean admitted=queue.enqueue(report);
   if(automatic&&admitted)recoverAutomatic(queue);
   if(!flushed)sent=queue.flush();
   // A full queue must be allowed to drain before admission of the newest ZIP.
   if(!admitted)admitted=queue.enqueue(report);
   if(automatic&&admitted)recoverAutomatic(queue);
   pending=queue.pending();setStatus(!admitted?"QUEUE_FULL":pending==0?"SENT":"QUEUED");
   AppLog.add(context,"REPORT_UPLOAD",status+" pending="+pending+" sent="+sent+(queue.lastError().isEmpty()?"":" reason="+queue.lastError()));
   if(pending>0)scheduleRetry();
  }catch(Exception failure){setStatus("ERROR");AppLog.add(context,"REPORT_ERROR","Report operation failed; local ZIP retained");}
  finally{capturing=false;busy.set(false);}
 }
 private void automatic(){
  if(stopped||!preferences.getBoolean("auto",true)||configuration()==null)return;
  submit("auto");
 }
 /** At most one marked automatic source exists; manual and pre-existing reports are untouched. */
 private boolean recoverAutomatic(UploadQueue queue)throws IOException {
  File marker=new File(context.getFilesDir(),DiagnosticReport.AUTOMATIC_SOURCE);if(!marker.exists())return true;
  String name=UploadQueue.readBounded(marker,256);if(!name.matches(UploadQueue.REPORT))return false;
  File source=new File(context.getFilesDir(),name);
  if(source.exists()){
   if(!queue.backedUp(source)&&!queue.enqueue(source))return false;
   if(!queue.backedUp(source)||!source.delete())return false;
  }
  File partial=new File(context.getFilesDir(),name+".partial");if(partial.exists()&&!partial.delete())return false;
  return marker.delete();
 }
 private synchronized void scheduleRetry(){
  if(stopped||!preferences.getBoolean("auto",true)||retry!=null&&!retry.isDone())return;
  retry=worker.schedule(()->retryPending(),5,TimeUnit.MINUTES);
 }
 private synchronized void cancelRetry(){if(retry!=null)retry.cancel(false);retry=null;}
 private void retryPending(){
  synchronized(this){retry=null;}
  if(stopped||!preferences.getBoolean("auto",true))return;
  if(!busy.compareAndSet(false,true)){scheduleRetry();return;}
  try{UploadQueue queue=queue();if(queue==null)return;int sent=queue.flush();pending=queue.pending();setStatus(pending==0?"SENT":"QUEUED");AppLog.add(context,"REPORT_RETRY",status+" pending="+pending+" sent="+sent);}
  finally{busy.set(false);if(pending>0)scheduleRetry();}
 }
 private void setStatus(String value){status=value;preferences.edit().putString("upload_status",value).apply();}
 private void saveDownloads(File report)throws IOException {
  if(Build.VERSION.SDK_INT<29)throw new IOException("Downloads requires Android 10");
  ContentResolver resolver=context.getContentResolver();ContentValues values=new ContentValues();
  values.put(MediaStore.MediaColumns.DISPLAY_NAME,report.getName());values.put(MediaStore.MediaColumns.MIME_TYPE,"application/zip");values.put(MediaStore.MediaColumns.RELATIVE_PATH,Environment.DIRECTORY_DOWNLOADS);values.put(MediaStore.MediaColumns.IS_PENDING,1);
  Uri destination=resolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI,values);if(destination==null)throw new IOException("Downloads unavailable");
  boolean done=false;try{
   try(InputStream in=new FileInputStream(report);OutputStream out=resolver.openOutputStream(destination)){if(out==null)throw new IOException("Downloads unavailable");UploadQueue.copy(in,out,UploadQueue.MAX_REPORT);}
   ContentValues complete=new ContentValues();complete.put(MediaStore.MediaColumns.IS_PENDING,0);if(resolver.update(destination,complete,null,null)<1)throw new IOException("Downloads unavailable");done=true;
  }finally{if(!done)resolver.delete(destination,null,null);}
 }
}
