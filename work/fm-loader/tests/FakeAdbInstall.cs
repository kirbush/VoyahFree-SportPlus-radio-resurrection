using System;
using System.IO;
public class FakeAdbInstall {
 public static int Main(string[] args){
  string mode=Environment.GetEnvironmentVariable("FM_INSTALL_MODE")??"root";
  File.AppendAllText(Environment.GetEnvironmentVariable("FM_INSTALL_CALLS"),String.Join("|",args)+"\n");
  if(args.Length==1&&args[0]=="devices"){
   Console.WriteLine("List of devices attached");
   if(mode!="none")Console.WriteLine("FAKE123\t"+(mode=="unauthorized"?"unauthorized":"device"));
   if(mode=="multiple")Console.WriteLine("OTHER456\tdevice");return 0;
  }
  if(args.Length<3||args[0]!="-s"||args[1]!="FAKE123")return 30;
  if(args[2]=="root"){Console.WriteLine(mode=="su"||mode=="noroot"?"adbd cannot run as root in production builds":"restarting adbd as root");return mode=="su"||mode=="noroot"?1:0;}
  if(args[2]=="wait-for-device")return 0;
  if(args[2]=="install"){
   if(mode=="main-install-fail"){Console.WriteLine("Failure [INSTALL_FAILED_TEST]");return 1;}
   Console.WriteLine("Success");return 0;
  }
  if(args[2]=="push"){
   if(mode=="su"&&File.Exists(Environment.GetEnvironmentVariable("FM_INSTALL_BOOTSTRAP")+".rootstage"))return 40;
   if(args[3].EndsWith("bootstrap.sh"))File.Copy(args[3],Environment.GetEnvironmentVariable("FM_INSTALL_BOOTSTRAP"),true);
   if(args[3].EndsWith("upload.json"))File.Copy(args[3],Environment.GetEnvironmentVariable("FM_INSTALL_BOOTSTRAP")+".upload",true);
   Console.WriteLine("1 file pushed");return 0;
  }
  if(args[2]!="shell")return 31;
  int start=3;bool su=args.Length>4&&args[3]=="su"&&args[4]=="0";if(su)start=5;
  string cmd=String.Join(" ",args,start,args.Length-start);
  if(cmd=="id -u"){Console.WriteLine(mode=="noroot"||mode=="su"&&!su?"2000":"0");return 0;}
  if(cmd=="getprop ro.build.version.sdk"){Console.WriteLine(mode=="sdk"?"31":"30");return 0;}
  if(cmd=="getenforce"){Console.WriteLine(mode=="enforcing"?"Enforcing":"Permissive");return 0;}
  if(cmd=="pm path ru.local.voyah.fmdiagnostics"){
   if(mode=="diag-query-fail"){Console.Error.WriteLine("error: device offline");return 1;}
   if(mode!="fresh"&&!File.Exists(Environment.GetEnvironmentVariable("FM_INSTALL_BOOTSTRAP")+".diagremoved"))Console.WriteLine("package:/data/app/old-diagnostics/base.apk");return 0;
  }
  if(cmd=="pm uninstall ru.local.voyah.fmdiagnostics"){
   if(mode=="diag-remove-fail"){Console.WriteLine("Failure [DELETE_FAILED_INTERNAL_ERROR]");return 1;}
   if(mode!="diag-remove-still-present")File.WriteAllText(Environment.GetEnvironmentVariable("FM_INSTALL_BOOTSTRAP")+".diagremoved","removed");Console.WriteLine("Success");return 0;
  }
  if(cmd.Contains("helper.sh install-components")&&mode=="install-fail"){Console.WriteLine("Failure [INSTALL_FAILED_SHARED_USER_INCOMPATIBLE]");return 1;}
  if(cmd.Contains("helper.sh check")&&mode=="hardware-fail"){Console.WriteLine("ERROR AMBIGUOUS_USB serial_count=0");return 1;}
  if(cmd.StartsWith("sh ")){Console.WriteLine("OK");return 0;}
  if(cmd.StartsWith("mkdir ")&&mode=="su"&&su)File.WriteAllText(Environment.GetEnvironmentVariable("FM_INSTALL_BOOTSTRAP")+".rootstage","root");
  if(cmd.StartsWith("mkdir ")||cmd.StartsWith("chmod ")||cmd.StartsWith("rm ")||cmd.StartsWith("rmdir ")||cmd.StartsWith("am "))return 0;
  return 32;
 }
}
