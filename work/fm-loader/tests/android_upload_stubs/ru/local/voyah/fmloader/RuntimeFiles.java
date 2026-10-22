package ru.local.voyah.fmloader;
public class RuntimeFiles {
 public static final java.util.List<String> actions=new java.util.concurrent.CopyOnWriteArrayList<>();public static volatile java.util.concurrent.CountDownLatch block;
 public static void prepare(android.content.Context c){}
 public static String run(String action)throws Exception{actions.add(action);if(action.equals("diagnostic")&&block!=null)block.await();return "ROOT_RESULT\nCRASH_TEXT_SENTINEL\nlogger alive\n";}
}
