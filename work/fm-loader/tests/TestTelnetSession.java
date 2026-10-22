import ru.local.voyah.fmloader.TelnetSession;
import java.net.*;
import java.io.*;
public class TestTelnetSession {
 static void trial(int code)throws Exception {
  try(ServerSocket server=new ServerSocket(0,1,InetAddress.getByName("127.0.0.1"))){
   Thread worker=new Thread(()->{try(Socket s=server.accept()){
    s.getOutputStream().write(new byte[]{(byte)255,(byte)251,1,(byte)255,(byte)253,24});
    s.getOutputStream().write(("echo command __FM_RC__$?\r\nBOOTSTRAP TEST\r\n__FM_RC__"+code+"\r\n").getBytes("UTF-8"));s.getOutputStream().flush();Thread.sleep(100);
   }catch(Exception e){throw new RuntimeException(e);}});worker.start();
   try(Socket s=new Socket("127.0.0.1",server.getLocalPort())){
    boolean failed=false;try{String r=TelnetSession.execute(s,"fixed-command");if(!r.contains("BOOTSTRAP TEST"))throw new AssertionError();}catch(IOException e){failed=true;}
    if(failed!=(code!=0))throw new AssertionError("exit code handling: "+code);
   }
   worker.join();
  }
 }
 public static void main(String[] args)throws Exception {trial(0);trial(81);System.out.println("PASS telnet negotiation, echoed-marker rejection, root-command status");}
}
