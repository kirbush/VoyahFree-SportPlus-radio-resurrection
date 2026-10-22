package ru.local.voyah.fmloader;

import java.io.*;
import java.net.*;
import java.nio.file.*;
import java.security.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.zip.*;
import javax.net.ssl.*;
import com.sun.net.httpserver.*;
import org.json.*;
import android.content.*;

public final class TestAndroidUpload {
 static final String TOKEN="test_token_abcdefghijklmnopqrstuvwxyz0123456789";
 static final String DIGEST="ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad";
 static volatile String mode="valid";
 static volatile int calls, redirects;
 static volatile String auth, source, name, method, path, contentType, contentLength;
 static volatile byte[] body;
 static CountDownLatch requestEntered,requestRelease;
 static HttpsServer server;
 static File base;
 static String endpoint;
 static void check(boolean ok,String why){if(!ok)throw new AssertionError(why);}
 static void write(File f,String data)throws Exception{f.getParentFile().mkdirs();Files.write(f.toPath(),data.getBytes("UTF-8"));}
 static File report(File dir,int id)throws Exception{File f=new File(dir,String.format(Locale.US,"Voyah-FM-report-20261022-%06d.zip",id));write(f,"abc");return f;}
 static UploadQueue.Config config(String url)throws Exception{return UploadQueue.Config.parse("{\"endpoint\":\""+url+"\",\"client\":\"tester\",\"token\":\""+TOKEN+"\"}");}
 static void reject(String json)throws Exception{try{UploadQueue.Config.parse(json);throw new AssertionError("Bad config accepted");}catch(IOException expected){}}
 static void receive(HttpExchange exchange)throws IOException{
  calls++;method=exchange.getRequestMethod();auth=exchange.getRequestHeaders().getFirst("Authorization");source=exchange.getRequestHeaders().getFirst("X-FM-Source");name=exchange.getRequestHeaders().getFirst("X-FM-Report-Name");path=exchange.getRequestURI().getPath();contentType=exchange.getRequestHeaders().getFirst("Content-Type");contentLength=exchange.getRequestHeaders().getFirst("Content-Length");
  ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] b=new byte[1024];int n;while((n=exchange.getRequestBody().read(b))!=-1)out.write(b,0,n);body=out.toByteArray();
  String hash=exchange.getRequestURI().getPath().substring(exchange.getRequestURI().getPath().lastIndexOf('/')+1);
  String result="{\"ok\":true,\"id\":\"tester/"+hash+"\",\"sha256\":\""+hash+"\",\"bytes\":"+body.length+"}";
  int code=201;
  if(mode.equals("offline")){code=503;result="{}";}
  if(mode.equals("redirect")){code=307;exchange.getResponseHeaders().set("Location",endpoint+"/redirect");}
  if(mode.equals("wrong-id"))result=result.replace("tester/","other/");
  if(mode.equals("wrong-hash"))result=result.replace("\"sha256\":\""+hash,"\"sha256\":\""+(hash.charAt(0)=='0'?'1':'0')+hash.substring(1));
  if(mode.equals("wrong-size"))result=result.replace("\"bytes\":"+body.length,"\"bytes\":"+(body.length+1));
  if(mode.equals("string-size"))result=result.replace("\"bytes\":"+body.length,"\"bytes\":\""+body.length+"\"");
  if(mode.equals("string-ok"))result=result.replace("true","\"true\"");
  if(mode.equals("junk"))result+="extra";
  if(mode.equals("large")){char[] huge=new char[8193];Arrays.fill(huge,'x');result=new String(huge);}
  if(mode.equals("blocked")){requestEntered.countDown();try{requestRelease.await(5,TimeUnit.SECONDS);}catch(InterruptedException e){Thread.currentThread().interrupt();}}
  byte[] bytes=result.getBytes("UTF-8");exchange.sendResponseHeaders(code,bytes.length);exchange.getResponseBody().write(bytes);exchange.close();
 }
 public static void main(String[] args)throws Exception{
  base=new File(args[0]);base.mkdirs();System.setProperty("fm.test.context",new File(base,"service").getPath());KeyStore keys=KeyStore.getInstance("PKCS12");try(InputStream in=new FileInputStream(args[1])){keys.load(in,"test-only-password".toCharArray());}
  KeyManagerFactory km=KeyManagerFactory.getInstance(KeyManagerFactory.getDefaultAlgorithm());km.init(keys,"test-only-password".toCharArray());SSLContext ssl=SSLContext.getInstance("TLS");ssl.init(km.getKeyManagers(),null,null);
  server=HttpsServer.create(new InetSocketAddress(InetAddress.getLoopbackAddress(),0),0);server.setHttpsConfigurator(new HttpsConfigurator(ssl));server.createContext("/voyah-fm/v1/reports/",TestAndroidUpload::receive);server.createContext("/voyah-fm/v1/redirect",e->{redirects++;e.sendResponseHeaders(500,-1);e.close();});server.start();endpoint="https://localhost:"+server.getAddress().getPort()+"/voyah-fm/v1";
  try{queue();untrusted(args[2]);healthGate();coordinator();automaticRetention();System.out.println("PASS Android HTTPS protocol, strict receipts, offline retry, persistence, bounds, coordinator and ordered menu commands, bounded automatic sources");}finally{ReportCoordinator.shutdown();server.stop(0);}
 }
 static void queue()throws Exception{
  reject("{\"endpoint\":\"http://localhost/voyah-fm/v1\",\"client\":\"tester\",\"token\":\""+TOKEN+"\"}");
  reject("{\"endpoint\":\""+endpoint+"\",\"client\":true,\"token\":\""+TOKEN+"\"}");
  for(String suffix:new String[]{"?query=1","#fragment","/extra","/"}){try{config(endpoint+suffix);throw new AssertionError("Endpoint accepted "+suffix);}catch(IOException expected){}}
  File dir=new File(base,"queue");UploadQueue q=new UploadQueue(dir,config(endpoint));File original=report(new File(base,"reports"),1);
  check(q.enqueue(original),"Initial enqueue");check(q.enqueue(original),"Duplicate admission");check(q.pending()==1,"Duplicate queue entry");
  mode="valid";check(q.flush()==1,"Valid acknowledgement not accepted");check(q.pending()==0&&original.isFile(),"Original ZIP lost or pending retained");check("PUT".equals(method)&&("Bearer "+TOKEN).equals(auth)&&"headunit".equals(source)&&original.getName().equals(name),"Wrong wire protocol");check(path.equals("/voyah-fm/v1/reports/"+DIGEST)&&"application/zip".equals(contentType)&&"3".equals(contentLength),"Wrong SHA256, type or fixed byte length");check(Arrays.equals(body,new byte[]{97,98,99}),"Wrong transmitted ZIP bytes");check(q.enqueue(original)&&q.pending()==0,"Acknowledged ZIP sent again");
  for(String bad:new String[]{"offline","redirect","wrong-id","wrong-hash","wrong-size","string-size","string-ok","junk","large"}){
   File f=report(new File(base,bad),2);write(f,"abc"+bad);UploadQueue item=new UploadQueue(new File(base,"queue-"+bad),config(endpoint));item.enqueue(f);mode=bad;
   check(item.flush()==0&&item.pending()==1,"Bad receipt removed queued ZIP: "+bad);check(!item.lastError().contains(TOKEN)&&!item.lastError().contains(endpoint),"Secrets in error");
   mode="valid";UploadQueue reopened=new UploadQueue(new File(base,"queue-"+bad),config(endpoint));check(reopened.flush()==1&&reopened.pending()==0,"Restart retry failed "+bad);
  }
  check(redirects==0,"Redirect followed");
  UploadQueue wrongHost=new UploadQueue(new File(base,"wrong-host"),config(endpoint.replace("localhost","127.0.0.1")));wrongHost.enqueue(original);check(wrongHost.flush()==0&&wrongHost.pending()==1,"TLS hostname verification bypassed");
  UploadQueue corrupt=new UploadQueue(new File(base,"corrupt"),config(endpoint));corrupt.enqueue(original);for(File f:corrupt.list())if(f.getName().endsWith(".zip"))write(f,"changed");int previousCalls=calls;check(corrupt.flush()==0&&corrupt.pending()==1&&calls==previousCalls&&original.isFile(),"Corrupted queue ZIP transmitted or original removed");
  UploadQueue bounded=new UploadQueue(new File(base,"bounded"),config(endpoint));for(int i=0;i<32;i++){File f=report(new File(base,"bound-reports"),i);write(f,"unique"+i);check(bounded.enqueue(f),"Premature queue limit");}File excess=report(new File(base,"bound-reports"),33);write(excess,"excess");check(!bounded.enqueue(excess)&&bounded.pending()==32&&excess.isFile(),"Queue count bound or original retention broken");mode="valid";check(bounded.flush()==5&&bounded.pending()==27,"Retry batch not bounded");check(bounded.enqueue(excess),"Full queue cannot admit after drain");
  UploadQueue big=new UploadQueue(new File(base,"big"),config(endpoint));File large=report(new File(base,"large-report"),34);try(RandomAccessFile f=new RandomAccessFile(large,"rw")){f.setLength(16L*1024*1024+1);}check(!big.enqueue(large)&&big.pending()==0&&large.isFile(),"Oversize ZIP admitted or deleted");
  UploadQueue separate=new UploadQueue(dir,config(endpoint.replace("localhost","LOCALHOST")));check(separate.pending()==0,"Configurations share private queue");
  UploadQueue bytesBound=new UploadQueue(new File(base,"byte-bound"),config(endpoint));for(int i=0;i<4;i++){File f=report(new File(base,"byte-reports"),i);try(RandomAccessFile out=new RandomAccessFile(f,"rw")){out.setLength(16L*1024*1024);out.seek(0);out.writeInt(i);}check(bytesBound.enqueue(f),"64MiB boundary rejected");}File one=report(new File(base,"byte-reports"),5);check(!bytesBound.enqueue(one)&&bytesBound.pending()==4,"Queue byte limit ignored");
  UploadQueue receipts=new UploadQueue(new File(base,"receipt-bound"),config(endpoint));for(int i=0;i<128;i++){String hash=String.format(Locale.US,"%064x",i);write(receipts.file(hash,".receipt.json"),"{\"ok\":true,\"id\":\"tester/"+hash+"\",\"sha256\":\""+hash+"\",\"bytes\":3}");}for(int i=0;i<2;i++){File f=report(new File(base,"receipt-reports"),i);write(f,"receipt"+i);receipts.enqueue(f);}check(receipts.flush()==2,"Restored receipt queue cannot flush");int count=0;for(File f:receipts.list())if(f.getName().endsWith(".receipt.json"))count++;check(count==128,"Receipt retention unbounded");
 }
 static void untrusted(String store)throws Exception{
  KeyStore keys=KeyStore.getInstance("PKCS12");try(InputStream in=new FileInputStream(store)){keys.load(in,"test-only-password".toCharArray());}KeyManagerFactory km=KeyManagerFactory.getInstance(KeyManagerFactory.getDefaultAlgorithm());km.init(keys,"test-only-password".toCharArray());SSLContext ssl=SSLContext.getInstance("TLS");ssl.init(km.getKeyManagers(),null,null);
  HttpsServer unknown=HttpsServer.create(new InetSocketAddress(InetAddress.getLoopbackAddress(),0),0);unknown.setHttpsConfigurator(new HttpsConfigurator(ssl));unknown.createContext("/voyah-fm/v1/reports/",TestAndroidUpload::receive);unknown.start();
  try{UploadQueue q=new UploadQueue(new File(base,"untrusted"),config("https://localhost:"+unknown.getAddress().getPort()+"/voyah-fm/v1"));q.enqueue(report(new File(base,"untrusted-report"),1));int previousCalls=calls;check(q.flush()==0&&q.pending()==1&&calls==previousCalls,"Untrusted TLS certificate accepted");}finally{unknown.stop(0);}
 }
 static void healthGate()throws Exception{
  CountDownLatch entered=new CountDownLatch(1),release=new CountDownLatch(1);ExecutorService executor=Executors.newSingleThreadExecutor();
  Future<?> owner=executor.submit(()->{check(ReportCoordinator.tryHealthCheck(),"Cannot acquire idle health gate");entered.countDown();try{release.await(5,TimeUnit.SECONDS);}catch(InterruptedException ignored){}finally{ReportCoordinator.endHealthCheck();}});
  Context context=new Context(new File(base,"gate-context"));LoaderService service=new LoaderService();
  try{
   check(entered.await(3,TimeUnit.SECONDS),"Health gate owner not started");int count=RuntimeFiles.actions.size();long start=System.nanoTime();service.tick();check(System.nanoTime()-start<500000000L&&RuntimeFiles.actions.size()==count,"Health tick failed to skip busy gate when capture flag was not visible");
   ReportCoordinator.command(context,"save");long until=System.currentTimeMillis()+3000;while(!ReportCoordinator.isCapturing()&&System.currentTimeMillis()<until)Thread.sleep(10);check(ReportCoordinator.isCapturing(),"Capture not waiting for health gate");Thread.sleep(50);check(RuntimeFiles.actions.size()==count,"Capture raced existing health owner");
   release.countDown();owner.get(3,TimeUnit.SECONDS);idle(context);check(context.downloads.size()==1,"Capture did not continue after health finished");
  }finally{release.countDown();executor.shutdownNow();service.onDestroy();RuntimeFiles.actions.clear();}
 }
 static void coordinator()throws Exception{
  Context c=new Context(new File(base,"context"));int before=calls;ReportCoordinator.start(c);Thread.sleep(150);JSONObject s=ReportCoordinator.command(c,"status");
  check(!s.getBoolean("configured")&&s.getBoolean("auto")&&!s.getBoolean("busy"),"Initial menu status");check(calls==before&&RuntimeFiles.actions.isEmpty(),"Startup captured or uploaded immediately");
  ReportCoordinator.command(c,"auto_off");check(!ReportCoordinator.command(c,"status").getBoolean("auto"),"Auto-off not saved");ReportCoordinator.shutdown();ReportCoordinator.start(c);check(!ReportCoordinator.command(c,"status").getBoolean("auto"),"Auto preference lost on restart");
  RuntimeFiles.block=new CountDownLatch(1);long start=System.nanoTime();JSONObject queued=ReportCoordinator.command(c,"save");check((System.nanoTime()-start)<500000000L&&queued.getBoolean("busy"),"Receiver blocks on capture");
  long until=System.currentTimeMillis()+3000;while(!ReportCoordinator.isCapturing()&&System.currentTimeMillis()<until)Thread.sleep(10);check(ReportCoordinator.isCapturing(),"Capture flag absent");check("BUSY".equals(ReportCoordinator.command(c,"send").getString("status")),"Duplicate capture allowed");
  LoaderService service=new LoaderService();int actionCount=RuntimeFiles.actions.size();service.tick();check(RuntimeFiles.actions.size()==actionCount,"Health tick ran during diagnostic capture");
  RuntimeFiles.block.countDown();idle(c);check(c.downloads.size()==1,"Manual save not copied to Downloads");check(c.startedActivities==0&&calls==before,"Save opened Activity or uploaded");
  JSONObject saved=ReportCoordinator.command(c,"status");check(!saved.getString("lastReport").isEmpty()&&"SAVED".equals(saved.getString("status")),"Save result missing");
  try(ZipFile z=new ZipFile(new File(c.getFilesDir(),saved.getString("lastReport")))){String diagnostic=read(z,"diagnostics.txt"),env=read(z,"environment.txt");check(diagnostic.contains("CRASH_TEXT_SENTINEL")&&env.contains("0.5.0-beta"),"Crash evidence or current version absent");}
  write(new File(c.getFilesDir(),"upload.json"),"{\"endpoint\":\""+endpoint+"\",\"client\":\"tester\",\"token\":\""+TOKEN+"\"}");mode="offline";ReportCoordinator.command(c,"send");idle(c);check("QUEUED".equals(ReportCoordinator.command(c,"status").getString("status")),"Offline report not queued");
  mode="valid";ReportCoordinator.command(c,"send");idle(c);s=ReportCoordinator.command(c,"status");check("SENT".equals(s.getString("status"))&&s.getBoolean("configured"),"Send did not retry and acknowledge");
  for(String action:RuntimeFiles.actions)check(action.equals("diagnostic"),"Hardware action from report subsystem: "+action);
  requestEntered=new CountDownLatch(1);requestRelease=new CountDownLatch(1);mode="blocked";ReportCoordinator.command(c,"send");check(requestEntered.await(5,TimeUnit.SECONDS),"Upload not running");check(!ReportCoordinator.isCapturing(),"Network incorrectly blocks health as capture");actionCount=RuntimeFiles.actions.size();start=System.nanoTime();service.tick();check(System.nanoTime()-start<500000000L&&RuntimeFiles.actions.size()==actionCount+2,"Network blocked FM health tick");requestRelease.countDown();idle(c);
  MenuActionReceiver receiver=new MenuActionReceiver();receiver.onReceive(c,new Intent("ru.local.voyah.fmloader.REPORT_MENU").putExtra("operation","status"));check(receiver.resultData!=null&&new JSONObject(receiver.resultData).getBoolean("configured"),"Ordered JSON reply missing");check(!receiver.resultData.contains(TOKEN),"Token exposed by menu");
  check("INVALID_OPERATION".equals(ReportCoordinator.command(c,"play").getString("status")),"Unknown operation accepted");
  service.onDestroy();check(!ReportCoordinator.isCapturing(),"Service shutdown left capture active");
  Context installed=new Context(new File(base,"installed"));write(new File(installed.getFilesDir(),"upload.json"),"{\"endpoint\":\""+endpoint+"\",\"client\":\"tester\",\"token\":\""+TOKEN+"\"}");before=calls;actionCount=RuntimeFiles.actions.size();ReportCoordinator.start(installed);ReportCoordinator.command(installed,"auto_on");Thread.sleep(150);check(calls==before&&RuntimeFiles.actions.size()==actionCount,"Configured install or auto-on uploads immediately");
 }
 static void idle(Context c)throws Exception{long until=System.currentTimeMillis()+15000;while(ReportCoordinator.command(c,"status").getBoolean("busy")&&System.currentTimeMillis()<until)Thread.sleep(20);check(!ReportCoordinator.command(c,"status").getBoolean("busy"),"Report task did not finish");}
 static void periodic(Context c)throws Exception{java.lang.reflect.Field f=ReportCoordinator.class.getDeclaredField("instance");f.setAccessible(true);Object instance=f.get(null);java.lang.reflect.Method tick=ReportCoordinator.class.getDeclaredMethod("automatic");tick.setAccessible(true);tick.invoke(instance);idle(c);}
 static int sourceReports(Context c){int count=0;for(File f:c.getFilesDir().listFiles())if(f.getName().matches(UploadQueue.REPORT))count++;return count;}
 static void automaticRetention()throws Exception{
  ReportCoordinator.shutdown();RuntimeFiles.actions.clear();Context c=new Context(new File(base,"auto-retention"));write(new File(c.getFilesDir(),"upload.json"),"{\"endpoint\":\""+endpoint+"\",\"client\":\"tester\",\"token\":\""+TOKEN+"\"}");ReportCoordinator.start(c);mode="valid";
  ReportCoordinator.command(c,"save");idle(c);File saved=new File(c.getFilesDir(),ReportCoordinator.command(c,"status").getString("lastReport"));byte[] savedBytes=Files.readAllBytes(saved.toPath());
  ReportCoordinator.command(c,"send");idle(c);File sent=new File(c.getFilesDir(),ReportCoordinator.command(c,"status").getString("lastReport"));byte[] sentBytes=Files.readAllBytes(sent.toPath());File old=report(c.getFilesDir(),123);write(old,"legacy report preserved");byte[] oldBytes=Files.readAllBytes(old.toPath());String manualPending=c.getSharedPreferences("fm",0).getString("pending_report","");
  mode="offline";int captures=RuntimeFiles.actions.size();for(int i=0;i<40;i++){periodic(c);check(sourceReports(c)==3,"Automatic source reports grow while offline");check(c.getSharedPreferences("fm",0).getString("pending_report","").equals(manualPending),"Deleted automatic source replaced legacy manual pending report");}
  UploadQueue q=new UploadQueue(new File(c.getFilesDir(),"upload-queue"),config(endpoint));check(q.pending()==32&&RuntimeFiles.actions.size()-captures==32,"Full queue did not pause new automatic captures");
  ReportCoordinator.shutdown();ReportCoordinator.start(c);captures=RuntimeFiles.actions.size();periodic(c);check(RuntimeFiles.actions.size()==captures&&sourceReports(c)==3,"Restart bypassed full queue capture limit");
  File unbacked=report(c.getFilesDir(),124);write(unbacked,"unbacked automatic report");File marker=new File(c.getFilesDir(),"automatic-report-source");write(marker,unbacked.getName());periodic(c);check(unbacked.isFile()&&marker.isFile()&&RuntimeFiles.actions.size()==captures,"Unbacked automatic report deleted or another capture started");
  mode="valid";for(int i=0;i<40;i++){periodic(c);check(sourceReports(c)<=4,"Sent automatic sources accumulate");}check(!unbacked.exists()&&!marker.exists()&&q.pending()==0,"Restored automatic source did not recover after network returned");
  check(Arrays.equals(savedBytes,Files.readAllBytes(saved.toPath()))&&Arrays.equals(sentBytes,Files.readAllBytes(sent.toPath()))&&Arrays.equals(oldBytes,Files.readAllBytes(old.toPath())),"Automatic cleanup changed manual or existing reports");
  File corrupt=report(c.getFilesDir(),125);write(corrupt,"automatic source needing valid backup");q.enqueue(corrupt);File copy=q.file(UploadQueue.hash(corrupt),".zip");write(copy,"corrupt copy");write(marker,corrupt.getName());captures=RuntimeFiles.actions.size();periodic(c);check(corrupt.isFile()&&marker.isFile()&&RuntimeFiles.actions.size()==captures,"Automatic source removed despite corrupt backup");Files.write(copy.toPath(),Files.readAllBytes(corrupt.toPath()));periodic(c);check(!corrupt.exists()&&!marker.exists(),"Verified queue backup did not release tracked source");
  File received=report(c.getFilesDir(),126);write(received,"automatic source with durable server receipt");q.enqueue(received);check(q.flush()==1,"Receipt recovery setup failed");String receiptHash=UploadQueue.hash(received);write(marker,received.getName());periodic(c);check(!received.exists()&&q.file(receiptHash,".receipt.json").isFile(),"Valid server receipt did not release automatic source");
  for(int i=0;i<4;i++){File entry=new File(c.getFilesDir(),"sparse-queue-entry");try(RandomAccessFile out=new RandomAccessFile(entry,"rw")){out.setLength(16L*1024*1024);out.seek(0);out.writeInt(i);}String hash=UploadQueue.hash(entry);Files.move(entry.toPath(),q.file(hash,".zip").toPath());write(q.file(hash,".name"),String.format(Locale.US,"Voyah-FM-report-20261022-%06d.zip",200+i));}
  mode="offline";captures=RuntimeFiles.actions.size();periodic(c);check(RuntimeFiles.actions.size()==captures&&sourceReports(c)==3&&q.pending()==4,"Byte-full queue admitted another automatic capture");for(File f:q.pendingFiles()){q.file(f.getName().substring(0,64),".name").delete();f.delete();}mode="valid";
  ReportCoordinator.command(c,"auto_off");int previousCalls=calls;captures=RuntimeFiles.actions.size();for(int i=0;i<5;i++)periodic(c);check(calls==previousCalls&&RuntimeFiles.actions.size()==captures,"Auto-off did not stop periodic work");ReportCoordinator.command(c,"auto_on");check(calls==previousCalls&&RuntimeFiles.actions.size()==captures,"Enabling auto started immediate upload");
  ReportCoordinator.shutdown();Context huge=new Context(new File(base,"auto-source-limit"));byte[] noise=new byte[8192];Random random=new Random(1);try(OutputStream out=new FileOutputStream(new File(huge.getFilesDir(),"events.log"))){for(int i=0;i<2176;i++){random.nextBytes(noise);out.write(noise);}}
  try{DiagnosticReport.createAutomatic(huge,"oversize automatic report");throw new AssertionError("Oversize automatic source accepted");}catch(IOException expected){}
  check(sourceReports(huge)==0&&new File(huge.getFilesDir(),"automatic-report-source").isFile(),"Oversize automatic source escaped tracking or size bound");for(File f:huge.getFilesDir().listFiles())check(!f.getName().endsWith(".partial"),"Oversize automatic partial retained");
 }
 static String read(ZipFile z,String name)throws Exception{try(InputStream in=z.getInputStream(z.getEntry(name));ByteArrayOutputStream out=new ByteArrayOutputStream()){byte[] b=new byte[1024];int n;while((n=in.read(b))!=-1)out.write(b,0,n);return out.toString("UTF-8");}}
}
