using System;
using System.IO;
using System.Security.Cryptography;
public class FakeAdbExport {
 public static int Main(string[] args) {
  string mode=Environment.GetEnvironmentVariable("FM_FAKE_MODE")??"private";
  string fixture=Environment.GetEnvironmentVariable("FM_FAKE_ZIP");
  string name="Voyah-FM-report-20261022-140000.zip";
  if(args.Length>0&&args[0]=="devices"){
   Console.WriteLine("List of devices attached");
   if(mode!="none")Console.WriteLine("FAKE123\tdevice");
   if(mode=="multiple-devices")Console.WriteLine("OTHER456\tdevice");
   return 0;
  }
  if(args.Length<4||args[0]!="-s"||args[1]!="FAKE123")return 20;
  string joined=String.Join(" ",args);
  if(mode=="root-no-su"&&joined.Contains("su 0"))return 1;
  if(args[2]=="shell"){
   if(joined.EndsWith("id -u")){Console.WriteLine(mode=="root-no-su"?"0":"2000");return 0;}
   if(mode=="root-no-su"){
    if(!joined.Contains("/data/user/0/"))return 1;
    Console.WriteLine("/data/user/0/ru.local.voyah.fmloader/files/"+name);return 0;
   }
   bool root=joined.Contains("su 0");
   if(root&&mode=="public")return 1;
   if(mode=="missing")return 1;
   if(mode=="many"){
    Console.WriteLine("/data/user/0/ru.local.voyah.fmloader/files/Voyah-FM-report-20261021-140000.zip");
    Console.WriteLine("/data/user/0/ru.local.voyah.fmloader/files/Voyah-FM-report-20261022-140001.zip");
    return 0;
   }
   Console.WriteLine((root?"/data/user/0/ru.local.voyah.fmloader/files/":"/sdcard/Download/")+name);
   return 0;
  }
  if(args[2]=="exec-out"&&joined.Contains("sha256sum")){
   if(mode=="no-sha")return 1;
   if(mode=="bad-hash"){Console.WriteLine(new string('0',64)+"  file");return 0;}
   using(var sha=SHA256.Create())using(var file=File.OpenRead(fixture))Console.WriteLine(BitConverter.ToString(sha.ComputeHash(file)).Replace("-","").ToLower()+"  file");
   return 0;
  }
  if(args[2]=="exec-out"&&joined.Contains("cat")){
   if(mode=="transfer-error"){Console.Error.WriteLine("simulated transfer failure");return 7;}
   using(var file=File.OpenRead(fixture)){file.CopyTo(Console.OpenStandardOutput());}
   return 0;
  }
  return 21;
 }
}
