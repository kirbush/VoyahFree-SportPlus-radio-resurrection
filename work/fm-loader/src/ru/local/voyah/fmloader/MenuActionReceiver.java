package ru.local.voyah.fmloader;
import android.content.*;
/** Manifest requires android.permission.DUMP; only fixed report commands are exposed. */
public final class MenuActionReceiver extends BroadcastReceiver {
 public static final String ACTION="ru.local.voyah.fmloader.REPORT_MENU";
 public void onReceive(Context c,Intent i){
  if(i==null||!ACTION.equals(i.getAction()))return;
  setResultData(ReportCoordinator.command(c,i.getStringExtra("operation")).toString());setResultCode(-1);
 }
}
