package ru.local.voyah.fmloader;

import java.io.*;
import java.net.*;
import java.security.MessageDigest;
import java.util.*;
import javax.net.ssl.HttpsURLConnection;
import org.json.*;

/** Private, durable upload-only queue. Source reports are never removed. */
public final class UploadQueue {
 static final long MAX_REPORT=16L*1024*1024,MAX_QUEUE=64L*1024*1024;
 static final int MAX_PENDING=32,MAX_RECEIPTS=128;
 static final String REPORT="Voyah-FM-report-[0-9]{8}-[0-9]{6}\\.zip",HASH="[0-9a-f]{64}";
 public static final class Config {
  final String endpoint,client;private final String token;
  private Config(String e,String c,String t){endpoint=e;client=c;token=t;}
  public static Config parse(String text)throws IOException {
   try{
    if(text.length()>16384)throw new IOException();
    JSONObject o=json(text);Object e=o.get("endpoint"),c=o.get("client"),t=o.get("token");if(!(e instanceof String)||!(c instanceof String)||!(t instanceof String))throw new IOException();String endpoint=(String)e,client=(String)c,token=(String)t;URI u=new URI(endpoint);
    if(endpoint.length()>512||!"https".equals(u.getScheme())||u.getHost()==null||u.getRawUserInfo()!=null||u.getRawQuery()!=null||u.getRawFragment()!=null||!"/voyah-fm/v1".equals(u.getRawPath())||u.getPort()>65535||u.getPort()==0||!client.matches("[a-zA-Z0-9_-]{1,64}")||!token.matches("[a-zA-Z0-9_-]{32,128}"))throw new IOException();
    return new Config(endpoint,client,token);
   }catch(Exception ignored){throw new IOException("INVALID_UPLOAD_CONFIG");}
  }
  public static Config read(File file)throws IOException{return parse(readBounded(file,16384));}
 }
 private final File directory;private final Config config;private volatile String error="";
 public UploadQueue(File root,Config c)throws IOException {
  config=c;directory=new File(root,digest((c.endpoint+"\n"+c.client).getBytes("UTF-8")));
  if(!directory.isDirectory()&&!directory.mkdirs())throw new IOException("QUEUE_UNAVAILABLE");
  for(File f:list())if(f.getName().matches("\\.[a-zA-Z0-9-]+\\.partial"))f.delete();
 }
 public synchronized boolean enqueue(File report)throws IOException {
  if(!report.isFile()||!report.getName().matches(REPORT)||report.length()<1||report.length()>MAX_REPORT){error="REPORT_SIZE_OR_NAME";return false;}
  String hash=hash(report);File target=file(hash,".zip"),receipt=file(hash,".receipt.json");
  if(receipt.isFile()){
   try{ack(readBounded(receipt,8192),hash,report.length());return true;}catch(IOException ignored){receipt.delete();}
  }
  if(target.isFile())return true;
  long total=0;int count=0;for(File f:pendingFiles()){total+=f.length();count++;}
  if(count>=MAX_PENDING||total+report.length()>MAX_QUEUE){error="QUEUE_FULL";return false;}
  File temporary=new File(directory,"."+UUID.randomUUID()+".partial");
  try{
   try(InputStream in=new FileInputStream(report);FileOutputStream out=new FileOutputStream(temporary)){copy(in,out,MAX_REPORT);out.getFD().sync();}
   if(!hash.equals(hash(temporary)))throw new IOException("REPORT_CHANGED");
   atomic(file(hash,".name"),report.getName());
   if(!temporary.renameTo(target))throw new IOException("QUEUE_WRITE_FAILED");
   return true;
  }finally{temporary.delete();}
 }
 /** At most five requests per batch; the first network/receipt failure defers the rest. */
 public synchronized int flush(){
  error="";int sent=0,attempted=0;long deadline=System.nanoTime()+35000000000L;
  for(File report:pendingFiles()){
   if(attempted++>=5||System.nanoTime()>deadline||Thread.currentThread().isInterrupted())break;
   String hash=report.getName().substring(0,64);
   try{
    String name=readBounded(file(hash,".name"),256);
    if(!name.matches(REPORT)||report.length()<1||report.length()>MAX_REPORT||!hash.equals(hash(report)))throw new IOException("QUEUE_ENTRY_INVALID");
    String response=put(report,hash,name);ack(response,hash,report.length());
    atomic(file(hash,".receipt.json"),response);
    if(!report.delete())throw new IOException("QUEUE_CLEANUP_FAILED");file(hash,".name").delete();sent++;
   }catch(Exception failure){error=failure instanceof IOException&&failure.getMessage()!=null&&failure.getMessage().matches("(?:HTTP_[0-9]{3}|QUEUE_[A-Z_]+|RECEIPT_INVALID)")?failure.getMessage():"UPLOAD_DEFERRED";break;}
  }
  pruneReceipts();return sent;
 }
 public int pending(){return pendingFiles().length;}
 /** Reserve a whole maximum-size report before starting an automatic capture. */
 synchronized boolean canCaptureAutomatic(){long bytes=0;File[] files=pendingFiles();for(File f:files)bytes+=f.length();return files.length<MAX_PENDING&&bytes<=MAX_QUEUE-MAX_REPORT;}
 /** Cleanup may remove an automatic source only after verifying durable backup bytes. */
 synchronized boolean backedUp(File source){
  try{
   if(!source.isFile()||!source.getName().matches(REPORT)||source.length()<1||source.length()>MAX_REPORT)return false;
   String id=hash(source);File queued=file(id,".zip"),receipt=file(id,".receipt.json");
   if(queued.isFile()&&queued.length()==source.length()&&id.equals(hash(queued))&&readBounded(file(id,".name"),256).matches(REPORT))return true;
   if(receipt.isFile()){ack(readBounded(receipt,8192),id,source.length());return true;}
  }catch(IOException ignored){}return false;
 }
 public String lastError(){return error;}
 File file(String hash,String suffix){return new File(directory,hash+suffix);}
 File[] list(){File[] files=directory.listFiles();return files==null?new File[0]:files;}
 File[] pendingFiles(){List<File> files=new ArrayList<>();for(File f:list())if(f.isFile()&&f.getName().matches(HASH+"\\.zip"))files.add(f);File[] result=files.toArray(new File[0]);Arrays.sort(result,Comparator.comparingLong(File::lastModified).thenComparing(File::getName));return result;}
 void pruneReceipts(){List<File> files=new ArrayList<>();for(File f:list())if(f.isFile()&&f.getName().matches(HASH+"\\.receipt\\.json"))files.add(f);files.sort(Comparator.comparingLong(File::lastModified).reversed());for(int i=MAX_RECEIPTS;i<files.size();i++)files.get(i).delete();}
 String put(File report,String hash,String name)throws IOException {
  HttpsURLConnection request=(HttpsURLConnection)new URL(config.endpoint+"/reports/"+hash).openConnection();
  try{
   request.setInstanceFollowRedirects(false);request.setConnectTimeout(15000);request.setReadTimeout(15000);request.setUseCaches(false);request.setRequestMethod("PUT");request.setDoOutput(true);request.setFixedLengthStreamingMode((int)report.length());
   request.setRequestProperty("Content-Type","application/zip");request.setRequestProperty("Accept","application/json");request.setRequestProperty("Authorization","Bearer "+config.token);request.setRequestProperty("X-FM-Source","headunit");request.setRequestProperty("X-FM-Report-Name",name);
   try(InputStream in=new FileInputStream(report);OutputStream out=request.getOutputStream()){copy(in,out,MAX_REPORT);}
   int code=request.getResponseCode();if(code!=200&&code!=201)throw new IOException("HTTP_"+code);
   try(InputStream in=request.getInputStream()){return readBounded(in,8192);}
  }finally{request.disconnect();}
 }
 void ack(String response,String hash,long size)throws IOException {
  try{JSONObject a=json(response);Object bytes=a.get("bytes");if(!Boolean.TRUE.equals(a.get("ok"))||!hash.equals(a.get("sha256"))||!(config.client+"/"+hash).equals(a.get("id"))||(!(bytes instanceof Integer)&&!(bytes instanceof Long))||((Number)bytes).longValue()!=size)throw new IOException();}
  catch(Exception ignored){throw new IOException("RECEIPT_INVALID");}
 }
 static JSONObject json(String text)throws Exception{JSONTokener tokens=new JSONTokener(text);JSONObject object=new JSONObject(tokens);if(tokens.nextClean()!=0)throw new IOException("JSON_TRAILING_DATA");return object;}
 static String readBounded(File file,int max)throws IOException{try(InputStream in=new FileInputStream(file)){return readBounded(in,max);}}
 static String readBounded(InputStream in,int max)throws IOException{ByteArrayOutputStream out=new ByteArrayOutputStream();copy(in,out,max);return out.toString("UTF-8");}
 static void copy(InputStream in,OutputStream out,long max)throws IOException{byte[] b=new byte[8192];long total=0;int n;while((n=in.read(b))!=-1){if(Thread.currentThread().isInterrupted())throw new InterruptedIOException();total+=n;if(total>max)throw new IOException("SIZE_LIMIT");out.write(b,0,n);}}
 static void atomic(File target,String content)throws IOException{File temp=new File(target.getParentFile(),"."+UUID.randomUUID()+".partial");try{try(FileOutputStream out=new FileOutputStream(temp)){out.write(content.getBytes("UTF-8"));out.getFD().sync();}if(!temp.renameTo(target))throw new IOException("QUEUE_WRITE_FAILED");}finally{temp.delete();}}
 static String hash(File file)throws IOException{try{MessageDigest d=MessageDigest.getInstance("SHA-256");try(InputStream in=new FileInputStream(file)){byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1){if(Thread.currentThread().isInterrupted())throw new InterruptedIOException();d.update(b,0,n);}}return hex(d.digest());}catch(java.security.NoSuchAlgorithmException e){throw new IOException("SHA256_UNAVAILABLE");}}
 static String digest(byte[] bytes)throws IOException{try{return hex(MessageDigest.getInstance("SHA-256").digest(bytes));}catch(java.security.NoSuchAlgorithmException e){throw new IOException("SHA256_UNAVAILABLE");}}
 static String hex(byte[] bytes){StringBuilder out=new StringBuilder();for(byte b:bytes)out.append(String.format(Locale.US,"%02x",b&255));return out.toString();}
}
