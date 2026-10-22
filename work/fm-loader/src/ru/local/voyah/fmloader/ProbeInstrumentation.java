package ru.local.voyah.fmloader;
import android.app.Instrumentation;
import android.os.Bundle;
import java.io.File;
/** Invoked explicitly through ADB; executes as the ordinary application UID. */
public class ProbeInstrumentation extends Instrumentation {
 public void onCreate(Bundle args){super.onCreate(args);start();}
 public void onStart(){Bundle result=new Bundle();try{
  if(android.os.Process.myUid()<10000)throw new Exception("Expected ordinary app UID");
  RuntimeFiles.prepare(getTargetContext());
  result.putString("uid",String.valueOf(android.os.Process.myUid()));
  result.putString("check",RuntimeFiles.run("check"));
  result.putString("log_start",RuntimeFiles.run("log-start"));
  android.util.Log.i("DABService","FM_TESTER_RECORDING_PROBE_UID_"+android.os.Process.myUid());
  Thread.sleep(1200);
  result.putString("log_stop",RuntimeFiles.run("log-stop"));
  File report=DiagnosticReport.create(getTargetContext(),"Automated normal-UID bootstrap/log/report test");
  result.putString("report",report.getAbsolutePath());finish(-1,result);
 }catch(Exception e){result.putString("error",e.toString());finish(0,result);}}
}
