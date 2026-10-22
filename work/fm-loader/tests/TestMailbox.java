package ru.local.voyah.fmloader;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.*;
public class TestMailbox {
 public static void main(String[] args)throws Exception {
  File box=new File(RuntimeFiles.DIR,"mailbox");box.mkdirs();
  final int count=8;List<Throwable> errors=Collections.synchronizedList(new ArrayList<Throwable>());
  Thread broker=new Thread(()->{try{for(int n=0;n<count;n++){
   File request=new File(box,"request");long end=System.currentTimeMillis()+3500;
   while(!request.exists()&&System.currentTimeMillis()<end)Thread.sleep(2);
   if(!request.exists())throw new IOException("Lost request");
   Thread.sleep(15);String[] parts=new String(Files.readAllBytes(request.toPath()),"UTF-8").trim().split(" ");
   request.delete();Thread.sleep(30);
   File response=new File(box,parts[0]+".reply"),temp=new File(box,"response.tmp");
   Files.write(temp.toPath(),("OK\n"+parts[1]).getBytes("UTF-8"));Files.move(temp.toPath(),response.toPath());
  }}catch(Throwable e){errors.add(e);}});broker.start();
  CountDownLatch ready=new CountDownLatch(count),go=new CountDownLatch(1);List<Thread> clients=new ArrayList<>();
  for(int n=0;n<count;n++){final String action=n%2==0?"check":"status";Thread t=new Thread(()->{try{ready.countDown();go.await();String result=RuntimeFiles.run(action);if(!action.equals(result))throw new AssertionError(action+" received "+result);}catch(Throwable e){errors.add(e);}});clients.add(t);t.start();}
  ready.await();go.countDown();for(Thread t:clients)t.join(6000);broker.join(6000);
  if(!errors.isEmpty())throw new AssertionError(errors.toString());
  for(Thread t:clients)if(t.isAlive())throw new AssertionError("Blocked client");
  Files.write(new File(RuntimeFiles.DIR,"test-boot-id").toPath(),"test-boot".getBytes("UTF-8"));
  Files.write(new File(RuntimeFiles.DIR,"payload-version").toPath(),"test".getBytes("UTF-8"));
  Files.write(new File(box,"online").toPath(),"test-boot".getBytes("UTF-8"));
  RuntimeFiles.prepare(new android.content.Context());
  if(LocalBootstrap.activations!=0)throw new AssertionError("healthy broker reactivated");
  try{RuntimeFiles.run("status");throw new AssertionError("dead broker accepted");}catch(IOException expected){}
  RuntimeFiles.prepare(new android.content.Context());
  if(LocalBootstrap.activations!=1)throw new AssertionError("stale online marker prevented recovery after timeout");
  System.out.println("PASS eight simultaneous UI/service requests receive their own replies");
  System.out.println("PASS stale broker marker recovered after request timeout");
 }
}
