package android.content;
import java.util.*;
public class SharedPreferences {
 final Map<String,Object> values=new HashMap<>();
 public String getString(String k,String d){Object v=values.get(k);return v instanceof String?(String)v:d;}
 public boolean getBoolean(String k,boolean d){Object v=values.get(k);return v instanceof Boolean?(Boolean)v:d;}
 public Editor edit(){return new Editor();}
 public class Editor {public Editor putString(String k,String v){values.put(k,v);return this;}public Editor putBoolean(String k,boolean v){values.put(k,v);return this;}public void apply(){}public boolean commit(){return true;}}
}
