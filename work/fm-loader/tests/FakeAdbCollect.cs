using System;
using System.IO;
using System.Text;
public class FakeAdbCollect {
 public static int Main(string[] args) {
  Console.OutputEncoding=new UTF8Encoding(false);
  string mode=Environment.GetEnvironmentVariable("FM_COLLECT_MODE")??"root";
  string trace=Environment.GetEnvironmentVariable("FM_COLLECT_CALLS");
  File.AppendAllText(trace,String.Join("|",args)+"\n",new UTF8Encoding(false));
  if(args.Length==1&&args[0]=="devices") {
   Console.WriteLine("List of devices attached");
   if(mode!="none")Console.WriteLine("FAKE123\t"+(mode=="unauthorized"?"unauthorized":"device"));
   if(mode=="multiple")Console.WriteLine("OTHER456\tdevice");return 0;
  }
  if(args.Length<3||args[0]!="-s"||args[1]!="FAKE123")return 20;
  string command=String.Join(" ",args,3,args.Length-3);
  string rooted=trace+".rooted";
  if(args[2]=="root") {
   if(mode!="adb-root"&&mode!="su-hang-adb-root")return 1;
   File.WriteAllText(rooted,"yes");Console.WriteLine("restarting adbd as root");return 0;
  }
  if(args[2]=="wait-for-device")return 0;
  if(args[2]=="shell") {
   if(command=="id -u") {Console.WriteLine(mode=="root"||mode=="transport-error"||mode=="incomplete"||File.Exists(rooted)?"0":"2000");return 0;}
   if(command=="su 0 id -u") {
    if(mode.StartsWith("su-hang"))System.Threading.Thread.Sleep(25000);
    Console.WriteLine(mode=="su"?"0":"2000");return mode=="su"?0:1;
   }
   return 21;
  }
  if(args[2]!="exec-out")return 22;
  if(!command.Contains("VOYAH_PC_DIAGNOSTIC_BEGIN"))return 23;
  bool su=command.StartsWith("su 0 sh -c ");
  if(mode=="su"&&!su||mode=="root"&&su)return 24;
  File.WriteAllText(Environment.GetEnvironmentVariable("FM_COLLECT_COMMAND"),command,new UTF8Encoding(false));
  if(mode=="transport-error") {Console.WriteLine("partial data");Console.Error.WriteLine("device disconnected");return 7;}
  Console.WriteLine("VOYAH_PC_DIAGNOSTIC_BEGIN");
  Console.WriteLine("=== DEVICE ===\nПроверка UTF-8 / 日本 / FM 106.6");
  Console.WriteLine("=== UI BEFORE ===\nmResumedActivity: radio\n=== CORE EVENTS ===\nFM_START_FAILED fixture");
  Console.WriteLine("=== FM HELPER ===\n"+(mode=="limited"?"HELPER_UNAVAILABLE_OR_DENIED":"READY serial=/dev/ttyACM0 audio_card=1"));
  Console.WriteLine("=== CRASH TEXT ===\nProcess: ru.local.voyah.fmdiagnostics\njava.lang.IllegalStateException: fixture");
  if(mode!="incomplete")Console.WriteLine("VOYAH_PC_DIAGNOSTIC_END");
  return 0;
 }
}
