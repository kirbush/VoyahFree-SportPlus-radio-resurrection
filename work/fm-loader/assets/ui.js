'use strict';
const UI_VERSION='0.5.1-beta-v1';
const UI_DIR='/data/local/tmp/voyah-fm-loader-v1';
function registerDisplayObserver(original,target,observer){
  if(observer && String(observer.getClass().getName())==='com.qinggan.media.helper.utils.DisplayUtils$1'){
    let duplicate=false;
    try{duplicate=target.mObservers.value.contains(observer);}catch(error){console.log('RDS_OBSERVER_GUARD_UNAVAILABLE');}
    if(duplicate){
      if(typeof console!=='undefined')console.log('RDS_DISPLAY_OBSERVER_ALREADY_REGISTERED');
      return;
    }
  }
  return original.call(target,observer);
}
if(typeof module!=='undefined')module.exports={registerDisplayObserver};
if(typeof Java!=='undefined')Java.perform(function(){
  if(String(Java.use('android.app.ActivityThread').currentPackageName())!=='com.pateo.rdsapp')throw new Error('Wrong UI target');
  const observable=Java.use('android.database.Observable');
  const register=observable.registerObserver.overload('java.lang.Object');
  register.implementation=function(observer){return registerDisplayObserver(register,this,observer);};
  Java.openClassFile(UI_DIR+'/radio-ui.dex').load();
  const bridge=Java.use('ru.local.voyah.fmloader.ui.MenuBridge');
  Java.scheduleOnMainThread(function(){
    // Obtain every instance in this JNI callback. Do not carry local jobjects
    // across threads or scan this firmware's 32-bit ART heap with Java.choose.
    const application=Java.use('android.app.ActivityThread').currentApplication();
    bridge.install(Java.cast(application,Java.use('android.app.Application')));
    const marker=new File(UI_DIR+'/runtime/ui-ready-'+Process.id,'w');
    marker.write(UI_VERSION+'\n');marker.flush();marker.close();
    console.log('RDS_MENU_READY '+UI_VERSION);
  });
});
