package android.content;
import java.io.*;import java.util.*;
public class Context {
 final File files;final SharedPreferences prefs=new SharedPreferences();
 public final Map<String,ByteArrayOutputStream> downloads=new HashMap<>();public int startedActivities;
 public Context(){this(new File(System.getProperty("fm.test.context")));}
 public Context(File f){files=f;f.mkdirs();}public File getFilesDir(){return files;}public Context getApplicationContext(){return this;}
 public <T>T getSystemService(Class<T> cls){try{return cls.newInstance();}catch(Exception e){throw new RuntimeException(e);}}
 public SharedPreferences getSharedPreferences(String n,int mode){return prefs;}
 public ContentResolver getContentResolver(){return new ContentResolver(this);}
 public void startActivity(Intent i){startedActivities++;}
}
