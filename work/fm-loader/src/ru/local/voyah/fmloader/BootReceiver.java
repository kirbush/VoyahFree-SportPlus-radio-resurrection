package ru.local.voyah.fmloader;
import android.content.*;
public class BootReceiver extends BroadcastReceiver {
 public void onReceive(Context c,Intent i){if(Intent.ACTION_BOOT_COMPLETED.equals(i.getAction())||Intent.ACTION_MY_PACKAGE_REPLACED.equals(i.getAction())){
  AppLog.add(c,"BOOT_EVENT",i.getAction());c.startForegroundService(new Intent(c,LoaderService.class));
 }}
}
