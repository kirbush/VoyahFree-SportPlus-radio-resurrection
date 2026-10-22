package ru.local.voyah.fmloader;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.regex.*;
/** Client for an already-existing local maintenance channel; never opens a listener. */
public final class TelnetSession {
 public static String execute(Socket socket,String command)throws Exception {
  socket.setSoTimeout(12000);InputStream in=socket.getInputStream();OutputStream out=socket.getOutputStream();
  out.write(("\r\n"+command+"; echo __FM_RC__$?\r\n").getBytes(StandardCharsets.UTF_8));out.flush();
  ByteArrayOutputStream text=new ByteArrayOutputStream();long deadline=System.currentTimeMillis()+15000;
  while(System.currentTimeMillis()<deadline){
   int b=in.read();if(b<0)throw new EOFException("Local maintenance channel closed");
   if(b==255){int c=in.read();if(c==251||c==252||c==253||c==254){int option=in.read();if(c==251||c==253){out.write(new byte[]{(byte)255,(byte)(c==251?254:252),(byte)option});out.flush();}}else if(c==250){int prev=0,v;while((v=in.read())>=0){if(prev==255&&v==240)break;prev=v;}}else if(c==255)text.write(255);continue;}
   text.write(b);if(text.size()>262144)throw new IOException("Maintenance reply too large");
   if(b==10){String value=text.toString("UTF-8").replace("\r","");Matcher m=Pattern.compile("(?m)^__FM_RC__([0-9]+)$").matcher(value);if(m.find()){if(!m.group(1).equals("0"))throw new IOException("Bootstrap failed: "+value);return value;}}
  }
  throw new IOException("Maintenance channel did not finish activation");
 }
}
